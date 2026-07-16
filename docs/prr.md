# Achtopus — Production Readiness Review

This is what Achtopus reviews and how it decides. A **Production Readiness Review (PRR)** asks
one question — *is this change safe to launch?* — and answers it per domain, with evidence,
ending in a **GO / GO-WITH-CONDITIONS / NO-GO** verdict.

## How a review runs

1. **Ground it in intent.** The composer/conductor reads the change and its context — the
   PRD or spec (scope, success metrics, stated risks, dependencies), the diff, and the
   service's existing config/IaC/dashboards. The PRD tells the review what *should* be true;
   the code tells it what *is*. A domain risk named in the PRD but absent from the code is a
   finding.
2. **Inventory the domains.** The conductor lists the readiness domains this change actually
   touches (below) and assigns one reviewer per domain. A domain with no owner is a coverage
   gap, called out explicitly — not skipped silently.
3. **Review each domain.** A soloist (or luthier, for hands-on exercise) works its domain and
   posts findings with a ✅/⚠️/🔴 rating and evidence.
4. **Verify before clearing.** Every load-bearing finding goes through the tuner/heckler pair
   and the evidence gate (`docs/protocol.md`): a rating that claims "verified" must log real
   proof-of-work, or it is downgraded and does not clear.
5. **Score and gate.** The scribe tallies the scorecard and applies the launch rule, then
   writes the verdict (`docs/report-template.md`).

## The domain rubric

Each domain carries concrete, checkable questions and a tag for how far an agent can take it:

- **[AGENT]** — verifiable by an agent from the repo / PR / IaC / dashboards-as-code.
- **[MIXED]** — the agent can confirm the artifact exists and is wired; a human judges adequacy.
- **[HUMAN]** — organizational sign-off; an agent can only confirm the record exists.

### A. Reliability & SLOs — [MIXED]
- Are SLOs/SLIs defined, with documented error-budget targets?
- Are the SLIs real measured signals, not aspirational prose?
- Is there an SLA, and does the SLO leave margin under it?

### B. Observability / Monitoring — [AGENT]
- Is there a dashboard covering RED (Rate/Errors/Duration) and USE (Utilization/Saturation/Errors)?
- Do the new code paths emit logs/metrics/traces with correct, low-cardinality tags?
- Can you attribute an error to a specific request/tenant/version from telemetry alone?

### C. Alerting & On-call — [MIXED]
- Do alerts exist on the key SLIs, defined as code and proven to fire?
- Is there a 24/7 rotation with a named owner and escalation path?
- Are alert thresholds tied to the SLO, not arbitrary?

### D. Capacity & Scale — [MIXED]
- What are the expected load and scale parameters; load-tested to a multiple (e.g. 10x)?
- Does it auto-scale, and are there hardcoded limits that will cap it?
- Are user-facing rate limits / quotas in place?

### E. Rollout, Deploy Safety & Rollback — [MIXED]
- Is there a documented, tested, *fast* rollback procedure?
- Is the change behind a feature flag / kill switch that disables it without a deploy?
- Is rollout staged (canary / percentage ramp) with defined gating metrics?
- Is infrastructure defined as code rather than hand-applied?

### F. Dependencies & Failure Modes — [MIXED]
- What upstreams does it rely on, and what happens when each is slow/down (timeouts, retries,
  circuit breakers, graceful degradation)?
- Who are the downstream consumers, and have they been notified?
- Does it introduce a new single point of failure?

### G. Data Integrity & Migrations — [AGENT]
- Are schema/data migrations backward-compatible and zero-downtime (expand/contract)?
- Is there an idempotent backfill/rollback plan for the data?
- Are backups and restore paths verified for any new data store?

### H. Security & Privacy — [MIXED]
- **AppSec:** Does it change authn/authz? Is untrusted input handled against XSS/SQLi/prompt-injection?
  Has a threat model / security review been done at appropriate depth?
- **InfraSec:** Network exposure behind a WAF? Data encrypted at rest/in transit with tenant
  isolation? Hardened, scanned base images?
- **Detection & Response:** Is there audit/event logging and misuse detection?
- **Compliance/Privacy:** New handling of sensitive data (PII/PHI/cardholder), new subprocessors,
  or compliance-framework impact?
- **Trust & Safety / Abuse:** For user-facing creation/UGC/comms — abuse controls, plan limits,
  rate limiting?
> Code-path sub-points (input handling, authz wiring, encryption config, audit-log emission) are
> **[AGENT]**; threat-model adequacy and compliance judgment are **[HUMAN]**.

### I. Operational Docs & Runbooks — [MIXED]
- Is there a runbook covering common failures and their remediation?
- Is there an architecture diagram and a config inventory (flags, secrets, rotation)?
- Are secrets managed with zero-downtime rotation?

### J. Cost — [MIXED]
- What is the incremental infra/compute/storage cost, and is it bounded?
- Are there cost guardrails/alerts on the new resources?

### K. Org / Launch-gate Readiness — [HUMAN]
- Are docs/support FAQ, enablement, and GTM/comms sign-off complete (where applicable)?
- Has the required approver signed off and have beta-exit criteria been met?
- (An agent can only confirm these artifacts exist and are linked, not that they suffice.)

**Where Achtopus earns its keep:** the agent-verifiable core — **B, G, and the code-path
parts of E, F, H** — is exactly what the adversarial-verify loop can confirm by reading and
exercising code/IaC. **A, C, D, I, J** are mixed (the agent checks the artifact exists and is
wired; a human judges adequacy). **K** is human sign-off. The report must be honest about
which is which — see the coverage section of the template.

## The scorecard and the gate

Rate each domain and tally:

- ✅ **green** — ready; evidence on the bus.
- ⚠️ **warning** — a tracked, non-blocking condition to close (soon, not necessarily pre-launch).
- 🔴 **red** — a launch blocker.

**The rule: you don't need everything green, but nothing red at launch.**

Map to Achtopus's severities and verdict:

| Scorecard | Severity | Effect |
|---|---|---|
| 🔴 red | `S1` launch-blocker | Blocks the gate — must clear before launch |
| ⚠️ warning | `S2`/`S3` condition | Tracked; allowed under GO-WITH-CONDITIONS |
| ✅ green | pass | No action |

Top-line verdict:

- **GO** — no reds; warnings acceptable or none.
- **GO-WITH-CONDITIONS** — no reds, but named warnings must be tracked with owners/dates.
- **NO-GO** — one or more reds, or a domain that could not be verified and cannot be waived.

A domain that could not be verified (evidence gate downgraded it, or it needs a human) is
**not** green by default — it is a warning or a red depending on stakes, never a silent pass.
Fail closed.

## Sign-off roles (generic)

- **Owner / DRI** — the person shipping the change; fills in context, owns the conditions.
- **Reviewer** — the independent function clearing the gate (Achtopus drafts this role's
  scorecard and evidence; a human confirms the mixed/human domains).

Specific org role names, gate names, and submission channels are **not** in this repo — they
belong to a private org preset layered on top of this generic rubric.
