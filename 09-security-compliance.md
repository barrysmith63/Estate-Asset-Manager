# Security & Compliance Specification
**Estate Asset Manager — Product & Engineering Deliverable 09**

---

## Executive Summary
This document defines the security architecture, encryption standards, audit log requirements, data classification, PII handling procedures, and compliance readiness checklist for the Estate Asset Manager. It is the primary reference for security reviews, SOC 2 audits, and enterprise customer due diligence questionnaires.

---

## 1. How to Complete This Template

1. **Assign a Data Protection Officer (DPO) or Security Lead** as owner of this document.
2. **Complete the data classification inventory** (§4) by walking through every data field stored by the system.
3. **Run a PII discovery scan** on all databases and exported artifacts to confirm PII fields are correctly tagged.
4. **Complete the compliance checklist** (§7) before each enterprise customer go-live.
5. **Schedule quarterly reviews**: security landscape changes; so does this document.
6. **Engage a third-party penetration testing firm** at least annually and before any major release.

> **References**
> - OWASP Top 10 (2021): https://owasp.org/Top10/
> - NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
> - NIST SP 800-53 Rev. 5 (Security Controls): https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
> - SOC 2 Type II overview (AICPA): https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report
> - GDPR official text: https://gdpr-info.eu/
> - CCPA: https://oag.ca.gov/privacy/ccpa
> - Search: `SOC 2 Type II security controls checklist SaaS`
> - Search: `OWASP RBAC access control testing guide`

---

## 2. RBAC Summary (Security View)

> Full RBAC matrix is defined in Deliverable 03. This section summarizes the security-relevant properties.

| Property | Implementation |
|---|---|
| Model | Role-Based Access Control (RBAC) with attribute-based conditions |
| Role evaluation | Server-side only — JWT claims validated on every request; client cannot elevate |
| Deny-by-default | Unrecognized roles and missing role claims result in 0 permissions |
| Privilege separation | No role can assign permissions equal to or exceeding its own level |
| Tenant isolation | Every DB query scoped by `tenant_id`; enforced at middleware layer |
| Machine identities | Integration Service role (R09) is non-human; separate credential lifecycle |
| Session management | JWT access tokens (1 h TTL); refresh tokens (30 days, rotated on use) |
| Token storage | Access token: memory only (never localStorage); refresh token: HttpOnly cookie |
| Audit trail | All RBAC changes produce immutable audit log entries — see §5 |

---

## 3. Encryption Standards

### 3.1 Encryption at Rest

| Data Store | Encryption Standard | Key Management | Notes |
|---|---|---|---|
| Primary database (PostgreSQL) | AES-256 (cloud provider managed) | AWS KMS / Azure Key Vault | Enable Transparent Data Encryption (TDE) |
| Audit log store | AES-256 | Dedicated KMS key (separate from app key) | Principle of least privilege on key access |
| Object storage (documents, exports) | AES-256 (SSE-S3 / SSE-KMS) | Per-tenant KMS key (optional) | Default: SSE-S3; enterprise: SSE-KMS |
| Secrets (tokens, API keys, certs) | AES-256 | AWS Secrets Manager / Azure Key Vault | Never stored in env vars or code |
| Backups | AES-256 | Same key as source | Backups encrypted before transfer to cold storage |
| Local developer machines | Full-disk encryption required | OS-native (FileVault / BitLocker) | Policy enforced via MDM |

### 3.2 Encryption in Transit

| Connection | Protocol | Certificate | Notes |
|---|---|---|---|
| Client ↔ API (all traffic) | TLS 1.2+ (TLS 1.3 preferred) | CA-signed cert; auto-renewed | Enforce HSTS; reject < TLS 1.2 |
| API ↔ Database | TLS 1.2+ | Internal CA or cloud-managed | Enforce `ssl=require` in connection string |
| API ↔ Connectors (accounting, IoT) | TLS 1.2+ + OAuth 2.0 / mTLS | Public CA | See Deliverable 02 per connector |
| API ↔ SIEM / Audit log sink | TLS 1.2+ | CA-signed | Mutual TLS where supported |
| Internal service ↔ service | TLS 1.2+ (mTLS preferred) | Service mesh (Istio / Linkerd) | Zero-trust internal networking |
| MQTT (IoT) | TLS 1.2+ + X.509 client certs | Rotated every 90 days | See Contract B, Deliverable 02 |

