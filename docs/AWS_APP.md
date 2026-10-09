# Packet D2 application deployment - October 9, 2026 IST

Finalization from `25be464` made no deployment/resource changes or new model calls.
Historical current-plan503 checks confirmed a same-minute Lambda throttle at
concurrency five, not an exact causal request match; see
[INCIDENT_503.md](INCIDENT_503.md). Existing cleanup instructions remain unchanged.

## Hosted verification from 4f8bddf

Actual public app: https://main.d29v8cmldu93l3.amplifyapp.com . Existing API/Lambda,
code ZIP and data/auth resources were reused unchanged. Only an Amplify app/branch
was created and the exact hosted origin added to existing API CORS; direct
Cognito sign-in has no required callbacks. See HOSTING.md for full commands,
resources, cleanup, failures and limitations.

Hosted UI admin -> teacher -> admin workflow passed with private password entry:
actual Nova Lite interpretation (one successful invocation), reviewed REPLAY
restrictions, stale approval409, OPTIMAL/independently valid 240-activity plan,
approval, separate teacher acknowledgement/execution exception, administrator
Review and nine-version history. Current plan `acd49a0b-0da2-421c-9d85-c7b7cbd35fcf`.
Actual analysis latency: 2,392ms browser, 978ms handler, 992ms Gateway integration;
not isolated Bedrock-service latency. Drafts18,948/5,429ms; measured requests fit
30s, but cold/warm reliability is not proven. No background jobs introduced.

Real ID/malformed/tampered token denials, teacher/cross-assignment403, session
refresh, local logout/reload and exact CORS checks passed. Actual throttle config
read back; small invalid-token burst401 did not demonstrate429. 714 recent events
scanned with no tested secrets/notice patterns; finite-sample limitation applies.
Initial read-only hosting timeout and hosted current-plan503 are documented;
corrected browser run exited0, no failed paid/approval mutation was retried.
76 backend tests, production build and syntax passed. Local logout revocation/
XSS hardening, natural token-expiry/wrong-client tests and wider latency samples
remain limitations; earlier health-only deployment records below are historical.

## Previous resume from 91e8824: approval/execution verification passed

October 9, 2026 IST. Reused the existing D2-mode Vite process (port 5173), verified
local HTTP 200 and performed a single readiness GET inside the browser harness
**before opening Chrome**. No resource creation/redeployment, ZIP rebuild/upload,
policy/account/region changes, password resets or paid model calls. Existing
API URL, configuration, code hash and cleanup scope below remain unchanged.

Private Cognito password entry was performed by the user, in three pauses:
synthetic-admin -> synthetic-teacher-a -> synthetic-admin. No password fill/read,
browser traces, credential dumps or token export. The existing app keeps its
normal tab-scoped session handling; test artifacts contain only safe results.

### Actual deployed workflow results

The test used browser-based calls through `/src/client.ts`'s normal authenticated
client, not mocks, local backend requests or a caller-supplied role. It also
clicked React's Review navigation and verified the report rendered. Mutation
checks exercised real API calls in the browser; they did not separately exercise
each approval/report form button. Private sign-in and Sign out used the real UI.

- Existing confirmed revision: `62df717d-a334-41fc-964d-179267716257`, binding
  **REPLAY**, preserved without changing restrictions or model interpretation.
- New draft/approved plan: `bfa79eb2-861e-4a14-8236-d5b11d669308`.
- OR-Tools on the actual application Lambda: **OPTIMAL**; independently valid;
  recommendation **baseline**; all **240** original activities retained.
- Only difference: `6-a:Mon-2` remains Monday period 2, moves `field` ->
  `room-6-a`, uses explicitly approved `indoor-movement` alternative.
  Deterministic counts: 0 changed periods, 1 substitution, 0 deferrals, 1 room move.
- Administrator approval **200**. Repeat approval **200**, same version;
  current pointer and immutable approved snapshot read back consistently.
- Teacher A read **40** own assignments. New version initially unacknowledged.
  Teacher approval **403**, Teacher B assignments **403**, administrator-only
  `/inputs` **403**, `/audit-events` **403**. No permission bypass introduced.
