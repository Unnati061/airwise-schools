# Packet B1 local repair

Synthetic only: one fictional school, six sections, five days/eight periods and
240 stable activity IDs. Monday has one outdoor PE activity and an explicitly
approved indoor-movement alternative. Ordinary classroom lessons fill other
slots; first-period lessons are fixed. Not claimed to represent real staffing.

## Demonstrate

Local server started on unused port 8001; no AWS operation performed. To restart
from the repository root:

```powershell
.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001
```

Exact PowerShell request against the running server:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/draft-plans -Method Post -ContentType 'application/json' -Body ((Invoke-RestMethod http://127.0.0.1:8001/repair-fixture) | ConvertTo-Json -Depth 30) | Select-Object solver_status,successful,recommendation,counts,differences | ConvertTo-Json -Depth 10
```

Actual: OPTIMAL, successful true, recommendation baseline. Activity 6-a:Mon-2
retains Mon-2, substitutes approved indoor-movement and moves field -> room-6-a.
Counts: changed periods 0, substitutions 1, deferrals 0, room moves 1.
All other activities unchanged. The baseline ties the best permitted plan.
GET /draft-plans/{returned-id} returned the identical stored draft in the live check.

## Semantics and limitations

- Every input activity appears once, including explicitly permitted deferrals.
  Stable activity IDs are retained. Teacher and section cannot change.
- Supervision comes from structured supervised_kinds, not inferred credentials.
  Each activity occupies one discrete period. No multi-period lessons, travel,
  team teaching, breaks, calendar dates or multiple rooms per activity.
- Changed periods compare period IDs, including deferral's null period. A deferral
  counts once as changed period and once as deferral, not substitution or room move.
  Room moves count only non-null rooms different from the original room.
- Sole objective tuple: (changed periods, substitutions + deferrals, room moves).
  N activities give weights (N+1)^2, N+1, 1, so lower priorities cannot outweigh
  one higher-priority change. No second preference or hard-constraint relaxation.
- Baseline keeps periods, choosing permitted classroom alternatives only for
  restricted outdoor activities, in input order. It does not resolve contention
  by moving periods; its independent audit can fail.
- One CP-SAT solve, one worker, seed 42, five-second budget with preparation
  deducted. If exhausted before solve, UNKNOWN. HTTP/validation/serialization is
  not guaranteed to complete within five seconds.
- OPTIMAL and FEASIBLE remain distinct. INFEASIBLE proves no permitted placement.
  UNKNOWN is inconclusive; a valid baseline may be returned with optimality
  explicitly unproven. MODEL_INVALID is not successful. Corrupted solver output
  cannot be successful even with OPTIMAL status; validation errors stay visible.
- Plain-Python validator imports no solver helpers. From the original snapshot
  it recomputes accounting, permissions, restriction scopes, occupancy, capacity,
  availability, supervision, fixed/unaffected placements and differences/counts.
- administrator_confirmed=true and confirmed_by are asserted local inputs, not
  authenticated administrator identity or legal evidence. Synthetic mode only.
- School/timetable/restriction versions and full snapshot are retained. Canonical
  freshness/authorization and atomic version checks belong to the next packet;
  local clients can currently submit their own synthetic snapshots.
- Draft storage is temporary: process-local deep copies, latest 100 only, lost on
  restart, independent across workers. Restart/eviction returns 404. No approval,
  activation or durable storage. PlanRepository is the replacement interface.

## Checks

```powershell
.venv\Scripts\python -m pytest backend/tests -q
.venv\Scripts\python -m pip check
cd frontend
npm exec -- openapi-typescript http://127.0.0.1:8001/openapi.json -o src/api.d.ts
npm run build
```

Live POST/GET passed as above. OpenAPI type generation and TypeScript/Vite build
passed; pip check passed. Final backend suite: 41 passed, two existing dependency
deprecation warnings. git diff --check passed. No dependencies changed.
First run: 37 passed, one diagnostic fixture assertion failed because it still
allowed an indoor alternative. Corrected the test's permissions, not solver rules.
Second run: 38 passed, two existing dependency warnings; pip check passed.
Cases include unchanged week, approved alternative, period-specific outdoor swap,
room contention/authorized move, capacity, teacher conflict/availability/supervision,
room availability, fixed lessons, infeasibility and explicit deferral accounting.
Missing/duplicate/unknown/unauthorized/overlapping/fixed/unaffected corruptions are
independently rejected. Controlled adapters exercise UNKNOWN, MODEL_INVALID and
FEASIBLE without guessing which problem will time out; corrupt selection is rejected
at the service boundary. Lexicographic test prefers a permitted substitution over
changing two periods, rather than adding an alternative optimization preference.
Controlled elapsed-clock test confirms exhausted preparation budget skips search
and reports UNKNOWN, not INFEASIBLE.
