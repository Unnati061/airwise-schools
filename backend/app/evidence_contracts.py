from datetime import date, datetime
from typing import Literal

from pydantic import Field, model_validator

from .models import Contract


class PollutantPoint(Contract):
    pollutant: Literal["PM2.5", "PM10"]
    value: float | None = Field(ge=0, allow_inf_nan=False)
    units: Literal["ug/m3"] = "ug/m3"
    valid_time: datetime
    averaging_period: Literal["instantaneous_model_output"] = "instantaneous_model_output"


class EvidenceSnapshot(Contract):
    id: str
    mode: Literal["LIVE", "REPLAY"]
    kind: Literal["REGIONAL_FORECAST"] = "REGIONAL_FORECAST"
    source: str
    source_url: str
    requested_latitude: float
    requested_longitude: float
    grid_latitude: float
    grid_longitude: float
    retrieved_at: datetime
    model_issue_time: datetime | None = None
    model_issue_time_status: Literal["not_provided"] = "not_provided"
    resolution: str = "CAMS global 0.4 degrees (~45 km), native 3-hourly output served hourly"
    source_units: dict[str, str]
    raw_sha256: str
    points: list[PollutantPoint]
    limitations: list[str]

    @model_validator(mode="after")
    def check_provenance(self):
        if self.retrieved_at.tzinfo is None or any(p.valid_time.tzinfo is None for p in self.points):
            raise ValueError("Evidence timestamps require time zones")
        return self


class EvidenceView(Contract):
    snapshot: EvidenceSnapshot
    freshness: Literal["FRESH", "STALE", "MISSING_VALUES", "REPLAY"]
    checked_at: datetime
    observations_available: Literal[False] = False
    observation_limitation: str = "No privately configured OpenAQ key and verified fresh suitable station; station observations unavailable"


class PolicyExcerpt(Contract):
    id: str
    title: str
    issuer: str
    document_date: str
    date_precision: Literal["day", "month", "internal"]
    jurisdiction: str
    classification: Literal["ADVISORY", "HISTORICAL_ORDER", "INTERNAL_POLICY"]
    active_order_verified: Literal[False] = False
    source_url: str
    reference: str
    excerpt: str
    excerpt_sha256: str
    document_sha256: str
    verified_at: datetime
    limitation: str


class AffectedDate(Contract):
    raw_text: str = Field(max_length=100)
    start: date | None
    end: date | None


class ProposedRestriction(Contract):
    id: str = Field(min_length=1, max_length=50)
    kind: Literal["outdoor_prohibited", "unsupported"]
    activity_ids: list[str] = Field(max_length=48)
    citation_ids: list[str] = Field(max_length=8)


class NoticeInterpretation(Contract):
    affected_dates: list[AffectedDate] = Field(max_length=8)
    activities: list[str] = Field(max_length=48)
    proposed_restrictions: list[ProposedRestriction] = Field(max_length=8)
    citation_ids: list[str] = Field(max_length=8)
    ambiguities: list[str] = Field(max_length=12)


class AnalysisRequest(Contract):
    notice: str = Field(min_length=1, max_length=3000)
    evidence_id: str
    mode: Literal["LIVE", "REPLAY"]
    policy_ids: list[str] = Field(min_length=1, max_length=3)


class AnalysisResult(Contract):
    id: str
    mode: Literal["LIVE", "REPLAY"]
    evidence_id: str
    input_revision: str
    notice_sha256: str
    notice_status: Literal["UNVERIFIED"] = "UNVERIFIED"
    requires_review: Literal[True] = True
    review_reasons: list[str]
    status: Literal["SUCCESS", "MODEL_FAILURE", "INVALID_OUTPUT", "PENDING"]
    interpretation: NoticeInterpretation | None
    model: str
    region: Literal["ap-southeast-2"] = "ap-southeast-2"
    usage: dict[str, int]
    created_at: datetime
    policy_ids: list[str]


class EvidenceBinding(Contract):
    analysis_id: str
    evidence_id: str
    mode: Literal["LIVE", "REPLAY"]
    calendar_date: date
    reviewed_by: str
    reviewed_at: datetime


class ReviewConfirmation(Contract):
    expected_revision: str
    proposal_ids: list[str] = Field(min_length=1, max_length=8)
    calendar_date: date
    period_ids: list[str] = Field(min_length=1, max_length=8)
    notice_reviewed: Literal[True]
    ambiguities_reviewed: Literal[True]


class PlanExplanation(Contract):
    draft_id: str
    text: str
    fact_ids: list[str]
    model: str | None
    grounded: Literal[True] = True
    model_status: Literal["SUCCESS", "MODEL_FAILURE", "INVALID_OUTPUT"]
