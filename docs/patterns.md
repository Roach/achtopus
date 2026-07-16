# Acht Opus — Coordination Patterns

Four patterns, one orchestra of eight. Each pattern is a way of wiring the same personas
through the same bus.

## 1. Orchestrator / worker (fan-out)

**Personas:** 🎩 conductor → 🎻 soloist ×N → ✒️ scribe

```
conductor: decompose → bus/plan.md (t1..tN, marked independent)
conductor: spawn N soloists in ONE message (concurrent)
soloist ti: claim ti → work → bus/ti.result.md → status done
conductor: poll board; route non-trivial results to verify
scribe: synthesize accepted results
```

Use when the work splits into independent chunks. The win is parallelism + a shared
ledger so nothing is lost or duplicated.

## 2. Peer message bus (no boss)

**Personas:** 🎻 soloist ×N as peers, ✒️ scribe keeps `board.md`

```
each soloist: claim a task on bus/board.md (claim guard prevents collisions)
peers coordinate by reading/writing the board — not by asking a lead
scribe: reconcile conflicts, flag overlaps, keep one source of truth
```

Use when agents are equals working a shared space and a central orchestrator would just
be a bottleneck. The board is the whole coordination surface.

## 3. Pipeline stages

**Personas:** 🎼 composer → 🔨 luthier → 📰 critic (→ 🎚️ tuner)

```
composer: goal → bus/plan.md (ordered steps + acceptance checks)
luthier:  build one step → run acceptance check → bus/<step>.result.md
critic:   review the diff → bus/<step>.review.md
tuner:    (if findings) verify each → bus/<step>.verdict.md
```

Stages flow per-item: step 2 can be building while step 1 is in review. Use for
plan → build → review → verify work with clear handoffs.

## 4. Adversarial verify

**Personas:** 🎚️ tuner (confirm) + 🍅 heckler (refute), judged by 🎩 conductor

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
  → peers reconcile shared state via the board (pattern 2)
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

Levers, roughly in order of impact:

- **Right-size the fleet.** A full triad per task is ~3 agents. Reserve it for
  high-consequence work. Low-stakes tasks want a single soloist, or a soloist + one
  verifier, or no separate verify at all. The conductor sizes this per task — don't
  reflexively fan out a triad for everything.
- **Pick the subagent model tier deliberately.** The subagent tier is where the agent
  count — and therefore most of the cost — lives, so the model you run subagents on is the
  biggest single dial. Running every soloist and verifier at the top tier (as some runs
  have) is the expensive default; consider a cheaper tier for routine soloists and
  verifiers and reserve the top tier for the orchestrator and the hardest verify/judge
  steps. This is a lever to set deliberately per run, not a fixed prescription.
- **Dedup before you fan out.** Overlapping task scopes pay two agents to cover the same
  code and then cost you a manual reconcile. The conductor's pre-fanout overlap check
  (step 1a) exists to avoid this.
- **Cache is your friend, breadth is the cost.** High cache-hit (~96% observed) means the
  spend is fan-out *breadth*, not wasted re-reads — so the dial that actually moves cost is
  how many agents you spawn, not how you prompt them.

Rule of thumb: if a lighter ad-hoc pass (say, a single reviewer or a 3-agent check) would
catch the same class of issue, use it. Bring the full orchestra out when being
*confidently wrong* is expensive.
