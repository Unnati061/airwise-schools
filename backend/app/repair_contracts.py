from typing import Literal

from pydantic import Field, model_validator

from .models import Contract, Section


class Period(Contract):
    id: str
    day: str
    number: int = Field(ge=1, le=8)


class Teacher(Contract):
    id: str
    available_period_ids: list[str]
    supervised_kinds: list[str]


class Room(Contract):
    id: str
    kind: Literal["classroom", "outdoor", "lab"]
    capacity: int = Field(gt=0)
    available_period_ids: list[str]


class Alternative(Contract):
    id: str
    label: str
    kind: str
    room_types: list[Literal["classroom", "outdoor", "lab"]] = Field(min_length=1)
    room_ids: list[str] = Field(min_length=1, max_length=64)


class Activity(Contract):
    id: str
    section_id: str
    teacher_id: str
    label: str
    kind: str
    room_types: list[Literal["classroom", "outdoor", "lab"]] = Field(min_length=1)
    original_period_id: str
    original_room_id: str
    permitted_period_ids: list[str] = Field(min_length=1, max_length=8)
    permitted_room_ids: list[str] = Field(min_length=1, max_length=64)
    fixed: bool = False
    approved_alternatives: list[Alternative] = Field(default_factory=list, max_length=8)
    allow_deferral: bool = False


class Restriction(Contract):
    id: str
    kind: Literal["outdoor_prohibited"]
    period_ids: list[str] = Field(min_length=1)
    section_ids: list[str] = Field(min_length=1)
    administrator_confirmed: Literal[True]
    confirmed_by: str = Field(min_length=1)


class InputVersions(Contract):
    school: str = Field(min_length=1)
    timetable: str = Field(min_length=1)
    restrictions: str = Field(min_length=1)


class RepairInput(Contract):
    mode: Literal["SYNTHETIC"]
    school_id: str
    versions: InputVersions
    affected_day: str
    sections: list[Section] = Field(min_length=6, max_length=6)
    periods: list[Period] = Field(min_length=1, max_length=40)
    teachers: list[Teacher] = Field(min_length=1, max_length=64)
    rooms: list[Room] = Field(min_length=1, max_length=64)
    activities: list[Activity] = Field(min_length=1, max_length=240)
    restrictions: list[Restriction] = Field(default_factory=list, max_length=40)

    @model_validator(mode="after")
    def references(self):
        for values in (self.sections, self.periods, self.teachers, self.rooms,
                       self.activities, self.restrictions):
            if len({v.id for v in values}) != len(values):
                raise ValueError("Duplicate stable ID")
        periods = {p.id: p for p in self.periods}
        sections = {s.id for s in self.sections}
        rooms = {r.id for r in self.rooms}
        teachers = {t.id for t in self.teachers}
        if len({(p.day, p.number) for p in self.periods}) != len(self.periods):
            raise ValueError("Duplicate day/period slot")
        if not any(p.day == self.affected_day for p in self.periods):
            raise ValueError("Affected day is absent")
        for resource in [*self.teachers, *self.rooms]:
            if not set(resource.available_period_ids) <= periods.keys():
                raise ValueError("Unknown availability period")
        for a in self.activities:
            if a.section_id not in sections or a.teacher_id not in teachers:
                raise ValueError("Unknown activity section or teacher")
            if a.original_period_id not in periods or a.original_room_id not in rooms:
                raise ValueError("Unknown original placement")
            if not set(a.permitted_period_ids) <= periods.keys() or not set(a.permitted_room_ids) <= rooms:
                raise ValueError("Unknown permitted placement")
            if any(periods[p].day != periods[a.original_period_id].day for p in a.permitted_period_ids):
                raise ValueError("Cross-day placement is outside B1")
            if len({v.id for v in a.approved_alternatives}) != len(a.approved_alternatives):
                raise ValueError("Duplicate alternative ID")
            if any(not set(v.room_ids) <= rooms for v in a.approved_alternatives):
                raise ValueError("Unknown alternative room")
        for r in self.restrictions:
            if not set(r.period_ids) <= periods.keys() or not set(r.section_ids) <= sections:
                raise ValueError("Unknown restriction scope")
            if any(periods[p].day != self.affected_day for p in r.period_ids):
                raise ValueError("Restriction outside affected day")
        return self


class Placement(Contract):
    activity_id: str
    period_id: str | None
    room_id: str | None
    alternative_id: str | None = None
    deferred: bool = False


class Counts(Contract):
    changed_periods: int = 0
    substitutions: int = 0
    deferrals: int = 0
    room_moves: int = 0


class Difference(Contract):
    activity_id: str
    original: Placement
    proposed: Placement


class Validation(Contract):
    valid: bool
    errors: list[str]
    counts: Counts
    differences: list[Difference]


class Baseline(Contract):
    placements: list[Placement]
    validation: Validation


class DraftPlan(Contract):
    id: str
    input_versions: InputVersions
    solver_status: Literal["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"]
    successful: bool
    recommendation: Literal["baseline", "repair", "none"]
    baseline: Baseline
    placements: list[Placement]
    validation: Validation | None = None
    counts: Counts | None = None
    differences: list[Difference] = Field(default_factory=list)
    diagnostic: str | None = None
    input_snapshot: RepairInput
