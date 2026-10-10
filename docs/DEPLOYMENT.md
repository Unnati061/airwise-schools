# Deployment

Existing resources use profile airwise in ap-southeast-2 (Sydney). Do not rerun
create-only helpers, broaden permissions, change account/region or alter the
separate smoke-test Lambda. No credentials are in browser builds or ZIPs.

| Resource | Existing identifier |
| --- | --- |
| Hosted app | https://main.d29v8cmldu93l3.amplifyapp.com |
| Amplify WEB app / branch | d29v8cmldu93l3 / main |
| HTTP API | lbckjkbfb4 |
| API URL | https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com |
| Application Lambda | airwise-app-api-a1f7411817 |
| Application execution role | airwise-app-role-a1f7411817 |
| DynamoDB PAY_PER_REQUEST table | airwise-b2-data-a1f7411817 |
| Cognito pool | ap-southeast-2_LhIz6g1r9 |
| Public Cognito client | 5gq58g4sp2o7ic7grg8k7cld2 |
| Local scoped runtime role | airwise-b2-runtime-a1f7411817 |
| Private artifact bucket | airwise-smoke-artifacts-a1f7411817 |
| Bedrock model | amazon.nova-lite-v1:0 |

Project=AirWiseSchools tags identify owned resources. Lambda is Python3.12/x86_64,
1024 MB, 28-second timeout, reserved concurrency five, no provisioned concurrency.
HTTP integration timeout is 30 seconds; default throttles are rate five/burst ten,
with rate 0.2/burst one on the paid analysis/explanation routes.
CloudWatch retention is seven days. Runtime access is scoped to the exact table,
model and logging, not administrator credentials. Health is public/status-only;
application routes use Cognito JWT/access scope and independent backend role checks.

CORS allows only http://127.0.0.1:5173 and the exact hosted origin. Direct Cognito
password/refresh sign-in has no OAuth callback flow. No callbacks or role selector
are needed. Local and hosted app configuration contains only public identifiers.

## Updating Existing Resources

The proven packaging approach installs Linux Python3.12 binary wheels, never
Windows site-packages. Product updates reuse verified dependency bytes from the
preserved release ZIP, replace application source/data and retain full notices.
Check compressed/extracted sizes, 250 MiB extracted limit, ELF architecture,
local SHA256, S3 FULL_OBJECT checksum and Base64 Lambda CodeSha256.

```powershell
npm --prefix frontend run build -- --mode d2
.venv\Scripts\python -m scripts.update_product package
.venv\Scripts\python -m scripts.update_product preflight
.venv\Scripts\python -m scripts.update_product update
```

These one-shot commands refuse existing/partial artifacts. Inspect state first;
do not blindly rerun them. The ignored work/product-deployment.json records the
exact artifact/key/stage without credentials. An interrupted S3 PUT does not prove
absence: stop, inspect the exact object and use the preserved file for console
upload. resume-existing verifies a supported full-object checksum and skips PUT.
Never treat custom metadata or multipart ETag as verified SHA256.

The updater checks ownership, prior code hash and RevisionId, updates only the
application Lambda, then manually deploys dist to the existing Amplify main branch.
Presigned URLs are never printed/persisted. Keep the previous working artifact.
Use real private Cognito browser verification before claiming the update works.

## Current Product Build

October 11, 2026: application ZIP 87,594,316 bytes compressed /241,244,231 bytes
extracted, Python3.12/x86_64. SHA256
`d76e76084641e125d3b5cce57735078695a5299ed56cee05ca0e1d808521240e`.
All 198 ELF entries and third-party notices were retained byte-for-byte from the
previous working release. S3 FULL_OBJECT SHA256
`1252CEZB4SXTtczldzUHhpWlKZ7VbO4Fyg4dgIUhJA4=` matches local bytes; Lambda
CodeSha256 matches using the same Base64 encoding, LastUpdateStatus=Successful.
Exact artifact key:
`application/features/d76e76084641e125d3b5cce57735078695a5299ed56cee05ca0e1d808521240e/airwise-app-features.zip`.

The single application upload completed; no retry or console upload was needed.
Existing Amplify jobs 4 and 5 succeeded; job 5 includes the verified mobile row
correction, static ZIP 137,921 bytes. No resources, roles, routes, CORS, model,
timeout/concurrency settings or smoke Lambda were added/changed. Commands were
update_product package/preflight/update and the static-only host-frontend action.
94 backend tests pass (two existing deprecation warnings), generated contracts
and production build pass, and labelled offline presentation/recovery checks pass.
Actual private Cognito hosted verification passed: administrator confirmed the
shared-teacher/room sample, generated an OPTIMAL independently validated repair
and approved it. All 240 weekly activities and the fixed lesson were retained;
two periods changed, two indoor substitutions and two room moves, no deferrals.
Duplicate approval kept the same current version. The teacher acknowledged it
without execution, recorded one could-not-implement exception and reused the
report receipt without duplication. Teacher approval, other-teacher assignments
and administrator-input access returned 403. After fresh administrator sign-in,
Review/Today showed one report, zero completions, one unresolved exception and
the persisted current version/history. Desktop 1440 and mobile 390 checks passed.
Sign-out followed by reload returned to sign-in. The headed verification runner
now uses natural window sizing for private sign-in: fixed screenshot emulation
had clipped controls on the owner's scaled display. No product workaround,
password reset or additional approval was needed to resume the teacher check.
Public HTML/assets and the unchanged third-party browser notice matched local
build bytes. This presentation pass made zero Bedrock calls.

## Runtime Limits

Previously verified hosted admin/teacher approval, reports, stale-version rejection,
permission denials, JWT tamper/ID-token rejection and session refresh/local logout.
One actual Nova request took 2,392 ms browser /978 ms handler /992 ms integration;
planning samples took 18,948 ms and 5,429 ms browser time. These are request-path
samples, not a service-latency distribution or reliability SLA.

An earlier single 503 coincided with a Lambda throttle at concurrency five, but
request-level causation remains unproven. No speculative concurrency fix was made.
Configured throttles were read back; 429 enforcement was not established by those
checks. No load test, extra model call or resource change is justified by that record.
Spending/remaining credits/expiry require the owner's billing-console check after
previous read-only access timeouts.

## Cleanup

Nothing is deleted automatically. To retire the application, first confirm ownership
and that no working app depends on each resource. Delete API lbckjkbfb4, Lambda
airwise-app-api-a1f7411817 and its /aws/lambda/airwise-app-api-a1f7411817 log group;
remove only that role's inline policy before deleting the role. Delete Amplify app
d29v8cmldu93l3 only when its hosted URL is no longer needed.

The table, pool, local runtime role, bucket and smoke Lambda are shared across
verified work; do not include them in application-only cleanup. Artifact cleanup
must target the exact unused object key, never recursively empty the shared bucket.
Preserve approved history/evidence or intentionally export it before any separate
data-retirement task. Private native archives are not cleared for public release;
see NATIVE_REDISTRIBUTION.md.
