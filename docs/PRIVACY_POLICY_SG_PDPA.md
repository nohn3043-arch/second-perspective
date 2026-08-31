# Privacy Policy (Singapore PDPA) — NOMOS Intelligent Decision Hub

> This policy describes how NOMOS handles personal data under the Singapore Personal Data Protection Act 2012 (PDPA) and the IMDA AI Governance framework.
> **This is a draft framework; final commercial use requires legal counsel review.**

## 1. Scope

This policy applies to NOMOS Intelligent Decision Hub (v0.3), deployed by NOHN AI TECHNOLOGY PTE. LTD. (Singapore entity) or its authorised commercial users, covering documentation, examples, and accompanying materials.

## 2. Responsibility for Personal Data

| Role | Entity |
|------|--------|
| **Organisation** (under PDPA) | The deploying organisation that decides the purposes for which personal data is collected, used, or disclosed |
| **Licensor** | NOHN AI TECHNOLOGY PTE. LTD. — does not access, process, or store the Organisation's business data |
| **Data Processor** (if engaged) | Third party processing data on behalf of the Organisation |

## 3. Consent (PDPA Section 13-17)

- Personal data is collected, used, and disclosed only with the consent of the individual or under a deemed consent / exception provision.
- NOMOS processes only the minimum data declared in `HubAnalysisRequest.decision` — the Organisation is responsible for obtaining consent from relevant individuals before inputting their data.
- Withdrawal of consent: The Organisation shall provide a mechanism for individuals to withdraw consent; NOMOS supports this by allowing decision inputs to be corrected or removed and re-evaluated.

## 4. Purpose Limitation (Section 18)

- Personal data is used only for the purposes for which it was collected (decision evaluation, audit, governance).
- NOMOS does not use decision data for any secondary purpose (e.g., model training, analytics, marketing).
- No profiling or behavioural tracking is performed.

## 5. Notification (Section 20)

- At or before collection, individuals shall be notified of:
  - The purposes for collection, use, or disclosure;
  - The types of personal data collected;
  - The contact details of the Organisation.
- The Organisation is responsible for providing this notification; NOMOS's `StructuralAuditor` flags missing variables, helping the Organisation collect only necessary data.

## 6. Accuracy (Section 23)

- NOMOS's `StructuralAuditor` performs pre-evaluation checks for data completeness and flags missing or malformed inputs.
- The `InformationPriorityBuilder` ranks missing variables by impact, guiding the Organisation to correct inaccurate or incomplete data.
- The Organisation is responsible for ensuring data accuracy before input.

## 7. Protection (Section 24)

NOMOS provides the following technical measures:

| Measure | Implementation |
|---------|---------------|
| Access control | Production mode requires `SP_API_KEY`; OIDC integration for identity-based access |
| Encryption in transit | API requires TLS (deployment responsibility) |
| Encryption at rest | Deployment-level disk encryption |
| Audit trail | Hash-chained audit ledger (`algorithm_audit_root_hash`) |
| Integrity | `HubReport.report_hash` seals the complete analysis |
| Minimum privilege | Engine processes only declared inputs |

The Organisation shall implement organisational measures: data security policy, incident response, staff training.

## 8. Retention Limitation (Section 25)

- **Default**: Data is stored in-process memory only; no persistent storage unless explicitly configured.
- **If persistence enabled**: The Organisation shall retain personal data only as long as necessary for the purpose, then anonymise or destroy it.
- The Organisation is responsible for defining retention periods per PDPA requirements.

## 9. Transfer Limitation (Section 26)

- By default, NOMOS does not transfer personal data outside Singapore or to any third party.
- If the Organisation enables remote capability (e.g., cross-border database), the transferee must provide comparable protection per PDPA Transfer Limitation Obligation (TLO) standard.
- NOMOS itself does not initiate any cross-border data transfer.

## 10. Data Subject Rights

| Right | PDPA Basis | NOMOS Support |
|-------|-----------|---------------|
| Access | Section 21 | Decision records retrievable via API |
| Correction | Section 22 | Decision inputs correctable and re-evaluable |
| Withdrawal of consent | Section 13(2) | Organisation provides withdrawal mechanism |
| Complaint | Section 32 | Organisation provides complaint channel |

## 11. Accountability (Section 11-12)

- The Organisation shall designate a Data Protection Officer (DPO) and make their business contact publicly available.
- The Organisation shall develop and implement policies for managing personal data (PDPA Section 12(2)).
- NOMOS's audit ledger and decision records can serve as evidence of compliance.

## 12. AI Governance (IMDA / PDPC)

- NOMOS scored 95/100 in the IMDA AI Verify causal-audit track (see `IMDA_AI_Verify_Causal_Audit_Report.pdf`).
- NOMOS aligns with the Singapore Model AI Governance Framework principles:
  - **Internal Governance Structures**: human approval gate, decision ownership tracking
  - **Human Involvement**: `HUMAN_APPROVAL_REQUIRED` state, cognitive risk challenge
  - **Operations Management**: hash-chained audit trail, deterministic execution
  - **Stakeholder Interaction & Communication**: transparent audit outputs, information priority queue

## 13. Final Review

This policy is a draft framework. Before commercial deployment, it must be reviewed by legal counsel against the PDPA (including the 2020 and 2021 amendments), IMDA/PDPC guidance, and the actual data processing behaviour of the deployment.
