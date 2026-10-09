# Amplify Hosting - October 9, 2026 IST

## Verified Follow-up

Follow-up from1b8c067 reused this app/main; manual job2 SUCCEED, staticZIP89,012
bytes. No frontend secrets, dependency/auth/CORS changes or new resources.
Existing Lambda also updated; exact artifact/checksum in FEATURE_COMPLETION.md.
Actual private admin -> teacher A -> admin sign-in passed approval, reviewed
English/Hindi previews, acknowledgement/completion, UUID receipt replay,
administrator Review and three teacher permission denials. Actual1440x960 and
390x844 pages had no horizontal overflow. Signed out after verification; no
password resets/token export. Zero paid model calls. Previous analysis timing
below is historical, not repeated or a new benchmark. Existing cleanup unchanged.

## Actual deployment

Public application: **https://main.d29v8cmldu93l3.amplifyapp.com**

Profile `airwise`, region `ap-southeast-2`. Resumed from `4f8bddf`.
Existing Amplify app listing was empty before creation. Created only:
- Static WEB app `airwise-schools-web-a1f7411817`, ID `d29v8cmldu93l3`.
- Production branch `main`, manual deployment job `1`, status **SUCCEED**.
- Tags Project=AirWiseSchools, Packet=Hosting; automatic builds disabled.

No API/Lambda/IAM/data/auth resources recreated or redeployed. No Git repository
connection, custom domain, additional bucket, SSR runtime or new service role.
Amplify manages its hosting/edge infrastructure. Existing application Lambda and
separate smoke Lambda remain unchanged.

Production Vite build uses the existing Sydney API URL and public Cognito IDs:
```text
VITE_API_BASE_URL=https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com
VITE_COGNITO_REGION=ap-southeast-2
VITE_COGNITO_POOL_ID=ap-southeast-2_LhIz6g1r9
VITE_COGNITO_CLIENT_ID=5gq58g4sp2o7ic7grg8k7cld2
```
These are public bootstrap identifiers, not secrets. The existing ignored
`frontend/.env.d2.local` supplied them to `vite build --mode d2`. Default local
mode remains unchanged. Build ZIP contains only dist contents at its root,
not environment/profile files, source maps, passwords or credentials.

Artifact: `work/airwise-hosted-web.zip`, **87,867 bytes**; SHA256
`dd40168600a986ede8f3ae5f7a777d6c20771a299c0db58b94829879ce810974`.
One presigned ZIP upload; its secret URL was never logged or persisted.
Resource record: ignored `work/aws-hosting.json`. Create-only helper refuses
recorded partial resources; inspect existing resources before a future deployment.

## Cognito and CORS

Current sign-in is direct Cognito USER_PASSWORD_AUTH, not OAuth/Hosted UI.
**No callback/logout URLs are required or configured.** No OAuth flows, password
resets or client-secret settings were added. Existing public client supports
USER_PASSWORD_AUTH and REFRESH_TOKEN_AUTH; access/ID tokens 15 minutes, refresh
one day. Callback configuration would be necessary only for a future OAuth flow.

The only API change was CORS: existing exact origin `http://127.0.0.1:5173` plus
`https://main.d29v8cmldu93l3.amplifyapp.com`. Existing methods/headers retained,
no wildcard. Configuration read-back matched. Actual OPTIONS /me returned 204
with the hosted allow-origin header; `https://not-authorized.example` received
204 **without** that header. CORS is browser policy, not an authentication boundary.

## Actual hosted browser verification

Fresh headed Chrome context started signed out. User privately entered passwords
as administrator -> teacher A -> administrator. No password filling/reading,
traces, HAR, storage-state export or credential dumps. Real UI controls exercised
interpretation, restriction confirmation, draft generation, approval,
acknowledgement, report entry, navigation and logout. Supplemental browser API
requests tested forbidden operations; no mocks or authentication bypass.

- Real access token: expected issuer/client/token_use; accepted by deployed API.
  Cognito ID token **403**; malformed token **401**; signature-tampered access
  token **401**. These do not separately prove rejection of a valid token from
  another client or a naturally expired token; targeted backend unit tests cover
  issuer/client/expiry checks. Gateway authorizer config was read independently:
  exact pool issuer and client audience, all 28 application routes JWT/access
  scope; only health unauthenticated. Backend independently checks RS256 access
  token_use, client_id, issuer, expiry and trusted identity/school/teacher binding.
- Forced the browser's local expiry timestamp (not JWT claims) to zero; reload
  performed an actual Cognito refresh-token exchange and restored signed-in UI.
- LIVE forecast read passed: Open-Meteo/CAMS global, retrieved
  **2026-10-09 17:12:51 IST** (11:42:51.302165Z), FRESH retrieval/value checks.
  Provider model issue time unknown; observations unavailable. No model-cycle
  freshness or campus-measurement claim.
- One actual bounded Nova Lite analysis, **amazon.nova-lite-v1:0**, Sydney,
  on a clearly labelled synthetic unverified notice and **REPLAY** evidence.
  SUCCESS, 773 input / 197 output / 970 total tokens. One matching durable
  MODEL_USAGE record verified, not a second model call or old cached result.
  Analysis ID `a44725835550a51e6bea9dc059060effe3df7fca2167ca74e9c9f366011a91d3`.
- Explicit administrator review confirmed restrictions; old draft approval
  rejected **409**. No interpretation automatically confirmed or approved a plan.
- New approved version `acd49a0b-0da2-421c-9d85-c7b7cbd35fcf`: **OPTIMAL**,
  independent validation passed, baseline recommended, **240 activities** retained.
  Section 6A Monday period 2 retained, approved indoor movement in room-6-a
  instead of field. Counts: 0 changed periods, 1 substitution, 0 deferrals, 1 move.
