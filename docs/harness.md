# Acht Opus — Do we need a harness?

Short answer: **yes — but only for the half of the framework that prose can't enforce.**
The field evals split the recurring failures cleanly into two buckets, and only one of
them is a harness problem.

## What the data says

The measured 30-agent run cost **≈$401 total**, and the single most expensive participant
was not any worker — it was the **driving session acting as conductor: $87.77, ~22% of the
whole run.** That thread alone out-produced all 30 subagents combined:

| Bucket | Cost | Why |
|---|---|---|
| Conductor output tokens | $43.50 | ~580K tokens of running summaries / play-by-play prose |
| Conductor cache **read** | $27.43 | ~18.3M tokens of its own transcript re-sent across 173 turns |
| Conductor cache **write** | $16.83 | growing context (peaked ~189K) re-cached each turn |

The bus did its job: raw worker results stayed out of the conductor's context (uncached
input ≈0). But the bus only solves **result bloat**. It does nothing about
**coordination-turn bloat** — the cost of an LLM sitting in the loop, re-sending its whole
accumulated narration on every single agent event.

### The structural root

**Acht Opus, as pure markdown personas, puts an LLM conductor in the hot loop.** Every
agent completion is an LLM turn. Every LLM turn re-bills the conductor's whole (and
growing) context and emits fresh summarizing prose. Cost therefore scales with
`agents × turns × context-size`, and the conductor's context is the term that grows
without bound over a long run. No amount of persona wording fixes this — a thing told to
"stay thin" still pays a full turn to say so.

## The split: judgment vs. enforcement

**Judgment / quality gaps — prose handles these.** They're about *what a smart agent
should decide*, and a well-written persona or template genuinely moves the needle:
- surface-coverage vs. overlap thinking (conductor step 1a)
- executed-vs-static verification rigor (tuner tier / protocol G6)
- diverse adversarial failure modes (heckler)
- honest severity + verification tags in the report (report-template)

These stay as markdown. They already improved run-over-run.

**Enforcement gaps — prose demonstrably does NOT hold these.** Each is a rule an agent can
read, agree with, and then violate anyway, because nothing mechanical stops it:
- **Budget.** "Gate on projected cost" is advice; the $401/6×-overrun run had that advice
  and blew through anyway. A budget is only real if something *refuses to spawn* past it.
- **Worktree isolation.** "Don't `gh pr checkout` in a shared tree" is advice; the
  collision still happened. Isolation is only real if each agent is *handed* its own tree.
- **Verdict gating.** "Accept only on HOLDS+SURVIVES" is advice a tired conductor can
  fudge. A gate is only real if accept/reject is *computed from the verdict files*, not
  narrated.
- **The conductor-in-hot-loop cost itself.** "Stay thin" is advice a token-billed LLM
  can't honor — the only real fix is to *not have an LLM in the coordination loop at all*.

Enforcement gaps need a **driver**, not better wording.

## The design: take the conductor out of the LLM loop

The fix is to make **coordination deterministic code** and reserve LLM agents for the work
that actually needs judgment (soloist, luthier, tuner, heckler, critic, scribe). The
driver does the parts that are pure control flow — fan-out, poll the bus, apply the
accept/reject gate, sequence stages, enforce the budget — and *none of that costs an LLM
turn*. There is no growing narration context because the coordinator isn't a language
model.

What the driver owns (deterministic, ~zero token cost):
1. **Spawn** N workers from the plan, each in its **own git worktree** automatically.
2. **Poll** the bus / collect structured results — no LLM summarizing between events.
3. **Gate** programmatically: read the `HOLDS/FAILS` + `SURVIVES/REFUTED` verdict files,
   apply the quorum rule in code, mark accepted/rejected. No conductor prose per finding.
4. **Budget governor:** track spend; refuse to spawn once projected `agents×turns×context`
   would breach the ceiling. A hard stop, not a suggestion.
5. **Hand only accepted work to the scribe** for the one genuinely-LLM synthesis step.

