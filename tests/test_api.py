"""FastAPI app + security coverage via TestClient."""

import os

import pytest
from fastapi.testclient import TestClient

from second_perspective.api.main import app
from second_perspective.api.security import assert_auth_configured, verify_api_key


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert "status" in body


def test_auth_me_dev_no_auth(client):
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["mode"] == "none"


def test_evaluate_decision_endpoint(client, make_request):
    payload = make_request(decision_id="DEC-API-EVAL-0001").model_dump(mode="json")
    resp = client.post("/v1/decisions/evaluate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["revision"] == 1
    assert body["record_hash"]
    decision_id = body["result"]["decision_id"]


def test_get_decision_endpoint(client, make_request):
    decision_id = "DEC-API-GET-0001"
    payload = make_request(decision_id=decision_id).model_dump(mode="json")
    created = client.post("/v1/decisions/evaluate", json=payload).json()
    assert created["result"]["decision_id"] == decision_id
    resp = client.get(f"/v1/decisions/{decision_id}")
    assert resp.status_code == 200
    assert resp.json()["result"]["decision_id"] == decision_id


def test_get_decision_not_found(client):
    resp = client.get("/v1/decisions/DEC-NOPE-0001")
    assert resp.status_code == 404


def test_history_endpoint(client, make_request):
    decision_id = "DEC-HIST-UNIQ-0001"
    payload = make_request(decision_id=decision_id).model_dump(mode="json")
    for _ in range(2):
        client.post("/v1/decisions/evaluate", json=payload)
    resp = client.get(f"/v1/decisions/{decision_id}/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_approval_endpoint(client, make_request):
    decision_id = "DEC-API-APPROVE-0001"
    payload = make_request(decision_id=decision_id).model_dump(mode="json")
    created = client.post("/v1/decisions/evaluate", json=payload).json()
    assert created["result"]["decision_id"] == decision_id
    resp = client.post(
        f"/v1/decisions/{decision_id}/approval",
        json={"approved": True, "approver": "human-1", "authorization_ref": "AUTH-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["approval"]["approved"] is True
    assert resp.json()["revision"] == 2


def test_approval_endpoint_conflict(client, make_request):
    decision_id = "DEC-API-APPROVE-CONFLICT-0001"
    payload = make_request(decision_id=decision_id).model_dump(mode="json")
    created = client.post("/v1/decisions/evaluate", json=payload).json()
    assert created["result"]["decision_id"] == decision_id
    body = {"approved": True, "approver": "human-1", "authorization_ref": "AUTH-1"}
    assert (
        client.post(f"/v1/decisions/{decision_id}/approval", json=body).status_code
        == 200
    )
    resp = client.post(f"/v1/decisions/{decision_id}/approval", json=body)
    assert resp.status_code in (409,)


def test_hub_analyze_endpoint(client, make_request):
    payload = {"decision": make_request().model_dump(mode="json"), "scenarios": []}
    resp = client.post("/v1/hub/analyze", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["hub_run_id"].startswith("HUB-")
    assert body["report_hash"]


def test_hub_report_get_endpoint(client, make_request):
    decision = make_request().model_dump(mode="json")
    created = client.post("/v1/hub/analyze", json={"decision": decision}).json()
    hub_run_id = created["hub_run_id"]
    resp = client.get(f"/v1/hub/reports/{hub_run_id}")
    assert resp.status_code == 200
    assert resp.json()["hub_run_id"] == hub_run_id


def test_hub_report_not_found(client):
    resp = client.get("/v1/hub/reports/HUB-MISSING-0001")
    assert resp.status_code == 404


def test_session_start_advance_human_endpoints(client, make_request):
    payload = {
        "decision": make_request().model_dump(mode="json"),
        "deviation_signals": [],
        "max_iterations": 2,
        "max_evidence_requests": 5,
    }
    created = client.post("/v1/hub/sessions", json=payload)
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    adv = client.post(f"/v1/hub/sessions/{session_id}/advance", json={"delta_vars": []})
    assert adv.status_code == 200
    assert len(adv.json()["rounds"]) == 1

    human = client.post(
        f"/v1/hub/sessions/{session_id}/human-decision",
        json={"approved": True, "evidence_status": {}},
    )
    assert human.status_code == 200
    assert human.json()["status"] == "sealed"

    got = client.get(f"/v1/hub/sessions/{session_id}")
    assert got.status_code == 200
    assert got.json()["status"] == "sealed"


def test_session_not_found(client, make_request):
    resp = client.post(
        "/v1/hub/sessions/SESS-NOPE-0001/advance",
        json={"delta_vars": []},
    )
    assert resp.status_code == 404


def test_verify_api_key_development_passes():
    os.environ["SP_ENV"] = "development"
    try:
        assert verify_api_key(None) is None
        assert verify_api_key("Bearer whatever") is None
        assert verify_api_key("Basic abc") is None
    finally:
        os.environ.pop("SP_ENV", None)


def test_verify_api_key_production_requires_header(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "secret-key-123")
    monkeypatch.delenv("SP_OIDC_ISSUER", raising=False)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        verify_api_key(None)
    assert exc.value.status_code == 401


def test_verify_api_key_production_wrong_token(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "secret-key-123")
    monkeypatch.delenv("SP_OIDC_ISSUER", raising=False)
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        verify_api_key("Bearer wrong-token")


def test_verify_api_key_production_valid_api_key(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "secret-key-123")
    monkeypatch.delenv("SP_OIDC_ISSUER", raising=False)
    assert verify_api_key("Bearer secret-key-123") is None


def test_verify_api_key_production_invalid_scheme(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "secret-key-123")
    monkeypatch.delenv("SP_OIDC_ISSUER", raising=False)
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        verify_api_key("Token abc")


def test_assert_auth_configured_development_passes(monkeypatch):
    monkeypatch.setenv("SP_ENV", "development")
    assert_auth_configured()  # must not raise


def test_assert_auth_configured_production_with_key(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.setenv("SP_API_KEY", "k")
    assert_auth_configured()


def test_assert_auth_configured_production_missing_key_raises(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.delenv("SP_API_KEY", raising=False)
    monkeypatch.delenv("SP_OIDC_ISSUER", raising=False)
    with pytest.raises(SystemExit):
        assert_auth_configured()


def test_assert_auth_configured_production_oidc_only(monkeypatch):
    monkeypatch.setenv("SP_ENV", "production")
    monkeypatch.delenv("SP_API_KEY", raising=False)
    monkeypatch.setenv("SP_OIDC_ISSUER", "https://issuer.example")
    assert_auth_configured()