- Acknowledgement **200**; teacher reports still empty immediately afterward.
  Execution report for `6-a:Mon-2`: **COULD_NOT_IMPLEMENT**, **200**, synthetic
  classroom-unavailable note. Identical repeat report **200**, same timestamp,
  exactly one execution record; no duplicate totals.
- Administrator Review read **200** and visible React Review displayed the note.
  Backend counts: reported 1, completed 0, could_not_implement 1,
  needs_clarification 0, unresolved 1. Eight approved versions and 46 audit events
  read, including this version's execution event; older versions retained.
- Persistence checked through separate HTTP Lambda requests, read-back and
  private sign-out/sign-in transitions. No forced Lambda restart was attempted.

Browser wall-clock timings (network/client time included, not isolated Lambda
integration measurements):

| Operation | Status | Duration |
| --- | --- | --- |
| Administrator identity explicit read | 200 | 6,361 ms |
| Draft generation and independent validation | 200 | 3,727 ms |
| First approval | 200 | 1,077 ms |
| Duplicate approval | 200 | 1,245 ms |
| Teacher acknowledgement | 200 | 1,282 ms |
| First execution report | 200 | 1,251 ms |
| Duplicate execution report | 200 | 918 ms |
| Administrator execution Review | 200 | 1,889 ms |

The corrected workflow-only run exited **0**, with no unexpected HTTP failures.
A preparatory harness process was intentionally cancelled before its authenticated
checks/actions after spotting a serialized-function scope error. The mode value
is now passed explicitly into the browser function. No failed cloud mutation was
retried. The earlier frontend navigation failure was not reproduced once readiness
was checked, but its original error code remains unknown.

### Commands, limits and next checks

```powershell
# Existing server was reused; this is its normal mode/port command if stopped:
node node_modules/vite/bin/vite.js --mode d2 --host 127.0.0.1 --port 5173 --strictPort
# From repository root, with the server ready:
$env:PLAYWRIGHT_MODULE='C:\Users\Ashwani\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
$env:AIRWISE_WORKFLOW_ONLY='1'
node scripts/check_d2_real.cjs
.venv\Scripts\python -m pytest backend/tests -q
node --check scripts/check_d2_real.cjs
npm --prefix frontend run build
git diff --check
```
Safe results/timings: ignored `work/d2-verification.json`. The full mode remains
separate and unverified; workflow-only deliberately skips forecast/paid analysis,
restriction revision, stale approval and ID-token rejection. Do not present the
skipped ID-token check as a pass. The server-side role denial checks above ran.

Local backend tests: **74 passed**, two existing Starlette/Mangum deprecation
warnings; Node syntax and default-mode frontend build passed. No backend/auth/
solver/validator code or generated contracts changed.
Planning fit the 30-second HTTP integration limit in this measured request;
this single run does not establish cold/warm reliability or analysis performance.
Full D2 still needs actual deployed live forecast, one bounded Bedrock analysis,
stale approval/ID-token checks and slow-path integration measurements before
deciding whether durable jobs are required. No untracked background work added.
Cleanup commands below remain applicable; none executed in this resume.

## Previous resume: deployed, authenticated verification incomplete

Resumed from `ce0ed8c`. `aws login --profile airwise` completed through private
browser sign-in. `aws sts get-caller-identity --profile airwise --region
ap-southeast-2 --cli-connect-timeout 4 --cli-read-timeout 12` passed: temporary
assumed-role `AccountFullAccessRole`, account ID redacted. No long-term keys,
password reset or credential/token export. Region/account and existing account
policies unchanged; only the authorized dedicated D2 role policy was created.

### Verified existing object

HeadObject with ChecksumMode=ENABLED at the exact key documented below returned
87,392,618 bytes, AES256, **ChecksumType=FULL_OBJECT**, actual S3
ChecksumCRC64NVME **`9F+qhS+qZOg=`**. CRC64NVME computed from the unchanged local
ZIP matched using big-endian eight-byte Base64 encoding. Custom Metadata was
empty; no custom metadata or ETag was treated as a verified checksum. Local
SHA256 remained `43f0c6d1bcfaa051db9f8f45f0502202faeec9f4d4ab95d1941bf3e60e435469`.
No rebuild or upload occurred. Extracted size remains 240,716,360 bytes.

