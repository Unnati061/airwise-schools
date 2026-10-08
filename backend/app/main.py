from pathlib import Path

from fastapi import FastAPI
from mangum import Mangum
from botocore.exceptions import BotoCoreError, ClientError
from fastapi.responses import JSONResponse

from .models import Health, School
from .workflow_api import router
from .evidence_api import router as evidence_router

app = FastAPI(title="AirWise Schools", version="0.1.0")
app.include_router(router)
app.include_router(evidence_router)


@app.exception_handler(BotoCoreError)
@app.exception_handler(ClientError)
async def aws_unavailable(request, error):
    return JSONResponse(status_code=503, content={"detail": "AWS backend unavailable; no operation success is claimed"})


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@app.get("/school", response_model=School)
def school() -> School:
    return School.model_validate_json(
        Path(__file__).with_name("data").joinpath("school.json").read_text(encoding="utf-8")
    )


handler = Mangum(app, lifespan="off")
