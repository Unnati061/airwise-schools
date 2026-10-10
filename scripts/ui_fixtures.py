"""Generate labelled offline browser-test fixtures; no AWS clients or credentials."""
import json
from datetime import date, datetime, timezone
from pathlib import Path

from backend.app.durable_store import DynamoStore
from backend.app.evidence_contracts import AnalysisResult, EvidenceBinding, NoticeInterpretation
from backend.app.policy_catalog import catalog
from backend.app.pollution import replay_forecast
from backend.app.repair_fixture import shared_resources_week, synthetic_week, room_resilience_week
from backend.app.workflow import Workflow
from backend.app.workflow_contracts import InputUpdate, ExecutionInput
from backend.tests.test_workflow import ADMIN, TEACHER, FakeDynamo


def run():
    workflow = Workflow(DynamoStore(FakeDynamo(), 'offline-browser-test-only'))
    snapshot, _ = replay_forecast()
    binding = EvidenceBinding(analysis_id='synthetic-browser-analysis', evidence_id=snapshot.id, mode='REPLAY', calendar_date=date(2026, 10, 12), reviewed_by=ADMIN.sub, reviewed_at=datetime.now(timezone.utc))
    first = workflow.confirm(ADMIN, InputUpdate(expected_revision=None, input=synthetic_week()))
    old_plan = workflow.draft(ADMIN, first.input)
    workflow.approve(ADMIN, old_plan.id)
    interpretation = NoticeInterpretation(affected_dates=[{'raw_text': 'tomorrow', 'start': None, 'end': None}], activities=['6-a:Mon-2'],
        proposed_restrictions=[{'id': 'p1', 'kind': 'outdoor_prohibited', 'activity_ids': ['6-a:Mon-2'], 'citation_ids': ['ncdc-2025-school-5ii']},
            {'id': 'unsupported', 'kind': 'unsupported', 'activity_ids': [], 'citation_ids': []}], citation_ids=['ncdc-2025-school-5ii'], ambiguities=['Relative date needs administrator review'])
    analysis = AnalysisResult(id=binding.analysis_id, mode='REPLAY', evidence_id=snapshot.id, input_revision=first.revision,
        notice_sha256='populated-in-offline-test', review_reasons=['SYNTHETIC OFFLINE BROWSER FIXTURE', 'Relative date needs administrator review'],
        status='SUCCESS', interpretation=interpretation, model='OFFLINE TEST DOUBLE: NO MODEL CALL', usage={}, created_at=datetime.now(timezone.utc), policy_ids=['ncdc-2025-school-5ii'])
    current = workflow.current(ADMIN)
    old_detail = workflow.approved_detail(ADMIN, old_plan.id)
    before_history = workflow.history(ADMIN)
    next_input = workflow.confirm(ADMIN, InputUpdate(expected_revision=first.revision, input=first.input), evidence_binding=binding)
    next_plan = workflow.draft(ADMIN, next_input.input)
    review_needed = workflow.current(ADMIN)
    next_approval = workflow.approve(ADMIN, next_plan.id)
    records = {'label': 'SYNTHETIC OFFLINE BROWSER FIXTURES ONLY', 'admin': ADMIN, 'teacher': TEACHER,
        'first': first, 'current': current, 'old_detail': old_detail, 'before_history': before_history,
        'next_input': next_input, 'next_plan': next_plan, 'review_needed': review_needed, 'next_approval': next_approval,
        'next_current': workflow.current(ADMIN), 'history': workflow.history(ADMIN), 'next_detail': workflow.approved_detail(ADMIN, next_plan.id),
        'review': workflow.execution_review(ADMIN, next_plan.id), 'audits': workflow.audits(ADMIN),
        'assignments': workflow.assignments(TEACHER, TEACHER.teacher_id), 'policies': catalog(), 'analysis': analysis,
        'evidence': {'snapshot': snapshot, 'freshness': 'REPLAY', 'checked_at': datetime.now(timezone.utc), 'observations_available': False,
                     'observation_limitation': 'SYNTHETIC OFFLINE TEST: no observation feed'}}
    shared_input = workflow.confirm(ADMIN, InputUpdate(expected_revision=next_input.revision, input=shared_resources_week()))
    shared_plan = workflow.draft(ADMIN, shared_input.input)
    records.update(shared_input=shared_input, shared_plan=shared_plan, shared_fixture=shared_resources_week())
    room_input = workflow.confirm(ADMIN, InputUpdate(expected_revision=shared_input.revision, input=room_resilience_week()))
    room_plan = workflow.draft(ADMIN, room_input.input)
    workflow.approve(ADMIN, room_plan.id)
    workflow.report(TEACHER, room_plan.id, '6-a:Mon-2', ExecutionInput(request_id='11111111-1111-4111-8111-111111111111', status='COULD_NOT_IMPLEMENT', note='Sample event: room unavailable at implementation.'))
    occupied = next(p.room_id for p in room_plan.placements if p.activity_id == '6-a:Mon-2')
    excluded = room_input.input.model_copy(deep=True)
    target = next(r for r in excluded.rooms if r.id == occupied)
    target.available_period_ids = [p for p in target.available_period_ids if not p.startswith('Mon-')]
    revised_input = workflow.confirm(ADMIN, InputUpdate(expected_revision=room_input.revision, input=excluded))
    revised_plan = workflow.draft(ADMIN, revised_input.input)
    records.update(room_input=room_input, room_plan=room_plan, room_fixture=room_resilience_week(),
                   room_detail=workflow.approved_detail(ADMIN, room_plan.id), room_history=workflow.history(ADMIN),
                   room_review=workflow.execution_review(ADMIN, room_plan.id),
                   room_current=workflow.current(ADMIN), excluded_room=occupied,
                   revised_input=revised_input, revised_plan=revised_plan)
    blocked_input = revised_input.input.model_copy(deep=True)
    next(r for r in blocked_input.rooms if r.id == 'movement-hall').available_period_ids = []
    blocked_input = workflow.confirm(ADMIN, InputUpdate(expected_revision=revised_input.revision, input=blocked_input))
    records.update(blocked_input=blocked_input, blocked_plan=workflow.draft(ADMIN, blocked_input.input))
    def encode(value):
        if hasattr(value, 'model_dump'):
            return value.model_dump(mode='json')
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        raise TypeError(type(value).__name__)
    Path('work/d1-ui-fixtures.json').write_text(json.dumps(records, default=encode, indent=2), encoding='utf-8')
    print('Generated labelled synthetic offline fixtures; no AWS or model requests')


if __name__ == '__main__':
    run()
