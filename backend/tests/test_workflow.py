from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock
from types import SimpleNamespace
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.testclient import TestClient
import jwt
import pytest

from backend.app import auth
from backend.app.durable_store import DynamoStore
from backend.app.main import app
from backend.app.workflow import SCHOOL, Workflow
from backend.app.workflow_contracts import Actor, ExecutionInput, InputUpdate, ResolutionInput
from backend.app.repair_fixture import synthetic_week

ADMIN = Actor(sub="synthetic-admin-sub", school_id=SCHOOL, role="administrator")
TEACHER = Actor(sub="synthetic-teacher-a-sub", school_id=SCHOOL, role="teacher", teacher_id="teacher-6-a")
OTHER = Actor(sub="synthetic-teacher-b-sub", school_id=SCHOOL, role="teacher", teacher_id="teacher-6-b")


class FakeDynamo:
    """Test-only transactional data double, never selected by application config."""
    def __init__(self):
        self.items = {}
        self.lock = Lock()

    def key(self, item):
        return item["pk"]["S"], item["sk"]["S"]

    def get_item(self, **args):
        assert args["ConsistentRead"]
        with self.lock:
            item = self.items.get(self.key(args["Key"]))
            return {"Item": deepcopy(item)} if item else {}

    def query(self, **args):
        pk, prefix = (args["ExpressionAttributeValues"][k]["S"] for k in (":pk", ":prefix"))
        with self.lock:
            return {"Items": [deepcopy(value) for key, value in sorted(self.items.items()) if key[0] == pk and key[1].startswith(prefix)]}

    def transact_write_items(self, **args):
        with self.lock:
            for action in args["TransactItems"]:
                put = action["Put"]
                old = self.items.get(self.key(put["Item"]))
                condition = put.get("ConditionExpression")
                failed = (condition == "attribute_not_exists(pk)" and old is not None)
                failed |= (condition == "etag = :expected" and (not old or old.get("etag") != put["ExpressionAttributeValues"][":expected"]))
                if failed:
                    raise ClientError({"Error": {"Code": "TransactionCanceledException", "Message": "conditional conflict"}}, "TransactWriteItems")
            for action in args["TransactItems"]:
                put = action["Put"]
                self.items[self.key(put["Item"])] = deepcopy(put["Item"])


@pytest.fixture
def service():
    return Workflow(DynamoStore(FakeDynamo(), "test-table"))


def confirmed_draft(service):
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=None, input=synthetic_week()))
    return service.draft(ADMIN, confirmed.input)


def approved(service):
    plan = confirmed_draft(service)
    return service.approve(ADMIN, plan.id)


def rejects(code, action):
    with pytest.raises(HTTPException) as error:
        action()
    assert error.value.status_code == code


def test_authenticated_confirmation_and_scope(service):
    rejects(403, lambda: service.confirm(TEACHER, InputUpdate(expected_revision=None, input=synthetic_week())))
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=None, input=synthetic_week()))
    assert confirmed.input.restrictions[0].confirmed_by == ADMIN.sub
    assert confirmed.input.versions.timetable == confirmed.revision
    outsider = ADMIN.model_copy(update={"school_id": "another-school"})
    rejects(403, lambda: service.inputs(outsider))
    assert service.store.query(SCHOOL, "RESTRICTIONS#")


def test_persistence_with_new_repository_instance(service):
    plan = confirmed_draft(service)
    fresh = Workflow(DynamoStore(service.store.client, "test-table"))
    assert fresh.get_draft(ADMIN, plan.id) == plan
    assert fresh.inputs(ADMIN).input == plan.input_snapshot


def test_teacher_cannot_approve_or_access_other_assignments(service):
    plan = confirmed_draft(service)
    rejects(403, lambda: service.approve(TEACHER, plan.id))
    service.approve(ADMIN, plan.id)
    rejects(403, lambda: service.assignments(TEACHER, OTHER.teacher_id))
    rejects(403, lambda: service.report(TEACHER, plan.id, "6-b:Mon-2", ExecutionInput(status="COMPLETED")))
    assert all(a.activity_id.startswith("6-a:") for a in service.assignments(TEACHER, TEACHER.teacher_id).assignments)


def test_stale_and_invalid_draft_rejected(service):
    plan = confirmed_draft(service)
    revision = service.inputs(ADMIN)
    service.confirm(ADMIN, InputUpdate(expected_revision=revision.revision, input=revision.input))
    rejects(409, lambda: service.approve(ADMIN, plan.id))
    data = service.inputs(ADMIN).input
    invalid = service.draft(ADMIN, data)
    invalid.placements.pop()
    service.store.transact([service.store.put(SCHOOL, f"DRAFT#{invalid.id}", invalid.model_dump(mode="json"))])
    rejects(422, lambda: service.approve(ADMIN, invalid.id))
    assert service.current(ADMIN).plan_version is None


