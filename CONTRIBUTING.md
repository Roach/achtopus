# Contributing to Achtopus

Thanks for considering a contribution. Achtopus is small on purpose — the driver
(`bin/run`) is stdlib-only Python, and the personas are plain markdown — so most
changes are easy to review in isolation.

## Before you start

- **Bugs / ideas:** open an issue first for anything beyond a small fix, so we can
  agree on direction before you invest time.
- **Personas** (`.claude/agents/*.md`): keep each persona's `tools:` list narrow —
  scope creep here (e.g. giving every persona every tool) causes decision paralysis
  and token waste in the fan-out. See `docs/harness.md`.
- **The driver** (`bin/run`, `bin/wire`): stays stdlib-only, no dependencies. Coordination
  logic belongs in code, not in a persona's prose — see `docs/harness.md` for why.

## Making a change

1. Fork and branch from `main`.
2. Run the free, zero-cost checks before opening a PR:
   ```bash
   python3 -c "import ast; ast.parse(open('bin/run').read())"   # syntax check
   bash -n bin/wire                                             # syntax check
   bin/run examples/plan.example.json --dry-run                 # exercises the full control flow
   bin/run examples/prr-plan.example.json --dry-run
   bin/run examples/scope-guard.example.json --dry-run
   ```
3. If your change touches `bin/run`/`bin/wire`, describe what you tested (dry-run output,
   or a real `--budget` run if you have API access) in the PR description — this repo has no
   CI-triggered LLM calls, so a live example carries real weight in review.
4. Keep the octopus/nautical persona theme consistent if you're touching names or docs —
   see `docs/prr.md` and the persona table in `README.md` for the existing conventions.

## Reporting a security issue

Please don't open a public issue for a security vulnerability — see `SECURITY.md`.
