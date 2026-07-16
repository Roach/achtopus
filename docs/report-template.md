# Achtopus — Launch-Readiness Report Template

The Ink fills this out at the finale of a Production Readiness Review. Copy it verbatim,
replace every `<…>` placeholder, and delete any section that genuinely does not apply (say
why). Keep it scannable and greppable: one domain/finding per block, stable ids, concrete
over abstract. Every rating in the report must trace to a wire artifact
(`*.result.md` / `*.verdict.md` / `*.refute.md`) — if it isn't on the wire, it doesn't go in
the report.

**Scorecard ratings** (per domain):
✅ `green` (ready; evidence on the wire) · ⚠️ `warning` (tracked, non-blocking condition) ·
🔴 `red` (launch blocker). **The rule: nothing red at launch.**

**Severity scale** (rank blockers/conditions by this):
`S1` launch-blocker (maps to 🔴) · `S2` high / `S3` medium (tracked condition, ⚠️) ·
`S4` low (nit).

**Verification tags** (per finding — how hard was it actually checked):
`VERIFIED` (tuner HOLDS + heckler SURVIVES, both with cited independent action + logged proof) ·
`PARTIAL` (checked, but only re-read / static, not independently exercised) ·
`UNVERIFIED` (accepted on the reviewer's word; no adversarial pass) ·
`REFUTED` (challenged and did not hold — see §4). A domain that could not be verified is
**never** ✅ by default.

---

# Launch-Readiness Report — <service / change>

| | |
|---|---|
| **Verdict** | **<GO / GO-WITH-CONDITIONS / NO-GO>** |
| Owner / DRI | <name or role> |
| Reviewer | <Achtopus run — conductor model + who confirmed human domains> |
| Date | <YYYY-MM-DD> |
| Grade | <✅ n · ⚠️ n · 🔴 n> |
| Scope | <one sentence: what change, what's explicitly out of scope> |

## 1. Verdict summary

<3–5 sentences: GO/CONDITIONS/NO-GO and why. The single most important blocker or condition,
and what must happen before launch. A reader who stops here knows whether it ships and what's
gating it.>

## 2. Domain scorecard

One row per readiness domain reviewed (see `docs/prr.md`). Rating traces to the wire artifact.

| Domain | Rating | Verification | Evidence / note | Artifact |
|---|---|---|---|---|
| B. Observability | ✅ / ⚠️ / 🔴 | VERIFIED / PARTIAL / … | <one line + the proof> | `wire/d2.result.md` |
| E. Rollback & deploy | … | … | … | `wire/d5.result.md` |
| … | | | | |

Domains **not reviewed** (out of scope or unowned): <list, with why> — never let an omitted
domain read as ✅.

## 3. Launch blockers & conditions (ranked, actionable)

Order by severity. 🔴 blockers first, then ⚠️ conditions. Collapse duplicates into one entry
citing all domains that surfaced it.

### 🔴 B1 — <one-line blocker> · `S1` · `VERIFIED`
- **Domain:** <E. Rollback>
- **Where:** `<path:line / config>`
- **What:** <the readiness gap in one or two sentences>
- **Evidence:** <the concrete failing case: input → actual, or the command run and its output>
- **Verification:** <tuner: HOLDS via `<action>`; heckler: SURVIVES — tried `<attack>`>
- **To clear:** <the specific action; smallest change that makes this ready>
- **Source:** <d5 (also corroborated by d2)>

### ⚠️ C1 — <one-line condition> · `S3` · `PARTIAL`
- **To clear (and by when/owner):** <…>

## 4. Refutations & caveats

Ratings that were challenged and did **not** hold, or were downgraded. Record them so the
report is honest and a rejected concern isn't silently retried later.

- **<claim>** — `REFUTED` by <domain> heckler: <concrete counter-evidence>. Disposition:
  <not a real blocker / cosmetic / overstatement corrected>.

## 5. Coverage & verification honesty

- **Agent-verified:** <domains/findings genuinely exercised with logged proof>.
- **Static / re-read only:** <ratings confirmed by reading, not running — weaker; flag them>.
- **Needs human sign-off:** <the [MIXED]/[HUMAN] domains an agent can't fully judge — on-call
  adequacy, threat-model depth, org gates. State that these are drafted/checked-for-existence,
  not cleared>.
- **Not covered:** <in-scope domains/paths NOT reviewed, planned checks that didn't run, any cap
  applied>. Never let a silent cap read as full coverage.

## 6. Pre-launch action list

Ordered, owner-assignable — the "what to do before we ship" the report exists for.

1. **<action>** — clears <B1>; <effort S/M/L>; <owner or "unassigned">; blocks launch: <yes/no>.
2. …

## 7. Review performance (self-eval)

These runs double as evals of Achtopus itself. Be specific and critical.

- **What worked:** <where the structure earned its cost — an adversarial leg that caught a
  launch risk the diff review missed; a domain the inventory surfaced that nobody owned>.
- **What to improve:** <uneven verify rigor, a mixed domain over-claimed as verified, cost/signal>.
- **Cost/signal verdict:** <were all eight arms worth it, or would a lighter pass have reached
  the same GO/NO-GO for less?>
