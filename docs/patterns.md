# Achtopus — Coordination Patterns

Four patterns, one octopus of eight arms. Each pattern is a way of wiring the same arms
through the same wire.

## 1. Orchestrator / worker (fan-out)

**Personas:** 🐙 conductor → 🔦 soloist ×N → 🖋️ scribe

```
conductor: decompose → wire/plan.md (t1..tN, marked independent)
conductor: spawn N soloists in ONE message (concurrent)
soloist ti: claim ti → work → wire/ti.result.md → status done
conductor: poll manifest; route non-trivial results to verify
scribe: synthesize accepted results
```

Use when the work splits into independent chunks. The win is parallelism + a shared
ledger so nothing is lost or duplicated.

## 2. Peer message wire (no boss)

**Personas:** 🔦 soloist ×N as peers, 🖋️ scribe keeps `manifest.md`

```
each soloist: claim a task on wire/manifest.md (claim guard prevents collisions)
peers coordinate by reading/writing the manifest — not by asking a lead
scribe: reconcile conflicts, flag overlaps, keep one source of truth
```

Use when agents are equals working a shared space and a central orchestrator would just
be a bottleneck. The manifest is the whole coordination surface.

## 3. Pipeline stages

**Personas:** 🧭 composer → 🔦/🔧 soloist/luthier → 🧐 critic (→ ✊ tuner)

```
composer: PRD/diff → ONE wire/context.md (shared grounding) + wire/cache/diff.patch (raw diff) + wire/cache/pr.json (raw PR metadata, if fetched)
soloist/luthier: do the domain's work (review end-to-end, or exercise it hands-on) → wire/<id>.result.md
critic:   coverage-gate the result against its domain's rubric → wire/<id>.coverage.md
tuner/heckler: verify the underlying claims → wire/<id>.verdict.md / .refute.md
```

The composer runs once, first, before any domain reviewer starts — it is not a per-item
stage, it is the shared brief that lets every downstream stage skip re-deriving the same
PRD read and `git diff`. Note the brief (`wire/context.md`) is a *summary* of what changed;
the actual patch text and PR metadata each downstream arm needs to cite line numbers from are
cached separately as raw bytes (`wire/cache/diff.patch`, `wire/cache/pr.json`, managed via
`bin/cache get/set/fetch`) precisely so no arm has to re-run `git diff`/`gh pr view` to get its
own copy of content that's identical across all of them — a summary alone doesn't stop that
re-fetch, since a citing reviewer still needs the literal diff. The driver itself precomputes
`diff.patch`/`changed-files.txt`/`pr.json` at $0.00 before any agent is spawned, whenever the
plan sets `base_ref` — the composer only fetches what the driver didn't already cache. The critic's coverage check is a gate on *completeness*
(did the domain answer every rubric question), separate from the tuner/heckler's gate on
*correctness* (is each answer actually true) — both must clear before synthesis.

## 4. Adversarial verify

**Personas:** ✊ tuner (confirm) + 🫳 heckler (refute), judged by 🐙 conductor

```
for each load-bearing claim:
  tuner:   try to CONFIRM by observation → HOLDS/FAILS
  heckler: try to BREAK it (different failure mode) → REFUTED/SURVIVES
  conductor: accept only if HOLDS + SURVIVES; else reject to owner
```

Use before accepting any claim that matters. Diversity is the point: the tuner and
heckler must probe *different* failure modes, not repeat each other. If the tuner returns
`INCONCLUSIVE`, the claim is **not** cleared — re-verify or mark the task `blocked`; never
accept on an inconclusive verify. For high-stakes claims, scale to an **odd** N (3/5)
verifiers and accept on strict majority (see `docs/protocol.md`).

## Composing them

The patterns nest. A typical rich run:

```
conductor decomposes (pattern 1)
  → each chunk runs the pipeline (pattern 3)
    → every load-bearing result goes through adversarial verify (pattern 4)
  → peers reconcile shared state via the manifest (pattern 2)
→ scribe synthesizes only the accepted work
```

Scale to the ask: a quick task might be one soloist + one tuner; "be thorough" earns the
full fan-out with a 3-voter adversarial pass.

## Cost & scaling to stakes

The full harness is not free, and the failure mode is spending casually. A `soloist +
tuner + heckler` triad per task means ~3 subagents per task plus the orchestrator, so a
5-task audit fans out ~15 subagents. Exact dollar attribution is hard to isolate — in the
one measured case the audit ran inside a multi-hour session doing lots of other deep work,
so the ~$26 session total reflects far more than the harness — but the shape is clear: the
cost scales with how many agents you spawn, and the subagent tier dominates. That breadth
is worth it for a security-sensitive domain where a missed evasion has real consequences;
it is *not* a sensible default for routine refactors or "audit the whole codebase" sweeps.