### Actual deployment and checks

API URL: **https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com**

Before any creation, bounded Sydney SDK checks passed for existing data/auth,
exact existing runtime policies, artifact bucket location/public blocking and
Lambda capacity. D2 role/Lambda/API/log-group collision checks found none.
Ran `.venv\Scripts\python -m scripts.aws_app --existing-object` once, with one
total SDK attempt. The helper now waits 15 seconds after the initial role/policy
creation and makes only one CreateFunction attempt, stopping on any error.

Created, tagged Project=AirWiseSchools / Packet=D2:
- Role `airwise-app-role-a1f7411817`, inline policy `airwise-app-runtime`.
- Lambda `airwise-app-api-a1f7411817`, Python 3.12/x86_64, 1024 MB, timeout 28s,
  reserved concurrency 5; no layers/VPC/Function URL/provisioned concurrency.
- HTTP API `airwise-app-api-a1f7411817`, ID `lbckjkbfb4`, `$default` auto-deploy
  stage, Cognito JWT authorizer `airwise-cognito-access`, Lambda integration and
  29 routes. Exact local origin CORS and throttles are as described below.
- `/aws/lambda/airwise-app-api-a1f7411817` and
  `/aws/apigateway/airwise-app-api-a1f7411817`, both verified seven-day retention.

Independent configuration reads verified runtime/architecture/memory/timeout,
reserved concurrency, and Lambda CodeSha256 equal to **Base64 of the local SHA256
digest bytes**. All 29 actual routes were checked: only GET /health is NONE;
all others JWT with access-token scope `aws.cognito.signin.user.admin`.
Backend role/school/teacher checks remain independent of that Cognito scope.
Existing B2/C resources and smoke Lambda were not altered; role credentials are
used by the deployed app, never a copied local AWS profile.

Actual unauthenticated HTTP checks (single requests, client wall-clock timings):
- GET /health: **200**, body exactly `{"status":"ok"}`, **7,483 ms**.
- GET /inputs without token: **401**, **1,844 ms**.
Health proves the packaged application imports/handler run on Lambda, not that
the repair solver or authenticated workflow has run successfully in this ZIP.

### Stop point and remaining verification

Started the normal local frontend in `d2` mode, public resource identifiers/API
URL in ignored `frontend/.env.d2.local`; default local mode remains unchanged.
Vite reported ready in **14,650 ms**, at http://127.0.0.1:5173/.
One headed Chrome verification attempt (`node scripts/check_d2_real.cjs`) failed
at **page.goto of the local frontend, before private application sign-in**.
The recorded error was generic `Error`, no HTTP status; the initial harness
withheld the message, so the exact navigation error code cannot be established.
Timing is consistent with a frontend startup race, **not a proven diagnosis**.
No workflow retry followed. Safe results are in ignored
`work/d2-verification.json`; no timings or successful workflow checks are present.
The script now records the precise navigation stage and a whitelisted net::ERR
code on a future failure, without logging credentials or request contents.

No D2 application Cognito sign-in, live forecast, Bedrock analysis, draft/approval,
teacher action, permission denial, stale approval or persistence test ran through
the deployed API. No paid model call or workflow mutation occurred in this resume.
Cold/warm analysis/planning integration latency and durable-job need remain
**unresolved**; the health timing is not evidence that slow paths fit 30 seconds.
The verification script is prepared, not end-to-end verified; any proposed
restriction still requires explicit administrator review. No background jobs added.

Next resume: inspect these existing D2 resources; **do not rerun the create-only
deployment helper**, rebuild or upload. Ensure the local frontend is ready before
the headed browser check. Private admin -> teacher A -> admin sign-in remains
required. The script records statuses, timings, deterministic counts and plan IDs;
tokens stay in browser memory/sessionStorage and are never exported.

Local checks after deployment: 74 backend tests passed (two existing deprecation
warnings); Node syntax, pip check and default-mode frontend build passed. Local checks do not
replace the missing deployed authenticated tests. No application code changed.

