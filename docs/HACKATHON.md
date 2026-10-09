# AirWise Schools: Hackathon Writeup Draft

Draft for the owner to adapt to actual submission rules. No project submission
or video upload/publication has been performed.

**App:** https://main.d29v8cmldu93l3.amplifyapp.com

## Problem and Users

School administrators need to translate reviewed pollution guidance into a
workable school day without losing lessons, double-booking teachers or assuming
every classroom is suitable. Teachers need specific approved assignments and a
way to say what happened, rather than acknowledgement being counted as execution.
AirWise Schools connects source provenance, constrained repair, human approval
and teacher execution reporting.

This prototype uses one fictional Greater Noida school, six sections and 240
synthetic weekly activities. It is not a real-school pilot and makes no measured
health, exposure-reduction or forecast-accuracy claims.

## What We Built

Five views connect Today, Evidence and restrictions, Plan comparison, Teacher
inbox and Review. An administrator inspects forecasts and official excerpts,
reviews a proposed notice interpretation and explicitly confirms structured
restrictions. CP-SAT compares permitted repairs with a baseline; a separate
plain-Python validator checks the returned plan.

Approval is administrator-only, revalidates the draft, rejects stale versions and
atomically records the current approved version. Teachers see only their own
assignments, acknowledge a version and separately report COMPLETED,
COULD_NOT_IMPLEMENT or NEEDS_CLARIFICATION. Administrators inspect exceptions
and history. New restrictions mark the current plan as needing review; they do
not silently replace it or transfer old acknowledgements.

## Architecture and AWS Usage

- **Amplify Hosting:** React/Vite/TypeScript static frontend, manual deployment,
  no frontend secrets or authentication bypass.
- **Cognito:** real administrator/teacher sign-in and refresh; backend permissions
  use verified identity bindings, not a browser role selector.
- **API Gateway HTTP API:** JWT-protected application routes and exact CORS
  origins; only minimal health is unauthenticated.
- **Lambda:** Python 3.12/x86_64 FastAPI/Mangum, OR-Tools and independent validation;
  1024MB, 28-second timeout, reserved concurrency five.
- **DynamoDB:** on-demand durable inputs, restrictions, evidence, drafts, approvals,
  current-plan pointer, teacher reports and audit events.
- **Bedrock:** Sydney `amazon.nova-lite-v1:0` via boto3 proposes schema-validated
  interpretation with supplied citation IDs and ambiguities. It cannot confirm,
  approve or publish; counts are computed outside the model.
- **IAM, S3, CloudWatch:** scoped runtime roles, private deployment artifacts and
  seven-day logs. Application services use `ap-southeast-2`; the separate earlier
  smoke Lambda was preserved.

Bounded model input/output, one SDK attempt, caching and an atomic authenticated
ten-attempt daily allowance limit analysis. Gateway throttling is additional
best-effort protection, not a strict spending cap. No automatic closures, general
AI chat, parent messaging or untracked background work was added.

## Actual Verification

The hosted app was tested in a fresh browser using private real Cognito sign-in:
administrator review/confirmation -> valid draft -> approval -> teacher
acknowledgement -> execution exception -> administrator Review/history.

The approved baseline was OPTIMAL and independently valid, retaining 240
activities. `6-a:Mon-2` used an approved indoor alternative at the same period,
moving field -> room-6-a: zero changed periods, one substitution, zero deferrals,
one room move. Its synthetic execution exception appeared as one unresolved
report, not a completed activity.

Teacher approval and another teacher's assignments returned 403; stale approval
returned 409. Token rejection, session refresh, local logout/reload and exact
CORS checks passed. Prior verification ran 76 backend tests and a production
build. Durable versions/report history were verified against the deployed app.

One actual bounded Nova Lite interpretation used a labelled synthetic notice and
REPLAY evidence: SUCCESS, 773 input / 197 output tokens. Browser request latency
was **2,392ms**, handler 978ms, Gateway integration 992ms. Isolated Bedrock latency
is unknown: this is one request, not a scale benchmark. Two draft requests took
18,948ms and 5,429ms, within the integration limit but not proof of future
cold/warm reliability.

One initial GET /current-plan 503 remains incompletely explained. Historical
checks found a same-minute Lambda throttle at concurrency five, not request-level
causal proof: [INCIDENT_503.md](INCIDENT_503.md). No load tests or extra Bedrock
calls were made during finalization. Throttle settings were verified, but a small
invalid-token burst did not demonstrate 429 enforcement. A bounded prior scan of
714 log events found none of the tested secret/private-text patterns, not a
comprehensive guarantee about future logs.

## Evidence and Product Limitations

LIVE PM2.5/PM10 comes from Open-Meteo/CAMS global regional model forecasts,
approximately 0.4-degree resolution (roughly 45km), not campus measurements.
The hosted fetch was retrieved October 9, 2026 at 17:12:51 IST. That is a
historical retrieval timestamp, **not current model freshness**. Model issue time
was not supplied. **Local station observations are unavailable**: no privately
configured OpenAQ key and verified fresh suitable station were available.
SYNTHETIC REPLAY remains separate for repeatable demonstrations.

Official policy excerpts retain source references and hashes; see
[EVIDENCE.md](EVIDENCE.md) for documents, jurisdiction and limitations. Advisories,
orders and internal policy must not be conflated. Pollution values or AI do not
establish an active GRAP stage or closure. Pasted notices remain unverified until
administrator review.

The MVP supports single-period activities, one affected day and synthetic data,
not operational rollout. Logout clears the local session; offline validation may
accept an unexpired stolen JWT. SessionStorage XSS hardening and additional real
wrong-client/expired-token tests remain future work. These are limitations, not
hidden claims of production readiness.

## Codex Disclosure and Build Lessons

Codex assisted code, tests, Linux ZIP packaging, AWS tooling, browser-check
harnesses, troubleshooting and documentation. The owner supplied the blueprint,
scope and deployment constraints, entered credentials privately and retains
review/submission responsibility. Codex is a development assistant; the runtime
model is Bedrock Nova Lite.

Local Python virtual environments came first. OR-Tools was verified locally and
on real Linux ZIP Lambda execution before the application API; Docker was not
needed. Independent validation, authentication and version checks were preserved
as evidence and hosting were added. Upload success was never treated as proof of
native execution or a complete workflow.

## Owner Actions Before Submission

No GitHub repository exists yet (owner-confirmed October 9, 2026); `git remote -v`
is empty. Public visibility cannot be verified. Amplify manual deployment does
not create a source repository. npm's `private` flag is not GitHub visibility.

1. Check the actual hackathon rules, required fields, AI disclosure and licensing.
   Review working files **and Git history** for secrets/private content before
   publication; ignore rules alone are not a historical audit.
2. Create an empty GitHub repository yourself. Choose Public if required and
   appropriate; do not initialize another README/license/gitignore. Choose a
   license intentionally rather than assuming one has been granted.
3. Connect and push the current branch using normal private authentication, never
   tokens in a remote URL. Replace the URL placeholders below.
4. Open the repository URL signed out to verify source visibility, then add the
   real URL to the writeup/submission. No visibility change is automated here.
5. Record the [2:50 demo script](DEMO.md) excluding passwords, tokens, account IDs
   and private console content. Review it, then publish/upload and submit yourself
   only as required by the rules.

```powershell
git remote add origin https://github.com/YOUR-USER/YOUR-REPO.git
git push -u origin codex/packet-a
```

Steps follow [GitHub's existing-code guidance](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
No repository, video or submission was published in this pass.
