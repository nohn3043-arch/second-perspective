"""Structural auditor coverage."""

from second_perspective.audit.auditor import StructuralAuditor
from second_perspective.models.enums import IssueSeverity


def _audit(request):
    policy = None
    return StructuralAuditor().audit(request, policy, request.evaluation_as_of)


def test_happy_path_no_blocking(make_request):
    issues, responsibility_map, unresolved = _audit(make_request())
    blocking = [i for i in issues if i.blocking]
    assert blocking == []
    codes = {issue.code for issue in issues}
    # default request references E1 on alternatives, so no "no evidence" issue
    assert "ALTERNATIVE_NO_ASSUMPTIONS" not in codes
    # every declared element appears in the responsibility map
    element_ids = {entry.element_id for entry in responsibility_map}
    assert {"A1", "K1", "C1", "E1"} <= element_ids
    assert {"decision"} <= {entry.element_type for entry in responsibility_map}


def test_critical_assumption_without_owner_blocking(make_request, make_assumption):
    request = make_request(
        assumptions=[
            make_assumption(
                "A1",
                evidence_ids=["E1"],
                no_responsibility=True,
            )
        ],
    )
    issues, _, unresolved = _audit(request)
    blocking = [i for i in issues if i.blocking]
    assert len(blocking) == 1
    assert blocking[0].code == "CRITICAL_ASSUMPTION_NO_OWNER"
    assert blocking[0].severity == IssueSeverity.ERROR
    assert f"assumptions.A1.responsibility" in unresolved


def test_alternative_without_assumptions_warns(make_request, make_alternative):
    request = make_request(
        alternatives=[
            make_alternative(
                "S1", metrics={"metric_K1": 80, "budget": 800}, evidence_ids=["E1"]
            ),
        ],
    )
    issues, _, unresolved = _audit(request)
    codes = {issue.code for issue in issues}
    assert "ALTERNATIVE_NO_ASSUMPTIONS" in codes
    assert "alternatives.S1.required_assumptions" in unresolved


def test_alternative_without_evidence_infos(make_request, make_alternative):
    request = make_request(
        alternatives=[
            make_alternative(
                "S1",
                metrics={"metric_K1": 80, "budget": 800},
                required_assumptions=["A1"],
            ),
        ],
    )
    issues, _, _ = _audit(request)
    info = [i for i in issues if i.code == "ALTERNATIVE_NO_EVIDENCE"]
    assert len(info) == 1
    assert info[0].severity == IssueSeverity.INFO
    assert info[0].blocking is False
