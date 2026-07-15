# Branch Manifest

Target branch: `intelligent-decision-engine`

Implemented release: Super Decision-Hub `0.3.0`

## v0.2 foundation retained

- strict structured decision inputs
- deterministic hard and soft constraints
- normalized weighted and constraint-only evaluation
- evidence quality, expiry, and responsibility anchors
- transitive causal assumption invalidation
- Pareto frontier and weight sensitivity
- human authorization gate
- append-only hash-chained decision revisions
- production fail-closed API-key behavior

## v0.3 Hub capabilities added

- hash-chained fine-grained algorithm audit events
- constraint operands, scoring normalization, penalty, and aggregation records
- counterfactual leader reselection after assumption failure
- metric, evidence-status, and assumption-failure scenario stress tests
- scenario-level algorithm ledgers and verification
- deterministic structural cognitive-risk scanner
- ranked information and review priorities
- versioned `HubPolicy`
- sealed, independently verifiable `HubReport`
- immutable in-memory Hub report retrieval interface
- `SuperDecisionHub` orchestration API and CLI
- `/v1/hub/analyze` OpenAPI contract
- expanded Hub, API, integrity, scenario, and validation tests

## New v0.3 core files

- `src/second_perspective/canonical.py`
- `src/second_perspective/audit/ledger.py`
- `src/second_perspective/audit/execution.py`
- `src/second_perspective/decision/selection.py`
- `src/second_perspective/decision/counterfactual.py`
- `src/second_perspective/hub/policy.py`
- `src/second_perspective/hub/cognitive.py`
- `src/second_perspective/hub/information.py`
- `src/second_perspective/hub/scenario.py`
- `src/second_perspective/hub/integrity.py`
- `src/second_perspective/hub/repository.py`
- `src/second_perspective/hub/orchestrator.py`
- `src/second_perspective/hub_cli.py`
- `src/second_perspective/models/hub.py`
- `tests/test_hub.py`
- `docs/SUPER_DECISION_HUB_V0_3.md`

## Explicitly deferred production and research components

- durable multi-tenant Hub/event database
- OIDC, delegated authority, RBAC/ABAC, and policy registry
- KMS/HSM signatures and trusted timestamps
- uncertainty distributions and seeded Monte Carlo analysis
- optimization over portfolios or alternative combinations
- external evidence connectors and provenance verification
- domain validation packs and historical benchmark datasets

These items are not claimed by v0.3.
