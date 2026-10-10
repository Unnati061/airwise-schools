from backend.app.repair_fixture import room_resilience_week
from backend.app.repair_validator import validate_plan
from backend.app.workflow import Workflow
from backend.app.workflow_contracts import InputUpdate
from backend.app.durable_store import DynamoStore
from backend.tests.test_workflow import ADMIN, FakeDynamo


def test_replay_approved_page_revision_stays_fixed_until_explicit_room_change(monkeypatch):
    import json
    from pathlib import Path
    from scripts.ui_fixtures import run

    captured = {}
    monkeypatch.setattr(Path, 'write_text', lambda path, content, **kwargs: captured.update(records=json.loads(content)))
    run()
    records = captured['records']
    assert records['evidence']['snapshot']['mode'] == 'REPLAY'
    current = records['room_current']
    assert current['plan_version'] == records['room_plan']['id']
    assert current['input_revision'] == records['room_input']['revision']
    assert not current['needs_review']
    assert records['room_detail']['approval']['input_versions'] == records['room_plan']['input_versions']
    # A genuine confirmed availability change still invalidates the old approval.
    revised = records['revised_current']
    assert revised['input_revision'] == records['revised_input']['revision'] != current['input_revision']
    assert revised['plan_version'] == current['plan_version'] and revised['needs_review']


def test_room_exclusion_repairs_and_never_replaces_approval():
    service = Workflow(DynamoStore(FakeDynamo(), 'offline-only'))
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=None, input=room_resilience_week()))
    previous = service.draft(ADMIN, confirmed.input)
    assert previous.successful and validate_plan(confirmed.input, previous.placements).valid
    service.approve(ADMIN, previous.id)
    frozen = service.approved_detail(ADMIN, previous.id)
    occupied = next(p.room_id for p in previous.placements if p.activity_id == '6-a:Mon-2')
    revised = confirmed.input.model_copy(deep=True)
    room = next(r for r in revised.rooms if r.id == occupied)
    room.available_period_ids = [p for p in room.available_period_ids if not p.startswith('Mon-')]
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=confirmed.revision, input=revised))
    plan = service.draft(ADMIN, confirmed.input)
    assert plan.successful and plan.solver_status == 'OPTIMAL'
    assert validate_plan(confirmed.input, plan.placements).valid
    assert len(plan.placements) == 240
    corrupted = [p.model_copy(update={'room_id': occupied}) if p.activity_id == '6-a:Mon-2' else p for p in plan.placements]
    assert not validate_plan(confirmed.input, corrupted).valid
    assert all(p.room_id != occupied or not p.period_id.startswith('Mon-') for p in plan.placements)
    assert service.current(ADMIN).plan_version == previous.id
    assert service.current(ADMIN).needs_review
    after = service.approved_detail(ADMIN, previous.id)
    assert after.plan == frozen.plan
    assert after.approval == frozen.approval
    changed = [p for p, old in zip(plan.placements, previous.placements) if p != old]
    assert changed  # Real revised assignments, not just new UUIDs.
    service.approve(ADMIN, plan.id)
    assert service.current(ADMIN).plan_version == plan.id


def test_fixed_hall_exclusion_is_proven_infeasible():
    from backend.app.repair_engine import repair
    inputs = room_resilience_week()
    next(r for r in inputs.rooms if r.id == 'movement-hall').available_period_ids = []
    plan = repair(inputs)
    assert not plan.successful and plan.solver_status == 'INFEASIBLE'
    assert not plan.baseline.validation.valid
    # Independently test the immovable original lesson against availability.
    assert any('availability' in e.lower() or 'unavailable' in e.lower() for e in plan.baseline.validation.errors)
