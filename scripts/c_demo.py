"""Synthetic notice, real Cognito, DynamoDB, Open-Meteo and bounded Sydney Bedrock calls.

Dedicated synthetic user passwords are reset privately, as in the B2 demonstration.
No credentials or pasted notice text are written to the verification record.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.pollution import utcnow
from scripts.b2_demo import demo_tokens


def run():
    tokens = demo_tokens()
    with TestClient(app) as client:
        def request(method, path, body=None, username="synthetic-admin", expected=200):
            response = client.request(method, path, headers={"Authorization": "Bearer " + tokens[username]}, json=body)
            if response.status_code != expected:
                raise RuntimeError(f"{method} {path}: expected {expected}, received {response.status_code}; response withheld")
            return response.json()

        previous = request("GET", "/inputs")
        fixture = request("GET", "/repair-fixture")
        fixture["restrictions"] = []
        before = request("POST", "/inputs", {"expected_revision": previous["revision"], "input": fixture})
        live = request("GET", "/evidence/forecast?mode=LIVE")
        assert live["freshness"] == "FRESH" and live["snapshot"]["mode"] == "LIVE"
        print("PASS actual live Open-Meteo regional forecast", flush=True)
        replay = request("GET", "/evidence/forecast?mode=REPLAY")
        assert replay["snapshot"]["id"] != live["snapshot"]["id"] and replay["freshness"] == "REPLAY"
        print("PASS separate labelled replay", flush=True)
        body = {"notice": "SYNTHETIC UNVERIFIED SCHOOL NOTICE: On 2026-10-12, restrict outdoor PE for section 6A in Monday period 2; use its explicitly approved indoor classroom alternative. Administrator review is required. This is not a legal closure or GRAP activation order.",
                "evidence_id": live["snapshot"]["id"], "mode": "LIVE", "policy_ids": ["ncdc-2025-school-5ii"]}
        analysis = request("POST", "/notice-analyses", body)
        assert analysis["status"] == "SUCCESS" and analysis["requires_review"]
        assert request("GET", "/inputs")["revision"] == before["revision"]
        assert request("POST", "/notice-analyses", body) == analysis
        print("PASS actual Sydney Nova Lite interpretation; cached repeat; no automatic confirmation", flush=True)
        proposals = [p["id"] for p in analysis["interpretation"]["proposed_restrictions"] if p["kind"] == "outdoor_prohibited" and p["activity_ids"] == ["6-a:Mon-2"]]
        assert proposals
        review = {"expected_revision": before["revision"], "proposal_ids": proposals, "calendar_date": "2026-10-12",
                  "period_ids": ["Mon-2"], "notice_reviewed": True, "ambiguities_reviewed": True}
        path = f"/notice-analyses/{analysis['id']}/confirm"
        request("POST", path, review, "synthetic-teacher-a", 403)
        confirmed = request("POST", path, review)
        assert confirmed["evidence_binding"]["mode"] == "LIVE"
        assert request("GET", "/current-plan")["needs_review"]
        draft = request("POST", "/draft-plans", confirmed["input"])
        assert draft["successful"] and draft["validation"]["valid"]
        request("POST", f"/draft-plans/{draft['id']}/approve", username="synthetic-teacher-a", expected=403)
        explanation = request("GET", f"/draft-plans/{draft['id']}/explanation")
        assert explanation["grounded"]
        approval = request("POST", f"/draft-plans/{draft['id']}/approve")
        assert request("GET", "/current-plan")["plan_version"] == approval["plan_version"]
        print("PASS authenticated administrator review, independent validation and separate approval", flush=True)
        record = {"checked_at": utcnow().isoformat(), "forecast": live,
                  "analysis": {k: analysis[k] for k in ("id", "status", "model", "region", "usage", "notice_status", "requires_review")},
                  "confirmation_revision": confirmed["revision"], "evidence_binding": confirmed["evidence_binding"],
                  "draft_id": draft["id"], "solver_status": draft["solver_status"], "counts": draft["counts"],
                  "differences": draft["differences"], "explanation": explanation, "approval_version": approval["plan_version"]}
        Path("work/c-verification.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(json.dumps({"model": analysis["model"], "region": analysis["region"], "usage": analysis["usage"],
                          "retrieved_at": live["snapshot"]["retrieved_at"], "solver_status": draft["solver_status"],
                          "counts": draft["counts"], "explanation_status": explanation["model_status"]}, indent=2), flush=True)


if __name__ == "__main__":
    run()
