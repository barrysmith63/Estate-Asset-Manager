# Gap Analysis — Complete-plan.md vs. Estate Asset Manager Baseline
**Estate Asset Manager — Product & Engineering Deliverable 05**

---

## Executive Summary
This document maps every feature described in Complete-plan.md against the Estate Asset Manager baseline, identifies coverage gaps, assesses risk, and recommends mitigations. Use it to drive sprint prioritization and ensure no planned capability is accidentally dropped.

---

## 1. How to Complete This Template

1. **List all features from Complete-plan.md** in column "Planned Feature." Use the epic/feature hierarchy from the backlog (Deliverable 06) as a reference.
2. **Assess baseline coverage**: review the current Estate Asset Manager codebase, API docs, or prototype against each feature. Mark coverage as Full / Partial / None.
3. **Score risk**: consider likelihood (L) and impact (I) on a 1–3 scale. Risk = L × I (max 9).
4. **Assign mitigation**: for each gap, decide — build, buy, defer, or accept risk.
5. **Link to backlog**: every gap with a mitigation of "build" must have a corresponding epic in Deliverable 06.
6. **Review with stakeholders**: walk through high-risk gaps (score ≥ 6) before finalizing the MVP scope.

> **References**
> - MoSCoW prioritization: https://en.wikipedia.org/wiki/MoSCoW_method
> - Lean product gap analysis: search `feature gap analysis template product management site:productboard.com`

---

## 2. Feature Coverage Summary

| Coverage Level | Count | % of Total |
|---|---|---|
| Full — baseline already covers | `[#]` | `[%]` |
| Partial — baseline covers core; gaps in edge cases | `[#]` | `[%]` |
| None — net-new capability required | `[#]` | `[%]` |
| **Total features assessed** | `[#]` | 100 % |

---

## 3. Detailed Gap Matrix

> **Coverage key**: ✅ Full | 🟡 Partial | ❌ None
> **Risk score** = Likelihood (1–3) × Impact (1–3)

### 3.1 Asset Lifecycle Management

| Feature (from Complete-plan.md) | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Create / edit asset records (CRUD) | ✅ Full | None | — | — | — | — | — |
| Multi-state workflow (Draft → Review → Approved) | 🟡 Partial | Baseline has Draft/Active; missing Review state and approval routing | 3 | 3 | **9** | Build: add state machine and reviewer role | EP-01 |
| Legal hold / freeze | ❌ None | No freeze mechanism in baseline | 2 | 3 | **6** | Build: compliance role + hold flag + audit log | EP-06 |
| Soft delete / archive with retention | 🟡 Partial | Delete exists but no retention policy or recovery UI | 2 | 2 | 4 | Build: add ARCHIVED state, recovery admin UI | EP-01 |
| Bulk edit (≤ 500 records) | ❌ None | No bulk operations in baseline | 2 | 2 | 4 | Build: batch PATCH endpoint + UI | EP-04 |
| Asset version history / audit trail | 🟡 Partial | Basic change log exists; not queryable or exportable | 2 | 3 | **6** | Build: structured event log per asset | EP-07 |

### 3.2 Connector Integrations

| Feature | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Accounting connector (OAuth 2.0 sync) | ❌ None | No external sync in baseline | 3 | 3 | **9** | Build: see Contract A (Deliverable 02) | EP-03 |
| IoT sensor data ingestion | ❌ None | No IoT layer in baseline | 2 | 2 | 4 | Build: MQTT subscriber + telemetry store | EP-03 |
| Identity provider (OIDC / SSO) | 🟡 Partial | Baseline has local auth; no OIDC/SSO | 3 | 3 | **9** | Build: OIDC connector; integrate with IdP | EP-05 |
| Webhook outbound notifications | ❌ None | No outbound webhooks in baseline | 2 | 2 | 4 | Build: webhook registry + delivery queue | EP-03 |
| Connector health dashboard | ❌ None | No observability for connectors | 2 | 2 | 4 | Build: sync status per connector + alerting | EP-08 |

### 3.3 RBAC & Access Control

| Feature | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Role-based access control (7 roles) | 🟡 Partial | Baseline has Admin/User; missing Reviewer, Auditor, Compliance, Integration | 3 | 3 | **9** | Build: full RBAC per Deliverable 03 | EP-05 |
| Resource-level permissions | ❌ None | Baseline is course-grained (all-or-nothing) | 3 | 3 | **9** | Build: attribute-based access checks on every endpoint | EP-05 |
| Tenant isolation | 🟡 Partial | Baseline has tenant_id but no enforcement on all queries | 3 | 3 | **9** | Build: middleware tenant scoping + integration tests | EP-05 |
| Audit log (immutable, exportable) | ❌ None | No audit log in baseline | 2 | 3 | **6** | Build: append-only event store; see §5.2 Deliverable 03 | EP-07 |

