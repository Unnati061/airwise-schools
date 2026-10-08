from copy import deepcopy
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from backend.app.durable_store import DynamoStore
from backend.app.evidence_contracts import AnalysisRequest, ReviewConfirmation
from backend.app.evidence_service import EvidenceService, DAILY_ALLOWANCE
from backend.app.pollution import freshness, parse_forecast, replay_forecast, utcnow
from backend.app.repair_fixture import synthetic_week
from backend.app.workflow import SCHOOL, Workflow
from backend.app.workflow_contracts import InputUpdate
from backend.app import notice_provider
from backend.tests.test_workflow import ADMIN, TEACHER, FakeDynamo, rejects

OUTPUT = {"affected_dates": [{"raw_text": "2026-10-12", "start": "2026-10-12", "end": "2026-10-12"}],
          "activities": ["6-a:Mon-2"], "proposed_restrictions": [{"id": "p1", "kind": "outdoor_prohibited",
          "activity_ids": ["6-a:Mon-2"], "citation_ids": ["ncdc-2025-school-5ii"]}],
          "citation_ids": ["ncdc-2025-school-5ii"], "ambiguities": []}


class Provider:
    def __init__(self, output=None, failure=False):
        self.output, self.failure, self.calls = deepcopy(output or OUTPUT), failure, 0

    def generate(self, system, supplied, max_tokens):
        self.calls += 1
        if self.failure:
            raise RuntimeError("Private notice content must not be logged")
        return deepcopy(self.output), {"inputTokens": 100, "outputTokens": 20, "totalTokens": 120}


@pytest.fixture
def service():
    workflow = Workflow(DynamoStore(FakeDynamo(), "test-table"))
    workflow.confirm(ADMIN, InputUpdate(expected_revision=None, input=synthetic_week()))
    return EvidenceService(workflow, Provider())


def request(service, notice="Synthetic review for 2026-10-12"):
    view = service.forecast(ADMIN, "REPLAY")
    return AnalysisRequest(notice=notice, evidence_id=view.snapshot.id, mode="REPLAY", policy_ids=["ncdc-2025-school-5ii"])


def review(result):
    return ReviewConfirmation(expected_revision=result.input_revision, proposal_ids=["p1"],
                              calendar_date=date(2026, 10, 12), period_ids=["Mon-2"],
                              notice_reviewed=True, ambiguities_reviewed=True)


def test_review_bound_to_versions_authentication_and_separate_approval(service):
    before = service.workflow.inputs(ADMIN)
    result = service.interpret(ADMIN, request(service))
    assert result.status == "SUCCESS" and result.requires_review and result.notice_status == "UNVERIFIED"
    assert service.workflow.inputs(ADMIN) == before
    rejects(403, lambda: service.confirm(TEACHER, result.id, review(result)))
    confirmed = service.confirm(ADMIN, result.id, review(result))
    assert confirmed.revision != before.revision
    assert confirmed.evidence_binding.analysis_id == result.id
    assert confirmed.evidence_binding.mode == "REPLAY"
    assert service.workflow.state(ADMIN)["current"] is None
    draft = service.workflow.draft(ADMIN, confirmed.input)
    assert draft.successful and draft.validation.valid
    rejects(409, lambda: service.confirm(ADMIN, result.id, review(result)))


def test_fabricated_citation_rejected_without_mutation(service):
    service.provider.output["proposed_restrictions"][0]["citation_ids"] = ["invented-order"]
    before = service.workflow.inputs(ADMIN)
    result = service.interpret(ADMIN, request(service))
    assert result.status == "INVALID_OUTPUT" and result.interpretation is None
    rejects(422, lambda: service.confirm(ADMIN, result.id, review(result)))
    assert service.workflow.inputs(ADMIN) == before


def test_ambiguous_date_requires_review_and_explicit_resolution(service):
    service.provider.output["affected_dates"] = [{"raw_text": "tomorrow", "start": None, "end": None}]
    result = service.interpret(ADMIN, request(service, "Avoid outdoor PE tomorrow until further notice"))
    assert result.requires_review
    assert any("Relative" in r for r in result.review_reasons)
    assert any("ambiguous" in r for r in result.review_reasons)
    assert service.workflow.inputs(ADMIN).revision == result.input_revision


