# RBAC Matrix & Audit Logging Requirements
**Estate Asset Manager — Product & Engineering Deliverable 03**

---

## Executive Summary
This document defines every role in the Estate Asset Manager, the permissions each role holds at the resource level, and the audit logging requirements tied to sensitive RBAC actions. Use it as the source of truth for access-control implementation, security review, and compliance audits.

---

## 1. How to Complete This Template

1. **List all roles**: start with the roles below; add tenant-specific roles in §2.4.
2. **Enumerate all resources**: add every API resource, report type, and admin action to the resource registry (§3).
3. **Fill the permission matrix** (§4): mark each cell C / R / U / D / X / — and note any conditions (e.g., "own records only").
4. **Map RBAC actions to audit log events** (§5): every permission that can modify data or configuration must produce an audit log entry.
5. **Review with legal/compliance**: confirm that RBAC satisfies your regulatory framework (SOC 2, HIPAA, GDPR, CCPA as applicable).
6. **Version-control this file**: treat changes to the matrix as security-relevant commits requiring a security review sign-off.

> **References**
> - NIST SP 800-207 Zero Trust Architecture: https://csrc.nist.gov/publications/detail/sp/800-207/final
> - OWASP Access Control Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Access_Control_Cheat_Sheet.html
> - Search: `RBAC matrix template enterprise SaaS site:github.com`
> - Search: `audit logging RBAC SOC2 requirements checklist`

---

## 2. Role Definitions

### 2.1 Core Roles

| Role ID | Role Name | Description | Scope | Max Users per Tenant |
|---|---|---|---|---|
| `R01` | Super Admin | Full platform access; manages tenants and global config | Platform | 2–5 |
| `R02` | Tenant Admin | Full access within a single tenant; manages users and settings | Tenant | 1–10 |
| `R03` | Estate Manager | Manages all assets and workflows within assigned estates | Estate | Unlimited |
| `R04` | Editor | Creates and edits asset records; cannot approve or archive | Estate | Unlimited |
| `R05` | Reviewer | Reviews and approves submitted assets; cannot edit | Estate | Unlimited |
| `R06` | Viewer | Read-only access to approved assets and reports | Estate | Unlimited |
| `R07` | Auditor | Read-only access to all records including audit logs and archived items | Tenant | 1–5 |
| `R08` | Compliance Officer | Applies/releases legal holds; views all audit logs | Tenant | 1–5 |
| `R09` | Integration Service | Machine identity for connector sync jobs; no human login | System | Per connector |
| `[R##]` | `[Role Name]` | `[Description]` | `[Scope]` | `[Max]` |

### 2.2 Role Hierarchy

```
Super Admin (R01)
  └─ Tenant Admin (R02)
       ├─ Estate Manager (R03)
       │    ├─ Editor (R04)
       │    └─ Reviewer (R05)
       ├─ Viewer (R06)
       ├─ Auditor (R07)
       └─ Compliance Officer (R08)

Integration Service (R09) — lateral, no inheritance
```

### 2.3 Permission Key

| Symbol | Meaning |
|---|---|
| `C` | Create |
| `R` | Read |
| `U` | Update |
| `D` | Delete (soft) |
| `X` | Execute / Trigger |
| `*` | Conditional — see note column |
| `—` | No access |

### 2.4 Tenant Custom Roles (Template)

| Role ID | Role Name | Based On | Additional Permissions | Restrictions |
|---|---|---|---|---|
| `R10` | `[Custom Role]` | `[Base Role]` | `[Extra permissions]` | `[Denied permissions]` |

---

## 3. Resource Registry

| Resource ID | Resource | Description | Sensitivity |
|---|---|---|---|
| `RES-01` | Asset Record | Individual asset (property, vehicle, account, etc.) | High |
| `RES-02` | Asset Valuation | Appraisal and financial values | High |
| `RES-03` | Estate | Grouping of assets under one beneficiary/owner | High |
| `RES-04` | Document | Attached files (deeds, appraisals, insurance) | High |
| `RES-05` | Report | Generated analytics and exports | Medium |
| `RES-06` | Audit Log | Immutable event history | Critical |
| `RES-07` | User Account | Platform user record | High |
| `RES-08` | Role Assignment | User-to-role mapping | Critical |
| `RES-09` | Integration Config | Connector credentials and settings | Critical |
| `RES-10` | Legal Hold | Freeze on an asset or estate | Critical |
| `RES-11` | Notification | Alerts, reminders, workflow triggers | Low |
| `RES-12` | Tenant Settings | Tenant-level config, branding, SSO | Critical |
| `[RES-##]` | `[Resource]` | `[Description]` | `[Sensitivity]` |

---

## 4. RBAC Permission Matrix

> **Reading the matrix**: rows = resources, columns = roles. Cell contains permitted operations (C/R/U/D/X). `*` = see condition notes below the table.

