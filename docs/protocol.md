# Acht Opus — Bus Protocol

The bus is the one thing the rest of the ecosystem lacks: a **greppable, agent↔agent
coordination channel** on the filesystem. No daemon, no DB. If you can `cat` it, you
know the state of the world.

## Files under `bus/`

| File | Written by | Purpose |
|---|---|---|
| `board.md` | scribe (and `bin/bus`) | The ledger — one fact per line, every task's owner + state |
| `plan.md` | composer / conductor | The shared plan: ordered steps with ids + acceptance checks |
| `<id>.result.md` | soloist / luthier | The deliverable/output for task `<id>` |
| `<id>.review.md` | critic | Ranked findings on a build |
| `<id>.verdict.md` | tuner | Verify verdict: `HOLDS` / `FAILS` / `INCONCLUSIVE` |
| `<id>.refute.md` | heckler | Refutation attempt: `REFUTED` / `SURVIVES` |
| `_archive/<stamp>/` | `bin/bus clear` | Prior performances, kept for the record |

## Task lifecycle

```
        claim              status done         tuner+heckler
  (owner set) ──► work ──► (result posted) ──► verify ──► accepted ─┐
       │                                          │                 ├─► synthesized
       └── blocked (needs help) ◄─────────────────┴─► rejected ─────┘   by scribe
```

States on the board: `claimed → done → (accepted | rejected)`. `blocked` is a stuck task
needing help. `claimed`/`done`/`accepted` are **held** (an active owner exists — do not
re-claim). `rejected`/`blocked` are **re-claimable** for reassignment.

### State semantics (last-line-wins)

The board is an append-only log, so a task's **current state is the last state line for
its id** — earlier lines are history, not the truth. A "state line" has the shape
`[<utc>] <id> <role> <state>`; free-text `post` notes use `note` and never affect state.
Id matching is **field-exact**, so `t1` never matches `t10`. `bin/bus` computes this for
you (`bus state <id>`); never hand-scan the raw log to decide current state.

### Recovery: unblock / reassign (G1)

A `blocked` or `rejected` task is not a dead end. Either:
- `bin/bus claim <id> <new-role>` — re-claims directly (logged as a reassignment), or
- `bin/bus unblock <id>` — moves it to `open` first, then claim.

The claim guard only refuses **held** states, so recovery never fights the guard.

### Id allocation & races (G2, G3)

- **Allocation.** In the orchestrator pattern the `conductor` is the sole id allocator
  (`t1..tN` in `plan.md`). In the peer pattern, the `scribe` owns id allocation on the
  board — peers request the next id from the scribe rather than both guessing `t4`.
- **Atomicity.** `bin/bus claim` takes an atomic lock (mkdir) around its read-modify-write,
  so two concurrent claimers cannot both pass the guard. Always claim via `bin/bus`, never
  by hand-appending to `board.md`.
- **Abandoned tasks.** `bin/bus stale [minutes]` lists tasks stuck in `claimed` past a
  threshold (default 30m). A stranded claim is recovered with `unblock`/re-claim after
  confirming the owner is truly dead (check with `SendMessage` first).

## The stable-id rule

Every unit of work gets a short stable id (`t1`, `t2`, … or a plan step id) that never
changes. All artifacts for that unit are named by the id (`t3.result.md`,
`t3.verdict.md`). This is what makes the bus greppable: `grep t3 bus/board.md` tells you
everything that ever happened to task 3.

## Two hard rules inherited from global CLAUDE.md

1. **Resume, don't respawn.** Before claiming a task, check the board. If it's already
   `claimed`/`done`/`accepted`, resume that owner (`SendMessage`) — never spawn a
   duplicate. `bin/bus claim` enforces this and exits non-zero on a double-claim.
2. **Never read a full result log into the orchestrator's context.** The conductor and
   scribe read board lines and one-line pointers, not raw worker transcripts. Use
   `grep`/`tail` on result files, never a blind `Read` of a long one.

## Accept/reject decision

A `done` result becomes `accepted` only when the adversarial pair clears it:

- `tuner` → `HOLDS` **and** `heckler` → `SURVIVES` → **accept**.
- Any `FAILS`/`REFUTED` on a load-bearing claim → **reject**, back to the owner.
- `tuner` → `INCONCLUSIVE` (G4): the pair has **not cleared** the claim. Do **not** accept.
  The conductor either re-verifies with a different method / a fresh tuner, or, if the claim
  can't be driven at all, marks the task `blocked` with the reason — never `accepted` on an
  inconclusive verify.

### Verification rigor tier (G6)

A verdict must state *how* it was reached, so rigor can't silently degrade from "I ran it"
to "I read it and it looks right" — especially in a repo that won't build/run locally,
where verifiers drift into static tracing without anyone noticing.

- `HOLDS(executed)` — confirmed by actually running the code / reproducing the case.
- `HOLDS(static)` — confirmed only by reading and tracing source; **no execution**.
- Same tiering for `REFUTED(executed)` vs `REFUTED(static)`.

`HOLDS(static)` is a real verdict, but a **weaker** one: the conductor may accept on it for a
low-stakes claim, but for an S1/S2-class claim it should demand `HOLDS(executed)` or escalate
(build a minimal harness, run in a sandbox, or mark `blocked` on "can't execute"). The scribe
carries the tier into the report's verification tag (`VERIFIED` requires `executed`; static-only
confirmation is `PARTIAL`). Never let a run report a wall of `HOLDS` that were all static.

### Quorum for multi-voter verify (G5)

The 2-agent pair above is the default. When a claim is important enough to warrant more
voters, fix an **odd** number `N` (3 or 5) of verifiers up front, each attacking a
*distinct* failure mode, and decide by majority:

- Accept iff a strict majority (`> N/2`) return a passing verdict (`HOLDS`/`SURVIVES`).
- Otherwise reject. There are no ties with odd `N`.
- Use one verdict vocabulary per voter (a voter is either confirming → `HOLDS`/`FAILS`, or
  refuting → `SURVIVES`/`REFUTED`); don't mix both scales inside a single "majority" count.

Note the 2-way rule is unanimity ("any `REFUTED` rejects"), which is *stricter* than
majority — that's intended: with only two voters, one credible refutation should block.

Only `accepted` work enters the scribe's final synthesis.
