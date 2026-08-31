# Data Processing Agreement (International) — NOMOS Intelligent Decision Hub

> This agreement defines the roles, obligations, and liabilities regarding data processing activities between the NOMOS Licensor and the authorised deploying party under GDPR (Regulation (EU) 2016/679).
> **This is a draft framework; final commercial use requires legal counsel review.**

## 1. Parties and Roles

- **Controller**: The deploying organisation (enterprise/institution user) that determines the purposes and means of processing decision data. The Controller is the party that inputs decision data into NOMOS.
- **Processor**: Any party engaged by the Controller to process data on its behalf (e.g., managed service provider, cloud infrastructure provider).
- **Licensor**: The entity granting use of NOMOS per [LICENSE](./LICENSE). The Licensor does not access, process, or store the Controller's business data.

## 2. Subject Matter and Duration of Processing (Art 28(3)(a))

- **Subject matter**: Processing of decision data for the purpose of structured decision evaluation, causal audit, and governance using NOMOS.
- **Duration**: For the term of the commercial authorisation agreement between the Controller and the Licensor, and thereafter until all processed data is deleted or returned.
- **Nature and purpose**: Deterministic decision evaluation, algorithmic audit trail generation, counterfactual analysis, stress scenario testing, and human governance workflow support.
- **Types of personal data**: Only the minimum data declared in `HubAnalysisRequest.decision` — typically decision owner identity, criteria inputs, and evidence references. No special category data (Art 9) is processed by default.
- **Categories of data subjects**: Decision owners, stakeholders referenced in decision requests, and individuals affected by decisions under evaluation.

## 3. Processor Obligations (Art 28(3)(b)-(h))

### 3.1 Process Only on Documented Instructions

- The Processor shall process personal data only on the Controller's documented instructions.
- NOMOS processes data exclusively from declared inputs (`HubAnalysisRequest`); no data is collected or inferred beyond what the Controller explicitly provides.
- The Processor shall not process personal data for any purpose other than as instructed by the Controller.

### 3.2 Confidentiality

- Persons authorised to process personal data shall be subject to confidentiality obligations.
- The Processor shall ensure that only authorised personnel with appropriate access rights can access decision data.

### 3.3 Security Measures (Art 32)

- **Encryption**: Data in transit (TLS) and at rest (deployment-level disk encryption).
- **Access control**: Production mode requires `SP_API_KEY`; OIDC integration for identity-based access.
- **Audit trail**: Hash-chained audit ledger (`algorithm_audit_root_hash`) provides tamper-evident logging.
- **Integrity**: `HubReport.report_hash` seals the complete analysis; any modification invalidates the hash.
- **Availability**: The Controller is responsible for backup and disaster recovery of persistent storage.

### 3.4 Sub-processors (Art 28(4))

- The Processor shall not engage another processor without prior specific or general written authorisation from the Controller.
- Where the Processor engages a sub-processor, the same data protection obligations shall be imposed by contract.
- The Processor remains liable to the Controller for the performance of the sub-processor's obligations.

### 3.5 Data Subject Rights (Art 28(3)(e))

- The Processor shall assist the Controller in responding to data subject rights requests, using NOMOS's audit trail and decision record retrieval capabilities.
- Decision records are JSON-structured and exportable via API (`GET /v1/decisions/{decision_id}`, `GET /v1/hub/reports/{hub_run_id}`).

### 3.6 Breach Notification (Art 28(3)(f))

- The Processor shall notify the Controller without undue delay after becoming aware of a personal data breach.
- NOMOS's hash-chained audit ledger can assist in breach detection and impact assessment.
- The Processor shall assist the Controller in fulfilling breach notification obligations to supervisory authorities and data subjects (Art 33-34).

### 3.7 Data Protection Impact Assessment (Art 28(3)(f))

- The Processor shall assist the Controller in conducting DPIAs where required (Art 35).
- NOMOS provides: documented architecture, deterministic execution model, audit trail design, and human oversight mechanisms as DPIA inputs.

### 3.8 Deletion or Return of Data (Art 28(3)(g))

- Upon termination of services, the Processor shall delete or return all personal data to the Controller.
- NOMOS's default in-process storage is ephemeral; persistent storage deletion is the Controller's responsibility.

## 4. Audit Rights (Art 28(3)(h))

- The Controller has the right to audit the Processor's compliance with this agreement.
- Audits may include: reviewing security configurations, access logs, and NOMOS audit ledger integrity.
- The Processor shall provide reasonable cooperation and information necessary for the audit.
- The Processor shall not disclose information that would breach confidentiality of other clients.

## 5. International Transfers (Chapter V)

- By default, NOMOS processes data locally; no international transfer occurs.
- If the Processor transfers personal data to a third country, an adequate safeguard must be in place:
  - Adequacy decision (Art 45);
  - Standard Contractual Clauses (Art 46);
  - Binding Corporate Rules (Art 47).

## 6. Automated Decision-Making (Art 22)

- NOMOS does not perform automated decision-making with legal or similarly significant effects.
- All decisions require human approval through the `HUMAN_APPROVAL_REQUIRED` gate.
- The Processor shall not configure NOMOS to bypass the human approval gate.

## 7. Liabilities and Indemnification

- Each party is liable for its own breaches of this agreement and applicable data protection law.
- The Processor's liability for data breaches caused by its non-compliance shall be determined under applicable law.
- The Licensor's liability is limited as set forth in [LICENSE](./LICENSE) Article 4.3 (Limitation of Liability).

## 8. Governing Law

- This agreement is governed by the law determined under [LICENSE](./LICENSE) Article 2:
  - Within PRC: PRC law; disputes submitted to the competent people's court at the Licensor's location.
  - Outside PRC: Singapore law; disputes resolved by SIAC arbitration under its rules then in force.

## 9. Final Review

This agreement is a draft framework. Before commercial deployment, it must be reviewed by legal counsel against the final GDPR text, applicable national implementation laws, and the actual data processing roles and contractual arrangements of the deployment.
