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
Docker is conditional on demonstrated ZIP native compatibility failure.

From repository root (PowerShell):
- `.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`
- `.venv\Scripts\python -m backend.app.solver_smoke`
- `.venv\Scripts\python -m pytest backend/tests -q`
- `npm --prefix frontend ci`
- `npm --prefix frontend run build`
- `npm --prefix frontend run dev -- --host 127.0.0.1`

Run relevant checks, record actual failures and blockers, then make one checkpoint commit.
