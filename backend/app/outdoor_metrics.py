"""Whole single-period restrictions intersect declared synthetic activity minutes."""
from .workflow_contracts import OutdoorMetrics


def outdoor_metrics(plan, reports):
    data = plan.input_snapshot
    rooms = {r.id: r for r in data.rooms}
    sizes = {s.id: s.size for s in data.sections}
    proposed = {p.activity_id: p for p in plan.placements}
    reports_by_id = {r.activity_id: r for r in sorted(reports, key=lambda r: r.timestamp)
                     if r.plan_version == plan.id}
    def restricted(section, period):
        return any(section in r.section_ids and period in r.period_ids for r in data.restrictions)
    totals = dict(original=0, approved=0, indoor=0, completed=0, unknown=0)
    missing = []
    for a in data.activities:
        p = proposed[a.id]
        before = rooms[a.original_room_id].kind == "outdoor" and restricted(a.section_id, a.original_period_id)
        after = not p.deferred and rooms[p.room_id].kind == "outdoor" and restricted(a.section_id, p.period_id)
        if not before and not after:
            continue
        if a.duration_minutes is None:
            missing.append(a.id)
            continue
        minutes = sizes[a.section_id] * a.duration_minutes
        totals["original"] += minutes if before else 0
        totals["approved"] += minutes if after else 0
        indoor = before and not p.deferred and rooms[p.room_id].kind != "outdoor" and p.alternative_id is not None
        if indoor:
            totals["indoor"] += minutes
            report = reports_by_id.get(a.id)
            if report and report.teacher_id == a.teacher_id and report.status == "COMPLETED":
                totals["completed"] += minutes
            elif not report or report.status == "NEEDS_CLARIFICATION":
                totals["unknown"] += minutes
    def hours(key):
        return None if missing else round(totals[key] / 60, 6)
    return OutdoorMetrics(available=not missing, missing_duration_activity_ids=sorted(missing),
        original_restricted_outdoor_student_hours=hours("original"),
        approved_restricted_outdoor_student_hours=hours("approved"),
        planned_indoor_substitution_student_hours=hours("indoor"),
        teacher_reported_completed_indoor_student_hours=hours("completed"),
        unknown_indoor_execution_student_hours=hours("unknown"))