def test_failure_cached_usage_logged_without_notice_and_restart(service):
    service.provider.failure = True
    body = request(service)
    result = service.interpret(ADMIN, body)
    assert result.status == "MODEL_FAILURE"
    fresh = EvidenceService(service.workflow, service.provider)
    assert fresh.interpret(ADMIN, body) == result and service.provider.calls == 1
    usage = service.store.query(SCHOOL, "MODEL_USAGE#")
    assert usage[0]["error"] == "RuntimeError"
    assert body.notice not in str(usage)
    rejects(422, lambda: service.confirm(ADMIN, result.id, review(result)))


def live_fixture():
    now = utcnow()
    raw = {"utc_offset_seconds": 0, "latitude": 28.4, "longitude": 77.6,
           "hourly_units": {"pm2_5": "\u03bcg/m\u00b3", "pm10": "\u03bcg/m\u00b3"},
           "hourly": {"time": [(now + timedelta(hours=1)).replace(tzinfo=None).isoformat()], "pm2_5": [50], "pm10": [70]}}
    return parse_forecast(raw, now, "a" * 64), raw


def test_live_cache_replay_separation_and_missing_stale(service):
    service.fetcher = live_fixture
    live = service.forecast(ADMIN, "LIVE")
    replay = service.forecast(ADMIN, "REPLAY")
    assert live.snapshot.id != replay.snapshot.id
    assert live.freshness == "FRESH" and replay.freshness == "REPLAY"
    assert not live.observations_available and live.snapshot.model_issue_time is None
    assert service.forecast(ADMIN, "LIVE").snapshot == live.snapshot
    wrong = request(service).model_copy(update={"evidence_id": live.snapshot.id})
    rejects(422, lambda: service.interpret(ADMIN, wrong))
    missing = wrong.model_copy(update={"evidence_id": "missing", "mode": "LIVE"})
    rejects(404, lambda: service.interpret(ADMIN, missing))
    snapshot = live.snapshot.model_copy(deep=True)
    snapshot.retrieved_at -= timedelta(hours=2)
    service.store.transact([service.store.put(SCHOOL, f"EVIDENCE#{snapshot.id}", snapshot.model_dump(mode="json"))])
    stale = wrong.model_copy(update={"mode": "LIVE"})
    rejects(409, lambda: service.interpret(ADMIN, stale))
    assert freshness(snapshot) == "STALE"
    snapshot.retrieved_at = utcnow()
    for point in snapshot.points:
        point.value = None
    assert freshness(snapshot) == "MISSING_VALUES"
    service.store.transact([service.store.put(SCHOOL, f"EVIDENCE#{snapshot.id}", snapshot.model_dump(mode="json"))])
    rejects(409, lambda: service.interpret(ADMIN, stale))


def test_failed_live_fetch_never_substitutes_replay(service):
    service.forecast(ADMIN, "REPLAY")
    def unavailable():
        raise OSError("offline")
    service.fetcher = unavailable
    rejects(503, lambda: service.forecast(ADMIN, "LIVE"))


def test_daily_allowance_atomic_pending_and_identical_cache(service):
    body = request(service)
    first = service.interpret(ADMIN, body)
    assert service.interpret(ADMIN, body) == first and service.provider.calls == 1
    for i in range(DAILY_ALLOWANCE - 1):
        service.interpret(ADMIN, body.model_copy(update={"notice": f"2026-10-12 synthetic notice {i}"}))
    rejects(429, lambda: service.interpret(ADMIN, body.model_copy(update={"notice": "one more"})))
    assert service.provider.calls == DAILY_ALLOWANCE


def test_unsupported_and_out_of_scope_activity_rejected(service):
    service.provider.output["proposed_restrictions"][0]["kind"] = "unsupported"
    result = service.interpret(ADMIN, request(service))
    rejects(422, lambda: service.confirm(ADMIN, result.id, review(result)))
    service.provider.output["activities"] = ["6-b:Tue-2"]
    result = service.interpret(ADMIN, request(service, "different synthetic notice 2026-10-12"))
    assert result.status == "INVALID_OUTPUT"


