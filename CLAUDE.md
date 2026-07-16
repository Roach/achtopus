# Achtopus — session instructions

This repo is a Claude Code multi-agent coordination framework. When working *inside* it:

- The eight agent personas live in `.claude/agents/` (conductor, composer, luthier,
  soloist, critic, tuner, heckler, scribe). Invoke them via the Agent tool by name.
- Coordination happens through the **file bus** in `bus/`. Read `docs/protocol.md` for the
  file schema and task lifecycle, and `docs/patterns.md` for the four coordination patterns.
- Drive the board with `bin/bus` (`init`, `claim`, `status`, `board`, `watch`, `clear`).
- `bin/run <plan.json>` is the **deterministic driver** (prototype): it fans out the personas,
  enforces a budget ceiling, gates accept/reject in code, and hands accepted work to the scribe
  — with no LLM in the coordination loop. Test the control flow free with `--dry-run`. See
  `docs/harness.md` and `examples/plan.example.json`.
- **Before claiming a task, read the board.** If it's already active, resume the owner via
  `SendMessage` — never spawn a duplicate. `bin/bus claim` guards this.
- Only `accepted` work (cleared by the tuner + heckler pair) enters the scribe's synthesis.

When coordinating a real task, the conductor writes `bus/plan.md`, assigns stable task ids,
and fans out — it does not do the deep work itself.