Commands run in this resume, in addition to the bounded read-only SDK/HTTP checks:
```powershell
aws login --profile airwise
aws sts get-caller-identity --profile airwise --region ap-southeast-2 --cli-connect-timeout 4 --cli-read-timeout 12
.venv\Scripts\python -m scripts.aws_app --existing-object
# Vite launched hidden from frontend/ with the following arguments:
node node_modules/vite/bin/vite.js --mode d2 --host 127.0.0.1 --port 5173 --strictPort
$env:PLAYWRIGHT_MODULE='C:\Users\Ashwani\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
node scripts/check_d2_real.cjs
.venv\Scripts\python -m pytest backend/tests -q
node --check scripts/check_d2_real.cjs
npm --prefix frontend run build
.venv\Scripts\python -m pip check
git diff --check
```

## Previous resume: blocked by expired authentication

October 9, 2026 IST, resumed from commit `975d31f`. The user reports a successful
console upload to the exact application object below, with expected size
87,392,618 bytes. This attempt did not rebuild or upload anything.

The first bounded read-only check, SDK STS GetCallerIdentity using profile
`airwise` and explicit `ap-southeast-2`, failed before an authenticated response:
`LoginRefreshRequired: Your session has expired or credentials have changed.
Please reauthenticate using 'aws login'.`
SDK limits were connect 4 seconds, read 12 seconds, one total attempt. No retry.
Stopped at this failure as requested. HeadObject and resource-existence checks
were not reached. Console upload success is user-reported, not independently
verified: object size, S3 checksum and custom metadata remain unchecked. The
earlier 404 below is historical, not evidence that the uploaded object is absent.

Resources created in this resume: **none**. No D2 API URL is known. Existing D2
resource presence was not rechecked; the previous checkpoint recorded none.
No model calls, deployed workflow tests or latency measurements occurred. No
application code/configuration, local ZIP, local app or smoke Lambda was changed.

Next, privately refresh temporary browser authentication:
```powershell
aws login --profile airwise
```
Use Sydney (`ap-southeast-2`) if prompted. After sign-in, resume the exact-object
size/checksum and collision checks before resource creation. Do not rebuild or
upload again. No cloud cleanup is required for this attempt because no create
operation ran; the scoped cleanup guidance below still applies to a future deploy.

## Previous checkpoint: blocked before application resource creation

Profile airwise / ap-southeast-2. Temporary assumed-role authentication passed.
The planned application Lambda was absent; HTTP API listing was empty. Standard
IAM initially timed out, then existing role/policy reads passed after the user
reconnected to mobile data. Existing DynamoDB, Cognito client, private bucket
location/public-access blocking and Lambda concurrency preflights passed.

One S3 PutObject attempt failed. No upload retry was made. A subsequent bounded
HeadObject returned HTTP 404 / error code 404. The object is absent. The original
helper did not retain the upload exception class; its concrete cause is unproven.
Future attempts now record only exception class/AWS error code, not private error
contents. Do not infer SCP denial or native incompatibility from this failure.

Created D2 resources: **none**. Actual API URL: **none**. No application Lambda,
role, HTTP API, stage, authorizer, integration or log group was created. Existing
smoke Lambda/bucket settings, local role, table, pool and identities were not altered.
No D2 Bedrock request or Cognito password operation occurred.

## Exact inspected artifact and console upload

Filename: `airwise-app-d2.zip`

Absolute path:
```text
C:\Users\Ashwani\Documents\Codex\2026-10-08\read-the-attached-airwise-schools-build\outputs\airwise-schools\work\airwise-app-d2.zip
```

- Compressed: **87,392,618 bytes** (above direct 50 MiB upload limit).
- Extracted, all dependencies included: **240,716,360 bytes**.
- Extracted limit: 262,144,000 bytes / 250 MiB, no layers; margin 21,427,640 bytes.
- SHA-256: `43f0c6d1bcfaa051db9f8f45f0502202faeec9f4d4ab95d1941bf3e60e435469`.
- Python 3.12 / Linux x86_64; fresh binary-wheel install from current requirements.
- Static wheel tags, ELF64 little-endian x86_64, absence of Windows binaries,
  ZIP integrity, current backend source equality and checksum checks passed.
- Includes current auth/evidence/workflow code, boto3 1.43.109, botocore 1.43.109,
  awscrt 0.36.0, cryptography 50.0.2 and PyJWT 2.15.1, plus existing native solver
  pins. Does not contain the local work manifest, profile, passwords or tokens.
