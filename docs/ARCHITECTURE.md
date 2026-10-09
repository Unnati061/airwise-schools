# AirWise architecture

## Current Deployed State

React/Vite on Amplify calls the Sydney JWT-protected HTTP API and Python3.12/x86_64
ZIP Lambda, reusing Cognito/DynamoDB/Nova Lite. Actual hosted interpretation,
approval, teacher execution and Review passed; HOSTING.md/AWS_APP.md give results.
Older packet descriptions below are history, not current deployment claims.

Follow-up preserves these boundaries: the same DynamoStore transaction now also
stores immutable execution request UUID receipts, while the latest unique
activity/version report drives totals. Safe explicit in-tab retries replay exact
requests; approval uses its existing draft receipt. Expired model-cache claims
are fenced into failure without a new model call. No worker/queue/resource added.
Administrator approved-detail/review reads return deterministic bilingual previews
and synthetic declared-duration metrics through generated contracts. Translation,
counts and student-hours do not use Bedrock. Historical durations remain nullable;
missing relevant duration means unavailable totals. Previews never send messages.
See FEATURE_COMPLETION.md for actual tests, deployed results and recovery limits.
No SQS/DLQ, ECR, SAM or model agent loop. Raw forecast refresh does not mark a plan
for review; confirmed input revision does. No bilingual previews/outdoor-hour
metrics. BLUEPRINT_AUDIT.md maps all requirement groups and current limitations.
The503 remains inconclusive at request level; no speculative concurrency change.

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
Evidence keeps provider/source/timestamps/units and mode; approval checks plan and
input versions atomically. No automatic legal activation.

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

## C evidence and bounded model interpretation

EvidenceService uses the same authenticated administrator/school scope and DynamoStore.
EVIDENCE/EVIDENCE_RAW retain immutable normalized snapshots, parsed provider JSON
and the original HTTP-body SHA-256; FORECAST_CACHE has separate LIVE/REPLAY pointers.
No raw public-response bucket is needed. A 15-minute cache preserves retrieval time;
failed refresh never relabels old data or substitutes replay into the live path.
One-hour retrieval freshness and missing/future-value checks gate analysis/review.
Provider model issue time is explicitly unknown; retrieval freshness is not proof
of model-cycle freshness. No station observations or AQI conversion exists.

POLICY records retain curated exact excerpts, references, document/excerpt hashes
and verification times. They are advisory/internal-policy evidence, not active orders.
NovaProvider uses existing boto3 scoped-role credential refresh and a single in-region
Converse call. Only bedrock:InvokeModel on amazon.nova-lite-v1:0 in Sydney was added
to the existing role. No Strands, streaming or cross-region profile. Schemas and
citation/activity membership are checked independently of model instructions.

MODEL_CACHE pending claims and daily ANALYSIS_ALLOWANCE counters are committed
atomically before a call, preventing duplicate concurrent requests and limiting
each authenticated administrator to ten attempts per India-calendar day. Durable
MODEL_USAGE records contain actor/time/model/usage/hash/error class, not prompt text.
ANALYSIS records contain validated results or explicit failure; model-cache records
are private output, not application logs. Original notice input is hashed, not
directly stored. Failed attempts consume allowance; no automatic model retry.

Confirmation is a separate authenticated operation. It checks current input revision,
evidence freshness/mode, explicit calendar-to-weekday mapping, permitted proposal
kind and explicit affected-day periods. Confirmation persists EvidenceBinding in
the immutable input revision; draft versions refer to that revision. Approval still
uses the unchanged independent validator and B2 atomic version/pointer checks.
No model output writes confirmation flags or current-plan pointers. Explanations
select only server-supplied fact IDs; final wording and counts are deterministic.
No solver, validation or teacher-execution logic changed. See EVIDENCE.md.

## Packet D1 interface

Five React views use generated OpenAPI contracts and existing authenticated APIs.
Cognito browser sign-in and tab-scoped refresh precede backend-authorized reads
and mutations; caller-selected roles are never trusted. Local Vite proxies port
8002. New read queries expose immutable inputs, approved history, own historical
teacher reports and deterministic administrator execution summaries. No new
storage, deployment or AWS permissions. See INTERFACE.md for session limitations,
real versus controlled browser verification and request retry behavior.

References: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
and https://developers.google.com/optimization/cp/cp_solver .

## Packet D2 prepared deployment

Dedicated application resources are deployed in Sydney; exact existing artifact
size/CRC64 and Lambda code SHA256 match verified. Health and unauthenticated denial
passed. Private real Cognito administrator approval, native solver/independent
validation, teacher acknowledgement/reporting and role-denial checks passed against
the deployed API; React Review showed the exception. Later hosting also verified
live forecast and one actual analysis within30s. Wider reliability/security edge
cases remain unverified, not the whole deployed workflow. See AWS_APP.md.
Path: local SPA environment-configured API origin -> HTTP API JWT scope
authorizer -> dedicated Mangum Lambda surface -> existing DynamoDB/Nova. Backend
also verifies access token/client and trusted identity bindings. Public health is
status-only; local foundation metadata stays out of the deployed surface. Lambda
uses its role credentials, not the ignored local profile/manifest. Existing local
defaults and smoke function remain intact. Planned finite budgets do not prove
latency reliability; measure real cold/warm operations before choosing durable jobs.

## Amplify static hosting

The same Vite SPA is manually hosted on the tagged Sydney Amplify WEB app/main
branch. Build includes public API/Cognito IDs only. Direct Cognito password and
refresh flows remain; no OAuth callback or new auth architecture. API CORS lists
exact local and hosted origins, while JWT/school/teacher checks remain server-side.
Actual hosted interpretation/approval/execution/Review and token/session checks
passed. One bounded Nova analysis fit30s; wider latency/reliability is not proven.
Local logout clears the tab session, not immediate global JWT revocation. See
HOSTING.md for actual timings, transient failures, log scan and cleanup scope.