| Resource | R01 Super Admin | R02 Tenant Admin | R03 Estate Mgr | R04 Editor | R05 Reviewer | R06 Viewer | R07 Auditor | R08 Compliance | R09 Integration |
|---|---|---|---|---|---|---|---|---|---|
| Asset Record (RES-01) | C R U D | C R U D | C R U D | C R U* | R* | R* | R | R | R U* |
| Asset Valuation (RES-02) | C R U D | C R U D | C R U D | C R U* | R* | R* | R | R | R U |
| Estate (RES-03) | C R U D | C R U D | R U* | — | R | R | R | R | R |
| Document (RES-04) | C R U D | C R U D | C R U D | C R U* | R | — | R | R | — |
| Report (RES-05) | C R U D X | C R U D X | C R X | R X* | R X* | R X* | R | R | R |
| Audit Log (RES-06) | R | R | — | — | — | — | R | R | — |
| User Account (RES-07) | C R U D | C R U D | R* | — | — | — | R | R | — |
| Role Assignment (RES-08) | C R U D | C R U D* | — | — | — | — | R | R | — |
| Integration Config (RES-09) | C R U D | C R U D | — | — | — | — | R | R | R* |
| Legal Hold (RES-10) | C R U D | R | — | — | — | — | R | C R U D | — |
| Notification (RES-11) | C R U D | C R U D | C R U D | R | R | R | R | R | C |
| Tenant Settings (RES-12) | C R U D | C R U D | — | — | — | — | R | R | — |

### 4.1 Condition Notes

| Code | Condition |
|---|---|
| `U* (Editor on Assets)` | Editor may update only assets in `DRAFT` state; cannot approve |
| `R* (Editor on Assets)` | Editor reads only assets within their assigned estates |
| `R* (Viewer on Assets)` | Viewer reads only `APPROVED` assets; cannot see `DRAFT` or `ARCHIVED` |
| `R* (Reviewer on Assets)` | Reviewer reads assets in `PENDING_REVIEW`; read-only on others |
| `R* (Estate Mgr on Users)` | Estate Manager may view but not modify user accounts |
| `C R U D* (Tenant Admin on Roles)` | Tenant Admin cannot assign roles above their own level |
| `R* (Integration on Assets)` | Integration Service reads asset metadata; updates only sync-status fields |
| `R* (Integration Config)` | Integration Service reads its own connector config; cannot modify |

---

## 5. Audit Logging Requirements

### 5.1 Audit Log Entry Schema

```json
{
  "event_id": "evt_uuid_v4",
  "timestamp": "2026-05-28T11:30:00.000Z",
  "tenant_id": "ten_abc123",
  "actor": {
    "user_id": "usr_xyz789",
    "role": "R03",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0 ..."
  },
  "action": "asset.approved",
  "resource": {
    "type": "asset",
    "id": "est_asset_9182",
    "estate_id": "est_001"
  },
  "outcome": "SUCCESS",
  "changes": {
    "before": { "state": "PENDING_REVIEW" },
    "after": { "state": "APPROVED" }
  },
  "metadata": {
    "request_id": "req_uuid",
    "session_id": "sess_uuid"
  }
}
```

### 5.2 Auditable Actions Matrix

| Action | RBAC Trigger | Audit Event Name | Log Level | Retention |
|---|---|---|---|---|
| User login | All roles | `auth.login.success` | INFO | 1 year |
| Failed login (×3) | All roles | `auth.login.failed` | WARN | 1 year |
| Role assignment | R01, R02 | `rbac.role.assigned` | WARN | 7 years |
| Role revocation | R01, R02 | `rbac.role.revoked` | WARN | 7 years |
| Asset created | R01–R04, R09 | `asset.created` | INFO | 7 years |
| Asset approved | R01–R03, R05 | `asset.approved` | INFO | 7 years |
| Asset archived | R01, R02 | `asset.archived` | WARN | 7 years |
| Asset deleted (soft) | R01, R02 | `asset.deleted` | WARN | 7 years |
| Legal hold applied | R01, R02, R08 | `hold.applied` | CRITICAL | 10 years |
| Legal hold released | R01, R02, R08 | `hold.released` | CRITICAL | 10 years |
| Integration config changed | R01, R02 | `integration.config.changed` | CRITICAL | 7 years |
| Data export / report | All with R | `report.exported` | INFO | 1 year |
| Bulk edit executed | R01–R04 | `asset.bulk_edited` | WARN | 7 years |
| Tenant settings changed | R01, R02 | `tenant.settings.changed` | CRITICAL | 7 years |
| `[Action]` | `[Roles]` | `[event.name]` | `[Level]` | `[Retention]` |

### 5.3 Audit Log Storage Requirements

| Requirement | Specification |
|---|---|
| Storage | Append-only, tamper-evident (e.g., WORM storage or cryptographic chaining) |
| Access | Read-only for Auditor (R07) and Compliance (R08); no role may delete |
| Encryption | AES-256 at rest; TLS 1.2+ in transit |
| Retention — standard events | 1 year hot, 6 years cold archive |
| Retention — critical events | 1 year hot, 9 years cold archive |
| Export | CSV/JSON on demand for Auditor/Compliance roles |
| Alerting | SIEM integration; alert on CRITICAL events within 60 s |

> **References**
> - OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
> - NIST SP 800-92 Guide to Computer Security Log Management: https://csrc.nist.gov/publications/detail/sp/800-92/final
> - Search: `audit log tamper-evident append-only cloud storage best practices`

---

## 6. RBAC Implementation Checklist

- [ ] All API endpoints enforce role check before processing request
- [ ] Role checks use server-side evaluation only (never trust client-supplied role claims)
- [ ] JWT claims include `roles` array; validated on every request
- [ ] Deny-by-default: unrecognized roles receive zero permissions
- [ ] Privilege escalation is blocked: users cannot assign roles ≥ their own level
- [ ] Audit log entries are written for every action in §5.2
- [ ] Audit logs are shipped to SIEM within 60 s of event
- [ ] RBAC matrix is reviewed and signed off each quarter
- [ ] Penetration test covers IDOR, privilege escalation, and horizontal access scenarios

---

*Last updated: 2026-05-28 | Owner: `[Security Engineering Lead]` | Review cycle: Quarterly + after any role change*
