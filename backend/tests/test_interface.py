from datetime import date, datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.app import auth, workflow_api
from backend.app.durable_store import DynamoStore
from backend.app.evidence_contracts import EvidenceBinding
from backend.app.main import app
from backend.app.repair_fixture import synthetic_week
from backend.app.workflow import SCHOOL, Workflow
from backend.app.workflow_contracts import ExecutionInput, InputUpdate, ResolutionInput
from backend.tests.test_workflow import ADMIN, TEACHER, OTHER, FakeDynamo, approved, rejects


@pytest.fixture
def service():
    return Workflow(DynamoStore(FakeDynamo(), 'test-table'))


def test_public_config_is_non_secret_and_identity_requires_auth(service, monkeypatch):
    monkeypatch.setattr(workflow_api, 'settings', lambda: dict(region='ap-southeast-2', pool_id='ap-southeast-2_test', client_id='public-client', runtime_role_arn='must-not-be-exposed', profile='airwise'))
    app.dependency_overrides[auth.workflow] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.get('/auth/config').json() == dict(region='ap-southeast-2', pool_id='ap-southeast-2_test', client_id='public-client')
            assert client.get('/me').status_code == 401
            app.dependency_overrides[auth.identity] = lambda: TEACHER
            assert client.get('/me').json()['teacher_id'] == TEACHER.teacher_id
    finally:
        app.dependency_overrides.clear()


def test_historical_teacher_assignments_reports_and_new_ack_boundary(service):
    first = approved(service)
    service.ack(TEACHER, first.plan_version)
    service.report(TEACHER, first.plan_version, '6-a:Mon-2', ExecutionInput(status='COULD_NOT_IMPLEMENT', note='Synthetic locked room'))
    service.report(OTHER, first.plan_version, '6-b:Mon-2', ExecutionInput(status='COMPLETED'))
    old = service.inputs(ADMIN)
    new = service.confirm(ADMIN, InputUpdate(expected_revision=old.revision, input=old.input))
    next_plan = service.draft(ADMIN, new.input)
    service.approve(ADMIN, next_plan.id)
    history = service.history(TEACHER)
    assert len(history) == 2 and all(entry.counts is None for entry in history)
    assert sum(entry.current for entry in history) == 1
    historical = service.assignments(TEACHER, TEACHER.teacher_id, first.plan_version)
    assert historical.acknowledged and len(historical.assignments) == 40
    assert not service.assignments(TEACHER, TEACHER.teacher_id).acknowledged
    reports = service.teacher_reports(TEACHER, TEACHER.teacher_id, first.plan_version)
    assert len(reports) == 1 and reports[0].activity_id == '6-a:Mon-2'
    rejects(403, lambda: service.teacher_reports(TEACHER, OTHER.teacher_id, first.plan_version))
    rejects(403, lambda: service.assignments(TEACHER, OTHER.teacher_id, first.plan_version))
    rejects(409, lambda: service.report(TEACHER, first.plan_version, '6-a:Mon-2', ExecutionInput(status='COMPLETED')))


def test_review_counts_are_unique_and_new_exception_reopens(service):
    version = approved(service).plan_version
    body = ExecutionInput(status='COULD_NOT_IMPLEMENT', note='Synthetic room inaccessible')
    service.report(TEACHER, version, '6-a:Mon-2', body)
    service.report(TEACHER, version, '6-a:Mon-2', body)
    service.ack(TEACHER, version)
    review = service.execution_review(ADMIN, version)
    assert review.counts.reported == 1 and review.counts.could_not_implement == 1
    assert review.counts.completed == 0 and review.counts.unresolved == 1
    note = ResolutionInput(request_id=uuid4(), note='Synthetic administrator reviewed room access')
    service.resolve(ADMIN, version, '6-a:Mon-2', note)
    assert service.execution_review(ADMIN, version).counts.unresolved == 0
    service.report(TEACHER, version, '6-a:Mon-2', ExecutionInput(status='NEEDS_CLARIFICATION', note='Different synthetic question'))
    review = service.execution_review(ADMIN, version)
    assert review.counts.reported == 1 and review.counts.needs_clarification == 1 and review.counts.unresolved == 1
    rejects(403, lambda: service.execution_review(TEACHER, version))
    rejects(404, lambda: service.execution_review(ADMIN, 'missing'))


def test_input_and_approved_provenance_are_version_bound(service):
    binding = EvidenceBinding(analysis_id='synthetic-analysis', evidence_id='synthetic-replay', mode='REPLAY', calendar_date=date(2026, 10, 12), reviewed_by=ADMIN.sub, reviewed_at=datetime.now(timezone.utc))
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=None, input=synthetic_week()), evidence_binding=binding)
    draft = service.draft(ADMIN, confirmed.input)
    service.approve(ADMIN, draft.id)
    assert service.approved_detail(ADMIN, draft.id).evidence_binding == binding
    assert service.input_version(ADMIN, confirmed.revision).evidence_binding == binding
    assert service.assignments(TEACHER, TEACHER.teacher_id).evidence_mode == 'REPLAY'
    rejects(403, lambda: service.approved_detail(TEACHER, draft.id))
    rejects(403, lambda: service.input_version(TEACHER, confirmed.revision))
    rejects(404, lambda: service.input_version(ADMIN, 'missing'))
    outsider = ADMIN.model_copy(update={'school_id': 'other-school'})
    rejects(403, lambda: service.history(outsider))
    rejects(403, lambda: service.approved_detail(outsider, draft.id))


def test_new_read_routes_enforce_teacher_permissions(service):
    version = approved(service).plan_version
    app.dependency_overrides[auth.workflow] = lambda: service
    app.dependency_overrides[auth.identity] = lambda: TEACHER
    try:
        with TestClient(app) as client:
            assert client.get('/approved-plans').status_code == 200
            assert client.get(f'/approved-plans/{version}').status_code == 403
            assert client.get(f'/approved-plans/{version}/review').status_code == 403
            assert client.get(f'/teachers/{OTHER.teacher_id}/reports?version={version}').status_code == 403
            assert client.get(f'/teachers/{TEACHER.teacher_id}/assignments?version={version}').status_code == 200
            assert client.get(f'/teachers/{TEACHER.teacher_id}/reports?version={version}').json() == []
    finally:
        app.dependency_overrides.clear()