- Teacher A approval, Teacher B assignments and administrator inputs each **403**.
  Own-version acknowledgement succeeded; execution reports remained empty until
  separately reporting **COULD_NOT_IMPLEMENT** for `6-a:Mon-2`.
- Administrator Review visibly displayed the synthetic classroom-unavailable
  note. Counts: 1 reported, 0 completed, 1 could_not_implement, 0 clarification,
  1 unresolved. Nine approved versions retained; current pointer matched.
- Sign out cleared the app auth session; reload stayed signed out after each of
  three sessions. This is **local logout**, not immediate global token revocation.
  Stolen unexpired JWTs may remain accepted by offline verification until expiry;
  tokens in tab-scoped sessionStorage remain an XSS/security-hardening limitation.

## Measured timings and controls

Actual analysis request: **2,392 ms browser network timing**, **978 ms Lambda
handler**, **992 ms API Gateway integration**. These include the respective
request-path work; isolated Bedrock-service latency is not exposed by this code.
One small call is not a latency distribution or large-input reliability proof.

Pre-revision draft: **18,948 ms** browser; revised draft: **5,429 ms**. Both
completed within HTTP API's 30-second integration limit; cold/warm state was not
classified. Retained Lambda 28s, 1024 MB, concurrency 5; bounded one-attempt SDK
and model limits. No untracked background work. These samples alone do not prove
all future requests will fit; the initial transient 503 below remains a reliability
limitation, not a demonstrated need for a new background-job architecture.

Actual stage read: 5 requests/s, burst 10. Paid routes: 0.2/s, burst 1. Four
bounded invalid-token analysis requests all returned **401**, reached no model;
**no 429 was observed**, so burst enforcement is not proven by that test.
Gateway throttles are best effort, not strict spending caps. Existing atomic
ten-attempt authenticated administrator daily allowance, identical-request cache,
3,000-character notice cap, 14KB supplied model payload and 700 output-token cap
remain server-side; no auto-retry of model or approval mutations was added.

Actual CloudWatch scan: preceding 60 minutes, **714 events**, both application
Lambda/API groups, pagination completed, **zero tested credential/notice patterns**.
Matched patterns included JWTs, Bearer values, AWS keys, token/secret/password
fields and the synthetic test notice/report text. Raw matches/log contents were
not printed or written. Access-log format contains requestId/route/status/latency;
handler logs route template/status/duration. No headers or bodies configured.
Limited regex inspection is not a comprehensive guarantee for all future logs.
Seven-day retention remains; no new logging/permissions infrastructure.

## Failures and repairs

First hosting helper attempt: read-only preflight **ReadTimeoutError**, before
resource creation/CORS changes. Initial code omitted the exact endpoint. User
reconnected mobile data and authorized one bounded read-only check; STS, Amplify
listing and API read passed, then the authorized deployment succeeded. Diagnostic
recording now retains precise step/hostname, never secret URLs; regression tests
verify this and preservation of partial manifests.

First hosted browser run: **GET /current-plan 503** caused administrator data not
to load. No authenticated analysis/mutation request reached the backend in that
run. Original harness's unattached response-wait promise escaped its recorder.
Fixed Promise.all handling and response completion waiting; allowed one existing
read-only UI Retry loading action, never a paid/mutation retry. Fresh corrected
run succeeded without needing that retry branch. Final read-only investigation
found one Lambda throttle in the failure minute, peak concurrency five at the
reserved limit, and no matching handler-route 503. Concurrency pressure is a
likely explanation, not a proven request-level cause or SDK error. See
[INCIDENT_503.md](INCIDENT_503.md) for timing, metrics and correlation limits.
No speculative backend dependency, timeout or infrastructure change was made.

## Commands and checks

```powershell
npm --prefix frontend run build -- --mode d2
.venv\Scripts\python -m scripts.amplify_host
$env:PLAYWRIGHT_MODULE='C:\Users\Ashwani\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules\playwright'
node scripts/check_hosted.cjs
node --check scripts/check_hosted.cjs
.venv\Scripts\python -m pytest backend/tests -q
git diff --check
```
Also ran bounded read-only configuration/checksum-independent resource preflight,
JWT/throttle/Cognito reads, rejected-token HTTP requests, CORS preflights, durable
usage lookup and sanitized CloudWatch scans. SDK one attempt, connect 4s/read12-15s;
ZIP upload one attempt/30s. No credential caches inspected.

**76 tests passed**, two existing deprecation warnings; production build and
hosted script syntax passed. Corrected hosted browser run exited 0; safe results
in ignored `work/hosted-verification.json`. No generated API contract changes.
Do not rerun create-only hosting helper against the existing app; inspect/reuse
its app/branch for a future update. No feature redesign or backend redeployment.

## Cleanup (not executed)

Verify Project=AirWiseSchools tags and app ID first. Remove only this hosting app:
```powershell
aws amplify delete-app --app-id d29v8cmldu93l3 --profile airwise --region ap-southeast-2
```
Restore the API's exact original CORS origins, leaving other settings unchanged:
```powershell
aws apigatewayv2 update-api --api-id lbckjkbfb4 --cors-configuration file://docs/hosting-local-cors.json --profile airwise --region ap-southeast-2
```
Inspect current configuration before executing; preserve any later authorized
origins rather than replacing them blindly. No Cognito cleanup is needed: no
callback/client changes. Preserve reused data/auth/model/API/smoke resources;
synthetic evidence/approval/report history remains in the existing table.

Sources checked: [Amplify manual deployment](https://docs.aws.amazon.com/amplify/latest/userguide/manual-deploys.html),
[CreateDeployment](https://docs.aws.amazon.com/amplify/latest/APIReference/API_CreateDeployment.html),
[JWT audience/client and scopes](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html).
