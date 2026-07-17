# Achtopus — Do we need a harness?

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

The wire did its job: raw worker results stayed out of the conductor's context (uncached
input ≈0). But the wire only solves **result bloat**. It does nothing about
**coordination-turn bloat** — the cost of an LLM sitting in the loop, re-sending its whole
accumulated narration on every single agent event.

### The structural root

**Achtopus, as pure markdown personas, puts an LLM conductor in the hot loop.** Every
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
driver does the parts that are pure control flow — fan-out, poll the wire, apply the
accept/reject gate, sequence stages, enforce the budget — and *none of that costs an LLM
turn*. There is no growing narration context because the coordinator isn't a language
model.

What the driver owns (deterministic, ~zero token cost):
1. **Spawn** N workers from the plan, each in its **own git worktree** automatically.
2. **Poll** the wire / collect structured results — no LLM summarizing between events.
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
     poll the manifest once per fan-out wave instead of emitting play-by-play on every
     completion; most of the $43.50 output was human-visibility prose that an unattended run
     doesn't need. These are stopgaps — they shrink the LLM-in-loop cost; only the driver
     removes it.
3. **Measure the same audit both ways.** The prediction is that the ~$88 conductor line
   collapses toward the cost of the plan-authoring call plus one scribe synthesis — the
   173 turns of re-billed narration simply stop existing.

The wire was the right first primitive; it removed result bloat. The driver is the second:
it removes the LLM coordinator that the wire can't touch.

## Prototype status

`bin/run <plan.json>` implements this design (stdlib Python, no deps). It reads a JSON plan,
fans out the personas via `claude -p` (persona body as the system prompt), captures each
agent's `total_cost_usd`, and does the coordination in code:

- **Budget governor** — refuses to spawn once `spend + reserved_estimate(...)` would breach
  `budget_usd`. Verified: with a tiny budget, later tasks are skipped and a task whose
  verifiers get starved falls to **INCONCLUSIVE → not accepted** — running out of money
  fails *safe*, never silently accepts unverified work.
  - **Adaptive per-call-kind reservation.** The plan's flat `est_agent_usd` is only a
    *starting* guess — real costs vary a lot by stage (a critic coverage-gate call often
    runs under $1; a domain soloist result call can run $1-3), and a pessimistic flat
    estimate reserves 3-4x more than most calls actually cost, starving later-dispatched
    work even when real spend stays well under budget. `reserved_estimate()`/
    `record_actual_cost()` track a running average **per call kind**
    (`"result"|"coverage"|"verify"`, stored in `spend["kinds"]`) and switch a kind over to
    `max(its own running average × 1.5, $0.05)` after just one real sample of that kind —
    tracked per kind rather than globally so an expensive result-stage average doesn't drag
    up the reservation for cheap coverage/verify calls, and trusted after one sample rather
    than several so it matures fast even when 6 domain tasks dispatch simultaneously the
    moment `brief` (the only task with no dependencies) clears. Live-canary validated:
    baseline flat-estimate run (4 accepted/2 rejected/3 skipped, $17.01/$20) → a
    single-global-average first attempt that made starvation *worse* (4/4/1, $19.01) →
    the per-kind fix (5/2/2, $19.72), recovering past the baseline.
  - **Spend resets per invocation, not per plan.** `bin/run` starts every invocation's
    `spend`/adaptive averages at $0, and idempotent reruns (below) skip real dispatch for
    already-`accepted`/`rejected` tasks entirely — so a top-up rerun at a higher
    `--budget` only pays for the tasks a prior run's governor actually skipped, not the
    prior run's full spend plus the new ceiling.
- **Idempotent reruns** — `wire/.run_state.json` records each task's outcome + a content
  fingerprint. Rerunning the same `plan.json` (without `--fresh`) reuses every already-
  `accepted`/`rejected` task for free and only re-dispatches tasks that were
  `budget-skipped`/`dep-skipped`/`scope-blocked` (nothing real ran for those) or whose
  task content changed since its last verdict (fingerprint mismatch). This is what makes
  "rerun at a higher budget to finish what the governor cut off" cheap: a run capped at
  $25 that left 2 of 9 tasks budget-skipped, rerun with `--budget 30` and no `--fresh`,
  cost **$2.45** — only the 2 unresolved tasks' real work, not a fresh 9-task pass.
  `--dry-run` bypasses this (it treats every task as unresolved so the whole control flow
  can be exercised for free) — note this means a `--dry-run` invocation overwrites
  `wire/<id>.result.md` for every task with dry-run stub text, including tasks a prior
  *real* run had already resolved; don't run `--dry-run` against a `wire/` you want to keep.
