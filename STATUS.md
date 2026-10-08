# AirWise Schools status - 2026-10-08 (IST)

## Packet C current checkpoint

Implemented authenticated pollution evidence, curated advisory excerpts and bounded
Sydney Nova Lite notice interpretation. One fictional school / single-period
activities / one affected weekday retained. Solver, independent validator, teacher
execution and atomic approval behavior preserved. No parallel agents or UI expansion.

Actual Open-Meteo / CAMS global PM2.5/PM10 fetch passed at 17:25:12.562767 UTC;
five-day hourly model horizon through October 12, grid 28.5/77.5. Retrieval age
2m42.5s at completed verification; model issue time unavailable, not invented.
Regional ~45 km model output, not campus observations or Indian AQI. Live/replay
caches and provenance are separate. No private OpenAQ key or verified fresh station;
observation discovery stopped early within its cap and observations are unavailable.
Verified official NCDC advisory PDF dates, passages and exact byte hashes: November
1, 2025 (school Annexure IV 5(ii)) and September 2022 (Annexure I item 9).
No active GRAP/closure order established; no numerical legal trigger invented.

Working model amazon.nova-lite-v1:0, direct ap-southeast-2. Availability preflight and
bounded JSON probe passed (23 tokens). Real authenticated demonstration passed:
live fetch -> Nova interpretation (771 input / 195 output tokens) -> explicit
administrator notice/date/period review -> confirmed restriction -> OPTIMAL draft
and independent validation -> grounded explanation -> separate approval. Teacher
confirmation/approval denied; identical analysis cached without another call.
6-a:Mon-2 keeps its period, uses approved indoor-movement and moves field -> room-6-a.
Counts: 0 changed periods, 1 substitution, 0 deferrals, 1 room move; 240 activities
retained. Demonstrated approved version: 12826b9f-8209-49c3-ac24-e8d95bfe821a.

Existing B2 table/pool/runtime role reused. Only AWS change: airwise-c-nova-lite
inline role policy, exact Sydney Nova Lite InvokeModel. No new resources or S3,
no Packet A Lambda changes, SCP/account-setting changes or cross-region calls.
Persisted snapshots, policy excerpts, analysis/cache, daily allowance and usage
records use the existing repository storage. Notices remain UNVERIFIED; model
output never confirms/approves automatically. Ten server-enforced attempts per
authenticated administrator per India-calendar day; failures count, duplicates cache.

Final verification: 65 backend tests passed, two existing deprecation warnings;
pip check, policy-byte/excerpt re-verification, generated API types, frontend
TypeScript/Vite build and git diff checks passed. Unscoped pytest initially collected
ignored historical ZIP staging dependencies and failed; targeted backend/tests passed,
with staging files preserved. Protected backend remains http://127.0.0.1:8002.
No dependency additions. Exact demonstration: .venv\Scripts\python -m scripts.c_demo.
Source hashes, actual freshness/results, resources, endpoints, limits and cleanup:
docs/EVIDENCE.md. Original notice text is not logged; credentials remain private.

Remaining limitations: no station observations, no verified current legal orders,
no polished evidence UI; pending model claims need deliberate recovery after a
process crash; no production retention/backup/MFA/session operations. Advisory
citations do not prove notice authenticity or semantic entailment. Fresh retrieval
cannot establish model issuance freshness or campus conditions. Grounded explanation
wording is deterministic fact assembly, not unconstrained model prose. All school
data and demonstration notices are synthetic; live forecasts remain separately labelled.

## Packet B2 historical checkpoint

Durable authenticated local workflow implemented in ap-southeast-2, profile airwise.
Created on-demand encrypted table airwise-b2-data-a1f7411817; Cognito LITE pool
airwise-b2-users-a1f7411817 (ap-southeast-2_LhIz6g1r9), public app client,
one synthetic administrator and two synthetic teachers; dedicated runtime role
airwise-b2-runtime-a1f7411817 with table/partition-scoped read and transactional
write permissions. No B2 Lambda, API Gateway, dashboards or messaging. The
successful Packet A Lambda, ZIP and resources were not modified or redeployed.

Real Cognito/DynamoDB API demonstration passed: authenticated confirmation,
teacher approval/cross-assignment denial, fresh-process persistence, duplicate
concurrent approval, acknowledgement without execution, report deduplication,
exception resolution, stale/corrupted draft rejection and revision approval with
no acknowledgement transfer. Local suite: 51 passed, two existing warnings;
pip check, generated OpenAPI types and frontend build passed.
Final real loopback HTTP check passed administrator approval, teacher acknowledgement
and COMPLETED reporting exactly once, with a 240-activity frozen approved snapshot.
Current demonstrated version: 4a905e76-acfb-4768-abc9-eba452e7272e.
Initial IAM transport preflight failed with no resources created; user restored
mobile data, then bounded preflight/provisioning and real integration succeeded.

Protected backend is at http://127.0.0.1:8002 . Previous unauthenticated B1 server
was stopped. Use docs/WORKFLOW.md private password prompts and demonstration
commands. No passwords or tokens printed, logged or committed; demo credentials
were random, memory-only and must be set privately for subsequent interactive use.
work/aws-b2.json is the ignored, non-secret local resource manifest.

MVP limitations: one synthetic school, single-period activities, one affected day;
only two of six fixture teachers have sign-in accounts. No polished sign-in UI,
MFA, production hosting or refresh-token UI. JWT revocation/disable does not revoke
offline verification immediately; access tokens expire after 15 minutes. Role and
school bindings come from trusted DynamoDB records, never request roles. Durable
input versions, approved snapshots, reports and audit events are retained. Next
packet needs production authentication/session operations and retention/backup
policy before real data. See WORKFLOW.md for schema, cleanup and actual limitations.

