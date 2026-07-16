## What changed and why

## Testing

- [ ] `python3 -c "import ast; ast.parse(open('bin/run').read())"` passes
- [ ] `bash -n bin/wire` passes
- [ ] `bin/run examples/plan.example.json --dry-run` passes
- [ ] `bin/run examples/prr-plan.example.json --dry-run` passes
- [ ] `bin/run examples/scope-guard.example.json --dry-run` passes
- [ ] If this touches persona markdown: ran a real (non-dry-run) invocation, or explain why not

## Checklist

- [ ] No internal/private references (see the scrub rule in `CONTRIBUTING.md` if unsure)
- [ ] Persona `tools:` lists stay narrow (no unscoped tool grants)
