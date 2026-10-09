# AirWise Schools

Read STATUS.md, docs/PRODUCT.md and docs/ARCHITECTURE.md first.
Implement only the requested packet. One agent; no scope expansion.
Python 3.12 / FastAPI / OR-Tools; React / Vite / TypeScript.
Use synthetic aggregate school data only; never commit secrets or child data.
Keep LIVE, REPLAY and SYNTHETIC evidence distinct; never infer legal activation.
Future plans require independent validation, authorized approval and version checks.
No paid services or broader AWS infrastructure in this foundation packet.
The user authorized a separate private S3/IAM/Lambda/log-group runtime smoke
spike; see docs/AWS_SMOKE.md. Do not change organization policies to bypass denial.
Packet B2 authorizes only its DynamoDB table, Cognito pool/client/synthetic users
and least-privilege local runtime role in Sydney. Protected APIs require real
Cognito access tokens; never add a runtime memory/authentication bypass.
Do not alter the Packet A smoke Lambda for B2. See docs/WORKFLOW.md.
Packet C authorizes bounded Sydney Nova Lite calls through the existing runtime
role and evidence persistence in the existing table. No new infrastructure,
cross-region inference, automatic legal activation or model-driven approval.
See docs/EVIDENCE.md for source provenance, review gates and daily limits.
Packet D1 adds a local authenticated interface only. No new AWS resources or
deployment. See docs/INTERFACE.md; Vite proxies the local backend on port 8002.
Docker is conditional on demonstrated ZIP native compatibility failure.
Packet D2 authorizes the dedicated Sydney application Lambda/role/HTTP API and
logs, reusing existing data/auth/model resources. See docs/AWS_APP.md. Existing
object checksum verified and D2 resources created; deployed administrator approval,
teacher execution and role denials passed. Hosted forecast/one actual analysis
also passed; broader latency/security edge cases remain unverified.
Inspect/reuse these resources, never rerun create-only
deployment. Do not rebuild/upload again or change the smoke Lambda. Measure
actual integration latency before deciding synchronous slow paths are adequate.
Hosting follow-up authorizes the existing frontend's tagged Amplify static app
and exact API CORS origin only. See docs/HOSTING.md for the deployed app/branch;
reuse them, never rerun create-only helpers. Cognito direct sign-in has no OAuth
callback. Keep model calls bounded, private sign-in manual and credentials out
of logs/artifacts. Do not redesign or recreate API/data/auth/smoke resources.

From repository root (PowerShell):
- `.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002`
- `.venv\Scripts\python -m backend.app.solver_smoke`
- `.venv\Scripts\python -m pytest backend/tests -q`
- `npm --prefix frontend ci`
- `npm --prefix frontend run build`
- `npm --prefix frontend run dev -- --host 127.0.0.1`

Run relevant checks, record actual failures and blockers, then make one checkpoint commit.