- **Stale base-ref guard** — `precompute_context_cache()`'s zero-cost diff precompute tries
  each `base_ref` candidate in order and skips one whose diff exceeds
  `MAX_PRECOMPUTE_DIFF_BYTES` (5MB) rather than trusting it. A months-stale local
  remote-tracking branch (e.g. an unfetched `origin/main`) can still resolve a merge-base
  successfully while producing a diff of the *entire* intervening history instead of the
  actual PR change — caching that as ground truth is worse than caching nothing, since
  every downstream persona would review the wrong thing. Set a plan's `base_ref` explicitly
  (e.g. `origin/dev`) when a repo's default branch isn't `main`/`master`.
- **Programmatic gate** — `decide()` parses the `HOLDS/FAILS/INCONCLUSIVE` (+executed/static
  tier) and `SURVIVES/REFUTED` verdict files and applies the protocol rules (pair =
  unanimity, quorum = strict majority, INCONCLUSIVE never accepts) with no LLM in the
  decision.
- **Worktree isolation** — a task with `"isolate": true` and a plan `target_repo` runs in
  its own `git worktree`, handed to the agent, not left to a prose rule. A plan's own
  `target_repo` is untrusted (a hand-authored or `--goal`/conductor-authored `plan.json` could
  otherwise point isolation's `git -C <target_repo> worktree add` at an arbitrary path) — it's
  only honored if it matches the human-supplied `--target-repo` CLI flag exactly; otherwise
  isolation is disabled for that run rather than trusting the plan.
- **Manifest ownership (driver mode only)** — under `bin/run`, only the driver writes the
  manifest (`bin/wire status`); agents write their own artifact to an absolute wire path and
  do no coordination. This supersedes `docs/protocol.md`'s file table and the `scribe`
  persona's own stated manifest-keeping duty, which describe **hand-run mode** (no driver,
  personas run via the Agent tool and coordinate through the wire themselves) — the two modes
  have different owners for the same file by design; see the `conductor` persona's
  plan-authoring-vs-hand-run split for the same distinction.

- **Plan authoring is the only coordination LLM call.** `bin/run --goal "<what to do>"`
  spawns the `conductor` once to author `wire/plan.json` (against a strict, driver-injected
  JSON contract — surface inventory, right-sized verify, a budget from its projection), then
  validates and executes it deterministically. Everything after the plan is code. This closes
  the loop: the expensive 173-turn narrating conductor is replaced by a single plan-authoring
  call plus one scribe synthesis. Malformed plans are rejected up front by `validate_plan()`
  (unknown persona, dup id, bad verify mode), never mid-run.

### Two design notes from the wider ecosystem

- **Leaf agents get real tools; scope them tight.** A known limitation of *in-session*
  subagents (spawned via the built-in Agent tool) is that they can be cut off from MCP
  server tools and restricted to file/bash. `bin/run` sidesteps this by spawning each leaf
  as its own `claude -p` process, which carries its own tool/MCP config. The flip side —
  exposing *all* tools to a worker causes decision paralysis and token waste — is why each
  persona's `tools:` list in `.claude/agents/*.md` is deliberately narrow (the tuner/heckler
  get read/exec tools, not Write-everything). Keep new personas scoped.
- **Model tier is now baked into the persona frontmatter, not left uniform** — but `bin/run`
  doesn't read that frontmatter field; it only applies when a persona is invoked directly via
  the Agent tool outside the driver. See `docs/patterns.md`'s "Pick the subagent model tier
  deliberately" lever for the actual tiers, what `--model`/`--premium-model`/a task's own
  `model` field each do (and don't) reach under the driver, and the rationale.

Run `bin/run examples/plan.example.json --dry-run` to exercise the whole control flow
(accept / reject / auto-accept / budget-skip) with stubbed agents at zero API cost, or
`bin/run --goal "<task>" --dry-run` to have the conductor author a real plan and then
simulate its execution for free. The live path needs the local `claude` CLI. Remaining work
before production: stream per-wave progress and persist a machine-readable run ledger.
