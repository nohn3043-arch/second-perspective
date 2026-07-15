from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status

from ..governance.approval import ApprovalError
from ..hub import HubReportNotFoundError, SuperDecisionHub
from ..models.hub import HubAnalysisRequest, HubReport
from ..models.schemas import (
    ApprovalRequest,
    DecisionRecord,
    DecisionRequest,
)
from ..service import DecisionNotFoundError, DecisionService
from ..version import VERSION
from .security import verify_api_key

app = FastAPI(
    title="Second Perspective Super Decision-Hub",
    version=VERSION,
    description=(
        "Auditable decision orchestration with deterministic evaluation, causal "
        "counterfactuals, scenario stress tests, cognitive risk challenges, and governance."
    ),
)

service = DecisionService()
hub = SuperDecisionHub(service=service)


@app.get("/health", operation_id="healthCheck")
def health_check() -> dict[str, str]:
    return {"status": "ok", "version": VERSION}


@app.post(
    "/v1/hub/analyze",
    response_model=HubReport,
    operation_id="analyzeDecisionHub",
    dependencies=[Depends(verify_api_key)],
)
def analyze_decision_hub(request: HubAnalysisRequest) -> HubReport:
    return hub.analyze(request)


@app.get(
    "/v1/hub/reports/{hub_run_id}",
    response_model=HubReport,
    operation_id="getDecisionHubReport",
    dependencies=[Depends(verify_api_key)],
)
def get_decision_hub_report(hub_run_id: str) -> HubReport:
    try:
        return hub.get_report(hub_run_id)
    except HubReportNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hub report not found.",
        ) from exc


@app.post(
    "/v1/decisions/evaluate",
    response_model=DecisionRecord,
    operation_id="evaluateDecision",
    dependencies=[Depends(verify_api_key)],
)
def evaluate_decision(request: DecisionRequest) -> DecisionRecord:
    return service.evaluate(request)


@app.get(
    "/v1/decisions/{decision_id}",
    response_model=DecisionRecord,
    operation_id="getDecision",
    dependencies=[Depends(verify_api_key)],
)
def get_decision(decision_id: str) -> DecisionRecord:
    try:
        return service.get(decision_id)
    except DecisionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found.",
        ) from exc


@app.get(
    "/v1/decisions/{decision_id}/history",
    response_model=list[DecisionRecord],
    operation_id="getDecisionHistory",
    dependencies=[Depends(verify_api_key)],
)
def get_decision_history(decision_id: str) -> list[DecisionRecord]:
    try:
        return service.history(decision_id)
    except DecisionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found.",
        ) from exc


@app.post(
    "/v1/decisions/{decision_id}/approval",
    response_model=DecisionRecord,
    operation_id="recordDecisionApproval",
    dependencies=[Depends(verify_api_key)],
)
def record_decision_approval(
    decision_id: str,
    approval: ApprovalRequest,
) -> DecisionRecord:
    try:
        return service.approve(decision_id, approval)
    except DecisionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found.",
        ) from exc
    except ApprovalError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
