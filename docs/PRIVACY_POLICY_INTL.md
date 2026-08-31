# Privacy Policy (International) — NOMOS Intelligent Decision Hub

> This policy describes how NOMOS processes personal data during deployment and use.
> **This is a draft framework; final commercial use requires legal counsel review.**

## 1. Scope

This policy applies to NOMOS Intelligent Decision Hub (v0.3) and its documentation, examples, and accompanying materials.

## 2. Controller and Processor

- The **Controller** is the deploying organization (enterprise/institution user) that determines the purposes and means of processing decision data.
- The **Processor** is any party engaged by the Controller to process data on its behalf (e.g., managed service provider, cloud provider).
- The **Licensor** (as defined in [LICENSE](./LICENSE)) does not access or process the Controller's business data.
- The Licensor entity is determined by user location per [LICENSE](./LICENSE): within PRC → Shanghai Linming Junhua Technology Co., Ltd.; outside PRC → NOHN AI TECHNOLOGY PTE. LTD.

## 3. Legal Bases for Processing (GDPR Art 6)

NOMOS processes personal data under the following legal bases:

| Processing Activity | Legal Basis |
|---------------------|-------------|
| Decision evaluation and audit | Art 6(1)(b) — necessary for performance of a contract |
| Compliance and regulatory audit | Art 6(1)(c) — legal obligation |
| Legitimate interests of the Controller | Art 6(1)(f) — legitimate interests |
| Explicit consent (if applicable) | Art 6(1)(a) — consent |

The Controller is responsible for determining and documenting the appropriate legal basis for each processing activity.

## 4. Data Minimisation (Art 5(1)(c))

- NOMOS processes only the minimum data set necessary for decision evaluation, audit, and governance.
- No personal data is collected beyond what is required for the declared decision request.
- No profiling or behavioural tracking is performed.
- The `StructuralAuditor` flags missing variables before evaluation, preventing unnecessary data collection.

## 5. Data Storage and Local Processing

- **Default**: Decision data is stored locally/on-premises; no cross-border transmission occurs by default.
- **Optional PostgreSQL persistence**: If `SP_DATABASE_DSN` is configured, the Controller is responsible for ensuring the database complies with GDPR storage requirements.
- **No telemetry**: NOMOS does not transmit usage data, analytics, or telemetry to the Licensor or any third party.

## 6. International Data Transfers (Chapter V)

- By default, no personal data leaves the deployment environment.
- If the Controller enables any remote capability (e.g., cloud database, OIDC provider), the Controller is responsible for ensuring an adequate transfer mechanism:
  - **Adequacy decision** (Art 45) — if transferring to a country with an adequacy decision;
  - **Standard Contractual Clauses** (Art 46) — if transferring to a third country without adequacy;
  - **Binding Corporate Rules** (Art 47) — for intra-group transfers.

## 7. Data Subject Rights (Chapter III)

The Controller shall facilitate the following data subject rights:

| Right | Article | NOMOS Support |
|-------|---------|---------------|
| Right of access | Art 15 | Decision records and audit logs are retrievable via API |
| Right to rectification | Art 16 | Decision inputs can be corrected and re-evaluated |
| Right to erasure | Art 17 | Deploying organisation must provide deletion capability |
| Right to restriction | Art 18 | Decision evaluation can be paused at `HUMAN_APPROVAL_REQUIRED` |
| Right to data portability | Art 20 | Decision records are JSON-structured and exportable |
| Right to object | Art 21 | Human approval gate ensures human intervention |
| Rights regarding automated decision-making | Art 22 | NOMOS never makes final decisions autonomously; human approval is always required |

## 8. Automated Decision-Making (Art 22)

**NOMOS does not make automated decisions with legal or similarly significant effects on data subjects.**

- The engine produces candidates and analysis; the final decision is always made by a human through the `HUMAN_APPROVAL_REQUIRED` gate.
- The `CognitiveRiskScanner` provides structural risk challenges to inform human review.
- The `ReconstructionSessionEngine` stops at `AWAITING_HUMAN` after each round, requiring explicit human action to proceed.

## 9. Data Retention and Deletion

- **Default**: Data is retained in-process memory only; no persistent storage unless explicitly configured.
- **If persistence is enabled**: The Controller shall define and document retention periods based on applicable legal requirements.
- **Deletion**: The Controller shall provide a deletion mechanism and complete deletion requests within a reasonable timeframe.
- **Audit logs**: Retention of audit logs may be subject to sector-specific legal retention requirements.

## 10. Security Measures (Art 32)

NOMOS provides the following technical and organisational measures:

- **Encryption in transit**: API requires TLS (deployment responsibility).
- **Encryption at rest**: Decision data can be encrypted via deployment-level disk encryption.
- **Access control**: Production mode requires `SP_API_KEY` (Bearer token); OIDC integration available for identity-based access.
- **Audit trail**: Hash-chained audit ledger (`algorithm_audit_root_hash`) provides tamper-evident logging.
- **Minimum privilege**: Role-based access via OIDC; the engine processes only declared inputs.

**Controller must implement**: Data security incident response and breach notification procedures (Art 33-34).

## 11. Data Protection Impact Assessment (Art 35)

When NOMOS is deployed in a high-risk scenario (as determined under the EU AI Act or GDPR criteria), the Controller shall conduct a DPIA. NOMOS supports this with:

- Documented system architecture and data flows;
- Deterministic execution model (no opaque ML);
- Audit trail design and integrity verification;
- Human oversight mechanisms.

## 12. Records of Processing Activities (Art 30)

The Controller shall maintain records of processing activities, including:

- Purpose of processing;
- Categories of data subjects and personal data;
- Categories of recipients;
- Transfers to third countries and safeguards;
- Retention periods;
- General description of technical and organisational security measures.

NOMOS's audit ledger and decision records can serve as input data for maintaining these records.

## 13. Breach Notification (Art 33-34)

- The Controller is responsible for notifying the competent supervisory authority within 72 hours of becoming aware of a personal data breach (Art 33).
- The Controller is responsible for communicating breaches to affected data subjects without undue delay (Art 34).
- NOMOS's hash-chained audit ledger can assist in breach detection and impact assessment.

## 14. Final Review

This policy is a draft framework. Before commercial deployment, it must be reviewed by legal counsel against the final GDPR text, applicable national implementation laws, and the actual data processing behaviour of the deployment.
