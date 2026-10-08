"""Real Cognito/DynamoDB local API checks. Synthetic demo passwords stay in memory."""
from concurrent.futures import ThreadPoolExecutor
import argparse
import json
import multiprocessing
import secrets
from uuid import uuid4

import boto3
import httpx
from fastapi.testclient import TestClient

from backend.app import auth
from backend.app.durable_store import DynamoPlanRepository
from backend.app.main import app
from backend.app.repair_contracts import DraftPlan
from scripts.aws_b2 import USERS, TAGS


def restarted_backend(token, draft_id, version, queue):
    """Fresh Windows-spawned interpreter: no repository/cache survives restart."""
    try:
        with TestClient(app) as client:
            header = {"Authorization": "Bearer " + token}
            assert client.get(f"/draft-plans/{draft_id}", headers=header).status_code == 200
            assert client.get("/current-plan", headers=header).json()["plan_version"] == version
        queue.put(True)
    except Exception:
        queue.put(False)


def demo_tokens():
    config = auth.settings()
    provisioner = boto3.Session(profile_name="airwise", region_name=auth.REGION).client("cognito-idp", config=auth.AWS_CONFIG)
    pool = provisioner.describe_user_pool(UserPoolId=config["pool_id"])["UserPool"]
    if pool.get("UserPoolTags") != TAGS:
        raise RuntimeError("Refusing to change passwords outside the dedicated synthetic B2 pool")
    tokens = {}
    for username, role, _ in USERS:
        password = "Aa1!" + secrets.token_urlsafe(32)
        provisioner.admin_set_user_password(UserPoolId=config["pool_id"], Username=username, Password=password, Permanent=True)
        tokens[username] = provisioner.initiate_auth(ClientId=config["client_id"], AuthFlow="USER_PASSWORD_AUTH",
                            AuthParameters={"USERNAME": username, "PASSWORD": password})["AuthenticationResult"]["AccessToken"]
        del password
    return tokens


def run():
    tokens = demo_tokens()
    with TestClient(app) as client:
        def request(method, path, username="synthetic-admin", status=200, body=None):
            response = client.request(method, path, headers={"Authorization": "Bearer " + tokens[username]}, json=body)
            if response.status_code != status:
                raise RuntimeError(f"{method} {path}: expected {status}, received {response.status_code}; response body withheld")
            return response.json()
        def passed(name):
            print(f"PASS {name}", flush=True)
        assert client.get("/inputs").status_code == 401
        passed("authentication required")
        fixture = request("GET", "/repair-fixture")
        state = client.get("/inputs", headers={"Authorization": "Bearer " + tokens["synthetic-admin"]})
        if state.status_code not in (200, 409):
            raise RuntimeError("Cannot inspect current input safely")
        revision = state.json()["revision"] if state.status_code == 200 else None
        confirmed = request("POST", "/inputs", body={"expected_revision": revision, "input": fixture})
        draft = request("POST", "/draft-plans", body=confirmed["input"])
        assert draft["successful"]
        passed("authenticated restriction confirmation and draft generation")
        request("POST", f"/draft-plans/{draft['id']}/approve", "synthetic-teacher-a", 403)
        passed("teacher approval denied")
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: request("POST", f"/draft-plans/{draft['id']}/approve"), range(2)))
        assert results[0] == results[1]
        version = results[0]["plan_version"]
        assert request("GET", "/current-plan")["plan_version"] == version
        events = request("GET", "/audit-events")
        assert sum(e["action"] == "PLAN_APPROVED" and e["plan_version"] == version for e in events) == 1
        passed("duplicate/concurrent approval has one version and audit event")
        # Start a separate process with real auth and fresh DynamoDB clients.
        context = multiprocessing.get_context("spawn")
        queue = context.Queue()
        child = context.Process(target=restarted_backend, args=(tokens["synthetic-admin"], draft["id"], version, queue))
        child.start()
        child.join(90)
        if child.is_alive():
            child.terminate()
            child.join()
            raise RuntimeError("Restart persistence check timed out")
        assert child.exitcode == 0 and queue.get(timeout=5)
        passed("persistence in a fresh backend process")
        request("GET", "/teachers/teacher-6-b/assignments", "synthetic-teacher-a", 403)
        request("GET", "/teachers/teacher-6-a/assignments", "synthetic-teacher-b", 403)
        passed("both teachers denied the other teacher's assignments")
        request("POST", f"/approved-plans/{version}/acknowledgements", "synthetic-teacher-a")
        assert request("GET", f"/approved-plans/{version}/reports") == []
        passed("acknowledgement without execution")
        report_path = f"/approved-plans/{version}/activities/6-a:Mon-2/report"
        body = {"status": "COULD_NOT_IMPLEMENT", "note": "Synthetic room access exception"}
        first = request("PUT", report_path, "synthetic-teacher-a", body=body)
        assert request("PUT", report_path, "synthetic-teacher-a", body=body) == first
        assert len(request("GET", f"/approved-plans/{version}/reports")) == 1
        passed("repeated execution reports retain one activity total")
        resolution = {"request_id": str(uuid4()), "note": "Synthetic administrator recorded room review"}
        request("POST", f"/approved-plans/{version}/activities/6-a:Mon-2/resolution", body=resolution)
        assert len(request("GET", f"/approved-plans/{version}/exceptions")["resolutions"]) == 1
        passed("administrator exception resolution")
        stale = request("POST", "/draft-plans", body=confirmed["input"])
        changed = json.loads(json.dumps(confirmed["input"]))
        changed["restrictions"][0]["period_ids"] = ["Mon-2"]
        confirmed = request("POST", "/inputs", body={"expected_revision": confirmed["revision"], "input": changed})
        current = request("GET", "/current-plan")
        assert current["needs_review"] and current["plan_version"] == version
        request("POST", f"/draft-plans/{stale['id']}/approve", status=409)
        passed("restriction revision marks review; stale draft rejected")
        new = request("POST", "/draft-plans", body=confirmed["input"])
        corrupted = DraftPlan.model_validate(new).model_copy(deep=True)
        corrupted.id = str(uuid4())
        corrupted.placements.pop()
        corrupted.diagnostic = "SYNTHETIC deliberately corrupted approval diagnostic"
        # Diagnostic injection is private test tooling, not a public mutation route.
        DynamoPlanRepository(auth.workflow().store, corrupted.input_snapshot.school_id).save(corrupted)
        request("POST", f"/draft-plans/{corrupted.id}/approve", status=422)
        passed("persisted corrupted plan rejected by independent revalidation")
        assert request("GET", "/current-plan")["plan_version"] == version
        approved = request("POST", f"/draft-plans/{new['id']}/approve")
        new_version = approved["plan_version"]
        assignments = request("GET", "/teachers/teacher-6-a/assignments", "synthetic-teacher-a")
        assert assignments["plan_version"] == new_version and not assignments["acknowledged"]
        request("POST", f"/draft-plans/{draft['id']}/approve")
        assert request("GET", "/current-plan")["plan_version"] == new_version
        passed("revision requires approval; old acknowledgement/duplicate approval cannot transfer or rewind")
        request("POST", f"/approved-plans/{new_version}/acknowledgements", "synthetic-teacher-a")
        completion = f"/approved-plans/{new_version}/activities/6-a:Mon-2/report"
        request("PUT", completion, "synthetic-teacher-a", body={"status": "COMPLETED", "note": "Synthetic indoor movement implemented"})
        request("PUT", completion, "synthetic-teacher-a", body={"status": "COMPLETED", "note": "Synthetic indoor movement implemented"})
        assert len(request("GET", f"/approved-plans/{new_version}/reports")) == 1
        passed("new-version execution completed once")
    print("Real Cognito JWT verification and DynamoDB persistence checks passed. Tokens/passwords were not printed or stored.")


