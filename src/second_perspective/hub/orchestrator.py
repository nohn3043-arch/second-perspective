from __future__ import annotations

from uuid import uuid4

from ..audit.ledger import verify_algorithm_audit
from ..models.hub import HubAnalysisRequest, HubReport
from ..service import DecisionService
from ..version import VERSION
from .cognitive import CognitiveRiskScanner
from .information import build_information_priorities
from .integrity import seal_hub_report
from .policy import HubPolicy
from .repository import HubReportRepository, InMemoryHubReportRepository
from .scenario import analyze_scenarios


class HubReportNotFoundError(LookupError):
    pass


class SuperDecisionHub:
    """Orchestrates evaluation, audit, challenge, scenarios, and governance records."""

    def __init__(
        self,
        service: DecisionService | None = None,
        policy: HubPolicy | None = None,
        repository: HubReportRepository | None = None,
    ) -> None:
        self.service = service or DecisionService()
        self.policy = policy or HubPolicy()
        self.repository = repository or InMemoryHubReportRepository()
        self.cognitive_scanner = CognitiveRiskScanner(self.policy)

    def analyze(self, request: HubAnalysisRequest) -> HubReport:
        record = self.service.evaluate(request.decision)
        result = record.result
        scenario_results = analyze_scenarios(
            engine=self.service.engine,
            request=record.request,
            baseline=result,
            scenarios=request.scenarios,
        )
        cognitive_report = (
            self.cognitive_scanner.scan(record.request, result)
            if request.run_cognitive_audit
            else None
        )
        report = HubReport(
            hub_run_id=f"HUB-{uuid4().hex[:12].upper()}",
            hub_version=VERSION,
            decision_record=record,
            scenarios=scenario_results,
            cognitive_audit=cognitive_report,
            information_priorities=build_information_priorities(record.request, result),
            hub_policy=self.policy.snapshot(),
            algorithm_audit_verified=verify_algorithm_audit(
                result.algorithm_audit,
                result.algorithm_audit_root_hash,
            ),
            generated_at=result.evaluation_as_of,
        )
        report = seal_hub_report(report)
        self.repository.put(report)
        return report

    def get_report(self, hub_run_id: str) -> HubReport:
        report = self.repository.get(hub_run_id)
        if report is None:
            raise HubReportNotFoundError(hub_run_id)
        return report
