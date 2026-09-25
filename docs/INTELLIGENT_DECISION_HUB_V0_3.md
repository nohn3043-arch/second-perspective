# Intelligent Decision-Hub v0.3: From Decision Foundation to Decision Hub

## Positioning

v0.2 solved "how to make a single decision computation verifiable, accountable, and replayable." v0.3 builds on that by adding hub orchestration: a single request completes the baseline decision, algorithm-process audit, counterfactual analysis, user-declared stress scenarios, structured cognitive challenge, information-prioritization ranking, and governance records in one pass.

v0.3 can therefore formally be called the **Intelligent Decision-Hub application core**, but it cannot yet claim to be a full enterprise-grade multi-tenant control plane.

## Relationship to v0.2

v0.3 does not replace `IntelligentDecisionEngine`; it adds `IntelligentDecisionHub` on top:

```text
IntelligentDecisionHub
├── DecisionService
│   ├── IntelligentDecisionEngine
│   ├── StructuralAuditor
│   ├── Counterfactual Analyzer
│   ├── Robustness Analyzer
│   └── Append-only DecisionRepository
├── Scenario Analyzer
├── CognitiveRiskScanner
├── Information Priority Builder
├── HubReport Integrity Sealer
└── Immutable HubReport Repository Interface
```

The existing `/v1/decisions/*` endpoints remain available; the new `/v1/hub/analyze` endpoint provides a unified hub report.
Sealed reports can be retrieved via `/v1/hub/reports/{hub_run_id}`; the default implementation remains the in-process development repository.

## 1. Fine-Grained Algorithm Audit

`DecisionResult.algorithm_audit` is no longer just a four-stage summary. A single baseline run generates independent events covering:

1. Request contract and the effective evaluation timestamp;
2. The status, timeliness, and quality dimensions of each piece of evidence, plus the responsibility node;
3. Each assumption's dependencies, evidence, and responsibility node;
4. Every structural audit finding;
5. Every constraint comparison for each alternative;
6. The range, rule, weight, normalized score, and weighted score of every metric;
7. Base score, soft penalty, total score, and alternative status aggregation;
8. Assumption-failure transitive closure;
9. Counterfactual candidate re-selection;
10. Pareto frontier and every weight perturbation;
11. Leading-candidate selection and the final governance status.

Every `AlgorithmAuditEvent` carries a sequence number, rule, operation, inputs, outputs, references, the previous event hash, and the current event hash. `algorithm_audit_root_hash` is the root digest of the entire execution chain. Any change to event content or ordering causes verification to fail.

This mechanism audits algorithm executions that successfully enter the engine. Illegal requests rejected before HTTP parsing must still be logged by the production gateway or event ingestion layer — that is the responsibility of the v0.4 control plane.

## 2. True Assumption Counterfactual Re-Selection

v0.2 could already report which alternatives would be affected if an assumption failed. v0.3 goes further and actually executes:

```text
Trigger assumption failure
-> Compute transitive failed-assumption set
-> Remove alternatives dependent on those assumptions
-> Re-select the leader among remaining viable alternatives
-> Recompute the Pareto frontier of the remaining set
-> Mark leader_stable / leader_changed / no_viable_alternative
```

This remains a structural counterfactual; it never fabricates failure probabilities.

## 3. Declarative Stress Scenarios

Callers can explicitly declare in `HubAnalysisRequest.scenarios`:

- A change in an existing metric of an alternative;
- Certain evidence becoming `missing` or `disputed`;
- Certain assumptions failing.

Each scenario re-runs the deterministic engine, applies assumption-failure removal and candidate re-selection, and returns:

- Scenario result status;
- Failed assumptions and removed alternatives;
- Viable alternatives and the new leader;
- Alternative scores, audit findings, and scenario fingerprint;
- Full scenario algorithm audit chain and verification result.

The system does not accept silent overrides of non-existent alternatives, metrics, evidence, or assumptions.

## 4. Second-Perspective Cognitive Risk Scan

`CognitiveRiskScanner` is a deterministic challenge rule set; it does not infer human mental states. It currently checks:

- Excessive concentration of weight on a single criterion;
- The final decision-maker controlling most weights and constraints simultaneously;
- The current leader depending on key assumptions that would swing the result;
- Excessive concentration of critical evidence sources or custody;
- Fragility of ranking under small weight perturbations;
- Too-narrow viable alternative set;
- Soft-constraint penalties reversing the base ranking.

Every finding must include a rule ID, severity, explanation, evidence references, and a challenge question answerable by a responsible party. These findings do not directly alter alternative scores and do not bypass the approval gate.

## 5. Information Prioritization

The hub ranks information using lexicographic ordering based on structural facts; it never fabricates "information value probabilities":

```text
blocking
> leader_exposed
> structural
> review
```

Within the same tier, variables affecting the current leader and more alternatives are processed first. The output indicates the variable reference, impact scope, ranking reason, and recommended action.

## 6. Integrity and Governance

v0.3 preserves three layers of integrity:

1. The event hash chain of a single algorithm execution;
2. The `DecisionRecord` parent-hash chain across multiple evaluations/approvals of the same decision;
3. The `HubReport.report_hash` that aggregates the baseline decision, scenarios, cognitive findings, and information queue.

Hashes can detect content modification, but without external signatures, trusted timestamps, and independent storage, they cannot prove that an entire database was not rewritten wholesale. Production deployments must integrate KMS/HSM and an immutable event store.

## 7. Core Request Structure

```json
{
  "decision": {
    "objective": "...",
    "decision_owner": {},
    "criteria": [],
    "constraints": [],
    "assumptions": [],
    "alternatives": [],
    "evidence": []
  },
  "scenarios": [
    {
      "id": "SC1",
      "name": "Critical assumption failure",
      "failed_assumption_ids": ["A1"]
    },
    {
      "id": "SC2",
      "name": "Cost shock",
      "metric_overrides": {
        "S2": {"capital_required": 6000000}
      }
    }
  ],
  "run_cognitive_audit": true
}
```

## 8. v0.4 Recommended Roadmap

### Production Control Plane

- PostgreSQL event repository, HubReport history, and optimistic concurrency control;
- OIDC, service identities, responsibility-delegation chains, RBAC/ABAC, and tenant isolation;
- Policy registry, signing, canary release, rollback, and historical replay;
- Request idempotency, rate limiting, asynchronous scenario tasks, metrics, logs, tracing, and alerts;
- KMS/HSM signing and trusted timestamps.

### Advanced Decision Analysis

- Metric intervals and probability distributions;
- Fixed-seed Monte Carlo;
- Multi-strategy comparison (TOPSIS, ELECTRE, etc.) showing divergence;
- Value of Information after explicit cost and probability inputs;
- Portfolio alternatives and resource-constrained optimization;
- Historical decision benchmark sets, outcome replay, and policy drift detection.

## 9. Explicit Boundaries

- The Hub never auto-approves a decision;
- The cognitive scan does not diagnose individual psychology;
- Scenarios only use changes explicitly declared by the user;
- There is currently no probabilistic inference, Monte Carlo, or machine-learning prediction;
- The current in-memory repository is unsuitable for multi-instance production;
- Medical, legal, financial, and security decisions remain the responsibility of the corresponding professional responsible parties.