def test_explanation_uses_independently_recomputed_facts(service):
    draft = service.workflow.draft(ADMIN, service.workflow.inputs(ADMIN).input)
    service.provider.output = {"fact_ids": ["rooms", "invented-999"]}
    explanation = service.explanation(ADMIN, draft.id)
    assert explanation.model_status == "INVALID_OUTPUT"
    assert "999" not in explanation.text and "Room moves:" in explanation.text


def test_durable_pending_claim_coalesces_identical_requests(service):
    class PendingProvider(Provider):
        def generate(self, system, supplied, max_tokens):
            with pytest.raises(HTTPException) as error:
                service.interpret(ADMIN, body)
            assert error.value.status_code == 409
            return super().generate(system, supplied, max_tokens)
    service.provider = PendingProvider()
    body = request(service)
    assert service.interpret(ADMIN, body).status == "SUCCESS"
    assert service.provider.calls == 1


def test_confirmation_rejects_stale_evidence_and_wrong_calendar_scope(service):
    result = service.interpret(ADMIN, request(service))
    wrong = review(result).model_copy(update={"calendar_date": date(2026, 10, 13)})
    rejects(422, lambda: service.confirm(ADMIN, result.id, wrong))
    wrong = review(result).model_copy(update={"period_ids": ["Tue-2"]})
    rejects(422, lambda: service.confirm(ADMIN, result.id, wrong))
    view = service.get_evidence(ADMIN, result.evidence_id)
    snapshot = view.snapshot.model_copy(update={"mode": "LIVE", "retrieved_at": utcnow() - timedelta(hours=2)})
    service.store.transact([service.store.put(SCHOOL, f"EVIDENCE#{snapshot.id}", snapshot.model_dump(mode="json"))])
    rejects(409, lambda: service.confirm(ADMIN, result.id, review(result)))


def test_confirmation_rejects_missing_review_date_pollutant(service):
    result = service.interpret(ADMIN, request(service))
    snapshot = service.get_evidence(ADMIN, result.evidence_id).snapshot.model_copy(deep=True)
    for point in snapshot.points:
        if point.pollutant == "PM10":
            point.value = None
    service.store.transact([service.store.put(SCHOOL, f"EVIDENCE#{snapshot.id}", snapshot.model_dump(mode="json"))])
    rejects(422, lambda: service.confirm(ADMIN, result.id, review(result)))


def test_provider_bounds_and_truncated_or_non_json_output(monkeypatch):
    class Runtime:
        def converse(self, **kwargs):
            assert kwargs["modelId"] == "amazon.nova-lite-v1:0"
            assert kwargs["inferenceConfig"]["maxTokens"] <= 700
            return {"stopReason": "max_tokens", "usage": {"inputTokens": 10, "outputTokens": 700}}
    monkeypatch.setattr(notice_provider, "settings", lambda: {})
    monkeypatch.setattr(notice_provider, "runtime_client", lambda config, service: Runtime())
    provider = notice_provider.NovaProvider()
    assert provider.generate("fixed system", {"notice": "synthetic"})[0] is None
    with pytest.raises(ValueError):
        provider.generate("fixed system", {"notice": "x" * 14001})
    with pytest.raises(ValueError):
        notice_provider.parse_json('Here is JSON: {"ok":true}')
    assert notice_provider.parse_json('```json\n{"ok":true}\n```') == {"ok": True}


def test_evidence_routes_require_authentication():
    from fastapi.testclient import TestClient
    from backend.app import auth
    from backend.app.main import app
    app.dependency_overrides[auth.workflow] = lambda: Workflow(DynamoStore(FakeDynamo(), "test-table"))
    try:
        with TestClient(app) as client:
            assert client.get("/evidence/forecast").status_code == 401
            assert client.get("/policy-excerpts").status_code == 401
            assert client.post("/notice-analyses", json={}).status_code == 401
    finally:
        app.dependency_overrides.clear()
