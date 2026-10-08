# Packet A execution record

## Inspection before editing

Current folder held only empty outputs/ and work/. Git resolved to
C:/Users/Ashwani with unrelated existing changes. No ancestor AGENTS.md found.
Created isolated outputs/airwise-schools repository on codex/packet-a, preserving
the ancestor repository. Read the full supplied blueprint. AWS CLI unavailable.

## Commands executed (PowerShell)

Initial inspection used Get-Location, Get-ChildItem -Force, git status --short,
git rev-parse --show-toplevel, Get-Content on the blueprint, python --version,
py -0p, node --version, npm --version and aws --version.

From workspace: `python -m venv outputs/airwise-schools/.venv`.
From project root unless stated otherwise:

```powershell
.venv\Scripts\python -m pip install fastapi uvicorn ortools mangum pytest httpx boto3
.venv\Scripts\python -m pip freeze
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Invoke-RestMethod http://127.0.0.1:8000/health
.venv\Scripts\python -m backend.app.solver_smoke
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python -m pip check
.venv\Scripts\python scripts/lambda_zip.py --deploy
node scripts/check_frontend.cjs
git init -b codex/packet-a
```

Frontend directory:

```powershell
npm install --save-exact react react-dom lucide-react
npm install --save-dev --save-exact vite @vitejs/plugin-react typescript @types/react @types/react-dom openapi-typescript
npm install --save-dev --save-exact typescript@5.9.3
npm run generate:api
npm run build
npm ls --depth=0
```

Browser command used bundled Playwright through PLAYWRIGHT_MODULE. Initial
default browser launch failed because bundled headless Chromium was missing;
installed Chrome channel succeeded. Frontend served by a hidden Node/Vite process
on loopback port 5173. A temporary launch from the wrong working directory and
an extra backend on 8001 were stopped, then correct frontend directory was used.
Final detached backend/frontend proxy health returned SYNTHETIC/ok; a direct
local call to backend.app.lambda_smoke.handler returned healthy and OPTIMAL.
ZIP structure check found 85 Linux .so entries, both required handler/data paths
and no Windows .dll/.pyd entries. scripts/lambda_zip.py --help passed.
git diff --cached --check passed; targeted secret-pattern scan found no matches.
Checkpoint command: git commit -m "Establish Docker-free Packet A foundation with verified local checks".
Immediate amendment included the ignored Vite cache and this final check record;
only one checkpoint exists. No AWS runtime success is implied by local checks.

The first backend launch preceded completion of pip installation and failed with
missing FastAPI; the rerun succeeded. Initial frontend generation/build failed
with TypeScript 7.0.2 and missing Vite CSS declarations; fixed and rerun passed.
Final frontend build passed after adding an effect disposal guard.

ZIP command internally ran pip install with platforms manylinux2014_x86_64 and
manylinux_2_28_x86_64, implementation cp, Python 3.12, binary-only, no bytecode,
target work/lambda-package and backend/requirements.txt. Linux wheel installation
passed. ZIP deployment preflight failed on unavailable credentials, not native
dependencies. AWS documentation was checked for ZIP native packaging requirements.

## Verified dependency pins

Backend: FastAPI 0.143.0, OR-Tools 9.15.6755, Pydantic 2.13.5,
Mangum 0.22.0, Uvicorn 0.54.0, pytest 9.1.1, HTTPX 0.28.1.
All transitive packages pinned in backend/requirements*.txt after local checks.
AWS tooling: boto3 1.43.109, installed for ZIP preflight; cloud use unverified.
Frontend: React/React DOM 19.3.0, Vite 8.3.4, plugin-react 6.1.2,
TypeScript 5.9.3, Lucide React 1.53.0, openapi-typescript 7.13.0,
React/React DOM types 19.3.0. package-lock.json retains exact resolution.

## Created files

- .gitignore, AGENTS.md, README.md, STATUS.md
- docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/CHECKS.md
- backend/__init__.py, backend/app/__init__.py
- backend/app/main.py, models.py, solver_smoke.py, lambda_smoke.py
- backend/app/data/school.json, backend/tests/test_foundation.py
- backend/requirements.txt, backend/requirements-dev.txt
- frontend/package.json, package-lock.json, index.html, tsconfig.json, vite.config.ts
- frontend/src/main.tsx, style.css, vite-env.d.ts, generated api.d.ts
- scripts/lambda_zip.py, scripts/check_frontend.cjs

Ignored local artifacts: .venv, node_modules, dist, work/ ZIP/staging, logs and
browser screenshots. No secrets or real school data are committed.
