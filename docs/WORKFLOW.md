# Packet B2 durable local workflow

## Actual resources

All in ap-southeast-2, profile airwise. Project=AirWiseSchools, Packet=B2,
Purpose=SyntheticApprovalExecution tags on the table, user pool and runtime role;
client/users/policy are children of those tagged resources (no independent tag API).

| Resource | Actual identifier |
| --- | --- |
| DynamoDB table | airwise-b2-data-a1f7411817 |
| Cognito LITE user pool | airwise-b2-users-a1f7411817 / ap-southeast-2_LhIz6g1r9 |
| Public app client (no secret) | airwise-b2-local / 5gq58g4sp2o7ic7grg8k7cld2 |
| Runtime role | airwise-b2-runtime-a1f7411817 |
| Inline policy | airwise-b2-table-runtime |
| Synthetic users | synthetic-admin, synthetic-teacher-a, synthetic-teacher-b |

Table verified ACTIVE, PAY_PER_REQUEST, SSE ENABLED; no indexes, provisioned
capacity, streams or TTL. No new Lambda, public endpoint, gateway, VPC, custom KMS
key, messaging, dashboards or AI calls. Packet A smoke resources were untouched.
Pool is admin-created-users only, no self-registration, no client secret or M2M
flow, no MFA/SMS/email delivery, 16-character password policy. Access/ID tokens
last 15 minutes; refresh tokens one day. Recovery is admin-only.

Runtime trusts the already authenticated AccountFullAccessRole, not the public.
Its policy grants only GetItem on the exact table's synthetic school/identity
partitions, Query on the synthetic school partition, and PutItem on that partition
only inside TransactWriteItems. No Scan, DeleteItem, table administration, identity
binding writes or Cognito admin rights. Local code assumes this role using temporary
STS credentials with automatic refresh; the deployment profile is not used for
runtime table operations. The role ARN's account ID is omitted from this document.
IAM transaction permissions use underlying item actions, per [AWS documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis-iam.html).

## Private demonstration

Backend is running at http://127.0.0.1:8002; old B1 server was stopped. All
operational routes require a verified Cognito access token; health/school and
OpenAPI schema remain public local foundation metadata, not operational records.
No memory/auth bypass is enabled, even if configuration or AWS is unavailable.

From repository root, set passwords privately for the dedicated synthetic users:

```powershell
.venv\Scripts\python -m scripts.b2_client set-password --username synthetic-admin
.venv\Scripts\python -m scripts.b2_client set-password --username synthetic-teacher-a
```

Passwords are prompted with getpass and never printed or saved. Then:

```powershell
.venv\Scripts\python -m scripts.b2_client demo --username synthetic-admin
.venv\Scripts\python -m scripts.b2_client demo --username synthetic-teacher-a
```

Administrator command uses real Cognito password authentication, confirms fixture
if needed, generates a draft from confirmed inputs and approves it. Teacher
command signs in separately, reads only their assignments, acknowledges that
version, then separately reports Mon-2 COMPLETED. It refuses its demonstration
when the plan needs review. Tokens remain in process memory, not shell arguments,
files or output. Username roles in this helper select requests only; the backend
enforces all actual permissions independently.

If restarting the backend (ignored work/aws-b2.json retains non-secret resource IDs):