### 3.3 Key Rotation Policy

| Key Type | Rotation Frequency | Trigger for Immediate Rotation |
|---|---|---|
| Application signing keys (JWT) | 90 days | Suspected compromise; team member departure |
| OAuth client secrets | 90 days | Token revocation event |
| Connector API keys | 90 days | Connector re-auth event |
| IoT device certificates | 90 days | Device decommission or compromise |
| Database master key | Annual | Suspected breach |
| Backup encryption key | Annual | Retention policy change |

---

## 4. Data Classification

### 4.1 Classification Levels

| Level | Label | Description | Handling |
|---|---|---|---|
| L1 | Public | Intentionally public information | No restrictions |
| L2 | Internal | Business data not meant for external parties | Access controls; TLS in transit |
| L3 | Confidential | Sensitive business or personal data | RBAC + encryption at rest + audit log |
| L4 | Restricted | PII, financial data, legal documents, credentials | All L3 controls + masking + DPO review for access |

### 4.2 Field-Level Data Inventory

| Table | Field | Classification | PII | Notes |
|---|---|---|---|---|
| `users` | `email` | L4 Restricted | ✅ | Normalize to lowercase; mask in logs |
| `users` | `name` | L4 Restricted | ✅ | Mask in logs; hash in analytics |
| `users` | `ip_address` | L4 Restricted | ✅ | Hash after 90 days for analytics |
| `assets` | `name` | L3 Confidential | — | May contain PII in free text — scan on ingest |
| `assets` | `notes` | L3 Confidential | ⚠️ Possible | Scan for PII patterns on save |
| `valuations` | `amount` | L3 Confidential | — | Financial data |
| `documents` | `file_content` | L4 Restricted | ⚠️ Possible | Encrypt per-file; scan for PII |
| `audit_events` | `actor_ip` | L4 Restricted | ✅ | Retain per §5; mask in user-facing exports |
| `connector_tokens` | `access_token` | L4 Restricted | — | Never log; encrypt at rest |
| `connector_tokens` | `refresh_token` | L4 Restricted | — | Never log; encrypt at rest |
| `[table]` | `[field]` | `[L1–L4]` | `[✅/—/⚠️]` | `[notes]` |

---

## 5. Audit Log Retention

> Full audit log schema and auditable actions are defined in Deliverable 03, §5.

| Requirement | Specification |
|---|---|
| Storage type | Append-only; WORM or cryptographic hash-chaining |
| Standard events | 7 years (1 year hot PostgreSQL; 6 years S3 Glacier) |
| Critical events (role changes, legal hold, config changes) | 10 years (1 year hot; 9 years cold) |
| Access to logs | Read-only: Auditor (R07), Compliance (R08); no role may delete |
| Export format | JSON (newline-delimited) or CSV on demand |
| SIEM integration | Events forwarded within 60 s of creation; alert if lag > 60 s |
| Backup | Daily snapshot of audit table; stored separately from primary DB |
| Tamper detection | Cryptographic chaining: each entry includes hash of previous entry |

---

## 6. PII Handling Procedures

| Procedure | Implementation |
|---|---|
| PII discovery | Run PII scanner on all DB tables quarterly; flag new fields |
| PII in logs | Block PII fields from structured logs at application layer; use log sanitizer middleware |
| PII in exports | Mask or redact PII fields unless explicitly authorized (Auditor/Compliance requesting audit export) |
| PII in analytics | Hash PII before sending to analytics pipeline; never send raw email or name |
| Right to erasure (GDPR Art. 17) | Soft-delete user record; overwrite PII fields with `[DELETED]` placeholder; retain audit log pointers |
| Data subject access request (DSAR) | Provide export of all data for a user within 30 days; see DSAR runbook in team wiki |
| Data breach notification | Notify DPO within 1 h of detection; notify affected users within 72 h per GDPR Art. 33 |
| Third-party data sharing | PII shared with connectors only as needed per integration contract (Deliverable 02); DPA required |

---

## 7. Compliance Checklist — Enterprise Readiness

### 7.1 SOC 2 Type II Readiness