- Native solver execution of this application ZIP is **not tested**; its handler
  imports and public health ran successfully. Packet A's
  successful ZIP is separate and unchanged. Docker was not needed or proposed.

In the S3 console select Sydney and the existing private bucket
`airwise-smoke-artifacts-a1f7411817`. Use/create these folders: `application`,
then `d2`, then the full SHA-256 string above. Upload this ZIP inside that prefix.
Do not replace `airwise-runtime-smoke.zip`.

Exact destination:
```text
s3://airwise-smoke-artifacts-a1f7411817/application/d2/43f0c6d1bcfaa051db9f8f45f0502202faeec9f4d4ab95d1941bf3e60e435469/airwise-app-d2.zip
```

After console success, resume without rebuilding/re-uploading:
```powershell
.venv\Scripts\python -m scripts.aws_app --existing-object
```
This verifies size and an available actual FULL_OBJECT SHA256/CRC64 checksum.
Custom metadata and multipart ETag are not full-file checksum evidence. Lambda
CodeSha256 must independently equal Base64-encoded local SHA256 after creation.
Existing/partial application resources cause a stop for inspection, not overwrite.

## Configuration (now deployed; workflow not yet verified)

- Lambda `airwise-app-api-a1f7411817`, handler `backend.app.lambda_app.handler`.
- Dedicated role `airwise-app-role-a1f7411817`, trusting Lambda only. Exact existing
  table/partition/transaction and Sydney Nova Lite policies copied into this role,
  plus CreateLogStream/PutLogEvents for this function's streams only. No S3 runtime,
  Cognito administration, STS assume-role or unrelated service permissions.
- Runtime uses Lambda role credentials and nonsecret environment resource IDs;
  local profile/role-assumption behavior remains the local default, not deployed.
- Python 3.12 / x86_64 / 1024 MB / 28-second timeout / reserved concurrency 5.
  No layers, VPC, Function URL, provisioned concurrency or account quota changes.
- HTTP API `airwise-app-api-a1f7411817`, integration 30,000 ms, `$default` stage.
  Each application route has JWT authorization; only GET /health is public and
  returns `{ "status": "ok" }`. Local foundation school/docs/schema are omitted.
- JWT issuer: existing Sydney Cognito pool; audience: existing public client ID.
  Cognito password-flow access tokens without aud use client_id at API Gateway.
  Require `aws.cognito.signin.user.admin` scope to exclude ID tokens; this is NOT
  school administrator authorization. Backend still independently checks signed
  access token_use, client_id, issuer, expiry and trusted school/teacher bindings.
- CORS allows exactly `http://127.0.0.1:5173`, Authorization/Content-Type and
  GET/POST/PUT/OPTIONS. No wildcard/hosted origin. Gateway handles preflight only.
- Stage 5 requests/second, burst 10; paid routes 0.2/second, burst 1 (best-effort
  throttles). Existing authenticated ten-attempt daily allowance remains the
  server-side cost control; no automatic model/mutation retry added.
- Lambda SDK: connect 2 seconds, DynamoDB read 3 seconds, Bedrock read 18 seconds,
  one total attempt. Forecast/JWKS limits remain finite. Body cap: 250,000 bytes;
  existing input/output/model limits remain. HTTP timeout is not a success signal.
- Seven-day groups: `/aws/lambda/airwise-app-api-a1f7411817` and
  `/aws/apigateway/airwise-app-api-a1f7411817`. Log route template/status/duration
  only, never JWT, request body, notice text or credentials. Project/Packet tags.

## Verification still required

No actual API integration durations are available. Cold/warm live forecast,
bounded actual analysis and independently validated planning must be measured
against the fixed HTTP API 30-second limit. Whether durable jobs/polling are needed
is **unresolved**, not assumed safe. No untracked background work was introduced.
If measurement cannot establish adequate margin, implement durable authenticated,
idempotent jobs before calling this deployment complete. Model calls interrupted
after reservation can leave the existing PENDING claim; do not blindly retry them.

