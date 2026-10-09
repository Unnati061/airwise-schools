from typing import Literal
from uuid import UUID

from pydantic import Field

from .models import Contract
from .evidence_contracts import EvidenceBinding
from .repair_contracts import Counts, DraftPlan, InputVersions, Placement, RepairInput


class Actor(Contract):
    sub: str
    school_id: str
    role: Literal["administrator", "teacher"]
    teacher_id: str | None = None


class ConfirmedInput(Contract):
    revision: str
    input: RepairInput
    actor: str
    timestamp: str
    evidence_binding: EvidenceBinding | None = None


class InputUpdate(Contract):
    expected_revision: str | None
    input: RepairInput


class ApprovedPlan(Contract):
    plan_version: str
    draft_id: str
    input_versions: InputVersions
    actor: str
    timestamp: str


class CurrentPlan(Contract):
    plan_version: str | None
    needs_review: bool
    input_revision: str


class Assignment(Contract):
    activity_id: str
    label: str
    proposed_label: str
    section_id: str
    placement: Placement


class TeacherAssignments(Contract):
    teacher_id: str
    plan_version: str
    needs_review: bool
    acknowledged: bool
    assignments: list[Assignment]
    evidence_mode: Literal["LIVE", "REPLAY", "MANUAL"] = "MANUAL"


class Acknowledgement(Contract):
    actor: str
    teacher_id: str
    timestamp: str
    plan_version: str


class ExecutionInput(Contract):
    request_id: UUID | None = None
    status: Literal["COMPLETED", "COULD_NOT_IMPLEMENT", "NEEDS_CLARIFICATION"]
    note: str = Field(default="", max_length=1000)


class ExecutionReport(ExecutionInput):
    actor: str
    teacher_id: str
    timestamp: str
    activity_id: str
    plan_version: str


class ResolutionInput(Contract):
    request_id: UUID
    note: str = Field(min_length=1, max_length=1000)


class Resolution(Contract):
    request_id: str
    actor: str
    timestamp: str
    activity_id: str
    plan_version: str
    note: str


class AuditEvent(Contract):
    event_id: str
    action: str
    actor: str
    timestamp: str
    activity_id: str | None
    plan_version: str | None


class ExceptionSummary(Contract):
    reports: list[ExecutionReport]
    resolutions: list[Resolution]


class PublicAuthConfig(Contract):
    region: Literal["ap-southeast-2"]
    pool_id: str
    client_id: str


class PlanVersionSummary(Contract):
    plan_version: str
    timestamp: str
    current: bool
    needs_review: bool
    counts: Counts | None = None


class MessagePreview(Contract):
    preview_only: Literal[True] = True
    plan_version: str
    mode: Literal["LIVE", "REPLAY", "MANUAL"]
    calendar_date: str | None
    needs_review: bool
    english: str
    hindi: str


class ApprovedPlanDetail(Contract):
    approval: ApprovedPlan
    plan: DraftPlan
    evidence_binding: EvidenceBinding | None = None
    message_preview: MessagePreview | None = None


class ExecutionCounts(Contract):
    reported: int
    completed: int
    could_not_implement: int
    needs_clarification: int
    unresolved: int


class OutdoorMetrics(Contract):
    available: bool
    missing_duration_activity_ids: list[str]
    original_restricted_outdoor_student_hours: float | None
    approved_restricted_outdoor_student_hours: float | None
    planned_indoor_substitution_student_hours: float | None
    teacher_reported_completed_indoor_student_hours: float | None
    unknown_indoor_execution_student_hours: float | None
    duration_basis: Literal["SYNTHETIC_DECLARED_ACTIVITY_MINUTES"] = "SYNTHETIC_DECLARED_ACTIVITY_MINUTES"
    limitation: str = "Synthetic timetable accounting and teacher self-reports, not measured exposure reduction or health benefit. Deferrals and acknowledgements are not completed indoor substitutions."


class ExecutionReview(Contract):
    reports: list[ExecutionReport]
    resolutions: list[Resolution]
    unresolved_activity_ids: list[str]
    counts: ExecutionCounts
    outdoor_metrics: OutdoorMetrics | None = None
