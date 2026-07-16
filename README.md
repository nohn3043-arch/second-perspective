<p align="center">
  <em>All uncertainty, all disasters, and all suffering<br/>ultimately arise from our ignorance of causal chains.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/IMDA_AI_Verify-95%2F100-D4AF37?style=flat-square" alt="IMDA">
  <img src="https://img.shields.io/badge/model-deterministic-2C2C2C?style=flat-square" alt="deterministic">
  <img src="https://img.shields.io/badge/runtime-offline-2C2C2C?style=flat-square" alt="offline">
  <img src="https://img.shields.io/badge/python-3.8+-2C2C2C?style=flat-square" alt="python">
</p>

---

&nbsp;

## ✦ Global Cognitive Audit Engine (GCAE)

The world's first **neutral, offline, decision-agnostic** cognitive bias auditing engine. It provides independent third-party security and compliance auditing for AI systems and enterprise decisions — without modifying internal model code.

&nbsp;

## ✦ The Constant Formula

<p align="center">
  <em>p &nbsp;♾️&nbsp; Q</em>
</p>

> **p** = principle, rule, or constraint &emsp;·&emsp; **Q** = outcome, state, or consequence<br/>
> **♾️** = an unbroken, continuous, non-bypassable causal linkage<br/>
> If the continuity between **p** and **Q** is severed, the system no longer operates under governance — it operates under narrative.

&nbsp;

## ✦ Audit Pipeline

```mermaid
flowchart TD
    D[("Decision<br/>Context")]:::input --> NS(("Narrative<br/>Stripping")):::process
    NS --> IAP(("Implicit<br/>Assumption Detection")):::process
    IAP --> LCA(("Logic<br/>Chain Audit")):::process
    LCA --> SV(("Structural<br/>Verification")):::process
    SV --> OUT{("Result")}:::output
    SV --> |pass| OK[("True")]:::pass
    SV --> |fail| NG[("False")]:::fail

    classDef input fill:#FAFAFA,stroke:#D4AF37,stroke-width:1px,color:#2C2C2C
    classDef process fill:#FAFAFA,stroke:#B8B8B8,stroke-width:1px,color:#2C2C2C
    classDef output fill:#F5F0E6,stroke:#C9A96E,stroke-width:2px,color:#2C2C2C
    classDef pass fill:#FAFAFA,stroke:#8B8B8B,stroke-width:1px,color:#2C2C2C
    classDef fail fill:#FAFAFA,stroke:#8B8B8B,stroke-width:1px,color:#2C2C2C
```

&nbsp;

## ✦ Core Features

|  | Feature | Description |
|--|---------|-------------|
| 🛡️ | **Neutral Auditing** | 100% third-party position, zero LLM vendor affiliation |
| 🔒 | **Fully Offline** | No internet or cloud data transmission required |
| 🔐 | **Privacy First** | Zero user data collection, local closed-loop isolation |
| 🔍 | **Bias Detection** | Hidden assumptions, uncertainties, cognitive blind spots |
| 🔧 | **No Model Modification** | Compatible with all mainstream LLMs |
| 📊 | **Structured Analysis** | Decision structure verification, no subjective conclusions |

&nbsp;

## ✦ Architecture

```
┌──────────────────────────────────────────────────┐
│                  GCAE Runtime                     │
│  ┌────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Narrative  │→│ Assumption│→│   Structural  │  │
│  │  Stripping  │  │ Detector  │  │  Verification│  │
│  └────────────┘  └──────────┘  └──────────────┘  │
│  ┌──────────────────────────────────────────────┐ │
│  │              Plugin System                    │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │           LLM Adapters (optional)             │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

&nbsp;

## ✦ Quick Start

```bash
pip install -r requirements.txt

# Optional: OpenAI adapter
pip install -r requirements-openai.txt
```

```python
from Cognitive_Audit_Engine import CognitiveAuditEngine, ResponsibilityAccount

account = ResponsibilityAccount(name="auditor", role="third_party")
engine = CognitiveAuditEngine(account=account)

result = engine.audit({
    "decision": "Approve project X",
    "assumptions": ["Market will grow 20%", "Team capacity is sufficient"],
    "context": {...}
})
print(result)  # → {True, False}
```

&nbsp;

## ✦ Application Scenarios

> Enterprise Strategy · Government Policy · Think Tank Research · Risk Control · AI System Auditing

&nbsp;

---

<p align="center">
  <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center">
  <sub>© 2026 Shanghai Linming Junhua &amp; NOHN AI Technology · All Rights Reserved</sub>
</p>
