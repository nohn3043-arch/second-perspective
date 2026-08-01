import json
from pathlib import Path

from fastapi.testclient import TestClient

from second_perspective.api.main import app


client = TestClient(app)


def load_example() -> dict:
    path = Path(__file__).parents[1] / "examples" / "market_entry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "0.3.0"

    missing_report = client.get("/v1/hub/reports/HUB-DOES-NOT-EXIST")
    assert missing_report.status_code == 404


def test_evaluate_and_fetch():
    response = client.post("/v1/decisions/evaluate", json=load_example())
    assert response.status_code == 200
    record = response.json()
    decision_id = record["result"]["decision_id"]

    fetched = client.get(f"/v1/decisions/{decision_id}")
    assert fetched.status_code == 200
    assert fetched.json()["result"]["decision_id"] == decision_id


def test_intelligent_decision_hub_endpoint():
    payload = {
        "decision": load_example(),
        "scenarios": [
            {
                "id": "SC_API",
                "name": "Partner assumption fails",
                "failed_assumption_ids": ["A1"],
            }
        ],
    }

    response = client.post("/v1/hub/analyze", json=payload)

    assert response.status_code == 200
    report = response.json()
    assert report["hub_version"] == "0.3.0"
    assert report["algorithm_audit_verified"] is True
    assert report["scenarios"][0]["leading_candidate_ids"] == ["S1"]

    fetched_report = client.get(f"/v1/hub/reports/{report['hub_run_id']}")
    assert fetched_report.status_code == 200
    assert fetched_report.json()["report_hash"] == report["report_hash"]

    decision_id = report["decision_record"]["result"]["decision_id"]
    fetched = client.get(f"/v1/decisions/{decision_id}")
    assert fetched.status_code == 200


def test_only_anchored_owner_can_approve():
    response = client.post("/v1/decisions/evaluate", json=load_example())
    record = response.json()
    decision_id = record["result"]["decision_id"]

    rejected = client.post(
        f"/v1/decisions/{decision_id}/approval",
        json={
            "approved": True,
            "approver": "Unrelated Person",
            "authorization_ref": "NONE"
        },
    )
    assert rejected.status_code == 409

    approved = client.post(
        f"/v1/decisions/{decision_id}/approval",
        json={
            "approved": True,
            "approver": "Board Strategy Committee",
            "authorization_ref": "GOV-2026-01"
        },
    )
    assert approved.status_code == 200
    assert approved.json()["result"]["status"] == "APPROVED"

    history = client.get(f"/v1/decisions/{decision_id}/history")
    assert history.status_code == 200
    assert [item["revision"] for item in history.json()] == [1, 2]
    assert history.json()[1]["parent_record_hash"] == history.json()[0]["record_hash"]


def test_production_authentication_fails_closed(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.delenv("SP_API_KEY", raising=False)

    response = client.post("/v1/decisions/evaluate", json=load_example())

    assert response.status_code == 503
    assert response.json()["detail"] == "SP_API_KEY or SP_OIDC_ISSUER must be configured in production."


def test_configured_api_key_is_required(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "test-secret")

    missing = client.post("/v1/decisions/evaluate", json=load_example())
    invalid = client.post(
        "/v1/decisions/evaluate",
        json=load_example(),
        headers={"Authorization": "Bearer wrong-secret"},
    )
    accepted = client.post(
        "/v1/decisions/evaluate",
        json=load_example(),
        headers={"Authorization": "Bearer test-secret"},
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert accepted.status_code == 200
