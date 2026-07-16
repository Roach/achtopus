# Acht Opus — Final Report Template

The Scribe fills this out at the finale. Copy it verbatim, replace every `<…>` placeholder,
and delete any section that genuinely does not apply (say why). Keep it scannable and
greppable: one finding per block, stable ids, concrete over abstract. Every claim in the
report must trace to a bus artifact (`*.result.md` / `*.verdict.md` / `*.refute.md`) — if
it isn't on the bus, it doesn't go in the report.

**Severity scale** (rank findings by this, most severe first):
`S1 critical` (correctness/security defect with real consequences) ·
`S2 high` (wrong behavior, likely to bite) · `S3 medium` (quality/maintainability) ·
`S4 low` (cosmetic/nit).

**Verification tags** (per finding — how hard was it actually checked):
`VERIFIED` (tuner HOLDS + heckler SURVIVES, both with cited independent action) ·
`PARTIAL` (checked, but a verifier only re-read rather than independently exercised) ·
`UNVERIFIED` (accepted on the soloist's word; no adversarial pass) ·
`REFUTED` (challenged and did not hold — see §3).

---

# Acht Opus Run Report — <subject>

**Date:** <YYYY-MM-DD> · **Conductor model:** <model> · **Run via:** <native subagent types | hand-injected markdown>
**Scope:** <one sentence: what was audited/built and what was explicitly out of scope>

## 1. Summary

<3–5 sentences: the headline outcome. How many findings at each severity, the single most
important one, and the bottom-line recommendation. A reader who stops here should know
whether to act and how urgently.>

## 2. Run metadata & cost

| | |
|---|---|
| Tasks | <t1..tN — count> |
| Subagents spawned | <count> (soloists <n>, verifiers <n>) |
| Verify coverage | <n of N tasks got a tuner+heckler pass> |
| Model tiers | orchestrator <model>, subagents <model> |
| Approx. cost | <$ or "not isolated — ran inside a larger session"> |
| Overlap check | <ran / not run> — <what it found or that it was skipped> |

Task ledger (from `bus/board.md`):

| id | intent | persona | final state | result artifact |
|----|--------|---------|-------------|-----------------|
| t1 | <…> | <soloist/…> | accepted / rejected / blocked | `bus/t1.result.md` |

## 3. Findings (ranked, actionable)

Group implementation findings first, then docs/other. Order by severity. Collapse
duplicates into one entry citing all tasks that found it (corroboration = signal).

### F1 — <one-line defect> · `S1` · `VERIFIED`
- **Where:** `<path:line>`
- **What:** <the defect in one or two sentences>
- **Evidence:** <the concrete failing case: input → wrong/actual output, or the command run>
- **Verification:** <tuner: HOLDS via `<action>`; heckler: SURVIVES — tried `<attack>`>
- **Recommended action:** <the specific fix; smallest change that resolves it>
- **Source:** <t2 (also corroborated by t1)>

### F2 — …

## 4. Refutations & caveats

Claims that were challenged and did **not** hold, or that were downgraded. These are
results in their own right — record them so the report is honest and so a rejected claim
isn't silently retried later.

- **<claim>** — `REFUTED` by <task> heckler: <the concrete counter-evidence>. Disposition:
  <intended design / cosmetic-only / overstatement corrected>.

## 5. Coverage & verification honesty

- **Independently exercised:** <which findings/tasks got genuine independent execution>.
- **Re-read only:** <which verifier legs confirmed by re-reading rather than constructing a
  new falsification — flag these; they are weaker>.
- **Not covered:** <files/paths/claims in scope that were NOT audited, planned checks that
  didn't run, any top-N or sampling cap applied>. Never let a silent cap read as full
  coverage.

## 6. Prioritized action list

Ordered, owner-assignable. This is the "what to do now" the report exists for.

1. **<action>** — addresses <F1>; <effort: S/M/L>; <owner or "unassigned">.
2. …

## 7. Framework performance (self-eval)

These runs double as evals of Acht Opus itself. Be specific and critical.

- **What worked:** <where the structure earned its cost — e.g. an adversarial leg that
  caught a net-new defect prose review missed; auditability from the bus>.
- **What to improve:** <where it was weak — uneven verify rigor, missing overlap dedup,
  UX friction, cost/signal concerns>. Tie each to a concrete mechanism if you can.
- **Cost/signal verdict:** <was the full harness worth it for this task, or would a lighter
  pass have hit the same findings for less?>
