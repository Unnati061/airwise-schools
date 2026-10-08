# Packet D1 local interface

React at http://127.0.0.1:5173 proxies the local FastAPI backend on port 8002.
No new infrastructure or dependencies are required. Existing Sydney Cognito,
DynamoDB and bounded Nova Lite services remain the backend dependencies.

## Connected views

- Today: regional PM2.5/PM10, valid times, provenance, retrieval age and missing
  model issue time. LIVE and invented SYNTHETIC REPLAY remain separate.
- Evidence & restrictions: official advisory excerpts, unverified pasted notices,
  bounded explicit interpretation, unsupported instructions and ambiguity review.
  Only an authenticated administrator can confirm reviewed dates and periods.
- Plan comparison: original/proposed activities, backend counts, solver status,
  independent validation, baseline recommendation and authenticated approval.
- Teacher inbox: only the verified teacher's assignments, separate acknowledgement
  and execution reporting, current and historical approved versions.
- Review: actual planned counts, unique execution-report counts, unresolved
  exceptions, resolution notes, approval versions and audit history.

No exposure, health-benefit, accuracy or legal-activation metrics are inferred.
Single-period activities and one fictional school remain the MVP scope.

## Authentication and requests

The public auth configuration returns only the existing region, pool and public
client identifiers. Browser Cognito InitiateAuth uses USER_PASSWORD_AUTH; backend
JWT verification and school/teacher permissions remain authoritative. There is no
role selector or public protected-data bypass. Passwords are not persisted.

Access/refresh tokens are held in tab-scoped sessionStorage for refresh support,
never URLs, logs, localStorage or repository files. This local MVP remains exposed
to same-origin script compromise; production CSP and hardened session design are
not implemented here. Sign-out removes the local session, but does not revoke an
already-issued JWT remotely (existing access lifetime: 15 minutes).

Before protected requests, expiring sessions refresh once through Cognito.
401 clears the session. Request/body timeouts are bounded. There is no automatic
mutation or paid-model retry. Approval uses the existing draft idempotency;
execution is keyed by version/activity; resolution retries reuse their request ID.
An unknown network result requires inspection before a deliberate retry.

Private user password setup is a separate user action; the interface and browser
checks never reset passwords. Real verification pauses for manual browser sign-in.
No traces, HAR files or persisted browser credential state are recorded.

## Compatible backend additions

Generated OpenAPI types include nonsecret auth configuration, verified /me,
immutable input lookup, approved-version history/detail, own historical teacher
assignments/reports and administrator execution summaries. All sensitive read
routes enforce existing actor/school/teacher permissions. Frozen approved plans
and evidence bindings are not substituted with current mutable inputs.

Execution summaries count one latest report per activity/version. Acknowledgement
is not execution. A later exception reopens a previously resolved activity.
Teacher history remains read-only when no longer current; acknowledgements do
not transfer across versions. No solver or validator logic is replaced.

## Checks

`python -m pytest backend/tests -q`: 70 passed, two existing deprecation warnings.
`npm --prefix frontend run build`: passed. `python -m pip check`: passed.

`scripts/ui_fixtures.py` and `scripts/check_d1_browser.cjs` provide explicitly
OFFLINE synthetic browser checks, with mocked Cognito/API responses, not proof of
real authentication or persistence. Five views, desktop/mobile document overflow,
ambiguity review, unsupported instructions, simulated stale approval, explicit
analysis-call count, refresh/logout and role navigation passed.

`scripts/check_d1_real.cjs` uses real local backend endpoints and private user
sign-in, with labelled synthetic replay and one explicit interpretation request.
Real completion passed on October 9, 2026 IST with private manual Cognito sign-in:
actual replay-bound interpretation and explicit review/confirmation, OPTIMAL
validated approval, teacher acknowledgement, COULD_NOT_IMPLEMENT report, reload,
then administrator exception/approval/audit history. Approved version
`aecb1ac8-fa27-4f54-912f-754aa01692e7`: 0 changed periods, 1 substitution,
0 deferrals, 1 room move; original Monday period 2 retained, approved classroom
movement in room-6-a. Review: one report and one unresolved exception, no completion.
Older approved versions and reports remained visible.

The first real generation was correctly rejected with 409 during a data-refresh
race. Canonical input fetching and refresh guards fixed the handoff; the resumed
check used AIRWISE_RESUME_CONFIRMED=1 and did not repeat a paid interpretation.
Windows scaling exposed clipping from the test browser's forced viewport. The
headed real check now uses viewport:null and a maximized window. Labelled sign-out
visibility and body overflow passed at 1440, 1280, 1024, 768 and 390 pixels.

Real reload is verified; expiry-triggered refresh, permission faults and stale
approval injection are controlled browser tests plus independent backend tests,
not a claim of live concurrent requests or waiting out a real Cognito expiry.
MFA/new-password challenges display an error and require private setup outside
this MVP. History uses existing complete repository queries without UI pagination;
the small synthetic-school dataset is the tested scale.

## Click-through demonstration

Sign in as synthetic-admin, open Today and select LIVE or labelled replay.
Evidence & restrictions shows official excerpts and an unverified notice. Explicit
interpretation consumes the existing daily allowance; review dates, periods and
ambiguities before confirmation. Plan comparison generates from canonical inputs,
shows validation/differences and approves through the existing endpoint.

Sign out in the header, sign in as synthetic-teacher-a, acknowledge the specific
approved version and report an execution result separately. Sign out and return
as synthetic-admin to Review to inspect exceptions, record a resolution note and
select older approved versions. The current saved synthetic exception can be
inspected without another interpretation or approval request.

Existing source/observation/model limitations remain in EVIDENCE.md. Localhost
only, no deployment, no new cloud resources, no automatic closure or publishing.
