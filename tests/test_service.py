"""DecisionService coverage — evaluate / get / approve / history."""

import pytest

from second_perspective.decision.integrity import verify_record
from second_perspective.models.enums import DecisionStatus
from second_perspective.models.schemas import ApprovalRequest
from second_perspective.repository import InMemoryDecisionRepository
from second_perspective.service import DecisionNotFoundError, DecisionService


def test_evaluate_seals_record_with_revision_one(make_request):
    service = DecisionService()
    record = service.evaluate(make_request())
    assert record.revision == 1
    assert record.parent_record_hash is None
    assert verify_record(record)
    assert record.record_hash
    assert record.result.decision_id == "DEC-TEST-0001"


def test_evaluate_increments_revision_on_same_decision(make_request):
    service = DecisionService()
    request = make_request()
    first = service.evaluate(request)
    second = service.evaluate(request)
    assert second.revision == 2
    assert second.parent_record_hash == first.record_hash
    assert verify_record(second)


def test_get_returns_latest_record(make_request):
    service = DecisionService()
    request = make_request()
    second = service.evaluate(request)
    service.evaluate(request)  # revision 3 latest
    got = service.get(request.decision_id)
    assert got.revision == second.revision + 1
    assert verify_record(got)


def test_get_unknown_raises():
    service = DecisionService()
    with pytest.raises(DecisionNotFoundError):
        service.get("DEC-UNKNOWN-XYZ")


def test_history_returns_chain_in_order(make_request):
    service = DecisionService()
    request = make_request()
    service.evaluate(request)
    service.evaluate(request)
    service.evaluate(request)
    history = service.history(request.decision_id)
    assert [r.revision for r in history] == [1, 2, 3]
    assert history[1].parent_record_hash == history[0].record_hash
    assert history[2].parent_record_hash == history[1].record_hash


def test_history_unknown_raises():
    service = DecisionService()
    with pytest.raises(DecisionNotFoundError):
        service.history("DEC-NOPE-0001")


def test_approve_records_approval_and_bumps_revision(make_request):
    service = DecisionService()
    request = make_request()
    record = service.evaluate(request)
    approved = service.approve(
        request.decision_id,
        ApprovalRequest(
            approved=True,
            approver="human-owner-1",
            authorization_ref="AUTH-REF-001",
        ),
    )
    assert approved.revision == record.revision + 1
    assert approved.parent_record_hash == record.record_hash
    assert approved.approval is not None
    assert approved.approval.approved is True
    assert approved.approval.approver == "human-owner-1"
    assert approved.result.status == DecisionStatus.APPROVED
    assert verify_record(approved)


def test_reject_status(make_request):
    service = DecisionService()
    request = make_request()
    service.evaluate(request)
    rejected = service.approve(
        request.decision_id,
        ApprovalRequest(
            approved=False,
            approver="human-owner-1",
            authorization_ref="AUTH-REF-002",
        ),
    )
    assert rejected.result.status == DecisionStatus.REJECTED
    assert rejected.approval.approved is False
    assert verify_record(rejected)


def test_approve_unknown_raises(make_request):
    service = DecisionService()
    with pytest.raises(DecisionNotFoundError):
        service.approve(
            "DEC-GHOST-000",
            ApprovalRequest(
                approved=True,
                approver="human-owner-1",
                authorization_ref="AUTH-REF-003",
            ),
        )


def test_approve_twice_raises(make_request):
    service = DecisionService()
    request = make_request()
    service.evaluate(request)
    approval = ApprovalRequest(
        approved=True,
        approver="human-owner-1",
        authorization_ref="AUTH-REF-004",
    )
    service.approve(request.decision_id, approval)
    with pytest.raises(ValueError):
        service.approve(request.decision_id, approval)


def test_custom_repository_is_used(make_request):
    repo = InMemoryDecisionRepository()
    service = DecisionService(repository=repo)
    record = service.evaluate(make_request())
    assert repo.get(record.result.decision_id) is not None
    assert record.record_hash == repo.get(record.result.decision_id).record_hash
