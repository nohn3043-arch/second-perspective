# Global Cognitive Audit Engine (GCAE)

## Project Overview

The **Global Cognitive Audit Engine (GCAE)** is the world's first neutral, offline, and decision-agnostic cognitive bias auditing engine. It provides independent third-party security and compliance auditing for AI systems and enterprise decisions without modifying internal model codes.

### Core Mission

> All uncertainty, all disasters, and all suffering ultimately arise from our ignorance of causal chains.

This engine delivers neutral, traceable structural support for high-stakes rational decision-making through systematic identification of implicit assumptions, objective uncertainties, and human cognitive biases.

### Key Achievement

✅ **Passed IMDA AI Verify assessment with an overall score of 95**

---

## The First Constant Formula

$$p♾️Q$$

Where **p** represents principle, rule, or constraint, and **Q** represents outcome, state, or consequence. The symbol **♾️** denotes an unbroken, continuous, and non-bypassable causal linkage.

If the continuity between **p** and **Q** is severed, obscured, or silently altered, the system no longer operates under governance, but under narrative.

---

## The Constant Formula

$$\Phi\{f_s, x, y\} \rightarrow \{True, False\}$$

- **Φ** refers to a structural audit predicate
- Verifies whether a given decision structure meets minimum requirements for rational consistency
- Based on system function $f_s$ and input conditions $x, y$
- Generates no recommendations or optimizations — only returns audit results

---

## Core Features

| Feature | Description |
|---------|-------------|
| 🛡️ **Neutral Auditing** | Maintains 100% neutral third-party position, no affiliation with any LLM vendor |
| 🔒 **Fully Offline** | No internet connection or cloud data transmission required |
| 🔐 **Privacy First** | Zero user data collection with local closed-loop data isolation |
| 🔍 **Bias Detection** | Identifies hidden assumptions, uncertainties, and cognitive blind spots |
| 🔧 **No Model Modification** | Compatible with all mainstream LLMs without altering source code |
| 📊 **Structured Analysis** | Provides decision structure verification without subjective conclusions |

---

## Architecture

### Main Components

#### Cognitive Audit Engine (`Cognitive Audit Engine.py`)

```python
@dataclass
class ResponsibilityAccount       # Responsibility tracking

class AuditConfigLoader:          # Configuration management
    - load_from_dict(config)      # Load from dictionary
    - load_from_json(path)        # Load from JSON file

class AuditPlugin:                # Plugin system for extensibility
    - analyze_func                # Custom analysis function

class CognitiveAuditEngine:       # Core auditing engine
    - register_plugin()           # Register analysis plugins
    - audit()                     # Execute audit on decision context
```

#### LLM Adapters (`llm_adapters/openai_adapter.py`)

```python
class OpenAIAdapter:              # OpenAI API integration
    - generate_narrative()        # Generate audit reports
```

---

## Second-Person Perspective Language

### Definition

A structured language dedicated to decision verification and risk decomposition. It makes no value judgments, provides no optimization suggestions, and draws no final conclusions.

### Core Structure

A complete and valid decision consists of three fixed components:

- **Decision (D)**: Executable, clearly defined judgments with clear accountability
- **Hypothesis Premise (A)**: Falsifiable preconditions that underpin decision validity
- **Branch Response (ΔD)**: Adjustment plans when core assumptions fail

### Formal Expression

$$\neg A \Rightarrow \Delta D$$

### Standard Expression Mode

```
Decision: D
Core Assumptions: A1, A2, A3

Risk Branch Logic:
¬A1 ⇒ ΔD
¬A2 ⇒ ΔD
¬A3 ⇒ ΔD
```

---

## Installation

### Requirements

- Python 3.8+
- See `requirements.txt` for core dependencies
- See `requirements-openai.txt` for OpenAI adapter dependencies

### Setup

```bash
# Install core dependencies
pip install -r requirements.txt

# Install OpenAI adapter (optional)
pip install -r requirements-openai.txt
```

---

## Usage

### Basic Audit Example