## Packet B1 historical checkpoint

Typed local repair API, approved-alternative baseline, CP-SAT repair and independent
plain-Python validator implemented. Synthetic fixture: six sections, five days,
eight discrete periods, 240 stable activity IDs; only Monday is repaired.
Live API returned OPTIMAL and recommended the baseline: 6-a:Mon-2 stays at Mon-2,
substitutes approved indoor movement and moves from field to room-6-a. Counts:
0 changed periods, 1 substitution, 0 deferrals, 1 room move. All activities retained;
fixed lessons and other days unchanged. Exact request and final checks: docs/REPAIR.md.
OpenAPI frontend types regenerated; no UI changes. No AWS operations, Docker, AI,
approval or parallel agents in B1. Existing AWS runtime gate remains passed.
Final checks: 41 backend tests passed (two existing warnings), pip check passed,
OpenAPI type generation and TypeScript/Vite production build passed.
Local API at http://127.0.0.1:8001 .

Limitations: single-period activities; same-day explicit permissions; administrator
confirmation is input, not authenticated identity. Versions are preserved, not
checked against durable canonical data. Draft storage is process-local, latest
100 only, lost on restart. UNKNOWN does not prove infeasibility. Next packet needs
durable/version-aware storage before approval or activation.

## Packet A verified checkpoint

AWS runtime gate PASSED in ap-southeast-2 using profile airwise and the existing
console-uploaded object airwise-runtime-smoke.zip. No rebuild or upload occurred.
S3 full-object CRC64NVME matched local bytes; Lambda CodeSha256 matched the local
SHA-256 after Base64 encoding. Invocation returned HTTP 200, no FunctionError,
OPTIMAL, periods [3, 2, 1], objective 6, OR-Tools 9.15.6755 and Python 3.12.14/x86_64.
CloudWatch confirms the result and seven-day retention. Created the dedicated
execution role, log group and Lambda; existing private bucket retained.
Targeted backend suite: 12 passed, two existing deprecation warnings; pip check
passed. No Docker needed. No runtime blocker remains; cleanup and any broader
application deployment require a separate task. See docs/AWS_SMOKE.md for names,
commands, verification evidence and cleanup. Previous uncommitted tooling/tests
were preserved and verified. Local application and solver were not changed.

## Historical checkpoint (superseded)

Local foundation complete and checked. AWS runtime gate was BLOCKED by S3
upload transport failure. User confirmed Sydney ap-southeast-2 in AWS Settings;
the airwise profile and deployment tooling now use this region explicitly.
Sydney Lambda preflight passed (unused function name returned ResourceNotFound).
Created only the private Sydney artifact bucket; no role, log group or Lambda.
Uploads failed with TLS EOF/ConnectionClosedError and a read timeout; final check
found no completed object or incomplete multipart uploads. No AWS solver result.
Current record and resume instructions: docs/AWS_SYDNEY.md. docs/AWS_SMOKE.md
preserves the historical us-east-1 SCP denial, which was a wrong-region assumption.
User request takes precedence over blueprint's container-first and broader AWS
spike. No Docker, Bedrock, SQS, Cognito, DynamoDB or parallel agents were used.

## Actual results

- Python 3.12.6; Node v22.23.2; npm 10.9.8.
- Windows Python virtual environment created successfully.
- HTTP GET /health returned 200 and SYNTHETIC mode.
- CP-SAT native import/solve: OPTIMAL, periods [3, 2, 1], objective 6.
- pytest: 3 passed; two dependency deprecation warnings (Starlette HTTPX,
  Mangum event loop). No broken requirements from pip check.
- OpenAPI types generated; TypeScript check and Vite production build passed.
- Browser: desktop 1280x800 and mobile 390x844; six sections, no horizontal
  overflow, no page errors; simulated API failure and retry recovery passed.
  Screenshots visually inspected. Local frontend at http://127.0.0.1:5173 .
- npm install audit reported zero vulnerabilities. Exact versions and lockfile
  recorded. TypeScript 7.0.2 failed with openapi-typescript; 5.9.3 verified.
- Linux Python 3.12 x86_64 wheels installed successfully without Docker.
- ZIP built: 61,637,032 compressed bytes; 190,107,199 extracted bytes.
- Deployment attempt exited 1: AWS credentials unavailable. No upload, AWS
  resource creation, Lambda invocation or native Lambda runtime test occurred.
- ZIP also exceeds direct 50 MiB upload size, but is below 250 MiB extracted
  limit. Next AWS attempt needs an S3 upload route plus credentials and a
  dedicated Python 3.12 x86_64 smoke function target.

## Next task blockers

AWS: complete ZIP upload to the existing private Sydney bucket, for example using
the S3 console after reviewing docs/AWS_SYDNEY.md. Then run the guarded
resume-upload action and invoke the dedicated handler through the CLI. Credentials
are currently usable; Sydney Lambda access is not denied. No account/SCP changes
are required by the observed failure. The underlying transport cause is unproven.
Linux wheel resolution is not proof of Lambda compatibility. Only a reproduced
native compatibility failure permits the proposed separate Docker fallback test.
No Docker fallback has been proposed or tested because that condition was not met.

Packet B local work is unblocked: add weekly timetable fixture, baseline repair,
CP-SAT constraints and independent validator. No current output is a valid school
repair plan; no authentication, live evidence, persistence or approvals exist.

See docs/CHECKS.md for commands, failures, file inventory and verified pins.
The original check history above describes the first local Packet A checkpoint;
the private-runtime follow-up is documented separately in docs/AWS_SMOKE.md.