What stays LLM (judgment, unchanged): the workers and verifiers themselves, and the final
synthesis. The personas become the *roles the driver spawns*, not a hand-run loop.

This is exactly the shape of a deterministic orchestration primitive (a driver script over
the Agent SDK, or a workflow engine): a `pipeline`/`parallel` control loop in code,
subagents spawned as leaves with structured-output schemas for the gate, a token budget
that actually throttles, and per-agent worktree isolation as a built-in — not a rule
someone has to remember.

## Recommendation

1. **Keep the 8 personas as the judgment layer** — they're working and cheap to iterate.
2. **Build a thin deterministic driver** (`bin/run` over the Agent SDK, or a workflow
   script) that replaces the hand-run conductor loop with code: budget governor,
   automatic per-agent worktree, programmatic verdict/quorum gate, and a coordination loop
   with **no LLM in it**. The conductor persona shrinks to "author the plan"; the *running*
   of the plan becomes deterministic.
   - **If you keep an LLM conductor for now (cheaper to reach):** two partial levers recover
     much of the $88 without the full driver. (a) **Run the conductor on a cheaper tier
     (Haiku/Sonnet)** — it routes and gates, it doesn't do deep judgment; ~$44 of Opus
     *output* for coordination is overkill. (b) **Batch-collect per wave, narrate tersely** —
     poll the board once per fan-out wave instead of emitting play-by-play on every
     completion; most of the $43.50 output was human-visibility prose that an unattended run
     doesn't need. These are stopgaps — they shrink the LLM-in-loop cost; only the driver
     removes it.
3. **Measure the same audit both ways.** The prediction is that the ~$88 conductor line
   collapses toward the cost of the plan-authoring call plus one scribe synthesis — the
   173 turns of re-billed narration simply stop existing.

The bus was the right first primitive; it removed result bloat. The driver is the second:
it removes the LLM coordinator that the bus can't touch.

## Prototype status

`bin/run <plan.json>` implements this design (stdlib Python, no deps). It reads a JSON plan,
fans out the personas via `claude -p` (persona body as the system prompt), captures each
agent's `total_cost_usd`, and does the coordination in code:

- **Budget governor** — refuses to spawn once `spend + est_agent_usd` would breach
  `budget_usd`. Verified: with a tiny budget, later tasks are skipped and a task whose
  verifiers get starved falls to **INCONCLUSIVE → not accepted** — running out of money
  fails *safe*, never silently accepts unverified work.
- **Programmatic gate** — `decide()` parses the `HOLDS/FAILS/INCONCLUSIVE` (+executed/static
  tier) and `SURVIVES/REFUTED` verdict files and applies the protocol rules (pair =
  unanimity, quorum = strict majority, INCONCLUSIVE never accepts) with no LLM in the
  decision.
- **Worktree isolation** — a task with `"isolate": true` and a plan `target_repo` runs in
  its own `git worktree`, handed to the agent, not left to a prose rule.
- **Board ownership** — only the driver writes the board (`bin/bus status`); agents write
  their own artifact to an absolute bus path and do no coordination.

- **Plan authoring is the only coordination LLM call.** `bin/run --goal "<what to do>"`
  spawns the `conductor` once to author `bus/plan.json` (against a strict, driver-injected
  JSON contract — surface inventory, right-sized verify, a budget from its projection), then
  validates and executes it deterministically. Everything after the plan is code. This closes
  the loop: the expensive 173-turn narrating conductor is replaced by a single plan-authoring
  call plus one scribe synthesis. Malformed plans are rejected up front by `validate_plan()`
  (unknown persona, dup id, bad verify mode), never mid-run.

Run `bin/run examples/plan.example.json --dry-run` to exercise the whole control flow
(accept / reject / auto-accept / budget-skip) with stubbed agents at zero API cost, or
`bin/run --goal "<task>" --dry-run` to have the conductor author a real plan and then
simulate its execution for free. The live path needs the local `claude` CLI. Remaining work
before production: stream per-wave progress and persist a machine-readable run ledger.
