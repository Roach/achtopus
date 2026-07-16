# Security Policy

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a security vulnerability. Instead, use
GitHub's private vulnerability reporting: go to the **Security** tab of this repository
and click **Report a vulnerability**. This opens a private advisory visible only to you
and the maintainers.

Include, if known:

- A description of the vulnerability and its potential impact
- Steps to reproduce (a minimal `plan.json` or command line is ideal, given this is a
  local CLI tool, not a hosted service)
- Any suggested fix or mitigation

We'll acknowledge reports as soon as we can and keep you updated as we work on a fix.

## Scope notes

Achtopus is a local, `git clone`-and-run CLI/agent-coordination framework — there is no
hosted deployment, and `bin/run` spawns `claude -p` subprocesses under whatever
permissions the invoking user already has. Relevant security surfaces are things like:

- Task/plan input handling in `bin/run` and `bin/wire` (e.g. path traversal via a task id,
  injection via `subprocess` argument construction)
- Worktree/`target_repo` isolation boundaries (see `docs/harness.md`)
- Anything that would let an untrusted `plan.json` or `--goal` string escalate beyond the
  scope the user intended when invoking `bin/run`
