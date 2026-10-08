# AirWise Schools: Packet A

Local-first foundation based on AirWise-Schools-Build-Blueprint.md, narrowed by
the user's Packet A request. Synthetic school data only. No live evidence,
schedule repair, approval, authentication or persistence is implemented yet.

## Local setup (PowerShell)

From this repository root, with Python 3.12 and Node 22:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
.venv\Scripts\python -m backend.app.solver_smoke
.venv\Scripts\python -m pytest backend/tests -q
npm --prefix frontend ci
npm --prefix frontend run generate:api
npm --prefix frontend run build
npm --prefix frontend run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173 . Backend docs: http://127.0.0.1:8000/docs .
Frontend uses Vite's development proxy; a production API origin is deferred.

## ZIP attempt

```powershell
.venv\Scripts\python scripts/lambda_zip.py --deploy
```

Installs Linux x86_64 Python 3.12 wheels and creates work/airwise-lambda.zip.
It checks credentials before any upload. To resume deployment, configure AWS
credentials and AIRWISE_LAMBDA_FUNCTION for an existing dedicated Python 3.12
x86_64 function with handler backend.app.lambda_smoke.handler. No AWS resources
are automatically created. The smoke handler imports and executes OR-Tools.
The API handler is backend.app.main.handler; do not expose the smoke function
as the production API. An existing staging directory is deliberately not erased.

See STATUS.md for executed results, package sizes and blockers. Linux wheel
resolution does not establish Lambda native compatibility. Docker is a fallback
only after a demonstrated native compatibility failure in the ZIP path.
The measured ZIP exceeds direct upload size; an S3 upload route is needed before
deployment can proceed. To reuse an inspected archive without rebuilding, pass
`--existing-zip work/airwise-lambda.zip --deploy`.

Optional browser verification uses Playwright and installed Chrome:
`node scripts/check_frontend.cjs`. Set PLAYWRIGHT_MODULE to an installed module
path when Playwright is provided by an external runtime, and PLAYWRIGHT_CHANNEL
to change the installed browser channel. This tooling is not a frontend dependency.

## Attribution

Implementation assisted by Codex. Uses FastAPI, Pydantic, Mangum, Google OR-Tools,
React, Vite, TypeScript and Lucide. Blueprint is the user's supplied planning
source. Product and architecture documents describe current scope and later gates.
