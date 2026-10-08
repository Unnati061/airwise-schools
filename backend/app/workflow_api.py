from fastapi import APIRouter, Depends

from .auth import identity, workflow
from .repair_contracts import DraftPlan, RepairInput
from .repair_fixture import synthetic_week
from .workflow import Workflow, admin
from .workflow_contracts import (Acknowledgement, Actor, ApprovedPlan, AuditEvent, ConfirmedInput,
                                 CurrentPlan, ExceptionSummary, ExecutionInput, ExecutionReport,
                                 InputUpdate, Resolution, ResolutionInput, TeacherAssignments)

router = APIRouter()


@router.get("/repair-fixture", response_model=RepairInput)
def fixture(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    admin(actor)
    service.school(actor)
    return synthetic_week()


@router.post("/inputs", response_model=ConfirmedInput)
def confirm_input(body: InputUpdate, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.confirm(actor, body)


@router.get("/inputs", response_model=ConfirmedInput)
def inputs(actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.inputs(actor)


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
def assignments(teacher_id: str, actor: Actor = Depends(identity), service: Workflow = Depends(workflow)):
    return service.assignments(actor, teacher_id)


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