Read-only component measurement used the existing trusted administrator binding
and canonical stored input, without saving a draft or altering records: local
canonical input reads took 3,516 ms; repair plus independent validation took
203 ms, OPTIMAL, all 240 activities retained. These are local component timings,
NOT Lambda or end-to-end API timings. Analysis was not called for this benchmark.

After upload: verify actual configuration/retention/CodeSha256, health, 401 without
access token, ID-token rejection, privately entered administrator/teacher access,
live forecast provenance, one bounded Nova request, confirmation, generation,
validation, approval, acknowledgement/report, review, teacher/cross-assignment
403, stale 409 and persistence across Lambda invocations. Passwords never reset.

Frontend support is connected to the deployed endpoint through ignored
`frontend/.env.d2.local` with VITE_API_BASE_URL,
VITE_COGNITO_REGION, VITE_COGNITO_POOL_ID and VITE_COGNITO_CLIENT_ID (public IDs
only), then start Vite with `--mode d2` on port 5173. Default mode still uses the
local backend. Auth config on the deployed API itself is JWT-protected, so the
public Cognito bootstrap identifiers come from this normal build configuration.
Exact hosted origin can be added later; frontend deployment is out of scope.

## Previous checkpoint commands and checks

Bounded read-only SDK STS/Lambda/IAM/API/DynamoDB/Cognito/S3/account-concurrency
preflights, one PutObject and one post-failure HeadObject. No resource creation.
Existing identity lookup/input reads and the local component benchmark were
read-only; no app password was requested, printed or changed.
```powershell
.venv\Scripts\python -m scripts.package_app
.venv\Scripts\python -m scripts.aws_app
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python -m pip check
npm --prefix frontend run build
$env:PLAYWRIGHT_MODULE='C:\Users\Ashwani\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
node scripts/check_d1_browser.cjs
git diff --check
```
74 tests passed, two existing deprecation warnings; pip check/build and controlled
D1 five-size browser regression passed. The new route test initially expected the
wrong parameter label and failed; corrected to canonical plan_id, then passed.
OpenAPI expansion is used because this FastAPI version keeps included routers
lazy in app.routes. Local success is not deployed authentication/native proof.

## Cleanup of actual D2 resources

No cleanup executed. First verify Project=AirWiseSchools / Packet=D2 tags and
resource names in the console/manifest. Delete only the dedicated D2 resources:
```powershell
aws apigatewayv2 delete-api --api-id lbckjkbfb4 --profile airwise --region ap-southeast-2
aws lambda delete-function --function-name airwise-app-api-a1f7411817 --profile airwise --region ap-southeast-2
aws logs delete-log-group --log-group-name /aws/lambda/airwise-app-api-a1f7411817 --profile airwise --region ap-southeast-2
aws logs delete-log-group --log-group-name /aws/apigateway/airwise-app-api-a1f7411817 --profile airwise --region ap-southeast-2
aws iam delete-role-policy --role-name airwise-app-role-a1f7411817 --policy-name airwise-app-runtime --profile airwise --region ap-southeast-2
aws iam delete-role --role-name airwise-app-role-a1f7411817 --profile airwise --region ap-southeast-2
aws s3 rm s3://airwise-smoke-artifacts-a1f7411817/application/d2/43f0c6d1bcfaa051db9f8f45f0502202faeec9f4d4ab95d1941bf3e60e435469/airwise-app-d2.zip --profile airwise --region ap-southeast-2
```
Deleting the HTTP API removes its authorizer/integration/routes/stage. Deleting
the Lambda removes its resource-based invocation permission. Preserve the reused
bucket/table/pool/client/users/local runtime role/smoke function and smoke object.
These commands do not remove synthetic workflow history in the reused table.

## Previous cleanup guidance (before creation)

Nothing new needs cloud cleanup now. Retain the local ZIP for the console handoff.
After a successful D2 deployment, inspect Project=AirWiseSchools/Packet=D2 tags
and the recorded API ID before deleting only the D2 API, application Lambda,
its two log groups, role/inline policy and the exact application artifact key.
Never delete the reused bucket, DynamoDB table, Cognito pool/client/identities,
local runtime role, smoke Lambda or smoke artifact as D2 cleanup.
No cleanup commands were executed.

Sources checked: [Lambda limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html),
[HTTP API fixed timeout](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html),
[JWT audience/client and scopes](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html).
