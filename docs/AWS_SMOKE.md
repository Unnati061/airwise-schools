# Private Lambda runtime smoke - 2026-10-08 IST

Status: BLOCKED by AWS organization policy before any resource creation.
Local configuration and package checks passed; real Lambda execution did not run.
No AWS solver result or runtime compatibility success is claimed.

## Package and configuration

Original ZIP remains untouched at work/airwise-lambda.zip. Derived smoke archive
work/airwise-runtime-smoke.zip changes only backend/app/lambda_smoke.py, retaining
all pinned dependencies. The handler imports the existing CP-SAT smoke solver,
returns health, solver status/periods/objective, Python and machine architecture,
plus OR-Tools, NumPy, pandas, protobuf, FastAPI, Pydantic and Mangum versions.
The response is also written to the function log without credentials or inputs.

- Compressed: 61,637,194 bytes (58.78 MiB).
- Uncompressed: 190,107,573 bytes (181.30 MiB), including dependencies.
- SHA-256: b78df0eae964653c3ee7f5a7230fab35d11f391d89716262f548fd21b4584e7a.
- No layers; extracted package is below the current 250 MiB limit.
- Exceeds 50 MiB direct Lambda upload limit; S3 code source is configured.
- Native ELF headers checked for 64-bit little-endian x86_64; no Windows binaries.
- Wheel metadata checked for Python 3.12-compatible CPython/abi3 or pure Python
  tags. Linux manylinux wheels are intended for the Python 3.12 Amazon Linux 2023
  runtime; static checks cannot establish dynamic-link compatibility on Lambda.
- Profile airwise, region us-east-1; Python 3.12; architecture x86_64.
- Handler backend.app.lambda_smoke.handler; 1024 MB; timeout 30 seconds.
- No provisioned concurrency, layers, VPC, triggers, URL, API Gateway or AI calls.
- Tags: Project=AirWiseSchools, Purpose=NativeRuntimeSmoke, Packet=A.

Limits checked against https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html .
Runtime and wheel guidance: https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html
and https://docs.aws.amazon.com/lambda/latest/dg/python-package.html .

## Prepared names (NOT created)

| Resource | Name |
| --- | --- |
| Private artifact bucket | airwise-smoke-artifacts-a1f7411817 |
| Execution role | airwise-smoke-role-a1f7411817 |
| Lambda | airwise-runtime-smoke-a1f7411817 |
| Log group | /aws/lambda/airwise-runtime-smoke-a1f7411817 |
| Artifact object | runtime-smoke.zip |
| Role inline policy | airwise-smoke-logging |

Bucket configuration: BucketOwnerEnforced (ACLs disabled), all four public-access
blocks enabled, AES256 server-side encryption, project tags. No public policy.
Role trust: lambda.amazonaws.com only. Inline permission policy permits only
logs:CreateLogStream and logs:PutLogEvents on this function's log-stream ARN.
No logs:CreateLogGroup permission: the deployer creates the group in advance with
seven-day retention. No managed AdministratorAccess or S3 runtime permissions.

## Commands actually run and results

From repository root, PowerShell:

```powershell
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python scripts/aws_smoke.py prepare
.venv\Scripts\python scripts/aws_smoke.py deploy
aws lambda get-function --function-name airwise-runtime-smoke-a1f7411817 --profile airwise --region us-east-1 --no-cli-pager
.venv\Scripts\python -c "from backend.app.lambda_smoke import handler; handler({}, None)"
.venv\Scripts\python -m pip check
```

- Initial pytest: 3 passed. Final suite: 8 passed, two existing dependency
  deprecation warnings. Added configuration checks reject region/architecture/name
  drift and an oversized package before cloud calls. Prepared manifest validation passed.
- Preparation: CRC, ELF architecture, wheel tags, extracted size and SHA checks passed.
- Local updated handler: OPTIMAL, periods [3,2,1], objective 6; returned versions.
- pip check: no broken requirements.
- Deployment: exit 1; boto3 collision preflight stopped on lambda:GetFunction.
- CLI reproduction: exit 254, AccessDeniedException with the same explicit SCP deny.
- AWS solver result/logs: unavailable, since function creation and invocation did not run.
- No bucket, role, Lambda or log group created; manifest created[] remains empty.
- No dependency changes for runtime packaging and no Docker used.
- Development requirements now include boto3's CRT extra and awscrt 0.36.0 so the
  already-verified airwise temporary login profile is reproducible after reinstall.

Error, account ID redacted:
`AccountFullAccessRole` is denied `lambda:GetFunction` in `us-east-1` by an
explicit AWS Organizations service control policy, policy ID `p-otrwugml`.
The policy's full contents and reason were not available from this response.
It could restrict a service, region or another condition; do not guess which.
IAM privilege expansion cannot override an SCP deny. No bypass was attempted.
Reference: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html .

## Resume and inspect real execution

Ask the account/organization administrator to confirm whether Lambda use in
us-east-1 is permitted and resolve the specific policy constraint. Alternatively,
authenticate airwise into the intended personal account where this use is allowed.
Do not silently change account or region. Re-run the read-only get-function check;
ResourceNotFoundException for this unused name is expected once access is allowed.

Then run scripts/aws_smoke.py deploy. It checks all names before writes, refuses
collisions, uploads the inspected ZIP through S3, creates only the four resources,
records each creation in work/aws-smoke.json, waits for Active and validates the
actual runtime/architecture/memory/timeout/no-layers/no-VPC configuration.
It never updates an existing Lambda. Partial creation requires inspection before
retry, not automatic deletion or reuse of unrelated resources.

The following commands are PREPARED, NOT EXECUTED because deployment was blocked:

```powershell
aws lambda invoke --function-name airwise-runtime-smoke-a1f7411817 --profile airwise --region us-east-1 --invocation-type RequestResponse --log-type Tail --payload '{}' --cli-binary-format raw-in-base64-out work/aws-smoke-response.json
Get-Content work/aws-smoke-response.json
aws logs filter-log-events --log-group-name /aws/lambda/airwise-runtime-smoke-a1f7411817 --profile airwise --region us-east-1
```

Inspect FunctionError and payload, decode LogResult if needed, and match the actual
OPTIMAL/objective 6/unique periods plus returned dependency versions and x86_64
Python 3.12 to the package. CloudWatch logs can arrive after the invocation.
Only this gate establishes runtime compatibility. Diagnose the concrete response
and logs before considering dependency changes or a separate Docker fallback.

## Cleanup

No cleanup is currently necessary: zero resources were created. After a later
successful or partial deployment, inspect the manifest and confirm ownership/tags
before running only commands for resources actually created by this spike:

```powershell
aws lambda delete-function --function-name airwise-runtime-smoke-a1f7411817 --profile airwise --region us-east-1
aws logs delete-log-group --log-group-name /aws/lambda/airwise-runtime-smoke-a1f7411817 --profile airwise --region us-east-1
aws iam delete-role-policy --role-name airwise-smoke-role-a1f7411817 --policy-name airwise-smoke-logging --profile airwise
aws iam delete-role --role-name airwise-smoke-role-a1f7411817 --profile airwise
aws s3api delete-object --bucket airwise-smoke-artifacts-a1f7411817 --key runtime-smoke.zip --profile airwise --region us-east-1
aws s3api delete-bucket --bucket airwise-smoke-artifacts-a1f7411817 --profile airwise --region us-east-1
```

No recursive deletion, IAM policy broadening or organization-policy editing is
part of this tooling. Future storage/logging costs persist until cleanup;
seven-day retention limits log history, not resource lifetime or total cost.
