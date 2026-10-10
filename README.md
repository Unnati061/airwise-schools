# AirWise Schools

[Open the hosted app](https://main.d29v8cmldu93l3.amplifyapp.com) |
[Source](https://github.com/Unnati061/airwise-schools)

A school-operations prototype for one fictional Greater Noida school, six sections
and sample school data. Administrators review pollution evidence, repair a timetable
and approve a version. Teachers acknowledge their assignments and report what
they actually implemented.

## How It Works

- **Today:** regional PM2.5/PM10, evidence needing attention, proposed timetable
  changes and actual teacher reports.
- **Evidence & restrictions:** official passages and grounded model interpretation.
  Only an authenticated administrator confirms restrictions.
- **Plan comparison:** explicit before/after activities, rooms and periods,
  preserved fixed lessons, baseline recommendation and independent validation.
- **Teacher inbox:** version-specific receipt acknowledgement, separate execution
  reports and retained earlier versions.
- **Review:** execution exceptions, resolution notes, approval/audit history,
  planned versus reported student-hours and English/Hindi previews. Nothing is sent.

The solver keeps every activity, enforces room/teacher/section constraints and
prefers the fewest changed periods, substitutions/deferrals, then room moves.
A five-second budget does not make UNKNOWN mean infeasible. Approval independently
revalidates and rejects stale inputs; revisions never silently replace approval.

Two labelled samples are available for administrator review: classroom alternatives
that retain periods, and competing shared-teacher/indoor-room constraints requiring
a period repair. Confirming a sample revises inputs, not approval.

## Run and Test

See [setup](docs/SETUP.md) for exact local commands and authentication prerequisites.
Existing school operations require privately provisioned Cognito identities:
no self-registration, shared passwords, role selector or authentication bypass.
Offline solver tests do not require AWS.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
.venv\Scripts\python -m pytest backend/tests -q
npm --prefix frontend ci
npm --prefix frontend run build
```

[Architecture](docs/ARCHITECTURE.md) | [Deployment and cleanup](docs/DEPLOYMENT.md) |
[Evidence](docs/EVIDENCE.md) | [Attribution](docs/ATTRIBUTION.md)

## Limits

Regional forecasts are **not campus measurements**; local station observations
are unavailable. Model issue time is unknown when not supplied. LIVE and SYNTHETIC
REPLAY remain separate. There is no Indian-AQI conversion, automatic closure/GRAP
activation, measured exposure reduction, indoor-air safety or health-benefit claim.

The MVP handles single-period activities and one affected day in a weekly timetable.
Student-hours use declared sample duration and section size; teacher reports are
self-reports, not independent observation. Bilingual text is a reviewed preview,
not messaging. Small latency samples do not prove reliability at scale.
Logout clears the local tab session, not immediate global JWT revocation;
sessionStorage requires further XSS hardening. See deployment notes for the
unproven request-level cause of an earlier 503 and the finite concurrency limit.

## Licence and Assistance

Original project code is [MIT licensed](LICENSE). Third-party software, forecast
data and official excerpts retain their own terms. Full notices are preserved in
[third_party](docs/third_party) and the hosted browser notice asset.
No dependency binaries or deployment ZIPs are distributed in this source repository.
[Native redistribution obligations](docs/NATIVE_REDISTRIBUTION.md) remain unresolved
for a downloadable native binary release; do not attach private ZIPs to GitHub Releases.

Codex assisted implementation, tests, packaging, debugging and documentation.
The owner supplied requirements, constraints and private authentication and retains
review responsibility. Runtime interpretation uses Bedrock Nova Lite, not Codex;
neither model confirms restrictions or approves plans.
