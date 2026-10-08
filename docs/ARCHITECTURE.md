# Foundation architecture

Browser -> Vite React SPA -> development proxy /api -> local FastAPI.
FastAPI reads a packaged JSON fixture through typed Pydantic models.
GET /health returns status, service and data_mode. GET /school returns the
synthetic school and six section IDs, labels and aggregate sizes.
GET /openapi.json is the authoritative API schema. No mutation routes exist.
The frontend generates contract types from that schema.

The standalone CP-SAT smoke model assigns three synthetic activities to distinct
periods and proves the minimum period sum. It uses one worker, fixed seed and a
five-second limit. This is an import/execution check, not a timetable validator.

Deployment order: Python venv; local FastAPI; local native solver; local React;
Python 3.12 x86_64 Lambda ZIP. Mangum adapts the same application to Lambda.
Install Linux binary wheels into a separate staging directory, never upload
Windows site-packages. Package code and data at the ZIP root. Check AWS identity
and an explicit existing function target before updating any function.
No IAM, gateway, database or authentication infrastructure is created here.
Only a demonstrated OR-Tools/native runtime compatibility failure can trigger a
separate minimal Docker fallback test; missing credentials is not that failure.

Local read-only endpoints are unauthenticated. Bind to loopback. Future paid or
mutation actions need server-side identity, school authorization and input caps.
Future evidence keeps provider/source/timestamps/units and mode; future approval
checks plan and input versions atomically. No automatic legal activation.

References: https://docs.aws.amazon.com/lambda/latest/dg/python-package.html
and https://developers.google.com/optimization/cp/cp_solver .
