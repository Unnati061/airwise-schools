"""A labelled sample with independently checked shared-resource competition."""
from backend.app.repair_fixture import shared_resources_week
from backend.app.repair_engine import repair
from backend.app.repair_validator import original, validate_plan
from fastapi.testclient import TestClient
from backend.app import auth
from backend.app.main import app
from backend.app.durable_store import DynamoStore
from backend.app.workflow import Workflow
from backend.tests.test_workflow import ADMIN, TEACHER, FakeDynamo


def test_shared_resources_sample_is_valid_before_restrictions_and_repairs():
    inputs = shared_resources_week()
    unrestricted = inputs.model_copy(update={"restrictions": []})
    assert validate_plan(unrestricted, [original(a) for a in unrestricted.activities]).valid
    plan = repair(inputs)
    assert plan.successful and plan.solver_status == "OPTIMAL"
    assert not plan.baseline.validation.valid
    assert plan.recommendation == "repair"
    assert validate_plan(inputs, plan.placements).valid
    assert len(plan.placements) == len(inputs.activities)
    assert plan.counts.changed_periods == 2
    assert plan.counts.substitutions == 2
    assert plan.counts.room_moves == 2
    assert plan.counts.deferrals == 0
    placed = {p.activity_id: p for p in plan.placements}
    assert placed["6-a:Mon-2"].period_id == "Mon-4"
    assert placed["6-a:Mon-2"].room_id == "movement-studio"
    assert placed["6-b:Mon-3"].period_id == "Mon-3"
    assert placed["6-b:Mon-3"].room_id == "movement-hall"
    assert placed["7-a:Mon-4"].period_id == "Mon-4"
    assert placed["7-a:Mon-4"].room_id == "movement-hall"


def test_independent_validator_rejects_corrupted_shared_resource_repair():
    inputs = shared_resources_week()
    plan = repair(inputs)
    teacher_conflict = [p.model_copy(update={"period_id": "Mon-3"})
                       if p.activity_id == "6-a:Mon-2" else p for p in plan.placements]
    assert not validate_plan(inputs, teacher_conflict).valid
    room_conflict = [p.model_copy(update={"room_id": "movement-hall"})
                    if p.activity_id == "6-a:Mon-2" else p for p in plan.placements]
    assert not validate_plan(inputs, room_conflict).valid


def test_sample_endpoint_requires_administrator_and_known_scenario():
    service = Workflow(DynamoStore(FakeDynamo(), "offline-test-only"))
    app.dependency_overrides[auth.workflow] = lambda: service
    try:
        client = TestClient(app)
        assert client.get("/repair-fixture?scenario=shared-resources").status_code == 401
        app.dependency_overrides[auth.identity] = lambda: ADMIN
        result = client.get("/repair-fixture?scenario=shared-resources")
        assert result.status_code == 200
        assert result.json()["versions"]["timetable"] == "sample-shared-resources-v1"
        assert len(result.json()["activities"]) == 240
        assert client.get("/repair-fixture?scenario=unknown").status_code == 422
        app.dependency_overrides[auth.identity] = lambda: TEACHER
        assert client.get("/repair-fixture?scenario=shared-resources").status_code == 403
    finally:
        app.dependency_overrides.clear()
