# Setup

Use Python 3.12 and Node 22. From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
npm --prefix frontend ci
.venv\Scripts\python -m pytest backend/tests -q
```

The solver and independent-validator tests run without AWS. Controlled browser
fixtures are labelled test doubles, never a runtime authentication bypass.

## Frontend Against the Existing API

Only public client identifiers belong in Vite variables:

```powershell
$env:VITE_API_BASE_URL='https://lbckjkbfb4.execute-api.ap-southeast-2.amazonaws.com'
$env:VITE_COGNITO_REGION='ap-southeast-2'
$env:VITE_COGNITO_POOL_ID='ap-southeast-2_LhIz6g1r9'
$env:VITE_COGNITO_CLIENT_ID='5gq58g4sp2o7ic7grg8k7cld2'
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173, an exact allowed CORS origin. Sign in privately with an
existing dedicated identity. Cloning does not create users or supply passwords.
Do not reset passwords automatically. The existing API writes sample school data;
analysis can incur bounded charges. Do not load-test it.

## Local Backend

The default frontend /api proxy targets loopback FastAPI on 8002. Full operations
require owner-provided ignored work/aws-b2.json resource configuration, temporary
AWS profile airwise and access to the scoped local runtime role. Review
backend/app/auth.py and workflow_api.py for required configuration fields.
Never copy credentials/cache files into the checkout or deploy the local profile.
Do not rerun create-only infrastructure helpers against existing resources.

```powershell
aws login --profile airwise
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002
```

In another terminal, without VITE_API_BASE_URL:

```powershell
npm --prefix frontend run generate:api
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Authentication remains enabled. Missing private configuration is a setup error,
not a reason to enable memory storage or a public bypass.

## Browser Regression Checks

Use separately installed Playwright/Chrome via PLAYWRIGHT_MODULE; no binaries are
committed. Start a local Vite server on 5174, then:

```powershell
.venv\Scripts\python -m scripts.ui_fixtures
node scripts/check_features.cjs
node scripts/check_presentation.cjs
npm --prefix frontend run build
```

These checks use labelled offline responses and synthetic non-credentials.
The hosted workflow harness requires private sign-in and explicitly mutates only
sample school versions/reports. It makes no model call.
