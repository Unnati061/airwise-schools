# AirWise Schools

Read README.md and docs/ARCHITECTURE.md; use docs/SETUP.md and docs/DEPLOYMENT.md
for operating instructions. Work only on the user-requested scope, with one agent.

- Python 3.12 / FastAPI / OR-Tools; React / Vite / generated TypeScript contracts.
- Keep school data fictional and aggregate. Never commit credentials, passwords,
  tokens, private notices, caches, dependency binaries or deployment archives.
- Preserve independent validation, server-side Cognito identity/school/teacher
  authorization, transactional approval, versions and idempotent report receipts.
- Keep LIVE and REPLAY distinct. Regional model output is not campus observation.
  Do not infer legal restrictions, measured health benefits or indoor-air safety.
- Model proposals require administrator review; deterministic metrics do not use AI.
- Use profile airwise, ap-southeast-2 only. Inspect and reuse owned resources.
  No policy/account changes, create-only reruns or smoke-Lambda changes.
- Private passwords are entered by the owner; never reset them automatically.
  Bound spending/retries; do not make model calls merely for verification.
- Deployment requires checked Linux Python3.12/x86_64 ZIP bytes and actual runtime/
  browser verification. Stop after upload connectivity failure; use the exact
  preserved ZIP for the console fallback. No speculative Docker workaround.
- Preserve applicable third-party notices and Git history/timestamps.

Relevant checks: .venv\Scripts\python -m pytest backend/tests -q;
npm --prefix frontend run generate:api (local backend 8002);
npm --prefix frontend run build. Browser harnesses clearly separate test doubles
from real authentication. Record real results in concise operating documentation,
not internal task diaries. Use product-focused commit messages.