def run_http():
    tokens = demo_tokens()
    with httpx.Client(base_url="http://127.0.0.1:8002", timeout=45) as client:
        def call(method, path, username="synthetic-admin", body=None, status=200):
            response = client.request(method, path, headers={"Authorization": "Bearer " + tokens[username]}, json=body)
            if response.status_code != status:
                raise RuntimeError(f"Loopback HTTP status {response.status_code}; response body withheld")
            return response.json()
        data = call("GET", "/inputs")["input"]
        draft = call("POST", "/draft-plans", body=data)
        approved = call("POST", f"/draft-plans/{draft['id']}/approve")
        version = approved["plan_version"]
        assigned = call("GET", "/teachers/teacher-6-a/assignments", "synthetic-teacher-a")
        assert assigned["plan_version"] == version and not assigned["acknowledged"]
        call("GET", "/teachers/teacher-6-b/assignments", "synthetic-teacher-b")
        call("GET", "/teachers/teacher-6-a/assignments", "synthetic-teacher-b", status=403)
        call("POST", f"/approved-plans/{version}/acknowledgements", "synthetic-teacher-a")
        body = {"status": "COMPLETED", "note": "Synthetic loopback HTTP execution"}
        path = f"/approved-plans/{version}/activities/6-a:Mon-2/report"
        call("PUT", path, "synthetic-teacher-a", body=body)
        call("PUT", path, "synthetic-teacher-a", body=body)
        reports = call("GET", f"/approved-plans/{version}/reports")
        assert len(reports) == 1 and reports[0]["status"] == "COMPLETED"
        record = auth.workflow().store.read(data["school_id"], f"APPROVED#{version}")
        assert "plan" in record and len(record["plan"]["placements"]) == 240
        print(f"PASS loopback HTTP administrator approval -> teacher acknowledgement -> COMPLETED once; frozen version {version}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http-smoke", action="store_true", help="Check the running loopback server instead of the full ASGI regression")
    args = parser.parse_args()
    try:
        run_http() if args.http_smoke else run()
    except Exception as error:
        print(f"B2 live check failed: {type(error).__name__}; no integration success claimed")
        raise SystemExit(1)
