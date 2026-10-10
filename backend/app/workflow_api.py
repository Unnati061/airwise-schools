from typing import Literal

from fastapi import APIRouter, Depends

from .auth import identity, workflow, settings
from .repair_contracts import DraftPlan, RepairInput
from .repair_fixture import synthetic_week, shared_resources_week
from .workflow import Workflow, admin
from .workflow_contracts import (Acknowledgement, Actor, ApprovedPlan, AuditEvent, ConfirmedInput,
                                 CurrentPlan, ExceptionSummary, ExecutionInput, ExecutionReport,
                                 InputUpdate, Resolution, ResolutionInput, TeacherAssignments)
from .workflow_contracts import PublicAuthConfig, PlanVersionSummary, ApprovedPlanDetail, ExecutionReview

router = APIRouter()


@router.get("/auth/config", response_model=PublicAuthConfig)
def auth_config():
    config = settings()
    return PublicAuthConfig(region=config["region"], pool_id=config["pool_id"], client_id=config["client_id"])


@router.get("/me", response_model=Actor)
def me(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    service.school(actor)
    return actor


@router.get("/approved-plans", response_model=list[PlanVersionSummary])
def history(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.history(actor)


@router.get("/approved-plans/{version}", response_model=ApprovedPlanDetail)
def approved_detail(version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.approved_detail(actor, version)


@router.get("/approved-plans/{version}/review", response_model=ExecutionReview)
def execution_review(version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.execution_review(actor, version)


@router.get("/teachers/{teacher_id}/reports", response_model=list[ExecutionReport])
def teacher_reports(teacher_id: str, version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.teacher_reports(actor, teacher_id, version)


@router.get("/repair-fixture", response_model=RepairInput)
def fixture(scenario: Literal['classroom', 'shared-resources'] = 'classroom', actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    admin(actor)
    service.school(actor)
    return shared_resources_week() if scenario == 'shared-resources' else synthetic_week()


@router.post("/inputs", response_model=ConfirmedInput)
def confirm_input(body: InputUpdate, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.confirm(actor, body)


@router.get("/inputs", response_model=ConfirmedInput)
def inputs(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.inputs(actor)


@router.get("/inputs/{revision}", response_model=ConfirmedInput)
def input_version(revision: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.input_version(actor, revision)


@router.post("/draft-plans", response_model=DraftPlan)
def draft(body: RepairInput, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.draft(actor, body)


@router.get("/draft-plans/{plan_id}", response_model=DraftPlan)
def inspect(plan_id: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.get_draft(actor, plan_id)


@router.post("/draft-plans/{plan_id}/approve", response_model=ApprovedPlan)
def approve(plan_id: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.approve(actor, plan_id)


@router.get("/current-plan", response_model=CurrentPlan)
def current(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.current(actor)


@router.get("/teachers/{teacher_id}/assignments", response_model=TeacherAssignments)
def assignments(teacher_id: str, version: str | None = None, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.assignments(actor, teacher_id, version)


@router.post("/approved-plans/{version}/acknowledgements", response_model=Acknowledgement)
def acknowledge(version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.ack(actor, version)


@router.put("/approved-plans/{version}/activities/{activity_id}/report", response_model=ExecutionReport)
def report(version: str, activity_id: str, body: ExecutionInput, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.report(actor, version, activity_id, body)


@router.get("/approved-plans/{version}/reports", response_model=list[ExecutionReport])
def reports(version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.reports(actor, version)


@router.get("/approved-plans/{version}/exceptions", response_model=ExceptionSummary)
def exceptions(version: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.exceptions(actor, version)


@router.post("/approved-plans/{version}/activities/{activity_id}/resolution", response_model=Resolution)
def resolve(version: str, activity_id: str, body: ResolutionInput, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.resolve(actor, version, activity_id, body)


@router.get("/audit-events", response_model=list[AuditEvent])
def audits(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.audits(actor)
