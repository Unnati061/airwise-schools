# AirWise Schools

A school-operations prototype for reviewing pollution evidence, repairing a
timetable, approving a version and tracking what teachers actually implemented.
One fictional Greater Noida school, six sections and synthetic data: not a real
school deployment or health intervention.

**Hosted app:** [AirWise Schools](https://main.d29v8cmldu93l3.amplifyapp.com)

The page is public; school operations require existing Cognito identities.
There is no self-registration, role selector or public authentication bypass.
Enter passwords privately. Do not reset demo passwords just to run the app.

## Workflow

1. **Today:** inspect regional PM2.5/PM10 with source and timestamps. LIVE and
   SYNTHETIC REPLAY are separate.
2. **Evidence and restrictions:** compare official excerpts with Nova Lite's
   proposed interpretation. Only an administrator can confirm restrictions.
3. **Plan comparison:** inspect original/proposed activities, baseline, solver
   status and independent validation. Approval checks permissions and versions.
4. **Teacher inbox:** read only your approved assignments, acknowledge their
   version, then separately report execution or an exception.
5. **Review:** inspect deterministic counts, exceptions, approvals and history.

CP-SAT retains every activity and enforces section/teacher/room constraints,
fixed lessons and explicitly permitted alternatives. Its five-second total budget
does not turn UNKNOWN into infeasibility. Approval revalidates independently;
revisions require new approval rather than silently replacing the current plan.

## Architecture

```text
React / Vite on Amplify Hosting
  -> Cognito access-token sign-in
  -> API Gateway HTTP API (JWT authorization)
  -> Python 3.12 / FastAPI / Mangum on Lambda
       -> OR-Tools CP-SAT + independent plain-Python validator
       -> DynamoDB inputs, evidence, versions, reports and audit events
       -> Open-Meteo regional forecasts
       -> bounded Amazon Nova Lite interpretation on Bedrock
```

AWS runs in Sydney (`ap-southeast-2`). Scoped IAM roles provide runtime access;
private S3 holds deployment artifacts and CloudWatch retains logs for seven days.
The separate native-runtime smoke Lambda is not the application API. Docker was
not needed: Linux Python 3.12/x86_64 ZIP execution was verified on Lambda.

## What Was Verified

The hosted administrator -> teacher -> administrator browser flow used real
Cognito authentication, DynamoDB persistence and deployed endpoints. Approval,
separate acknowledgement/execution reporting, administrator review, stale-draft
409 rejection, teacher/cross-assignment 403 denials, token rejection, refresh and
local logout/reload passed. The approved baseline retained 240 activities: one
approved indoor substitution and room move, no period changes or deferrals.

One actual Sydney `amazon.nova-lite-v1:0` analysis succeeded: 773 input / 197 output
tokens; **2,392 ms browser request**, 978 ms handler, 992 ms Gateway integration.
These are request-path timings, not isolated Bedrock-service latency. The prior
verification ran **76 backend tests**, production build and browser checks.
[STATUS.md](STATUS.md) distinguishes those results from this documentation pass.

## Evidence and Limits

Open-Meteo/CAMS global supplies regional forecasts, not measured campus conditions.
**Local station observations are unavailable.** Model issue time was not supplied;
retrieval age must not be called model freshness. No Indian AQI conversion,
automatic GRAP activation or closure inference is made. Pasted notices require
review; model output cannot approve a plan. No health benefits, exposure reduction
or forecast accuracy are claimed.

The MVP repairs one affected day in a synthetic weekly timetable and supports
single-period activities only. One small model call and two planning latency
samples do not establish reliability at scale. An initial 503 coincided with a
Lambda throttle at concurrency five; request-level causation is unproven. See
[the incident record](docs/INCIDENT_503.md). Throttle settings were read back, but
a small rejected-token burst did not demonstrate 429 enforcement. Logout clears
the local session, not immediate global revocation of unexpired JWTs;
tab-scoped sessionStorage remains an XSS-hardening limitation.

## Local Development

Python 3.12 and Node 22 are the verified toolchain. The authenticated backend
requires existing private runtime configuration and temporary AWS credentials;
a fresh checkout alone does not reproduce that setup. See
[WORKFLOW.md](docs/WORKFLOW.md) and [EVIDENCE.md](docs/EVIDENCE.md). Do not rerun
create-only deployment helpers against existing resources.

From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

In another terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open [the local frontend](http://127.0.0.1:5173). Default development mode proxies
the local backend; deployed API configuration is in [HOSTING.md](docs/HOSTING.md).
Never place AWS credentials in Vite variables.

```powershell
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python -m backend.app.solver_smoke
npm --prefix frontend run generate:api
npm --prefix frontend run build
```

## Records and Disclosure

- [Product](docs/PRODUCT.md) and [architecture](docs/ARCHITECTURE.md)
- [Application deployment and cleanup](docs/AWS_APP.md)
- [Hosting verification and cleanup](docs/HOSTING.md)
- [Hackathon writeup draft](docs/HACKATHON.md)
- [2 minute 50 second demo script](docs/DEMO.md)
- [Blueprint coverage and prioritized gaps](docs/BLUEPRINT_AUDIT.md)
- [Source/dependency attribution and licence review](docs/ATTRIBUTION.md)

Codex assisted code, tests, packaging, deployment tooling, debugging and
documentation. The owner supplied requirements, deployment constraints and private
authentication, and retains responsibility for review and submission. Runtime
interpretation uses Bedrock Nova Lite, distinct from Codex development assistance.
Dependencies include FastAPI, Pydantic, Mangum, OR-Tools, React, Vite, TypeScript
and Lucide.

No GitHub repository exists yet (owner-confirmed October 9, 2026); this checkout
has no Git remote. Publication and submission remain manual owner actions.
Current [event rules](https://www.wemakedevs.org/aws/env/rules) require public
source and a YouTube demo under three minutes showing AWS; these are incomplete.
Bilingual previews/outdoor student-hour metrics, SQS/background jobs and automatic
evidence revisions are not implemented. See the audit rather than treating the
whole planning blueprint as shipped.
