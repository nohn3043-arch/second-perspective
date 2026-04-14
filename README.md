一个用于决策前的理性审计工具。

用于在高风险决策前，暴露假设、不确定性与认知偏差。
离线运行，中立立场，不做决策，也不替代决策。
所有责任始终由使用者承担。不提供保证，不提供损害赔偿，适用发布者所在地法律法规。
## 重要声明
本项目的核心逻辑、架构设计、方法论，均属于首创性工作，受相关法律保护。
任何对本项目核心思想的复现、重构、再发布，请确保：
1. 明确引用本项目为思想来源
2. 通过 [邮箱] 通知作者
3. 不得用于削弱作者参与标准制定的合法性基础
## 许可证与法律条款

本项目采用 [请选择一种]：
A. **商业保护许可证**：源代码可见，但禁止任何形式的商业使用、内部部署、或提供基于本项目的服务。个人研究、教育、非商业性内部审计除外。商业使用需单独获取许可证（联系上方邮箱）。
B. **GPL v3 + 附加条款**：允许自由使用，但任何衍生作品必须开源，且不得用于削弱原作者的标准制定参与权。

管辖法律：本项目的所有法律争议，适用 [瑞士/新加坡/爱沙尼亚] 法律，并由 [日内瓦/新加坡/塔林] 法院专属管辖。

净室实现限制：任何在访问本项目代码、文档或任何衍生信息后，开发出的功能与本项目核心思想实质相似者，推定为侵权，除非能提供独立开发的完整证据链。
作者保留采取法律及公开手段维护首创地位的权利。
README.md](https://github.com/user-attachments/files/26661292/README.md)
# Global Cognitive Audit Engine (GCAE)

The world's first neutral, offline, decision-independent cognitive bias audit engine.

Purpose:
- Expose hidden assumptions
- Identify uncertainty
- Detect cognitive biases
- Support rational decision-making

Features:
- Offline only, no network required
- No data collection
- No decision substitution

For enterprise, government, think tanks
1. Obtain commercial license
2. Integrate internally
3. Audit before critical decisions
4. For enterprise/government authorization inquiries: contact [nohn3043@gmail.com]

# Second Perspective Language · Decision Structure Language
## 第二视角语言 · 决策结构语言（One Page）

### Definition
A structural language for expressing **how decisions are validated**.
No judgment, no recommendation, only dependency and vulnerability exposure.

### Core Structure
Any decision must be expressed in three components:
1. **Decision**
   The actionable judgment to execute (specific, accountable).
2. **Assumptions**
   Premises that validate the decision (negatable).
3. **Branches**
   How the decision path changes when assumptions fail.

### Formal Expression
¬A ⇒ ΔD

### Core Principle
A decision = a bet on the validity of a set of assumptions.
Once premises fail, the decision must structurally change.

### Mandatory Constraints
- No output recommendations
- No conclusions
- No judgment of superiority or inferiority
- No compression of uncertainty

### Minimal Expression
Decision: D
Assumptions: A1, A2, A3
Branches:
¬A1 ⇒ ΔD
¬A2 ⇒ ΔD
¬A3 ⇒ ΔD

### Purpose
- Expose hidden assumptions
- Visualize decision dependencies
- Reveal path forks in advance

### Boundary
This language only audits the **decision-making formation process**
and does not participate in any decision-making.
