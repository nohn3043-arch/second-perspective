from __future__ import annotations

import hmac

from ..models.enums import DecisionStatus
from ..models.schemas import ApprovalRecord, ApprovalRequest, DecisionRecord


class ApprovalError(ValueError):
    pass


def apply_approval(record: DecisionRecord, request: ApprovalRequest) -> DecisionRecord:
    if record.result.status != DecisionStatus.HUMAN_APPROVAL_REQUIRED:
        raise ApprovalError(
            f"Decision is not ready for approval; current status is {record.result.status}."
        )

    expected_owner = record.request.decision_owner.owner.casefold()
    if request.approver.casefold() != expected_owner:
        raise ApprovalError(
            "Approver does not match the anchored decision owner. "
            "Delegated authority must first be represented in the decision input."
        )

    expected_authorization = record.request.decision_owner.authorization_ref
    if not expected_authorization:
        raise ApprovalError(
            "The decision owner has no anchored authorization_ref; approval cannot be verified."
        )
    if not hmac.compare_digest(
        request.authorization_ref.encode("utf-8"),
        expected_authorization.encode("utf-8"),
    ):
        raise ApprovalError(
            "Approval authorization_ref does not match the authority anchored in the decision input."
        )

    approval = ApprovalRecord(**request.model_dump())
    new_status = DecisionStatus.APPROVED if request.approved else DecisionStatus.REJECTED
    result = record.result.model_copy(
        update={
            "status": new_status,
            "human_approval_required": False,
        }
    )
    return record.model_copy(update={"result": result, "approval": approval})
