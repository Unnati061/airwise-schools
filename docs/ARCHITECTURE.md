# Architecture

```text
React / Vite on Amplify Hosting
  -> Cognito access-token sign-in
  -> API Gateway HTTP API, JWT authorizer
  -> FastAPI / Mangum, Python 3.12 x86_64 Lambda
       -> OR-Tools CP-SAT + independent Python validator
       -> DynamoDB versioned documents and transactions
       -> Open-Meteo regional forecasts
       -> bounded Sydney Amazon Nova Lite interpretation
```

Local Vite proxies /api to FastAPI on 8002. Pydantic OpenAPI contracts generate
frontend/src/api.d.ts. Production uses the same operations with a status-only
public health route; school data and auth configuration are not public endpoints.

## Identity and Persistence

The backend verifies Cognito RS256 access tokens, fixed issuer, JWKS, expiry,
token_use=access and client_id. API Gateway additionally requires the access-token
scope. Trusted DynamoDB bindings map verified sub to school, role and teacher;
caller-supplied roles and teacher IDs cannot grant authority.

One PAY_PER_REQUEST table holds compressed bounded documents with strongly
consistent reads and conditional transactions. Inputs, restrictions, drafts,
approved snapshots, evidence, acknowledgements, execution reports, resolution notes,
request receipts and audit events retain their versions. PlanRepository is the
save/get boundary; the running API uses DynamoPlanRepository, never memory storage.
Only two sample teachers have sign-in accounts, although the timetable has six.

Confirmation is authenticated and versions the canonical input. Approval reruns the
independent validator, rejects unsuccessful/stale plans and atomically records an
immutable approved snapshot plus the current pointer and audit. Duplicate approval
returns its receipt without moving the pointer. Revisions mark needs_review and
preserve the previously approved version until a separate new approval.

Acknowledgements are version/teacher-specific and are not execution. Reports are
unique by activity/version; durable request UUID receipts make exact retries safe.
Latest unique reports, rather than increment operations, drive totals. Teacher writes
require their own assignment and current approval. Previous versions are read-only.
Administrator resolutions are separate notes with idempotent request IDs.

## Repair Engine

Activities occupy one discrete period. Fixed lessons and unaffected weekdays stay
fixed. Section, room and teacher exclusivity, room capacity/type/availability,
teacher supervision/availability and administrator-confirmed restriction scope are
hard constraints. Alternatives and deferrals enter only with explicit permission.
Stable activity IDs account for every original activity.

A keep-period baseline uses approved classroom alternatives. CP-SAT uses one worker,
seed 42 and one objective encoding changed periods, then substitutions/deferrals,
then room moves lexicographically. Preparation is deducted from a five-second solve
budget; total HTTP latency is not a five-second SLA. Plain-Python validation does not
import or reuse solver constraint-building code. Both baseline and output are
checked. UNKNOWN can recommend a valid baseline but cannot claim optimality or
infeasibility.

The second labelled sample starts from a valid original timetable. A shared PE
teacher, indoor room opening times and a fixed hall lesson compete after an explicit
outdoor restriction. It permits a two-period repair without relaxing constraints.
Sample confirmation follows the existing input/version/approval path.

The room-availability sample declares one reserve studio (capacity 40, Monday
period 4) as an explicitly permitted alternative. The administrator can exclude a
room on the affected day by reviewing and confirming its availability revision,
then generating a draft through the same endpoints. Exploration marks review
needed but does not change the approved snapshot/current pointer. The UI compares
the revised assignments with that approval; a separate approval revalidates and
changes the pointer. A fixed lesson in an excluded hall is a directly verifiable
conflict, not an invented alternative or relaxed constraint.

## Evidence and Model Boundary

[Evidence provenance](EVIDENCE.md) distinguishes regional forecast/model values,
unknown model issue time, unavailable observations and separate invented replay.
Normalized/raw response snapshots and hashes are persisted in the existing table;
no extra raw-response S3 bucket is needed. LIVE/REPLAY cache pointers are separate.

NovaProvider uses boto3 Converse with finite input/output/timeouts, no automatic
model retry and the exact Sydney model. Durable cache claims and daily allowances
are transactional before calls; each authenticated administrator has ten attempts
per India-calendar day. Failed attempts consume allowance. Expired pending claims
are fenced into failure rather than silently calling again.

Notice output is schema-validated against supplied policy citations and activity IDs.
Ambiguities/unsupported instructions require review; pasted notices are unverified.
An administrator explicitly maps dates/weekdays and confirms reviewed restrictions.
EvidenceBinding freezes provenance in the input revision. AI cannot confirm, publish
or approve plans. Explanations, counts, bilingual templates and student-hours are
computed deterministically from validated facts.

## Interface and Runtime

Today separates evidence attention, proposed changes and teacher-reported
implementation. Comparison distinguishes preserved fixed lessons from changed
periods, activities and rooms. Evidence detail and message previews are expandable.
Teacher acknowledgement and execution are separate actions. Safe retry controls
replay exact approval/report requests, not paid analysis.

Cognito passwords are entered privately; public client IDs are not secrets.
Tokens stay in tab-scoped sessionStorage and refresh normally. Logout clears the
local session, not immediate revocation of every unexpired JWT. XSS hardening,
revocation delay and interrupted-tab draft recovery remain limitations.

Lambda uses its scoped role credentials, never a copied local profile. CloudWatch
logs route templates, status and duration, not bodies/tokens/passwords. Exact CORS,
timeouts/concurrency and cleanup are in [deployment](DEPLOYMENT.md).
No SQS, untracked background work, VPC, automatic messaging or new architecture
is claimed. Synchronous paths fit measured samples, not an established latency SLA.
