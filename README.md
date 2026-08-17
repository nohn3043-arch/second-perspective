<p align="center">
  <img src="https://img.shields.io/badge/causal-audit-D4AF37?style=flat-square" alt="causal-audit">
  <img src="https://img.shields.io/badge/offline-D4AF37?style=flat-square" alt="offline">
  <img src="https://img.shields.io/badge/imda-score-95-D4AF37?style=flat-square" alt="imda-score-95">
  <img src="https://img.shields.io/badge/second-perspective-language-D4AF37?style=flat-square" alt="second-perspective-language">
</p>

<blockquote align="center">
  <em>Global Cognitive Audit Engine (GCAE) · Second-Perspective Language</em>
</blockquote>

<div style="max-width:880px;margin:0 auto;padding:0 16px">

## ✦ About

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
The <strong>Global Cognitive Audit Engine (GCAE)</strong> is the world's first neutral, offline, and decision-agnostic cognitive bias auditing engine. It provides independent third-party security and compliance auditing for AI systems and enterprise decisions without modifying internal model codes.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>Core mission</strong> — all uncertainty, all disasters, and all suffering ultimately arise from our ignorance of causal chains. The engine delivers neutral, traceable structural support for high-stakes rational decision-making through systematic identification of implicit assumptions, objective uncertainties, and human cognitive biases.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
✅ <strong>Passed the IMDA AI Verify assessment with an overall score of 95</strong> — full report in <code>IMDA_AI_Verify_Causal_Audit_Report.pdf</code>.
</p>

</div>

<p align="center">— ✦ —</p>

## ✦ Try It Online

<div style="max-width:880px;margin:0 auto;padding:0 16px">

Experience the full five-operator causal audit pipeline directly in your browser — zero installation, zero data upload, fully deterministic:

