from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .durable_store import Conflict, DynamoPlanRepository
from .repair_contracts import DraftPlan
from .repair_engine import repair
from .repair_validator import validate_plan
from .workflow_contracts import (Acknowledgement, ApprovedPlan, Assignment, AuditEvent,
                                 ConfirmedInput, CurrentPlan, ExceptionSummary, ExecutionReport,
                                 Resolution, TeacherAssignments)

SCHOOL = "synthetic-school-001"


def now():
    return datetime.now(timezone.utc).isoformat()


def admin(actor):
    if actor.role != "administrator":
        raise HTTPException(403, "Administrator required")


def approval_receipt(record):
    return ApprovedPlan.model_validate(record.get("approval", record))


class Workflow:
    def __init__(self, store):
        self.store = store

    def school(self, actor):
        if actor.school_id != SCHOOL:
            raise HTTPException(403, "School access denied")
        return actor.school_id

    def state(self, actor):
        school = self.school(actor)
        state = self.store.read(school, "STATE")
        if not state:
            raise HTTPException(409, "Administrator must confirm inputs first")
        return state

    def event(self, actor, action, activity=None, version=None):
        event = AuditEvent(event_id=str(uuid4()), action=action, actor=actor.sub,
                           timestamp=now(), activity_id=activity, plan_version=version)
        return self.store.put(actor.school_id, f"AUDIT#{event.timestamp}#{event.event_id}", event.model_dump(), create=True)

    def transact(self, actions):
        try:
            self.store.transact(actions)
        except Conflict:
            raise HTTPException(409, "Concurrent modification; refresh and retry") from None

    def confirm(self, actor, update, *, evidence_binding=None):
        admin(actor)
        school = self.school(actor)
        data = update.input.model_copy(deep=True)
        if data.school_id != school:
            raise HTTPException(403, "School access denied")
        old = self.store.read(school, "STATE")
        if (old["revision"] if old else None) != update.expected_revision:
            raise HTTPException(409, "Stale input revision")
        if old:
            previous = self.store.read(school, f"INPUT#{old['revision']}")["input"]
            if {a["id"] for a in previous["activities"]} != {a.id for a in data.activities}:
                raise HTTPException(422, "Revision must retain every stable activity ID")
        revision = str(uuid4())
        # Version labels and confirmation actor come from the authenticated server.
        data.versions.school = "synthetic-v1"
        data.versions.timetable = revision
        data.versions.restrictions = revision
        for restriction in data.restrictions:
            restriction.confirmed_by = actor.sub
        confirmed = ConfirmedInput(revision=revision, input=data, actor=actor.sub, timestamp=now(), evidence_binding=evidence_binding)
        state = dict(revision=revision, etag=str(uuid4()), current=old["current"] if old else None,
                     needs_review=bool(old and old["current"]))
        self.transact([self.store.put(school, f"INPUT#{revision}", confirmed.model_dump(mode="json"), create=True),
                       self.store.put(school, f"RESTRICTIONS#{revision}", {"restrictions": [r.model_dump() for r in data.restrictions],
                           "actor": actor.sub, "timestamp": confirmed.timestamp, "revision": revision}, create=True),
                       self.store.put(school, "STATE", state, expected=old["etag"] if old else None, create=old is None),
                       self.event(actor, "INPUT_CONFIRMED", version=state["current"])])
        return confirmed

    def inputs(self, actor):
        admin(actor)
        state = self.state(actor)
        return ConfirmedInput.model_validate(self.store.read(actor.school_id, f"INPUT#{state['revision']}"))

    def draft(self, actor, data):
        admin(actor)
        canonical = self.inputs(actor).input
        if data != canonical:
            raise HTTPException(409, "Draft must use the current confirmed input snapshot and versions")
        plan = repair(canonical)
        repository = DynamoPlanRepository(self.store, actor.school_id)
        # Save draft and its audit event together through the same storage boundary.
        try:
            repository.save(plan, self.event(actor, "DRAFT_GENERATED", version=plan.id))
        except Conflict:
            raise HTTPException(409, "Draft conflict") from None
        return plan

    def get_draft(self, actor, plan_id):
        admin(actor)
        self.school(actor)
        plan = DynamoPlanRepository(self.store, actor.school_id).get(plan_id)
        if not plan:
            raise HTTPException(404, "Draft not found")
        return plan

    def approve(self, actor, draft_id):
        admin(actor)
        self.school(actor)
        existing = self.store.read(actor.school_id, f"APPROVED#{draft_id}")
        if existing:
            return approval_receipt(existing)
        plan = self.get_draft(actor, draft_id)
        state = self.state(actor)
        canonical = self.inputs(actor).input
        if plan.input_versions != canonical.versions or plan.input_snapshot != canonical:
            raise HTTPException(409, "Stale draft input/restriction versions")
        audit = validate_plan(canonical, plan.placements)
        if not plan.successful or not audit.valid or plan.solver_status in ("INFEASIBLE", "MODEL_INVALID"):
            raise HTTPException(422, "Unsuccessful or independently invalid draft")
        approved = ApprovedPlan(plan_version=draft_id, draft_id=draft_id, input_versions=canonical.versions,
                                actor=actor.sub, timestamp=now())
        frozen = plan.model_copy(deep=True)
        frozen.validation, frozen.counts, frozen.differences = audit, audit.counts, audit.differences
        record = {"approval": approved.model_dump(mode="json"), "plan": frozen.model_dump(mode="json")}
        updated = {**state, "current": draft_id, "needs_review": False, "etag": str(uuid4())}
        try:
            self.store.transact([self.store.put(actor.school_id, f"APPROVED#{draft_id}", record, create=True),
                                 self.store.put(actor.school_id, "STATE", updated, expected=state["etag"]),
                                 self.event(actor, "PLAN_APPROVED", version=draft_id)])
        except Conflict:
            # Durable idempotency: old duplicate approvals never rewind the pointer.
            existing = self.store.read(actor.school_id, f"APPROVED#{draft_id}")
            if existing:
                return approval_receipt(existing)
            raise HTTPException(409, "Input or current plan changed during approval") from None
        return approved

    def current(self, actor):
        admin(actor)
        state = self.state(actor)
        return CurrentPlan(plan_version=state["current"], needs_review=state["needs_review"], input_revision=state["revision"])

    def teacher(self, actor, teacher_id):
        self.school(actor)
        if actor.role != "teacher" or actor.teacher_id != teacher_id:
            raise HTTPException(403, "Teacher assignment access denied")

    def approved_draft(self, actor, version):
        self.school(actor)
        record = self.store.read(actor.school_id, f"APPROVED#{version}")
        if not record:
            raise HTTPException(404, "Approved version not found")
        if "plan" in record:
            return DraftPlan.model_validate(record["plan"])
        # Receipts from the first B2 integration run reference immutable drafts.
        return DynamoPlanRepository(self.store, actor.school_id).get(version)

    def assignments(self, actor, teacher_id):
        self.teacher(actor, teacher_id)
        state = self.state(actor)
        if not state["current"]:
            raise HTTPException(404, "No approved plan")
        plan = self.approved_draft(actor, state["current"])
        by_id = {a.id: a for a in plan.input_snapshot.activities}
        assignments = []
        for p in plan.placements:
            a = by_id[p.activity_id]
            if a.teacher_id == teacher_id:
                label = next((v.label for v in a.approved_alternatives if v.id == p.alternative_id), a.label)
                assignments.append(Assignment(activity_id=a.id, label=a.label, proposed_label=label,
                                              section_id=a.section_id, placement=p))
        return TeacherAssignments(teacher_id=teacher_id, plan_version=state["current"], needs_review=state["needs_review"],
                                  acknowledged=bool(self.store.read(actor.school_id, f"ACK#{state['current']}#{teacher_id}")),
                                  assignments=assignments)

    def ack(self, actor, version):
        self.teacher(actor, actor.teacher_id)
        state = self.state(actor)
        if state["current"] != version:
            raise HTTPException(409, "Acknowledgement requires the current approved version")
        key = f"ACK#{version}#{actor.teacher_id}"
        existing = self.store.read(actor.school_id, key)
        if existing:
            return Acknowledgement.model_validate(existing)
        acknowledgement = Acknowledgement(actor=actor.sub, teacher_id=actor.teacher_id, timestamp=now(), plan_version=version)
        try:
            self.store.transact([self.store.put(actor.school_id, key, acknowledgement.model_dump(), create=True),
                                 self.store.put(actor.school_id, "STATE", state, expected=state["etag"]),
                                 self.event(actor, "ACKNOWLEDGED", version=version)])
        except Conflict:
            existing = self.store.read(actor.school_id, key)
            if not existing:
                raise HTTPException(409, "Plan changed during acknowledgement") from None
            return Acknowledgement.model_validate(existing)
        return acknowledgement

    def report(self, actor, version, activity_id, body):
        self.teacher(actor, actor.teacher_id)
        state = self.state(actor)
        if state["current"] != version:
            raise HTTPException(409, "Report requires the current approved version")
        plan = self.approved_draft(actor, version)
        a = next((a for a in plan.input_snapshot.activities if a.id == activity_id), None)
        if not a or a.teacher_id != actor.teacher_id:
            raise HTTPException(403, "Teacher assignment access denied")
        placement = next(p for p in plan.placements if p.activity_id == activity_id)
        if placement.deferred and body.status == "COMPLETED":
            raise HTTPException(422, "Deferred activity cannot be reported completed")
        key = f"REPORT#{version}#{activity_id}"
        old = self.store.read(actor.school_id, key)
        if old and old["status"] == body.status and old["note"] == body.note:
            return ExecutionReport.model_validate({k: v for k, v in old.items() if k != "etag"})
        report = ExecutionReport(**body.model_dump(), actor=actor.sub, teacher_id=actor.teacher_id,
                                 timestamp=now(), activity_id=activity_id, plan_version=version)
        document = {**report.model_dump(), "etag": str(uuid4())}
        try:
            self.store.transact([self.store.put(actor.school_id, key, document, expected=old["etag"] if old else None, create=old is None),
                                 self.store.put(actor.school_id, "STATE", state, expected=state["etag"]),
                                 self.event(actor, f"EXECUTION_{body.status}", activity_id, version)])
        except Conflict:
            duplicate = self.store.read(actor.school_id, key)
            if duplicate and duplicate["status"] == body.status and duplicate["note"] == body.note:
                return ExecutionReport.model_validate({k: v for k, v in duplicate.items() if k != "etag"})
            raise HTTPException(409, "Report or current version changed") from None
        return report

    def reports(self, actor, version):
        admin(actor)
        self.school(actor)
        return [ExecutionReport.model_validate({k: v for k, v in r.items() if k != "etag"})
                for r in self.store.query(actor.school_id, f"REPORT#{version}#")]

    def exceptions(self, actor, version):
        return ExceptionSummary(reports=[r for r in self.reports(actor, version) if r.status != "COMPLETED"],
                                resolutions=[Resolution.model_validate(r) for r in self.store.query(actor.school_id, f"RESOLUTION#{version}#")])

    def resolve(self, actor, version, activity_id, body):
        admin(actor)
        self.school(actor)
        report = self.store.read(actor.school_id, f"REPORT#{version}#{activity_id}")
        if not report or report["status"] == "COMPLETED":
            raise HTTPException(409, "Execution exception required")
        key = f"RESOLUTION#{version}#{activity_id}#{body.request_id}"
        existing = self.store.read(actor.school_id, key)
        if existing:
            if existing["note"] != body.note:
                raise HTTPException(409, "Resolution request ID reused with different note")
            return Resolution.model_validate(existing)
        resolution = Resolution(request_id=str(body.request_id), actor=actor.sub, timestamp=now(),
                                activity_id=activity_id, plan_version=version, note=body.note)
        self.transact([self.store.put(actor.school_id, key, resolution.model_dump(), create=True),
                       self.store.put(actor.school_id, f"REPORT#{version}#{activity_id}", report, expected=report["etag"]),
                       self.event(actor, "EXCEPTION_RESOLVED", activity_id, version)])
        return resolution

    def audits(self, actor):
        admin(actor)
        self.school(actor)
        return [AuditEvent.model_validate(e) for e in self.store.query(actor.school_id, "AUDIT#")]
