from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from ortools.sat.python import cp_model
from pydantic import ValidationError

from backend.app.main import app
from backend.app.plan_repository import MemoryPlanRepository
from backend.app.repair_contracts import RepairInput
from backend.app.repair_engine import build_baseline, repair
from backend.app.repair_fixture import synthetic_week
from backend.app.repair_validator import original, validate_plan


def scoped_pair():
    """Synthetic diagnostic case: two sections' Monday second-period lessons."""
    data = synthetic_week()
    data.restrictions = []
    data.activities = [a for a in data.activities if a.id in ("6-a:Mon-2", "6-b:Mon-2")]
    for a in data.activities:
        a.permitted_period_ids = ["Mon-2"]
    return data


def test_unchanged_week_and_fixed_lessons():
    data = synthetic_week()
    data.restrictions = []
    plan = repair(data)
    assert plan.successful and plan.solver_status == "OPTIMAL"
    assert plan.recommendation == "baseline" and plan.differences == []
    assert len(plan.placements) == 240
    assert validate_plan(data, plan.placements).valid
    assert all(p == original(a) for p, a in zip(plan.placements, data.activities))


def test_approved_alternative_baseline_is_best_and_preserves_versions():
    data = synthetic_week()
    plan = repair(data)
    assert plan.successful and plan.solver_status == "OPTIMAL"
    assert plan.recommendation == "baseline" and plan.baseline.validation.valid
    assert plan.input_versions == data.versions
    assert plan.counts.model_dump() == dict(changed_periods=0, substitutions=1, deferrals=0, room_moves=1)
    assert [d.activity_id for d in plan.differences] == ["6-a:Mon-2"]
    assert plan.differences[0].proposed.alternative_id == "indoor-movement"
    assert plan.differences[0].proposed.room_id == "room-6-a"


def test_period_specific_restriction_can_be_repaired_by_swap():
    data = synthetic_week()
    data.restrictions[0].period_ids = ["Mon-2"]
    data.activities[1].approved_alternatives = []
    plan = repair(data)
    assert plan.successful and plan.recommendation == "repair"
    assert plan.counts.changed_periods == 2 and plan.counts.substitutions == 0
    assert next(p for p in plan.placements if p.activity_id == "6-a:Mon-2").period_id != "Mon-2"
    assert next(p for p in plan.placements if p.activity_id == "6-a:Mon-1").period_id == "Mon-1"
    assert validate_plan(data, plan.placements).valid


def test_room_contention_then_explicit_room_move_repairs_it():
    data = scoped_pair()
    a, b = data.activities
    a.kind, a.room_types = "lesson", ["classroom"]
    a.approved_alternatives = []
    a.original_room_id = "room-6-b"
    a.permitted_room_ids = ["room-6-b"]
    next(r for r in data.rooms if r.id == "room-6-b").capacity = 40
    assert not build_baseline(data).validation.valid
    assert repair(data).solver_status == "INFEASIBLE"
    a.permitted_room_ids.append("room-6-a")
    result = repair(data)
    assert result.successful and result.counts.room_moves == 1
    assert validate_plan(data, result.placements).valid


@pytest.mark.parametrize("failure", ["capacity", "teacher_conflict", "teacher_availability", "supervision", "room_availability"])
def test_hard_constraints_do_not_relax(failure):
    data = scoped_pair()
    a, b = data.activities
    a.approved_alternatives = []
    if failure == "capacity":
        next(r for r in data.rooms if r.id == "field").capacity = 29
    elif failure == "teacher_conflict":
        b.teacher_id = a.teacher_id
    elif failure == "teacher_availability":
        data.teachers[0].available_period_ids.remove("Mon-2")
    elif failure == "supervision":
        data.teachers[0].supervised_kinds.remove("pe")
    else:
        next(r for r in data.rooms if r.id == "field").available_period_ids.remove("Mon-2")
    assert not validate_plan(data, [original(a) for a in data.activities]).valid
    result = repair(data)
    assert result.solver_status == "INFEASIBLE" and not result.successful
    assert result.placements == []


def test_fixed_outdoor_lesson_cannot_be_substituted_or_deferred():
    data = synthetic_week()
    data.activities[1].fixed = True
    data.activities[1].allow_deferral = True
    plan = repair(data)
    assert plan.solver_status == "INFEASIBLE" and not plan.successful