🌐 **Live Demo**: [https://nohnlins.com/audit/](https://nohnlins.com/audit/)

> Runs entirely client-side. Your decision data never leaves your browser.

</div>

<p align="center">— ✦ —</p>

## ✦ The Five Operators

<div style="max-width:880px;margin:0 auto;padding:0 16px">

Each operator ships as a plugin in `plugins/`:

| Operator | Plugin | Description |
|---|---|---|
| Narrative Strip (NS) | `plugins/ns.py` | Strips rhetoric, emotion, and vague quantifiers to extract the logical core |
| Implicit Assumption Perspective (IAP) | `plugins/iap.py` | Uncovers hidden assumptions, privilege bypass, circular justification |
| Fragility Latch (LCH) | `plugins/lch.py` | Computes ΔD collapse probability per assumption, finds the weakest variable |
| Causal Chain Sync (CCS) | `plugins/ccs.py` | Inverse check + counterfactual verification + black hole detection |
| State Anchor (STATE) | `plugins/state.py` | Responsibility anchoring + SHA-256 audit certificate |

</div>

<p align="center">— ✦ —</p>

## ✦ The Constant Formula

<div style="max-width:880px;margin:0 auto;padding:0 16px">

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>p → Q</strong> — where <strong>p</strong> represents principle, rule, or constraint, and <strong>Q</strong> represents outcome, state, or consequence. The arrow denotes an unbroken, continuous, and non-bypassable causal linkage.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
If the continuity between p and Q is severed, obscured, or silently altered, the system no longer operates under governance, but under narrative.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>Structural audit predicate</strong> — Φ{f_s, x, y} → {True, False}: verifies whether a given decision structure meets minimum requirements for rational consistency, based on system function f_s and input conditions x, y. It generates no recommendations or optimizations — only audit results.
</p>

<p style="font-size:15px;line-height:1.8;color:#2C2C2C">
<strong>Second-perspective decision form</strong> — a valid decision is a three-part structure: Decision (D) · Hypothesis Premise (A) · Branch Response (ΔD), expressed as <strong>¬A ⇒ ΔD</strong> (when a core assumption fails, the branch response fires).
</p>

</div>

## ✦ Core Features

| Feature | Description |
|---|---|
| 🛡️ **Neutral Auditing** | Maintains 100% neutral third-party position, no affiliation with any LLM vendor |
| 🔒 **Fully Offline** | No internet connection or cloud data transmission required |
| 🔐 **Privacy First** | Zero user data collection with local closed-loop data isolation |
| 🔍 **Bias Detection** | Identifies hidden assumptions, uncertainties, and cognitive blind spots |
| 🔧 **No Model Modification** | Compatible with all mainstream LLMs without altering source code |
| 📊 **Structured Analysis** | Provides decision structure verification without subjective conclusions |

<p align="center">— ✦ —</p>

## ✦ Quick Start

```bash
# Primary: GitHub
git clone https://github.com/nohn3043-arch/second-perspective.git
# Mirror: Gitee
# git clone https://gitee.com/nohn-ecosystem/second-perspective.git
cd second-perspective
pip install -r requirements.txt          # core dependencies
# optional: pip install -r requirements-openai.txt   # OpenAI narrative adapter

# Run the five-operator end-to-end demo
python demo_audit.py
```

<p align="center">— ✦ —</p>

## ✦ Usage

<div style="max-width:880px;margin:0 auto;padding:0 16px">

The engine file uses spaces in its name by design — load it with `importlib`:

```python
import importlib.util

spec = importlib.util.spec_from_file_location("ca", "cognitive audit engine.py")
ca = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ca)

account = ca.ResponsibilityAccount(
    organization="audit_team",
    role="third_party_auditor",
    stage="review",
)

config = ca.AuditConfigLoader.load_from_dict({
    "allowed_stages": ["pre_decision", "in_decision", "post_decision", "review"],
    "disclaimer": "Structural audit only — does not replace human judgment.",
    "custom_fields": {"standard_version": "2026"},
})

engine = ca.CognitiveAuditEngine(account=account, config=config)
engine.load_core_plugins()               # registers NS / IAP / LCH / CCS / STATE

report = engine.audit(decision_context)  # static diagnosis

# Causal reconstruction: inject correction variables and test convergence
result = engine.reconstruct(decision_context, delta_vars={"assumption_x": False})
```

The five operators are also importable as plugins directly:

```python
from plugins import (
    NarrativeStripPlugin,
    ImplicitAssumptionPlugin,
    FragilityLatchPlugin,
    CausalChainSyncPlugin,
    StateAnchorPlugin,
)
```

An optional narrative-generation adapter is available via
[`llm_adapters/openai_adapter.py`](llm_adapters/openai_adapter.py).

</div>

<p align="center">— ✦ —</p>

## ✦ Project Structure

```
second-perspective/
├── cognitive audit engine.py      # core engine (spaces in name by design)
├── demo_audit.py                  # five-operator end-to-end demo
├── plugins/                       # the five operators as plugins
│   ├── ns.py                      #   Narrative Strip
│   ├── iap.py                     #   Implicit Assumption Perspective
│   ├── lch.py                     #   Fragility Latch
│   ├── ccs.py                     #   Causal Chain Sync
│   └── state.py                   #   State Anchor
├── llm_adapters/openai_adapter.py # optional OpenAI narrative adapter
├── web/                           # client-side audit demo
├── docs/                          # documentation / index.html
├── language Standard/             # Language Standard 2026
├── 全新决策结构语言/              # decision-structure language specification
├── IMDA_AI_Verify_Causal_Audit_Report.pdf
├── requirements.txt · requirements-openai.txt
└── LICENSE
```

<p align="center">— ✦ —</p>

## ✦ Ecosystem

GCAE is one member of the NOHN AI ecosystem — a family of projects built around second-perspective causal audit and deterministic execution:

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

This repository is a technical showcase for the **Global Cognitive Audit Engine (GCAE)**. This repository is **not open-source**. Dual-track model: free for individual non-commercial research; paid commercial authorization required for government / enterprise. See [LICENSE](./LICENSE).

| User | Purpose | License Requirement |
|---|---|---|
| Individual (natural person) | Non-commercial academic research / study / personal experimentation | **Free** under the "Free Individual Research License" in [LICENSE](./LICENSE) |
| Government agency / public institution / enterprise | Any purpose (incl. internal deployment, product development, service provision) | **Requires prior written paid authorization** |

- **Individual researchers** may use the Work free of charge for non-commercial research under [LICENSE](./LICENSE), but not for any commercial purpose, nor to provide services to any enterprise or government organization.
- **Government / enterprise users** may not copy, deploy, run, integrate, or distribute the Work before signing a Commercial Authorization Agreement and paying the agreed fee.
- **Apply for authorization**:
  - International / Global: [ai@nohnlins.com](mailto:ai@nohnlins.com)
  - China: [lin@secondai.top](mailto:lin@secondai.top)

The licensor, governing law, and dispute resolution are determined by the user's location as set out in [LICENSE](./LICENSE): users within the PRC → Shanghai Linming Junhua Technology Co., Ltd. (laws of the PRC); users outside the PRC → NOHN AI TECHNOLOGY PTE. LTD. (laws of Singapore, SIAC arbitration).

### Clean-Room Notice

Any party who independently develops products with substantially similar core functions, architectures, or decision models shall be presumed to have committed substantive derivative infringement unless they can provide complete, continuous, and traceable evidence proving independent development.

**Disclaimer**: This language system is only applied to structural review and decomposition during the decision-making process. It does not participate in decision formulation, nor interfere with final decisions. The author assumes no legal liability or operational responsibility for any subsequent execution results.

<p align="center">
  <a href="https://github.com/nohn3043-arch">GitHub</a>
  &nbsp;·&nbsp;
  <a href="https://www.nohnlins.com/">nohnlins.com</a>
  &nbsp;·&nbsp;
  <a href="mailto:ai@nohnlins.com">ai@nohnlins.com</a>
</p>
<p align="center"><sub>NOHN AI · SECOND-PERSPECTIVE</sub></p>
