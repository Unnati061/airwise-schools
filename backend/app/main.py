from pathlib import Path

from fastapi import FastAPI
from mangum import Mangum

from .models import Health, School

app = FastAPI(title="AirWise Schools", version="0.1.0")


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@app.get("/school", response_model=School)
def school() -> School:
    return School.model_validate_json(
        Path(__file__).with_name("data").joinpath("school.json").read_text(encoding="utf-8")
    )


handler = Mangum(app, lifespan="off")
