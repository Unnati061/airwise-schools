from copy import deepcopy
from uuid import uuid4

import pytest

from backend.app.message_preview import message_preview
from backend.app.outdoor_metrics import outdoor_metrics
from backend.app.workflow_contracts import ExecutionInput, InputUpdate
from backend.tests.test_workflow import ADMIN, TEACHER, OTHER, approved, rejects, service


def test_bilingual_preview_contains_only_approved_facts_and_requires_admin(service):
    version = approved(service).plan_version
    detail = service.approved_detail(ADMIN, version)
    preview = detail.message_preview
    assert preview.preview_only and preview.calendar_date is None
    assert 'Not specified' in preview.english and 'निर्दिष्ट नहीं' in preview.hindi
    assert version in preview.english and version in preview.hindi
    assert '6-a:Mon-2' in preview.english and '6-a:Mon-2' in preview.hindi
    assert 'room-6-a' in preview.english and 'room-6-a' in preview.hindi
    replay = message_preview(detail.plan, {'mode': 'REPLAY', 'calendar_date': '2026-10-12'}, True)
    assert '2026-10-12' in replay.english and '2026-10-12' in replay.hindi
    assert 'SYNTHETIC REPLAY' in replay.english and 'काल्पनिक रीप्ले' in replay.hindi
    assert replay.needs_review
    rejects(403, lambda: service.approved_detail(TEACHER, version))


def test_synthetic_metrics_acknowledgement_is_not_execution_and_reports_unique(service):
    version = approved(service).plan_version
    plan = service.approved_draft(ADMIN, version)
    a = next(a for a in plan.input_snapshot.activities if a.id == '6-a:Mon-2')
    size = next(s.size for s in plan.input_snapshot.sections if s.id == a.section_id)
    expected = round(size * 40 / 60, 6)
    service.ack(TEACHER, version)
    metrics = service.execution_review(ADMIN, version).outdoor_metrics
    assert metrics.original_restricted_outdoor_student_hours == expected
    assert metrics.approved_restricted_outdoor_student_hours == 0
    assert metrics.planned_indoor_substitution_student_hours == expected
    assert metrics.teacher_reported_completed_indoor_student_hours == 0
    assert metrics.unknown_indoor_execution_student_hours == expected
    body = ExecutionInput(request_id=uuid4(), status='COMPLETED')
    for _ in range(2):
        service.report(TEACHER, version, a.id, body)
    metrics = service.execution_review(ADMIN, version).outdoor_metrics
    assert metrics.teacher_reported_completed_indoor_student_hours == expected
    assert metrics.unknown_indoor_execution_student_hours == 0
    wrong_version = service.reports(ADMIN, version)[0].model_copy(update={'plan_version': 'old'})
    assert outdoor_metrics(plan, [wrong_version]).teacher_reported_completed_indoor_student_hours == 0


@pytest.mark.parametrize('status', ['COULD_NOT_IMPLEMENT', 'NEEDS_CLARIFICATION'])
def test_exceptions_not_reported_as_completed_indoor_hours(service, status):
    version = approved(service).plan_version
    service.report(TEACHER, version, '6-a:Mon-2', ExecutionInput(status=status))
    assert service.execution_review(ADMIN, version).outdoor_metrics.teacher_reported_completed_indoor_student_hours == 0


def test_old_duration_unknown_and_repeated_restriction_not_double_counted(service):
    version = approved(service).plan_version
    plan = service.approved_draft(ADMIN, version).model_copy(deep=True)
    before = outdoor_metrics(plan, [])
    plan.input_snapshot.restrictions.append(deepcopy(plan.input_snapshot.restrictions[0]))
    assert outdoor_metrics(plan, []) == before
    next(a for a in plan.input_snapshot.activities if a.id == '6-a:Mon-2').duration_minutes = None
    metrics = outdoor_metrics(plan, [])
    assert not metrics.available and metrics.missing_duration_activity_ids == ['6-a:Mon-2']
    assert metrics.original_restricted_outdoor_student_hours is None


def test_deferral_is_not_an_indoor_substitution(service):
    version = approved(service).plan_version
    plan = service.approved_draft(ADMIN, version).model_copy(deep=True)
    p = next(p for p in plan.placements if p.activity_id == '6-a:Mon-2')
    p.period_id = p.room_id = p.alternative_id = None
    p.deferred = True
    metrics = outdoor_metrics(plan, [])
    assert metrics.original_restricted_outdoor_student_hours > 0
    assert metrics.planned_indoor_substitution_student_hours == 0
