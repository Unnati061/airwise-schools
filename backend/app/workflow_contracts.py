from typing import Literal
from uuid import UUID

from pydantic import Field

from .models import Contract
from .evidence_contracts import EvidenceBinding
from .repair_contracts import InputVersions, Placement, RepairInput


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


class Acknowledgement(Contract):
    actor: str
    teacher_id: str
    timestamp: str
    plan_version: str


class ExecutionInput(Contract):
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
