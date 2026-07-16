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