| Control | Status | Evidence Location | Owner |
|---|---|---|---|
| Access control (CC6.1) | `[✅/🟡/❌]` | RBAC matrix (Deliverable 03) | Security Eng |
| Logical access provisioning (CC6.2) | `[✅/🟡/❌]` | User provisioning runbook | IT Admin |
| Multi-factor authentication (CC6.3) | `[✅/🟡/❌]` | MFA policy (EP05-S03) | Security Eng |
| Encryption at rest (CC6.7) | `[✅/🟡/❌]` | §3.1 this document | DevOps |
| Encryption in transit (CC6.7) | `[✅/🟡/❌]` | §3.2 this document | DevOps |
| Audit logging (CC7.2) | `[✅/🟡/❌]` | Deliverable 03 §5 | Backend Eng |
| Incident response plan (CC7.3) | `[✅/🟡/❌]` | Deliverable 08 runbooks | SRE |
| Change management (CC8.1) | `[✅/🟡/❌]` | Git PR policy; deploy runbook | Engineering |
| Availability (A1.1) | `[✅/🟡/❌]` | SLO-01 (Deliverable 04) | SRE |
| Vendor management (CC9.2) | `[✅/🟡/❌]` | Connector contracts (Deliverable 02) | Procurement |

### 7.2 GDPR / CCPA Readiness

| Requirement | Status | Notes |
|---|---|---|
| Privacy policy published | `[✅/🟡/❌]` | Link: `[URL]` |
| Data processing agreements (DPA) with all vendors | `[✅/🟡/❌]` | See vendor register |
| Consent mechanism for marketing communications | `[✅/🟡/❌]` | Opt-in on signup |
| DSAR process documented and tested | `[✅/🟡/❌]` | 30-day response target |
| Right to erasure implemented | `[✅/🟡/❌]` | §6 this document |
| Data breach notification procedure | `[✅/🟡/❌]` | 72-h GDPR; 45-day CCPA |
| Data retention policy enforced | `[✅/🟡/❌]` | §5 this document; automated archival job |
| Cross-border data transfer safeguards | `[✅/🟡/❌]` | Standard Contractual Clauses (SCCs) for EU data |

### 7.3 OWASP Top 10 Mitigation Checklist

| OWASP Risk | Mitigation | Status |
|---|---|---|
| A01 Broken Access Control | RBAC + tenant scoping + integration tests | `[✅/🟡/❌]` |
| A02 Cryptographic Failures | AES-256 at rest; TLS 1.2+ in transit; no MD5/SHA1 | `[✅/🟡/❌]` |
| A03 Injection | Parameterized queries only; ORM-enforced; no raw SQL from user input | `[✅/🟡/❌]` |
| A04 Insecure Design | Threat model reviewed; security design review for each epic | `[✅/🟡/❌]` |
| A05 Security Misconfiguration | CIS benchmarks applied; IaC scanning (Checkov / tfsec) | `[✅/🟡/❌]` |
| A06 Vulnerable Components | Dependabot / Snyk in CI; no known critical CVEs | `[✅/🟡/❌]` |
| A07 Authentication Failures | OIDC + MFA + account lockout after 5 failed attempts | `[✅/🟡/❌]` |
| A08 Integrity Failures | Signed container images; IaC checksums; webhook HMAC | `[✅/🟡/❌]` |
| A09 Security Logging Failures | Audit log per Deliverable 03; SIEM within 60 s | `[✅/🟡/❌]` |
| A10 SSRF | Allowlist for outbound connector URLs; no user-supplied URLs in backend | `[✅/🟡/❌]` |

---

## 8. Penetration Testing Schedule

| Test Type | Frequency | Scope | Last Completed | Next Scheduled |
|---|---|---|---|---|
| External network pentest | Annual | Internet-facing APIs and endpoints | `[Date]` | `[Date]` |
| Application pentest (OWASP Top 10) | Annual + major release | Full application | `[Date]` | `[Date]` |
| RBAC / privilege escalation test | Semi-annual | All role and permission combinations | `[Date]` | `[Date]` |
| Connector / integration security test | Per new connector | Connector auth and data flow | `[Date]` | `[Date]` |
| Social engineering / phishing | Annual | All employees | `[Date]` | `[Date]` |

---

*Last updated: 2026-05-28 | Owner: `[Security Lead / DPO]` | Review cycle: Quarterly + before every enterprise customer go-live*