**Estimate on `agents × turns-per-agent × context-size`, not agent count.** A 30-agent
audit of a large monorepo ran ~6× over a naive per-agent projection: each agent took many
turns, and every turn re-sent a large repo context (~90% of the cost was cache read/write
traffic, not output). Agent count is the dial you *set*; turns × context is what actually
bills. Gate on the turns×context projection before you fan out — see the conductor's step 1b.

Levers, roughly in order of impact:

- **Right-size the fleet — exhaustive over-provisions by default.** A full triad per task
  is ~3 agents. Reserve it for high-consequence work. Low-stakes tasks want a single
  soloist, or a soloist + one verifier, or no separate verify at all. In the 30-agent run,
  the findings that actually changed the merge decision came from a handful of tasks (the
  coverage/completeness critic and the null-semantics work); most of the 3-voter quorums
  spent their budget *confirming things were clean* — reassuring but low marginal value. A
  targeted run at roughly a third of the cost would very likely have returned ~90% of the
  decision-relevant findings. Heuristic: **single-verifier by default, escalate to a
  quorum only on the two or three riskiest claims** — not uniformly. "Be thorough" is a
  request to widen *coverage of surfaces*, not to add voters to already-clean claims.
- **Keep the driving session thin.** If a human-facing session plays conductor and does the
  coordinating/summarizing inline, every such step re-bills its whole growing transcript —
  a silent, compounding cost. Run the conductor and scribe as delegated subagents with
  isolated, disposable context, and coordinate on one-line wire summaries, not full artifacts.
- **Pick the subagent model tier deliberately.** The subagent tier is where the agent
  count — and therefore most of the cost — lives, so the model you run subagents on is the
  biggest single dial. Running every soloist and verifier at the top tier (as some runs
  have) is the expensive default; consider a cheaper tier for routine soloists and
  verifiers and reserve the top tier for the orchestrator and the hardest verify/judge
  steps. This is a lever to set deliberately per run, not a fixed prescription. The persona
  frontmatter now bakes this in as the default: `composer`/`soloist`/`luthier`/`critic`/
  `scribe` (context-gathering, routine domain work, mechanical coverage checks, synthesis)
  default to `sonnet`; `conductor` (orchestration/decomposition) and `tuner`/`heckler`
  (the adversarial verify pair judging correctness of load-bearing claims) stay on `opus`
  — matching the "frontier only for genuinely difficult work, Sonnet for everyday work"
  principle from Webflow's AI-spend-discipline guidance (Slack, 2026-07-16). Note the
  frontmatter tier only takes effect when a persona is invoked directly via the Agent tool
  — `bin/run` never reads it; every task-execution persona (including the tuner/heckler
  verify pair) runs on the plan's `default_model` (or a task's own `model` field) unless
  `--model` overrides it, and `--model` moves every task uniformly, not just the verify
  pair. `--premium-model` is separate and narrower: it only sets the tier for the
  conductor's plan-authoring call and the scribe's final synthesis, never task execution
  or verify. To run the verify pair on a stronger tier *under the driver*, set `"model"`
  on the tuner/heckler-triggering tasks in the plan directly (or on all tasks via
  `--model`) — there is no flag that targets "just the hard judgment steps" today.
- **Dedup before you fan out.** Overlapping task scopes pay two agents to cover the same
  code and then cost you a manual reconcile. The conductor's pre-fanout overlap check
  (step 1a) exists to avoid this.
- **Cache is your friend, breadth is the cost.** High cache-hit (~96% observed) means the
  spend is fan-out *breadth*, not wasted re-reads — so the dial that actually moves cost is
  how many agents you spawn, not how you prompt them.
- **Keep a fan-out wave tight in wall-clock — the cache TTL is short.** Prompt caching
  expires on a short idle timeout (single-digit minutes by default). A wave whose agents are
  spawned close together shares warm cache; one that dribbles out over a long idle window
  re-pays the cache *write* for the shared prefix. The corollary matters too: don't trim the
  shared context just to save pennies — invalidating a cached prefix (cache rot) costs far
  more than the tokens you shaved. Stabilize the shared prefix, spawn each wave promptly.

Rule of thumb: if a lighter ad-hoc pass (say, a single reviewer or a 3-agent check) would
catch the same class of issue, use it. Bring all eight arms out when being
*confidently wrong* is expensive.
