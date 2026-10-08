# Packet A status - 2026-10-08 (IST)

## Current verified checkpoint

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
