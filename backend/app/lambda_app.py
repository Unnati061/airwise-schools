"""Deployed surface: status-only health, authenticated application routes."""
import base64
import json
import time

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum

from .auth import identity
from .evidence_api import router as evidence_router
from .workflow_api import router

app = FastAPI(title="AirWise Schools", docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(router, dependencies=[Depends(identity)])
app.include_router(evidence_router, dependencies=[Depends(identity)])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(BotoCoreError)
@app.exception_handler(ClientError)
async def unavailable(request, error):
    return JSONResponse(status_code=503, content={"detail": "AWS backend unavailable; inspect state before retrying"})


adapter = Mangum(app, lifespan="off")


def handler(event, context):
    body = event.get("body") or ""
    size = len(base64.b64decode(body)) if event.get("isBase64Encoded") else len(body.encode())
    if size > 250_000:
        return {"statusCode": 413, "body": '{"detail":"Request exceeds application limit"}'}
    started = time.monotonic()
    response = adapter(event, context)
    # Log route templates, not IDs, JWTs, query strings, bodies or provider errors.
    print(json.dumps({"route": event.get("routeKey", "unknown"), "status": response["statusCode"],
                      "duration_ms": round((time.monotonic() - started) * 1000)}))
    return response