def test_explicit_deferral_accounts_for_every_activity():
    data = synthetic_week()
    a = data.activities[1]
    a.approved_alternatives = []
    assert repair(data).solver_status == "INFEASIBLE"
    a.allow_deferral = True
    plan = repair(data)
    assert plan.successful and len(plan.placements) == len(data.activities)
    assert plan.counts.deferrals == 1 and plan.counts.changed_periods == 1
    assert next(p for p in plan.placements if p.activity_id == a.id).deferred


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "fixed", "unauthorized_alternative", "unauthorized_deferral", "outdoor", "outside_day", "unknown_room", "section_overlap"])
def test_independent_validator_rejects_corruption(corruption):
    data = synthetic_week()
    placements = build_baseline(data).placements
    if corruption == "missing":
        placements.pop()
    elif corruption == "duplicate":
        placements.append(placements[0])
    elif corruption == "fixed":
        placements[0].period_id = "Mon-3"
    elif corruption == "unauthorized_alternative":
        placements[1].alternative_id = "unapproved"
    elif corruption == "unauthorized_deferral":
        placements[2].deferred = True
        placements[2].period_id = placements[2].room_id = None
    elif corruption == "outdoor":
        placements[1] = original(data.activities[1])
    elif corruption == "outside_day":
        placements[8].period_id = "Tue-3"
    elif corruption == "unknown_room":
        placements[1].room_id = "unknown"
    else:
        placements[2].period_id = "Mon-2"
    assert not validate_plan(data, placements).valid


class ControlledStatus:
    def __init__(self, status):
        self.status = status
        self.parameters = SimpleNamespace()

    def solve(self, model):
        assert 0 < self.parameters.max_time_in_seconds <= 5
        return self.status

    def status_name(self, status):
        return status


@pytest.mark.parametrize("status", ["UNKNOWN", "MODEL_INVALID"])
def test_controlled_status_without_difficult_problem_assumptions(status):
    data = synthetic_week()
    data.activities[1].approved_alternatives = []
    result = repair(data, solver_factory=lambda: ControlledStatus(status))
    assert result.solver_status == status and not result.successful and result.placements == []
    if status == "UNKNOWN":
        assert "not proven infeasible" in result.diagnostic


def test_unknown_can_return_valid_baseline_without_optimality_claim():
    result = repair(synthetic_week(), solver_factory=lambda: ControlledStatus("UNKNOWN"))
    assert result.successful and result.solver_status == "UNKNOWN"
    assert "optimality unproven" in result.diagnostic


def test_preparation_exhaustion_skips_search(monkeypatch):
    clock = iter([0.0, 6.0])
    monkeypatch.setattr("backend.app.repair_engine.monotonic", lambda: next(clock))
    class NoSearch(ControlledStatus):
        def solve(self, model):
            pytest.fail("Search must not start with an exhausted budget")
    result = repair(synthetic_week(), solver_factory=lambda: NoSearch("UNKNOWN"))
    assert result.solver_status == "UNKNOWN" and result.successful


def test_solver_corruption_is_not_successful():
    class CorruptSolver(cp_model.CpSolver):
        def boolean_value(self, var):
            return True
    result = repair(synthetic_week(), solver_factory=CorruptSolver)
    assert not result.successful and result.placements == []
    assert not result.validation.valid


def test_feasible_status_is_not_promoted_to_optimal():
    class FeasibleSolver(cp_model.CpSolver):
        def solve(self, model):
            super().solve(model)
            return cp_model.FEASIBLE
    result = repair(synthetic_week(), solver_factory=FeasibleSolver)
    assert result.successful and result.solver_status == "FEASIBLE"


def test_lexicographic_priority_prefers_periods_before_substitutions():
    data = synthetic_week()
    data.restrictions[0].period_ids = ["Mon-2"]
    result = repair(data)
    # A swap avoids substitution but changes two periods; approved baseline wins.
    assert result.recommendation == "baseline"
    assert result.counts.changed_periods == 0 and result.counts.substitutions == 1


def test_api_contracts_inspection_and_temporary_repository_isolation():
    from backend.app import auth
    from backend.app.durable_store import DynamoStore
    from backend.app.workflow import Workflow
    from backend.tests.test_workflow import ADMIN, FakeDynamo
    service = Workflow(DynamoStore(FakeDynamo(), "test"))
    app.dependency_overrides[auth.workflow] = lambda: service
    app.dependency_overrides[auth.identity] = lambda: ADMIN
    client = TestClient(app)
    fixture = client.get("/repair-fixture").json()
    fixture = client.post("/inputs", json={"expected_revision": None, "input": fixture}).json()["input"]
    response = client.post("/draft-plans", json=fixture)
    assert response.status_code == 200
    result = response.json()
    assert result["successful"] and result["input_versions"] == fixture["versions"]
    assert client.get(f"/draft-plans/{result['id']}").json() == result
    assert client.get("/draft-plans/nonexistent").status_code == 404
    fixture["restrictions"][0]["administrator_confirmed"] = False
    assert client.post("/draft-plans", json=fixture).status_code == 422
    app.dependency_overrides.clear()
    repository = MemoryPlanRepository()
    plan = repair(synthetic_week())
    repository.save(plan)
    copy = repository.get(plan.id)
    copy.placements.clear()
    assert repository.get(plan.id).placements


def test_input_references_and_versions_are_strict():
    data = synthetic_week().model_dump()
    data["activities"][1]["permitted_period_ids"] = ["Tue-2"]
    with pytest.raises(ValidationError, match="Cross-day"):
        RepairInput.model_validate(data)
