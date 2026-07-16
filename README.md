# 🐙 Achtopus

> An **AI Production Readiness Review** for Claude Code — an evidence-gated, adversarial
> launch gate. Eight arms, one review: *acht* (eight) subagent personas review a change across
> every readiness domain, try to break their own findings, and return a **GO /
> GO-WITH-CONDITIONS / NO-GO** verdict you can audit line by line.

Achtopus runs a **Production Readiness Review (PRR)**: before a change ships, it fans out
specialized reviewers across the domains that decide whether a service is safe to launch —
observability, rollback safety, dependencies, data migrations, security, capacity, on-call —
adversarially verifies each finding, and synthesizes a scored launch-readiness report. The
whole review is the octopus's eight arms coordinating through a shared, greppable file
**wire**, so a human can always reconstruct what was checked, what was challenged, and why the
gate opened or held.

<img width="700" alt="achtopus" src="https://github.com/user-attachments/assets/08a7c493-c86a-48cb-8fc4-de3430355274" />


## Why a PRR needs this

A production readiness review is only as good as the honesty of its checks, and the usual
failure modes are structural — not something a longer checklist fixes:

1. **Checkboxes get ticked without proof.** "Rollback tested ✅" is asserted, not
   demonstrated. A review that trusts the box is theater. Achtopus requires each pass to
   log real proof-of-work — a command run, an output observed — or it does not count as
   verified.
2. **Reviews miss what isn't in the diff.** Launch risks hide in the surfaces the change
   *doesn't* touch — an export path, an async job, a downstream consumer. A reviewer reading
   only the PR can't see them. Achtopus starts from a **domain inventory** and assigns an
   owner to every readiness surface, so an unowned surface is a visible gap, not a silent one.
3. **"Ready" is a vibe, not a verdict.** Go/no-go often comes down to whoever is loudest in
   the room. Achtopus produces a per-domain scorecard (✅ / ⚠️ / 🔴) and a fail-closed rule
   — **no red at launch** — with every rating traceable to evidence on the wire.
4. **The reasoning evaporates.** When the review lives in a chat thread or a parent agent's
   context, it can't be grepped, handed off, or reconstructed after the fact — exactly when a
   post-incident review needs it most. Here the whole review is markdown files you can `cat`.

Achtopus answers each with a concrete mechanism: a **domain rubric** (what a PRR must
cover), an **adversarial-verify pair** (confirm + refute before a domain is cleared), an
**evidence gate** (a pass must log proof, not a claim), and a **fail-closed verdict** (an
unverified or red domain never silently passes).

## What it produces

A launch-readiness report: a top-line **GO / GO-WITH-CONDITIONS / NO-GO**, a per-domain
scorecard with ✅/⚠️/🔴 ratings and evidence, ranked launch blockers, tracked conditions,
and an honest coverage statement (what was verified vs. what still needs a human). See
`docs/report-template.md`; the methodology and the domain rubric are in `docs/prr.md`.

## The review, eight arms

The engine is the octopus's eight arms — Claude Code subagent personas that coordinate
through a shared file wire with no central brain micromanaging each move. Each arm owns its
domain and stays in sync through the wire, the way a real octopus's arms each carry their own
neurons and coordinate through a shared medium rather than a single controller.

| Display name | Agent | Role in a PRR |
|---|---|---|
| 🎯 The Helm | `conductor` | Inventory the readiness domains, assign one arm each, own the budget and gate the verdict |
| 🧭 The Surveyor | `composer` | Read the PRD/diff once and write the one shared context brief every arm reads |
| 🔧 The Prober | `luthier` | Exercise a domain hands-on (run the rollback, trip the alert) |
| 🔦 The Scout | `soloist` | Review one domain end to end and post findings |
| 🧐 The Critic | `critic` | Gate rubric coverage — did the domain answer every A–K question before verify runs |
| ✊ Grip | `tuner` | Confirm a finding — grip it and try to hold it up (independent observation) |
| 🫳 Release | `heckler` | Refute a finding — try to make it let go (a different failure mode) |
| 🖋️ The Ink | `scribe` | Keep the manifest; write the launch-readiness verdict — the ink the octopus leaves behind |

