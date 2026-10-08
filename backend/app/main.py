from pathlib import Path

from fastapi import FastAPI, HTTPException
from mangum import Mangum

from .models import Health, School
from .plan_repository import MemoryPlanRepository, PlanRepository
from .repair_contracts import DraftPlan, RepairInput
from .repair_engine import repair
from .repair_fixture import synthetic_week

app = FastAPI(title="AirWise Schools", version="0.1.0")
plans: PlanRepository = MemoryPlanRepository()


@app.get("/health", response_model=Health)
def health() -> Health:
    return Health()


@app.get("/school", response_model=School)
def school() -> School:
    return School.model_validate_json(
        Path(__file__).with_name("data").joinpath("school.json").read_text(encoding="utf-8")
    )


@app.get("/repair-fixture", response_model=RepairInput)
def repair_fixture() -> RepairInput:
    return synthetic_week()


@app.post("/draft-plans", response_model=DraftPlan)
def generate_draft(data: RepairInput) -> DraftPlan:
    plan = repair(data)
    plans.save(plan)
    return plan


@app.get("/draft-plans/{plan_id}", response_model=DraftPlan)
def inspect_draft(plan_id: str) -> DraftPlan:
    plan = plans.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Draft not found (temporary process-local storage)")
    return plan


handler = Mangum(app, lifespan="off")
