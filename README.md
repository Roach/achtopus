# Acht Opus 🎼

> *Acht* — German for **eight**. An orchestra of eight Claude Code subagent personas that
> coordinate through a shared, greppable file **message bus**.

Acht Opus is a coordination framework for Claude Code. It gives eight distinct agent
personas one shared channel — the bus — so they can decompose work, hand it down a
pipeline, adversarially verify each other, and reconcile as peers, all through files you
can `cat` and `grep`.

## Why it exists (the gap)

The existing ecosystem is strong on *knowledge* and weak on *coordination*:

- **Agentflow** (`~/webflow/.agentflow`) is a deliberately orchestration-free knowledge
  harness — its manifesto says "no orchestration layers." Its agents are single-shot
  specialist reviewers that never talk to each other.
- **`slack-bus`** is a message bus, but only Claude ↔ *you* — there is no agent ↔ agent
  channel.
- Native subagent fan-out returns values to a parent, but has **no shared plan, no
  task-id ledger, and no re-synthesis contract**.
- **Adversarial verify** exists only as prose principles — never as an actual
  verifier/skeptic agent pair.

Acht Opus fills exactly those holes: a real peer channel, a task ledger, and an
adversarial pair — without re-implementing what Claude Code already does natively.

## The eight personas

| Persona | Agent | Role |
|---|---|---|
| 🎩 The Maestro | `conductor` | Orchestrator — decompose, assign, synthesize |
| 🎼 The Composer | `composer` | Pipeline 1 — turn a goal into a plan |
| 🔨 The Luthier | `luthier` | Pipeline 2 — build one planned step |
| 🎻 The Soloist | `soloist` | Worker / peer — own one task end to end |
| 📰 The Critic | `critic` | Pipeline 3 — review the build |
| 🎚️ The Tuner | `tuner` | Adversarial — confirm a claim by observation |
| 🍅 The Heckler | `heckler` | Adversarial — try to break a claim |
| ✒️ The Scribe | `scribe` | Bus keeper — maintain the board, synthesize |

Full definitions in `.claude/agents/`.

## The bus

The filesystem *is* the bus (`bus/`). No daemon, no database.

```bash
bin/bus init                    # start a performance
bin/bus claim   t1 soloist      # claim a task (atomic; guards against double-play)
bin/bus status  t1 done         # advance its state (keeps the owner's role)
bin/bus state   t1              # current state of one task (last-line-wins)
bin/bus unblock t1              # reopen a blocked/rejected task for re-claim
bin/bus board                   # read the ledger
bin/bus stale   30              # list tasks stuck in `claimed` > 30 min
bin/bus watch                   # tail for actionable state changes
bin/bus clear                   # archive and reset
```

Everything else — plans, results, reviews, verdicts — is a markdown file named by the
task's stable id (`t1.result.md`, `t1.verdict.md`). See `docs/protocol.md`.

## The four patterns

Orchestrator/worker · peer message bus · pipeline stages · adversarial verify — and how
they nest — are documented in `docs/patterns.md`.

## Using it

From a Claude Code session in this directory, invoke a persona and let it drive the bus:

```
> Use the conductor to research X: decompose it, fan out soloists, verify with the
  tuner/heckler pair, and have the scribe synthesize the result.
```

The personas read `docs/protocol.md` and `bus/board.md` to coordinate. To make them
available in other projects, symlink `.claude/agents/*.md` into that project's
`.claude/agents/` (or into `~/.claude/agents/` for every session).

## Design rules it inherits

- **Resume, don't respawn** — check the board before claiming; the claim guard enforces it.
- **Keep raw logs out of the orchestrator's context** — read board lines, not transcripts.
- **Only `accepted` work ships** — nothing enters synthesis until the adversarial pair clears it.
- **Extend, don't replace** — for webflow/PR-stack work, defer to Agentflow; for human
  steering, layer on `slack-bus`.
