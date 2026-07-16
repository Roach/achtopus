# Acht Opus 🎼

> *Acht* — German for **eight**. An orchestra of eight Claude Code subagent personas that
> coordinate through a shared, greppable file **message bus**.

Acht Opus is a coordination framework for Claude Code. It gives eight distinct agent
personas one shared channel — the bus — so they can decompose work, hand it down a
pipeline, adversarially verify each other, and reconcile as peers, all through files you
can `cat` and `grep`.

## Mission

**Give Claude Code a coordination layer that is legible, adversarial, and boring on
purpose.**

Acht Opus lets several agents work on one problem the way a small, disciplined team does:
work is decomposed and owned, results are handed off through a shared record, claims are
challenged before they are believed, and one voice writes the final answer. The whole
apparatus is eight agent personas and a pile of markdown files you can `cat`. There is no
daemon, no database, no bespoke protocol server — coordination state is human-readable text
on disk, so a person (or any agent) can always see who is doing what, what was accepted, and
why.

The framework optimizes for **trust in the output**, not throughput. Its central bet: the
failure mode of multi-agent systems is not "too slow" but "confidently wrong and impossible
to audit" — so every mechanism here exists to make coordination inspectable and to make
unverified claims fail closed.

## The problem

Claude Code can already spawn subagents and run tools in parallel. What it lacks is a
**shared, durable, agent-to-agent coordination medium** and a **structural discipline for
believing results**. That gap produces four recurring failures.

1. **Agents can't talk through a shared record.** Native subagent fan-out returns a value to
   the *parent* and nowhere else. Two workers on the same problem have no common surface to
   read or write — no shared plan, no ledger of who owns what, no place to flag a conflict.
   Parallel agents duplicate work, silently diverge, or drop results, and no one can
   reconstruct what happened.
2. **"Done" is asserted, never verified.** Adversarial checking tends to exist only as prose
   advice — "verify carefully," review checklists — with no structural pair that actually
   tries to *confirm* and *break* a claim before it is accepted. A plausible-but-wrong
   result, the most dangerous output an agent produces, sails through because nothing is
   charged with attacking it.
3. **Coordination state is invisible and lossy.** When orchestration lives inside a parent
   agent's context window, it evaporates on compaction, can't be grepped, and can't be
   handed to a fresh session — exactly when a long or failed run makes "what was decided and
   why" most urgent.
4. **Recovery is undefined.** Real runs have agents that die mid-task, claims that can't be
   settled, and tasks that need reassigning. Without an explicit lifecycle, a system either
   wedges (a dead owner strands its task forever) or papers over failure by spawning
   duplicates.

Acht Opus answers each with a concrete mechanism: a **file message bus** (the shared
record), an **adversarial-verify pair** (confirm + refute before accept), **eight legible
personas** (one per coordination primitive), and an **explicit task lifecycle with
recovery** (claim, block, unblock, reassign, reap) — without re-implementing what Claude
Code already does natively.

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

## What success looks like

1. **Auditability** — for any run, a person can open `bus/` and reconstruct who did what,
   what was challenged, what was accepted, and why, without reading a single agent transcript.
2. **Fail-closed correctness** — no claim reaches the final synthesis without surviving an
   independent attempt to break it. An inconclusive verify blocks; it never defaults to accept.
3. **No lost or duplicated work** — the claim guard and shared ledger make double-claims and
   dropped results structurally hard, and stranded tasks are recoverable rather than terminal.
4. **It eats its own dog food** — the framework can run its full loop against its own codebase
   and surface real defects. (It has: two self-audit rounds found and fixed eleven issues in
   v1 and three more in v2, each confirmed by the adversarial pair.)

## Non-goals

- **Not a replacement for native subagent spawning or parallel tool calls.** Acht Opus adds
  the shared channel and the verify gate that native execution lacks; it does not re-wrap
  what Claude Code already does well.
- **Not a general workflow engine or scheduler.** No DAG runtime, no retry service, no cron.
  The bus is a record and a protocol, not an execution platform.
- **Not built for raw throughput.** Where speed and trust conflict, it chooses trust: an
  extra verification pass over a faster unverified answer, every time.

## Design rules it inherits

- **Resume, don't respawn** — check the board before claiming; the claim guard enforces it.
- **Keep raw logs out of the orchestrator's context** — read board lines, not transcripts.
- **Only `accepted` work ships** — nothing enters synthesis until the adversarial pair clears it.
- **Compose, don't absorb** — layer on other tools (e.g. a human-in-the-loop chat bus) rather
  than reimplementing them; Acht Opus fills the agent↔agent coordination gap, not everything.