```python
from "Cognitive Audit Engine" import (
    CognitiveAuditEngine,
    ResponsibilityAccount,
    AuditConfigLoader
)

# Initialize responsibility account
account = ResponsibilityAccount(
    name="audit_team",
    role="third_party_auditor"
)

# Load configuration
config = AuditConfigLoader.load_from_json("config.json")

# Create audit engine
engine = CognitiveAuditEngine(account=account, config=config)

# Register custom plugins (optional)
def my_analysisPlugin(data):
    # Custom analysis logic
    return {"result": "analysis_complete"}

plugin = AuditPlugin(name="custom_analysis", analyze_func=my_analysisPlugin)
engine.register_plugin(plugin)

# Perform audit
decision_context = {
    "decision": "Approve project X",
    "assumptions": ["A1", "A2", "A3"],
    "context": {...}
}

result = engine.audit(decision_context)
print(result)  # Returns: {True, False}
```

### Using OpenAI Adapter

```python
from llm_adapters.openai_adapter import OpenAIAdapter

# Initialize adapter
adapter = OpenAIAdapter(
    api_key="your-api-key",
    model="gpt-3.5-turbo",
    temperature=0.0
)

# Generate audit narrative
report = {...}  # Audit results
narrative = adapter.generate_narrative(report)
```

---

## Application Scenarios

- 🏢 **Enterprise Strategy** - Major investment and strategic decisions
- 🏛️ **Government Policy** - Public policy research and impact assessment
- 🧠 **Think Tank Studies** - Research and analysis support
- ⚠️ **Risk Control** - Institutional risk management
- 🤖 **AI System Auditing** - LLM output verification and bias detection

---

## License & Authorization

This repository is a technical showcase for the **Global Cognitive Audit Engine (GCAE)**. Copyright © 2026 Shanghai Linming Junhua Technology Co., Ltd. and NOHN AI TECHNOLOGY PTE. LTD. All rights reserved.

| User | Purpose | License Requirement |
|---|---|---|
| Individual (natural person) | Non-commercial academic research / study / personal experimentation | **Free** under the "Free Individual Research License" in [LICENSE](./LICENSE) |
| Government agency / public institution / enterprise | Any purpose (incl. internal deployment, product development, service provision) | **Requires prior written paid authorization** |

- **Individual researchers** may use the Work free of charge for non-commercial research under [LICENSE](./LICENSE), but not for any commercial purpose, nor to provide services to any enterprise or government organization.
- **Government / enterprise users** may not copy, deploy, run, integrate, or distribute the Work before signing a Commercial Authorization Agreement and paying the agreed fee.
- **Apply for authorization**:
  - International / Global: [ai@nohnlins.com](mailto:ai@nohnlins.com)
  - China: [ai@tx.nohnlins.com](mailto:ai@tx.nohnlins.com)

The licensor, governing law, and dispute resolution are determined by the user's location as set out in [LICENSE](./LICENSE): users within the PRC → Shanghai Linming Junhua Technology Co., Ltd. (laws of the PRC); users outside the PRC → NOHN AI TECHNOLOGY PTE. LTD. (laws of Singapore, SIAC arbitration).

---

## Important Notices

### LEGAL NOTICE

> GOVERNMENTS, ENTERPRISES, AND PUBLIC INSTITUTIONS ARE PROHIBITED FROM USING, COPYING, DEPLOYING, OR DERIVING THIS PROJECT WITHOUT EXPLICIT WRITTEN AUTHORIZATION.

This document contains original copyrighted works, theoretical systems, structured paradigms, and mathematical expression models. All content is fully protected by copyright law.

### Clean-Room Implementation

Any party who independently develops products with substantially similar core functions, architectures, or decision models shall be presumed to have committed substantive derivative infringement unless they can provide complete, continuous, and traceable evidence proving independent development.

---

## Contact

For institutional authorization, customized integration, and business inquiries:

- 📧 Email (International): ai@nohnlins.com
- 📧 Email (China): ai@tx.nohnlins.com

---

## References

- [IMDA AI Verify Assessment Report](./IMDA_AI_Verify_Causal_Audit_Report.pdf)
- [Language Standard 2026](./language%20Standard/2026)

---

**Disclaimer**: This language system is only applied to structural review and decomposition during the decision-making process. It does not participate in decision formulation, nor interfere with final decisions. The author assumes no legal liability or operational responsibility for any subsequent execution results.