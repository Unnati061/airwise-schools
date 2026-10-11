# Deployment

The hosted application uses existing resources in ap-southeast-2 (Sydney),
profile airwise. Inspect ownership before any operation; do not rerun create-only
helpers, alter the separate smoke-test Lambda or broaden permissions.

| Resource | Existing identifier |
| --- | --- |
| Hosted app | https://main.d29v8cmldu93l3.amplifyapp.com |
| Amplify app / branch | d29v8cmldu93l3 / main |
| HTTP API | lbckjkbfb4 |
| API URL | https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com |
| Application Lambda | airwise-app-api-a1f7411817 |
| Execution role | airwise-app-role-a1f7411817 |
| DynamoDB on-demand table | airwise-b2-data-a1f7411817 |
| Cognito pool | ap-southeast-2_LhIz6g1r9 |
| Public Cognito client | 5gq58g4sp2o7ic7grg8k7cld2 |
| Local scoped runtime role | airwise-b2-runtime-a1f7411817 |
| Private artifact bucket | airwise-smoke-artifacts-a1f7411817 |
| Bedrock model | amazon.nova-lite-v1:0 |

These resource/client identifiers are not credentials. Project=AirWiseSchools
tags identify owned resources. Lambda uses its execution role, never a copied
local AWS profile. No password, token or presigned URL belongs in a build or Git.

## Runtime Configuration

- Python 3.12/x86_64, 1024 MB memory, 28-second Lambda timeout, reserved concurrency
  five; no provisioned concurrency. HTTP integration timeout is 30 seconds.
- Default API throttles: rate five/burst ten; analysis/explanation: rate 0.2/burst
  one. Seven-day CloudWatch retention; logs omit bodies, passwords and tokens.
- Runtime permissions are scoped to the exact table, model and logging.
- Health is public/status-only. Application routes require Cognito access-token
  JWT/scope and independent backend school/administrator/teacher authorization.
- Exact CORS origins: http://127.0.0.1:5173 and the hosted app URL above. Direct
  Cognito password/refresh authentication has no OAuth callback or role selector.
- Paid analysis has bounded requests, no automatic retries and a server-enforced
  daily allowance. Measured synchronous requests fit the integration timeout, but
  a few samples do not establish reliability or scale. Concurrency can throttle;
  do not increase limits speculatively or load-test the shared demonstration.

## Build and Update

Use [setup](SETUP.md) for public frontend configuration and private authentication.
Build frontend assets with the actual API/Cognito variables set:

```powershell
npm --prefix frontend run build -- --mode d2
```

Environment files containing private local settings are ignored and not supplied
by cloning. Verify the build contains the intended public API URL before hosting.
Frontend-only changes require an Amplify deployment, not a Lambda redeployment.
Keep the browser notice asset with the published assets.

Backend packaging must use Linux Python 3.12/x86_64 wheels, never Windows
site-packages. The existing update_product/update_features tools reuse verified
dependency bytes, retain notices and check ownership, prior code hash and RevisionId.
Their pinned source ZIP/hash and ignored work/*-deployment.json state are specific
to a release: inspect and prepare a fresh record before use. Do not blindly rerun
historical commands or overwrite preserved artifacts.

Check extracted size against Lambda's 250 MiB limit, native architecture, local
SHA256, S3 supported FULL_OBJECT checksum and Base64 Lambda CodeSha256. An
interrupted upload means object existence is unknown until checked. Stop retries;
use the exact preserved ZIP for a console upload if needed. Custom metadata and
multipart ETag are not verified SHA256. Keep the previous working artifact.

The working backend artifact is 87,594,462 bytes compressed / 241,244,926 bytes
extracted; SHA256 `5542f63b96936ba91094400eb3176b75c840eac61710d20f2474b03822cd0214`.
It contains private native binaries, not a cleared public binary release.
See [native redistribution](NATIVE_REDISTRIBUTION.md) before transferring archives.

After any update, verify published asset bytes and privately authenticated
administrator/teacher workflows. Replay approval must stay current after reload;
explicit input changes must preserve the old approval while marking it stale.
Revised drafts need independent validation and separate approval. Check teacher
permissions, report idempotency, persistence and logout; screenshots stay outside Git.
Read-only health or a successful ZIP upload is not sufficient verification.

## Retiring Resources

Nothing is deleted automatically. Confirm ownership and dependencies first.
Application-only retirement covers HTTP API lbckjkbfb4, the application Lambda and
its /aws/lambda/airwise-app-api-a1f7411817 log group, and its dedicated role after
removing only that role's inline policy. Delete Amplify app d29v8cmldu93l3 only
when the hosted URL is no longer required.

The table, pool, local runtime role, bucket and smoke Lambda are shared; do not
include them in application-only cleanup. Target only exact unused artifact keys,
never recursively empty the shared bucket. Preserve approved history/evidence or
deliberately export it before any separate data-retirement operation.
