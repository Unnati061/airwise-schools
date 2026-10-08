# AirWise architecture

Browser -> Vite React SPA -> development proxy /api -> local FastAPI.
FastAPI reads a packaged JSON fixture through typed Pydantic models.
GET /health returns status, service and data_mode. GET /school returns the
synthetic school and six section IDs, labels and aggregate sizes.
GET /openapi.json is the authoritative API schema.
The frontend generates contract types from that schema.

The standalone CP-SAT smoke model assigns three synthetic activities to distinct
periods and proves the minimum period sum. It uses one worker, fixed seed and a
five-second limit. This is an import/execution check, not a timetable validator.

Deployment order: Python venv; local FastAPI; local native solver; local React;
Python 3.12 x86_64 Lambda ZIP. Mangum adapts the same application to Lambda.
Install Linux binary wheels into a separate staging directory, never upload
Windows site-packages. Package code and data at the ZIP root. Check AWS identity
and an explicit existing function target before updating any function.
Packet A foundation itself created no database or authentication infrastructure.
Follow-up private runtime spike is prepared in scripts/aws_smoke.py; its separate
role, bucket, function and retained log group are authorized only for native
verification. The confirmed region is ap-southeast-2. The runtime test passed
using the existing S3 ZIP; see AWS_SMOKE.md. B1 does not touch AWS resources.
The earlier us-east-1 policy denial was a wrong-region assumption. No public API
was deployed; the application and CP-SAT problem remain unchanged.
Only a demonstrated OR-Tools/native runtime compatibility failure can trigger a
separate minimal Docker fallback test; missing credentials is not that failure.

Public foundation health/synthetic-school endpoints remain read-only. Operational
endpoints now require Cognito authentication (B2 below). Bind to loopback. Future paid or
mutation actions need server-side identity, school authorization and input caps.
Future evidence keeps provider/source/timestamps/units and mode; future approval
checks plan and input versions atomically. No automatic legal activation.

## Local B1 repair path

GET /repair-fixture exposes a labelled synthetic weekly RepairInput.
POST /draft-plans generates a draft; GET /draft-plans/{id} inspects it.
Typed inputs check references, stable IDs, scopes and size caps. Activities occupy
one discrete period and carry original placement and explicit permissions. Rooms
define capacity/type/availability; teachers define availability and supervised
kinds. Confirmed restrictions prohibit outdoor rooms at listed section/period scopes.

repair_engine builds a keep-period classroom-alternative baseline and one-hot
CP-SAT choices. Section, teacher and room exclusivity is hard; unauthorized
substitutions/deferrals never enter the model. Fixed/unaffected activities are
locked. One weighted objective exactly encodes the lexicographic preference.
One worker, seed 42, one solve; preparation deducted from the five-second search
allowance. Request validation/serialization is not a hard five-second latency SLA.

repair_validator separately audits returned placements from the input snapshot
without solver imports. Both baseline and solver output are checked; invalid
solver output cannot be successful. It recomputes all constraints and counts.
UNKNOWN may return a valid baseline, explicitly without an optimality proof.

PlanRepository remains the save/get boundary. B2 uses DynamoPlanRepository;
MemoryPlanRepository is retained only for historical unit checks, never selected
by the running API. No solver or independent validator logic changed in B2.

## B2 authentication and durability

Loopback FastAPI verifies Cognito RS256 access tokens against the fixed Sydney
pool's JWKS, issuer, expiry, token_use and app client_id. Identity-to-school/role/
teacher bindings are trusted DynamoDB records keyed by verified sub, not frontend
roles, request bodies or arbitrary token claims. Token/password values never enter
documents or logs. Short-lived offline verification has revocation-delay limits.

One PAY_PER_REQUEST table uses pk/sk and compressed JSON documents below a
350 KB compressed item bound. Strongly consistent reads and conditional
TransactWriteItems provide version concurrency. Local runtime refreshes temporary
STS credentials for a dedicated role, with only exact-table GetItem/Query and
transactional PutItem access to allowed partitions. No runtime Cognito admin rights.

Confirmed input/restriction snapshots and server versions are stored atomically
with state/audit. Drafts bind to the canonical snapshot. First approval re-runs
the independent validator, checks canonical versions and conditionally creates an
immutable approved snapshot, updates the current pointer and appends an audit.
Duplicate draft approval returns its existing receipt without moving the pointer.
Room/restriction revisions mark needs_review and preserve the old pointer; only
a separately validated approval installs a new version. Approved snapshots freeze
placements and refreshed audit/counts, not just a reference to mutable draft data.

Teacher acknowledgements are keyed by version/teacher. Latest execution reports
are keyed by version/activity, retaining actor/time/status; audit events preserve
changes. Totals derive from these unique records, never retry-sensitive increments.
Teacher reporting requires their current approved version and assigned activity;
administrator resolution notes are separate, idempotent by request UUID.
No approval or identity override exists in the public API. See WORKFLOW.md.

References: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
and https://developers.google.com/optimization/cp/cp_solver .
