<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>Super Decision-Hub · v0.3.0</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ About

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
Super Decision-Hub is an auditable orchestration layer built on the v0.2 deterministic Decision Foundation. It scored <strong>95/100</strong> in Singapore's IMDA AI Verify compliance assessment. The engine combines structured evaluation, fine-grained algorithm audit, causal counterfactual reselection, declared scenario stress tests, structural cognitive challenges, information priorities, and human governance in one report.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
It does not invent missing facts, weights, thresholds, owners, evidence, or probabilities. It produces leading candidates under declared inputs and always keeps final authority outside the algorithm.
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ What v0.3 adds

- hash-chained audit events for every major deterministic operation
- explicit operands and outputs for constraint and criterion calculations
- true candidate reselection after transitive assumption invalidation
- user-declared metric, evidence, and assumption-failure stress scenarios
- a deterministic cognitive-risk challenge layer that does not infer mental state
- a ranked information-acquisition and review queue
- one `SuperDecisionHub` orchestrator and one sealed `HubReport`
- full audit ledgers inside both baseline and scenario runs
- `POST /v1/hub/analyze` while preserving every v0.2 endpoint
- v0.3 package, CLI demonstration, generated OpenAPI, and CI coverage gates

The detailed architecture and boundaries are documented in
[`docs/SUPER_DECISION_HUB_V0_3.md`](docs/SUPER_DECISION_HUB_V0_3.md).
The v0.2 foundation design remains available in
[`docs/DECISION_FOUNDATION_V0_2.md`](docs/DECISION_FOUNDATION_V0_2.md).

## ✦ Architecture

```text
HubAnalysisRequest
  -> Decision Foundation
       -> structural/evidence audit
       -> hard + soft constraint evaluation
       -> normalized scoring
       -> causal invalidation
       -> counterfactual reselection
       -> Pareto + weight sensitivity
       -> hash-chained algorithm audit
  -> declared scenario stress runs
  -> structural cognitive-risk challenges
  -> information priority queue
  -> append-only DecisionRecord
  -> sealed HubReport
  -> human approval/rejection
```

## ✦ Install and test

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

## ✦ Run demonstrations

Core Decision Foundation:

```bash
second-perspective-demo
```

Super Decision-Hub with two stress scenarios:

```bash
super-decision-hub-demo
```

## ✦ Python usage

```python
from second_perspective import SuperDecisionHub
from second_perspective.models import HubAnalysisRequest

request = HubAnalysisRequest.model_validate(
    {
        "decision": decision_payload,
        "scenarios": [
            {
                "id": "SC1",
                "name": "Critical assumption fails",
                "failed_assumption_ids": ["A1"],
            },
            {
                "id": "SC2",
                "name": "Cost shock",
                "metric_overrides": {"S2": {"capital_required": 6000000}},
            },
        ],
    }
)
report = SuperDecisionHub().analyze(request)
```

The returned report contains the stored baseline decision record, scenario
results, cognitive findings, information priorities, algorithm-ledger
verification status, policy snapshot, and report hash.

## ✦ Run the API

Local development may run without a key:

```bash
export SP_ENV=development
uvicorn second_perspective.api.main:app --reload
```

Production fails closed unless a key is configured:

```bash
export SP_ENV=production
export SP_API_KEY="replace-with-a-strong-secret"
uvicorn second_perspective.api.main:app --host 0.0.0.0 --port 8000
```

Protected clients send `Authorization: Bearer &lt;SP_API_KEY&gt;`.

Endpoints:

- `POST /v1/hub/analyze`
- `GET /v1/hub/reports/{hub_run_id}`
- `POST /v1/decisions/evaluate`
- `GET /v1/decisions/{decision_id}`
- `GET /v1/decisions/{decision_id}/history`
- `POST /v1/decisions/{decision_id}/approval`
- `GET /health`

## ✦ Regenerate the Action/OpenAPI schema

```bash
SP_PUBLIC_BASE_URL=https://decision.example.com \
python scripts/export_openapi.py
```

## ✦ Compatibility

All v0.2 decision requests and endpoints remain valid. Responses add
`counterfactuals`, `algorithm_audit`, and `algorithm_audit_root_hash`. Clients
that strictly deserialize response fields should update their models.

## ✦ Production boundary

v0.3 is a functioning Super Decision-Hub application core, not yet a complete
multi-tenant enterprise control plane. The default repository is still
process-local memory. Production requires durable event storage, OIDC and
authorization enforcement, tenant isolation, KMS signatures, rate limiting,
observability, backups, migrations, and domain control packs.

The cognitive scanner challenges structural risks. It does not diagnose people,
read motives, or replace legal, medical, financial, or safety professionals.

---

<p align="center">
  <a href="https://github.com/NOHN-AI">GitHub</a> · <a href="https://www.nohnlins.com">Website</a> · <a href="mailto:ai@nohnlins.com">Contact</a>
</p>