```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

The self-contained synthetic regression demo actually executed:

```powershell
.venv\Scripts\python -m scripts.b2_demo
.venv\Scripts\python -m scripts.b2_demo --http-smoke
```

It resets only the three dedicated pool users to random memory-only passwords,
signs in with real Cognito, uses authenticated local ASGI HTTP requests and real
DynamoDB, and starts a fresh backend interpreter to verify persistence. No dependency
overrides, fake Cognito, fake DynamoDB or authentication bypass are used in this
integration check. It creates synthetic version/report/audit documents, not AWS
resources, and leaves its current approved version intact. Private set-password
commands above restore usable interactive passwords afterward.
The --http-smoke mode actually exercised the running loopback HTTP server using
real Cognito tokens: administrator approval, both teachers' assignment permissions,
teacher acknowledgement and a repeated COMPLETED report with exactly one total.
It verified the frozen approved snapshot contains all 240 activities. Actual final
version: 4a905e76-acfb-4768-abc9-eba452e7272e.

## Storage and concurrency

Table pk is synthetic-school-001, with sk prefixes INPUT, RESTRICTIONS, DRAFT,
APPROVED, STATE, ACK, REPORT, RESOLUTION and AUDIT. IDENTITIES is a separate read-only
runtime partition keyed by Cognito sub, binding administrator or teacher to school
and teacher ID. Only two of the fixture's six teachers have sign-in accounts.

Authenticated confirmation generates school/timetable/restriction versions on the
server and overwrites confirmed_by with verified sub. The whole input update is
compare-and-swap against expected_revision; stable activity IDs must be retained.
Room availability or restriction changes use POST /inputs with the current revision.
Snapshot, restrictions, needs_review state and audit are one transaction.
Any confirmed revision conservatively marks an existing approved plan for review.
An existing approved pointer is never replaced by input update or draft generation.

POST /draft-plans requires the exact current confirmed snapshot. First approval
uses the independent validator again and compares both versions and full snapshot.
Approved schedule snapshot, current pointer and audit are atomically conditional.
Draft ID is the stable approved plan version and durable approval idempotency key.
Concurrent conflicts return 409 unless the same approval receipt already exists.
Repeated approval of an older version returns its original receipt, not a pointer
update. Early integration receipts without frozen snapshots retain their immutable
draft reference for compatibility; all final-code approvals freeze their own copy.

ACK is version/teacher-specific and has no execution effect. REPORT is unique by
version/activity: identical retries return the same report without duplicate audit;
changed statuses replace the latest report conditionally and append an audit event.
Totals are counts of unique latest report records, not mutable counters. Reports
on non-current versions or another teacher's activities are rejected. Deferred
activities cannot be reported COMPLETED. Review flags remain visible to teachers;
backend reporting is not silently blocked by review, allowing clarification reports.

Exception reports are inspected by administrator; resolution notes are separate
records keyed by plan/activity/request UUID. Reports, resolutions and activity
audit events retain verified actor, timestamp, activity ID and plan version.
Whole-plan/input audit actions have null activity_id; pre-approval input actions
can have null plan_version. Old acknowledgements never transfer to new versions.

## Actual checks

Commands run: python -m scripts.aws_b2; python -m scripts.b2_demo;
python -m pytest backend/tests -q; python -m pip check; OpenAPI type generation
from port 8002 and npm run build. Provisioning preflight initially timed out at
https://iam.amazonaws.com/ via SDK and CLI with no writes. Regional read-only
DynamoDB returned ResourceNotFound and Cognito succeeded. After the user restored
mobile data, standard-endpoint preflight/provisioning succeeded; no TLS bypass,
SCP change, alternate account or region was used.

Local suite: 51 passed, two existing Starlette/Mangum warnings. pip check passed;
OpenAPI contracts and frontend TypeScript/Vite build passed. B1 solver/validator
remain unchanged. New dependency pins were installed and checked, including
PyJWT 2.15.1, cryptography 50.0.2 and existing boto3/CRT runtime dependencies.

Real integration checks passed for authenticated restriction confirmation;
teacher approval denied; both cross-teacher assignment reads denied; fresh-process
persistence; duplicate/concurrent approval with one current version and one audit;
acknowledgement without execution; repeated report with one total; administrator
exception resolution; revision requiring approval; stale and deliberately corrupted
draft rejection; old acknowledgement and duplicate approval not transferring or
rewinding; and new-version COMPLETED report counted once.
Local tests additionally cover room-only availability review and approved snapshot
independence from draft mutation. Diagnostic corrupt drafts are labelled SYNTHETIC
and injected through private test tooling, never a public mutation endpoint.

## Limitations and cleanup

Single synthetic school, one affected day, single-period activities; no real pupils,
evidence feeds, polished sign-in UI, deployment of this backend, production MFA,
backups/PITR, retention policy, granular multi-school IAM or credential recovery UI.
Compressed documents are capped at 350 KB to stay below the [400 KB DynamoDB limit](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html).
Small school-scoped history queries paginate internally but return the full result;
large histories need bounded API pagination before production.
Offline JWT verification checks RS256/JWKS, issuer, expiry, access token_use and
client_id as [Cognito documents](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html).
Logout/disable does not invalidate cached tokens immediately; expiry bounds that
window to 15 minutes. No production security/readiness claim. Provider, local
configuration and runtime role must be available; errors fail closed.

Resources persist and can incur database/auth costs; no exact dollar cost claimed.
After confirming ownership/tags, stopping the local backend and intentionally
retiring synthetic data, cleanup commands (NOT executed) are:

```powershell
aws cognito-idp delete-user-pool --user-pool-id ap-southeast-2_LhIz6g1r9 --profile airwise --region ap-southeast-2
aws dynamodb delete-table --table-name airwise-b2-data-a1f7411817 --profile airwise --region ap-southeast-2
aws iam delete-role-policy --role-name airwise-b2-runtime-a1f7411817 --policy-name airwise-b2-table-runtime --profile airwise --region ap-southeast-2
aws iam delete-role --role-name airwise-b2-runtime-a1f7411817 --profile airwise --region ap-southeast-2
```

Deleting the pool deletes its client/users. These commands never target the
Packet A smoke bucket, role, log group or Lambda. Provisioning refuses existing
names/manifests; inspect partial resources rather than resetting or overwriting.