### 3.4 Reporting & Data

| Feature | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Asset valuation summary report | 🟡 Partial | Baseline exports CSV; no filtering or grouping | 2 | 2 | 4 | Build: parameterized report engine | EP-06 |
| Connector sync status report | ❌ None | No sync visibility | 2 | 2 | 4 | Build: sync health report | EP-06 |
| Scheduled report delivery (email/export) | ❌ None | No scheduled jobs in baseline | 2 | 2 | 4 | Build: job scheduler + email delivery | EP-06 |
| Data retention / archival policy enforcement | ❌ None | No archival automation | 1 | 2 | 2 | Build: retention job (post-MVP) | EP-09 |

### 3.5 Security & Compliance

| Feature | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Encryption at rest (AES-256) | ✅ Full | Cloud provider default encryption enabled | — | — | — | — | — |
| TLS 1.2+ in transit | ✅ Full | Already enforced by load balancer | — | — | — | — | — |
| PII data classification & masking | ❌ None | No data classification layer in baseline | 2 | 3 | **6** | Build: field-level tagging + masking for exports | EP-07 |
| SOC 2 Type II readiness checklist | ❌ None | Baseline not assessed for SOC 2 | 2 | 3 | **6** | Process: begin audit evidence collection; see Deliverable 09 | EP-09 |
| MFA enforcement | 🟡 Partial | Baseline supports MFA opt-in; not enforceable by tenant | 2 | 3 | **6** | Build: tenant-level MFA policy | EP-05 |

### 3.6 UX & Frontend

| Feature | Baseline Coverage | Gap Description | Likelihood | Impact | Risk Score | Mitigation | Backlog Epic |
|---|---|---|---|---|---|---|---|
| Mobile-responsive asset views | 🟡 Partial | Desktop-first baseline; breakpoints incomplete | 2 | 2 | 4 | Build: mobile-first refactor; see Deliverable 10 | EP-04 |
| Bulk edit UI with inline validation | ❌ None | No bulk edit UI | 2 | 2 | 4 | Build: multi-select + inline errors | EP-04 |
| Accessibility (WCAG 2.1 AA) | ❌ None | Baseline not audited | 2 | 2 | 4 | Build: accessibility audit + remediation | EP-04 |
| Onboarding / empty-state guidance | ❌ None | No onboarding flow in baseline | 1 | 1 | 1 | Build: post-MVP onboarding wizard | EP-10 |

---

## 4. Risk Summary

| Risk Score | Count | Example Gaps |
|---|---|---|
| 9 (Critical) | 6 | State machine, OIDC/SSO, RBAC roles, resource-level permissions, tenant isolation, accounting connector |
| 6 (High) | 5 | Legal hold, asset version history, audit log, PII masking, MFA enforcement, SOC 2 readiness |
| 4 (Medium) | 9 | Bulk edit, webhook outbound, soft delete retention, IoT connector, mobile-responsive |
| 2–1 (Low) | 3 | Data retention automation, onboarding wizard |

---

## 5. Mitigation Recommendations

| Priority | Gap | Recommended Action | Owner | Target Sprint |
|---|---|---|---|---|
| P0 | Multi-state workflow | Build state machine (EP-01) | Backend Eng | Sprint 1–2 |
| P0 | RBAC + resource permissions | Build full RBAC (EP-05) | Security Eng | Sprint 1–2 |
| P0 | Tenant isolation enforcement | Add middleware + integration tests | Backend Eng | Sprint 1 |
| P0 | OIDC / SSO integration | Build IdP connector (EP-05) | Security Eng | Sprint 2–3 |
| P0 | Accounting connector | Build OAuth sync (EP-03) | Integrations | Sprint 3–4 |
| P1 | Audit log (immutable) | Build append-only event store (EP-07) | Backend Eng | Sprint 2–3 |
| P1 | Legal hold | Build freeze mechanism (EP-06) | Backend Eng | Sprint 4 |
| P1 | MFA enforcement | Add tenant MFA policy | Security Eng | Sprint 3 |
| P2 | PII masking | Field-level tagging (EP-07) | Data Eng | Sprint 5 |
| P2 | Bulk edit UI | Multi-select UI + batch API (EP-04) | Frontend Eng | Sprint 5–6 |
| P3 | Onboarding wizard | Post-MVP (EP-10) | Product / Frontend | Post-MVP |

---

## 6. Blank Template Row

```markdown
| [Feature from plan] | [✅/🟡/❌] | [Gap description] | [1–3] | [1–3] | [L×I] | [Build/Buy/Defer/Accept] | [EP-##] |
```

---

*Last updated: 2026-05-28 | Owner: `[Product Manager]` | Review cycle: Before each sprint planning*