def test_duplicate_concurrent_approval_is_one_atomic_version(service):
    plan = confirmed_draft(service)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.approve(ADMIN, plan.id), range(2)))
    assert results[0] == results[1]
    assert service.current(ADMIN).plan_version == plan.id
    assert len(service.store.query(SCHOOL, "APPROVED#")) == 1
    assert len([e for e in service.audits(ADMIN) if e.action == "PLAN_APPROVED"]) == 1


def test_approved_snapshot_does_not_follow_a_changed_draft(service):
    version = approved(service).plan_version
    draft = service.get_draft(ADMIN, version)
    draft.placements.clear()
    service.store.transact([service.store.put(SCHOOL, f"DRAFT#{version}", draft.model_dump(mode="json"))])
    assert len(service.assignments(TEACHER, TEACHER.teacher_id).assignments) == 40


def test_revision_needs_approval_and_ack_does_not_transfer(service):
    first = approved(service)
    service.ack(TEACHER, first.plan_version)
    assert service.assignments(TEACHER, TEACHER.teacher_id).acknowledged
    assert service.reports(ADMIN, first.plan_version) == []
    previous = service.inputs(ADMIN)
    updated = previous.input.model_copy(deep=True)
    updated.rooms[0].available_period_ids.remove("Mon-2")
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=previous.revision, input=updated))
    assert service.current(ADMIN).needs_review
    assert service.current(ADMIN).plan_version == first.plan_version
    # Restore room availability through another authenticated input revision.
    restored = previous.input.model_copy(deep=True)
    confirmed = service.confirm(ADMIN, InputUpdate(expected_revision=confirmed.revision, input=restored))
    new = service.draft(ADMIN, confirmed.input)
    assert service.current(ADMIN).plan_version == first.plan_version
    service.approve(ADMIN, new.id)
    assert not service.current(ADMIN).needs_review
    assert not service.assignments(TEACHER, TEACHER.teacher_id).acknowledged
    service.approve(ADMIN, first.draft_id)
    assert service.current(ADMIN).plan_version == new.id
    rejects(409, lambda: service.ack(TEACHER, first.plan_version))


def test_repeated_reports_one_total_and_resolution_audit(service):
    version = approved(service).plan_version
    body = ExecutionInput(status="COULD_NOT_IMPLEMENT", note="Synthetic room access issue")
    first = service.report(TEACHER, version, "6-a:Mon-2", body)
    assert service.report(TEACHER, version, "6-a:Mon-2", body) == first
    assert len(service.reports(ADMIN, version)) == 1
    assert not service.assignments(TEACHER, TEACHER.teacher_id).acknowledged
    resolution = ResolutionInput(request_id=uuid4(), note="Synthetic administrator will review room access")
    result = service.resolve(ADMIN, version, "6-a:Mon-2", resolution)
    assert service.resolve(ADMIN, version, "6-a:Mon-2", resolution) == result
    assert len(service.exceptions(ADMIN, version).resolutions) == 1
    service.report(TEACHER, version, "6-a:Mon-2", ExecutionInput(status="COMPLETED"))
    assert len(service.reports(ADMIN, version)) == 1
    assert service.exceptions(ADMIN, version).reports == []
    audit = service.audits(ADMIN)
    assert len([e for e in audit if e.action == "EXECUTION_COULD_NOT_IMPLEMENT"]) == 1
    assert all(e.actor and e.timestamp for e in audit)


def test_auth_missing_and_forged_token_are_denied(service):
    app.dependency_overrides[auth.workflow] = lambda: service
    try:
        client = TestClient(app)
        assert client.get("/inputs").status_code == 401
        assert client.get("/inputs", headers={"Authorization": "Bearer invalid"}).status_code in (401, 503)
    finally:
        app.dependency_overrides.clear()


def test_jwt_signature_issuer_client_use_and_expiry(monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import rsa
    import time
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    config = {"pool_id": "ap-southeast-2_test", "client_id": "test-client"}
    monkeypatch.setattr(auth, "settings", lambda: config)
    monkeypatch.setattr(auth, "key_client", lambda: SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())))
    claims = dict(iss="https://cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_test", sub="synthetic-sub",
                  exp=int(time.time()) + 60, iat=int(time.time()), token_use="access", client_id="test-client")
    token = jwt.encode(claims, key, algorithm="RS256")
    assert auth.verify_token(token)["sub"] == "synthetic-sub"
    for change in ({"iss": "https://untrusted"}, {"client_id": "other"}, {"token_use": "id"}, {"exp": 1}):
        bad = jwt.encode({**claims, **change}, key, algorithm="RS256")
        rejects(401, lambda: auth.verify_token(bad))
    forged = jwt.encode(claims, "untrusted-test-key-at-least-32-bytes", algorithm="HS256")
    rejects(401, lambda: auth.verify_token(forged))
