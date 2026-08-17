<p align="center">
  <img src="assets/banner.png" alt="NOMOS banner" style="width:100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-D4AF37?style=flat-square" alt="python">
  <img src="https://img.shields.io/badge/hub-v0.3.0-D4AF37?style=flat-square" alt="hub-v0.3.0">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
</p>

<blockquote align="center">
  <em>NOMOS · v0.3.0 — Auditable Decision Hub</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ About

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS is an auditable orchestration layer built on the deterministic Decision Foundation. It scored <strong>95/100</strong> in Singapore's IMDA AI Verify compliance assessment. The engine combines structured evaluation, fine-grained algorithm audit, causal counterfactual reselection, declared scenario stress tests, structural cognitive challenges, information priorities, and human governance in one report.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
It does not invent missing facts, weights, thresholds, owners, evidence, or probabilities. It produces leading candidates under declared inputs and always keeps final authority outside the algorithm.
</p>

<p align="center">
  <img src="assets/overview.png" alt="NOMOS overview" style="width:100%">
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ Built-in Universal Audit Engine

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
NOMOS ships with a <strong>built-in universal audit engine</strong> — not a bolt-on patch. Audit tracing lives inside the deterministic core, so every decision, assumption, constraint, and causal step is recorded, hash-chained, and independently verifiable by design rather than grafted on afterward.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
In Singapore's <strong>IMDA AI Verify</strong> causal-audit assessment the engine scored <strong>95/100</strong>. The full compliance report is included in this repository as <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>.
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
- one `IntelligentDecisionHub` orchestrator and one sealed `HubReport`
- full audit ledgers inside both baseline and scenario runs
- `POST /v1/hub/analyze` while preserving every v0.2 endpoint
- v0.3 package, CLI demonstrations, generated OpenAPI, and CI coverage gates

The detailed architecture and boundaries are documented in
[`docs/INTELLIGENT_DECISION_HUB_V0_3.md`](docs/INTELLIGENT_DECISION_HUB_V0_3.md).
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
nomos-demo
```

NOMOS with two stress scenarios (Intelligent Decision Hub):

```bash
nomos-hub-demo
```

## ✦ Python usage

```python
from second_perspective import IntelligentDecisionHub
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
report = IntelligentDecisionHub().analyze(request)
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

Protected clients send `Authorization: Bearer <SP_API_KEY>`.

Endpoints:

- `GET /health`
- `GET /v1/auth/me`
- `POST /v1/hub/analyze`
- `GET /v1/hub/reports/{hub_run_id}`
- `POST /v1/decisions/evaluate`
- `GET /v1/decisions/{decision_id}`
- `GET /v1/decisions/{decision_id}/history`
- `POST /v1/decisions/{decision_id}/approval`

Optional PostgreSQL persistence is enabled by setting `SP_DATABASE_DSN`
(`asyncpg`); OIDC-aware identity is available via `SP_OIDC_ISSUER`.

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

v0.3 is a functioning NOMOS application core, not yet a complete
multi-tenant enterprise control plane. The default repository is still
process-local memory. Production requires durable event storage, OIDC and
authorization enforcement, tenant isolation, KMS signatures, rate limiting,
observability, backups, migrations, and domain control packs.

The cognitive scanner challenges structural risks. It does not diagnose people,
read motives, or replace legal, medical, financial, or safety professionals.

## ✦ Project Structure

```
nomos/
├── pyproject.toml              # package: nomos-decision-engine v0.3.0
├── src/second_perspective/
│   ├── cli.py / hub_cli.py     # demo entry points (nomos-demo / nomos-hub-demo)
│   ├── service.py / repository.py / canonical.py / version.py
│   ├── api/                    # FastAPI: main.py, security.py
│   ├── audit/                  # auditor, execution, graph, ledger
│   ├── decision/               # causal, counterfactual, engine, evaluator,
│   │                           #   integrity, policy, robustness, selection
│   ├── governance/             # approval
│   ├── hub/                    # orchestrator, cognitive, information, integrity,
│   │                           #   policy, repository, scenario
│   ├── models/                 # enums, hub, schemas
│   └── persistence/            # asyncpg PostgreSQL repositories (SP_DATABASE_DSN)
├── docs/                       # DECISION_FOUNDATION_V0_2.md, INTELLIGENT_DECISION_HUB_V0_3.md
├── examples/market_entry.json  # sample decision request
├── scripts/export_openapi.py
├── tests/                      # test_api / test_engine / test_foundation / test_hub
├── Dockerfile · docker-compose.yml · openapi-action.yaml
├── requirements-engine.txt · requirements-engine-dev.txt
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
└── assets/                     # banner.svg/png, overview.svg/png
```

<p align="center">— ✦ —</p>

## ✦ Ecosystem

NOMOS is one member of the NOHN AI ecosystem — a family of projects built around second-perspective causal audit and deterministic execution:

| Project | Repository | What it is |
|---|---|---|
| **Second-Perspective (GCAE)** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) | Global cognitive audit engine — the five-operator causal audit core (IMDA 95/100) |
| **NOMOS** | [nohn3043-arch/second-perspective](https://github.com/nohn3043-arch/second-perspective) (`Intelligent-Decision-Hub--Nomos` branch) | Auditable deterministic decision hub (IMDA 95/100) |
| **SPL-G1** | [nohn3043-arch/SPL-G1-General-purpose-processor](https://github.com/nohn3043-arch/SPL-G1-General-purpose-processor) | Hardware causal-audit Trusted Compute Unit (TCU) |
| **SPL-Virtual-World-Base** | [nohn3043-arch/Second-Reality](https://github.com/nohn3043-arch/Second-Reality) | Virtual-world & metaverse infrastructure (Constitution / Law / Bridge) |
| **Story-Engine** | [nohn3043-arch/story-engine](https://github.com/nohn3043-arch/story-engine) | Long-form narrative consistency engine |
| **Antares** | [nohn3043-arch/Antares](https://github.com/nohn3043-arch/Antares) | GFSIP v1.0 — federated stable interoperability protocol with causal audit |
| **Anthropomorphic-Agent-Engine** | [nohn3043-arch/Anthropomorphic-Agent-Engine](https://github.com/nohn3043-arch/Anthropomorphic-Agent-Engine) | Deterministic anthropomorphic psychology engine (SPL Pure Core V8.0) |
| **PAGES** | [nohn3043-arch/pages](https://github.com/nohn3043-arch/pages) | Official NOHN AI ecosystem landing page |

<p align="center">— ✦ —</p>

## ✦ License & Authorization

This repository is **not open-source**. Dual-track model: free for individual non-commercial research; paid commercial authorization required for government / enterprise. See [LICENSE](./LICENSE) — licensor and governing law follow the user's location (within the PRC → Shanghai Linming Junhua Technology Co., Ltd.; outside the PRC → NOHN AI TECHNOLOGY PTE. LTD., Singapore law + SIAC arbitration).

- **Apply for authorization**: International / Global — [ai@nohnlins.com](mailto:ai@nohnlins.com) · China — [lin@secondai.top](mailto:lin@secondai.top)

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a> · <a href="https://www.nohnlins.com">Website</a> · <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · NOMOS</sub></p>