Full definitions in `.claude/agents/`.

## The domains it reviews

Observability · alerting & on-call · reliability/SLOs · capacity & scale · rollout, deploy
safety & rollback · dependencies & failure modes · data integrity & migrations · security &
privacy · operational docs & runbooks · cost — plus the organizational launch-gate artifacts.
Each domain carries concrete, checkable questions and is tagged by how far an agent can take
it (**agent-verifiable** from code/config, **mixed**, or **human sign-off**). Full rubric in
`docs/prr.md`.

## Running a review

Deterministic driver (recommended) — one plan-authoring call, then the review runs itself:

```bash
bin/run --goal "PRR for <service/change>: review it for launch readiness" --budget 5.00
```

The conductor authors a `plan.json` whose tasks are the readiness domains; the driver fans
out the reviewers, enforces the budget, gates accept/reject in code (evidence required to
pass), and hands the cleared results to the scribe for the verdict. Everything after the plan
is deterministic — no LLM narrating in the coordination loop. A task that reads another
task's result (`depends_on`, or auto-inferred from its prompt) has its dispatch held until
that dependency actually posts, so domain reviews and their verifiers never race ahead of the
work they're reading. See `docs/harness.md`. Try it free:
`bin/run examples/prr-plan.example.json --dry-run`.

Or drive it from a Claude Code session:

```
> Use the conductor to run a PRR on <change>: inventory the readiness domains, fan out a
  reviewer per domain, verify findings with the tuner/heckler pair, and have the scribe
  write the GO/NO-GO report.
```

To make the personas available as native subagent types (rather than hand-injecting their
markdown), install the defs once:

```bash
bin/install                 # symlink into ~/.claude/agents (every session)
bin/install /path/to/proj   # symlink into one project's .claude/agents
bin/install --uninstall     # remove them
```

## The wire

The filesystem *is* the coordination record (`wire/`). No daemon, no database — if you can
`cat` it, you know the state of the review.

```bash
bin/wire init                # start a review
bin/wire claim   d1 soloist  # claim a domain (atomic; guards double-review)
bin/wire status  d1 done     # advance its state (keeps the owner's role)
bin/wire manifest            # read the ledger
bin/wire stale   30          # list domains stuck in `claimed` > 30 min
bin/wire clear               # archive and reset
```

Every artifact — plan, per-domain findings, verdicts, refutations — is a markdown file named
by the domain's stable id (`d1.result.md`, `d1.verdict.md`). See `docs/protocol.md`.

## What "good" looks like

1. **Auditability** — for any review, a person can open `wire/` and reconstruct which domains
   were checked, what was challenged, what cleared, and why the gate opened, without reading a
   single agent transcript.
2. **Fail-closed gating** — no domain is marked ready without surviving an independent attempt
   to break the finding. An inconclusive or evidence-free pass blocks; it never defaults to green.
3. **No lost or duplicated review** — the claim guard and shared ledger make double-reviews
   and dropped findings structurally hard; a stranded domain is recoverable, not terminal.
4. **Honest coverage** — the report states plainly what an agent verified vs. what still needs
   human sign-off. It augments the launch gate; it does not fake the human parts.

## Non-goals

- **Not a rubber stamp.** Where speed and trust conflict it chooses trust — an extra
  verification pass over a faster green light, every time. A red domain blocks.
- **Not a replacement for the human gate.** It automates the code/config-verifiable domains
  and drafts the rest; on-call staffing, threat-model adequacy, and final sign-off remain
  human. It checks that those artifacts *exist and are wired*, never that they are *sufficient*.
- **Not a general workflow engine or scheduler.** No DAG runtime, no cron. The wire is a review
  record and a protocol, not an execution platform.
- **Not tied to one org's checklist.** The public rubric is the industry-standard PRR; specific
  org criteria are configuration layered on top, never baked in.

## Under the hood

The review engine is a general multi-agent coordination framework — orchestrator/worker,
peer message wire, pipeline stages, and adversarial verify (`docs/patterns.md`), driven by a
deterministic harness with a budget governor and a programmatic evidence gate
(`docs/harness.md`, `docs/protocol.md`). The PRR is what it's *for*; the engine is how it
stays trustworthy and cheap.
