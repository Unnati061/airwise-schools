# Foundation architecture

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
No IAM, gateway, database or authentication infrastructure is created here.
Follow-up private runtime spike is prepared in scripts/aws_smoke.py; its separate
role, bucket, function and retained log group are authorized only for native
verification. The confirmed region is ap-southeast-2. The runtime test passed
using the existing S3 ZIP; see AWS_SMOKE.md. B1 does not touch AWS resources.
The earlier us-east-1 policy denial was a wrong-region assumption. No public API
was deployed; the application and CP-SAT problem remain unchanged.
Only a demonstrated OR-Tools/native runtime compatibility failure can trigger a
separate minimal Docker fallback test; missing credentials is not that failure.

Local endpoints are unauthenticated. Bind to loopback. Future paid or
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

PlanRepository is a storage protocol. MemoryPlanRepository stores deep snapshots,
latest 100 drafts per process; restarts lose drafts and workers do not share them.
Next packet must add durable storage and version concurrency checks before approval.
No B1 UI, authentication, activation or cloud deployment is added.

References: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
and https://developers.google.com/optimization/cp/cp_solver .
