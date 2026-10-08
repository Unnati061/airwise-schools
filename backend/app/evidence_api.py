from typing import Literal

from fastapi import APIRouter, Depends

from .auth import identity, workflow
from .evidence_contracts import AnalysisRequest, AnalysisResult, EvidenceView, PlanExplanation, PolicyExcerpt, ReviewConfirmation
from .evidence_service import EvidenceService
from .workflow_contracts import Actor, ConfirmedInput

router = APIRouter()


def evidence(service=Depends(workflow)):
    return EvidenceService(service)


@router.get("/evidence/forecast", response_model=EvidenceView)
def forecast(mode: Literal["LIVE", "REPLAY"] = "LIVE", actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.forecast(actor, mode)


@router.get("/evidence/{evidence_id}", response_model=EvidenceView)
def snapshot(evidence_id: str, actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.get_evidence(actor, evidence_id)


@router.get("/policy-excerpts", response_model=list[PolicyExcerpt])
def policies(actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.policies(actor)


@router.post("/notice-analyses", response_model=AnalysisResult)
def interpret(body: AnalysisRequest, actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.interpret(actor, body)


@router.get("/notice-analyses/{analysis_id}", response_model=AnalysisResult)
def analysis(analysis_id: str, actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.analysis(actor, analysis_id)


@router.post("/notice-analyses/{analysis_id}/confirm", response_model=ConfirmedInput)
def confirm(analysis_id: str, body: ReviewConfirmation, actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.confirm(actor, analysis_id, body)


@router.get("/draft-plans/{draft_id}/explanation", response_model=PlanExplanation)
def explanation(draft_id: str, actor: Actor = Depends(identity), service=Depends(evidence)):
    return service.explanation(actor, draft_id)
