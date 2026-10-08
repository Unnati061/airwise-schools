"""Independent placement audit: no solver imports or candidate-building helpers."""
from .repair_contracts import Counts, Difference, Placement, RepairInput, Validation


def original(a):
    return Placement(activity_id=a.id, period_id=a.original_period_id, room_id=a.original_room_id)


def validate_plan(data: RepairInput, placements: list[Placement]) -> Validation:
    errors = []
    counts = Counts()
    differences = []
    activities = {a.id: a for a in data.activities}
    periods = {p.id: p for p in data.periods}
    rooms = {r.id: r for r in data.rooms}
    teachers = {t.id: t for t in data.teachers}
    sections = {s.id: s for s in data.sections}
    seen = set()
    occupied = set()
    for p in placements:
        if p.activity_id not in activities or p.activity_id in seen:
            errors.append(f"{p.activity_id}: unknown or duplicate activity")
            continue
        seen.add(p.activity_id)
        a = activities[p.activity_id]
        before = original(a)
        if p != before:
            differences.append(Difference(activity_id=a.id, original=before, proposed=p))
        counts.changed_periods += p.period_id != a.original_period_id
        counts.room_moves += p.room_id is not None and p.room_id != a.original_room_id
        counts.substitutions += p.alternative_id is not None
        counts.deferrals += p.deferred
        outside = periods[a.original_period_id].day != data.affected_day
        if (a.fixed or outside) and p != before:
            errors.append(f"{a.id}: fixed or unaffected activity changed")
        if p.deferred:
            if not a.allow_deferral or p.period_id is not None or p.room_id is not None or p.alternative_id is not None:
                errors.append(f"{a.id}: unauthorized or malformed deferral")
            continue
        if p.period_id not in periods or p.room_id not in rooms:
            errors.append(f"{a.id}: missing or unknown placement")
            continue
        if p.period_id not in a.permitted_period_ids or periods[p.period_id].day != periods[a.original_period_id].day:
            errors.append(f"{a.id}: unauthorized period")
        kind = a.kind
        types = a.room_types
        allowed_rooms = a.permitted_room_ids
        if p.alternative_id is not None:
            alternatives = [v for v in a.approved_alternatives if v.id == p.alternative_id]
            if not alternatives:
                errors.append(f"{a.id}: unauthorized substitution")
                continue
            alternative = alternatives[0]
            kind, types, allowed_rooms = alternative.kind, alternative.room_types, alternative.room_ids
        room = rooms[p.room_id]
        teacher = teachers[a.teacher_id]
        if p.room_id not in allowed_rooms or room.kind not in types or room.capacity < sections[a.section_id].size:
            errors.append(f"{a.id}: room permission/type/capacity")
        if p.period_id not in room.available_period_ids:
            errors.append(f"{a.id}: room unavailable")
        if p.period_id not in teacher.available_period_ids or kind not in teacher.supervised_kinds:
            errors.append(f"{a.id}: teacher unavailable or inappropriate supervision")
        if room.kind == "outdoor" and any(p.period_id in r.period_ids and a.section_id in r.section_ids for r in data.restrictions):
            errors.append(f"{a.id}: outdoor restriction")
        for resource, identifier in (("section", a.section_id), ("teacher", a.teacher_id), ("room", p.room_id)):
            key = (resource, identifier, p.period_id)
            if key in occupied:
                errors.append(f"{a.id}: {resource} overlap")
            occupied.add(key)
    for missing in sorted(activities.keys() - seen):
        errors.append(f"{missing}: activity missing")
    return Validation(valid=not errors, errors=errors, counts=counts,
                      differences=sorted(differences, key=lambda d: d.activity_id))
