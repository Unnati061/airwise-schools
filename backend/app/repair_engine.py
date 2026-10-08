from time import monotonic
from uuid import uuid4

from ortools.sat.python import cp_model

from .repair_contracts import Baseline, DraftPlan, Placement, RepairInput
from .repair_validator import original, validate_plan


def candidates(data, a):
    periods = {p.id: p for p in data.periods}
    rooms = {r.id: r for r in data.rooms}
    teacher = next(t for t in data.teachers if t.id == a.teacher_id)
    size = next(s.size for s in data.sections if s.id == a.section_id)
    locked = a.fixed or periods[a.original_period_id].day != data.affected_day
    variants = [(None, a.kind, a.room_types, a.permitted_room_ids)]
    if not locked:
        variants += [(v.id, v.kind, v.room_types, v.room_ids) for v in a.approved_alternatives]
    choices = []
    for alternative, kind, types, room_ids in variants:
        if kind not in teacher.supervised_kinds:
            continue
        for period in sorted(set(a.permitted_period_ids)):
            if period not in teacher.available_period_ids:
                continue
            for room_id in sorted(set(room_ids)):
                room = rooms[room_id]
                if room.kind not in types or room.capacity < size or period not in room.available_period_ids:
                    continue
                if room.kind == "outdoor" and any(period in r.period_ids and a.section_id in r.section_ids for r in data.restrictions):
                    continue
                p = Placement(activity_id=a.id, period_id=period, room_id=room_id, alternative_id=alternative)
                if not locked or p == original(a):
                    choices.append(p)
    if a.allow_deferral and not locked:
        choices.append(Placement(activity_id=a.id, period_id=None, room_id=None, deferred=True))
    return choices


def build_baseline(data: RepairInput) -> Baseline:
    rooms = {r.id: r for r in data.rooms}
    periods = {p.id: p for p in data.periods}
    placements = []
    for a in data.activities:
        placement = original(a)
        restricted = rooms[a.original_room_id].kind == "outdoor" and any(
            a.original_period_id in r.period_ids and a.section_id in r.section_ids for r in data.restrictions)
        if restricted and not a.fixed and periods[a.original_period_id].day == data.affected_day:
            approved = [p for p in candidates(data, a) if p.period_id == a.original_period_id
                        and p.alternative_id is not None and rooms[p.room_id].kind == "classroom"]
            if approved:
                placement = approved[0]
        placements.append(placement)
    return Baseline(placements=placements, validation=validate_plan(data, placements))


def score(counts):
    return (counts.changed_periods, counts.substitutions + counts.deferrals, counts.room_moves)


def repair(data: RepairInput, *, solver_factory=cp_model.CpSolver) -> DraftPlan:
    start = monotonic()
    baseline = build_baseline(data)
    model = cp_model.CpModel()
    choices = []
    occupancy = {}
    objective = []
    n = len(data.activities)
    # Bounded scalar weights exactly encode the single lexicographic preference.
    for a in data.activities:
        options = []
        for i, p in enumerate(candidates(data, a)):
            var = model.new_bool_var(f"{a.id}:{i}")
            options.append((var, p))
            if not p.deferred:
                for resource, identifier in (("section", a.section_id), ("teacher", a.teacher_id), ("room", p.room_id)):
                    occupancy.setdefault((resource, identifier, p.period_id), []).append(var)
            cost = ((p.period_id != a.original_period_id) * (n + 1) ** 2
                    + (int(p.alternative_id is not None) + int(p.deferred)) * (n + 1)
                    + int(p.room_id is not None and p.room_id != a.original_room_id))
            objective.append(cost * var)
        model.add_exactly_one([v for v, _ in options])
        choices.append(options)
    for occupied in occupancy.values():
        model.add_at_most_one(occupied)
    model.minimize(sum(objective))
    solver = solver_factory()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    remaining = 5.0 - (monotonic() - start)
    if remaining <= 0:
        status = "UNKNOWN"
    else:
        solver.parameters.max_time_in_seconds = remaining
        status = solver.status_name(solver.solve(model))
    proposed = []
    audit = None
    recommendation = "none"
    diagnostic = None
    if status in ("OPTIMAL", "FEASIBLE"):
        proposed = [p for options in choices for v, p in options if solver.boolean_value(v)]
        audit = validate_plan(data, proposed)
        if not audit.valid:
            diagnostic = "Independent validator rejected solver output"
            proposed = []
        elif baseline.validation.valid and score(baseline.validation.counts) <= score(audit.counts):
            proposed, audit, recommendation = baseline.placements, baseline.validation, "baseline"
        else:
            recommendation = "repair"
    elif status == "UNKNOWN" and baseline.validation.valid:
        proposed, audit, recommendation = baseline.placements, baseline.validation, "baseline"
        diagnostic = "Search inconclusive; independently valid baseline, optimality unproven"
    else:
        diagnostic = {"UNKNOWN": "Search inconclusive; not proven infeasible",
                      "INFEASIBLE": "No feasible permitted placement",
                      "MODEL_INVALID": "CP-SAT rejected the model"}.get(status)
    return DraftPlan(id=str(uuid4()), input_versions=data.versions, input_snapshot=data,
                     solver_status=status, successful=bool(proposed) and audit is not None and audit.valid,
                     recommendation=recommendation, baseline=baseline, placements=proposed,
                     validation=audit, counts=audit.counts if audit and audit.valid else None,
                     differences=audit.differences if audit and audit.valid else [], diagnostic=diagnostic)
