# Feature Priority Backlog & MVP Roadmap
**Estate Asset Manager — Product & Engineering Deliverable 06**

---

## Executive Summary
This document organizes all planned capabilities into a prioritized backlog of epics, features, and user stories, each with acceptance criteria, dependencies, and rough estimates. An 8-week MVP roadmap and a prioritization rubric are included.

---

## 1. How to Complete This Template

1. **Review the gap analysis** (Deliverable 05) — every P0/P1 gap must map to an epic here.
2. **Write user stories** in the "As a [role], I want [capability], so that [value]" format.
3. **Define acceptance criteria**: 3–5 testable statements per story (Given/When/Then or checklist).
4. **Estimate story points**: use a Fibonacci scale (1, 2, 3, 5, 8, 13). Anything > 8 should be split.
5. **Mark dependencies**: if Story B cannot start before Story A is merged, note `depends: [story-id]`.
6. **Assign to MVP or post-MVP**: use the prioritization rubric in §2 before assigning.

> **References**
> - INVEST criteria for user stories: https://agilealliance.org/glossary/invest/
> - Shape Up — Ryan Singer: https://basecamp.com/shapeup
> - Search: `product backlog template epics user stories acceptance criteria site:atlassian.com`

---

## 2. Prioritization Rubric

Score each feature 1–5 on each dimension. Features with total score ≥ 14 are MVP candidates.

| Dimension | 1 (Low) | 3 (Medium) | 5 (High) |
|---|---|---|---|
| **User Value** | Nice-to-have convenience | Improves existing flow | Blocks core user job |
| **Business Value** | Low revenue / retention impact | Moderate differentiation | Required for enterprise sales |
| **Urgency** | Can wait 6+ months | Needed in next quarter | Blocking current customers |
| **Effort (inverted)** | > 13 SP (hard) | 5–8 SP (medium) | 1–3 SP (easy) |
| **Risk (inverted)** | High unknowns / dependencies | Some unknowns | Well-understood |

**Score = User Value + Business Value + Urgency + Effort(inv) + Risk(inv)**

---

## 3. Epic Registry

| Epic ID | Epic Name | Description | Priority | Estimated SP | Gap Ref |
|---|---|---|---|---|---|
| EP-01 | Asset Lifecycle State Machine | Full workflow: Draft → Review → Approved → Archived | MVP | 21 | §3.1 |
| EP-02 | Asset Record Management | Core CRUD, validation, attachments, version history | MVP | 13 | §3.1 |
| EP-03 | Connector Integrations | Accounting, IoT, webhook outbound | MVP | 34 | §3.2 |
| EP-04 | Frontend UX & Bulk Operations | Bulk edit, inline validation, mobile, accessibility | MVP | 21 | §3.6 |
| EP-05 | RBAC & Identity | Full RBAC, OIDC/SSO, tenant isolation, MFA policy | MVP | 34 | §3.3 |
| EP-06 | Reporting & Data Export | Reports, filters, export formats, scheduled delivery | MVP | 21 | §3.4 |
| EP-07 | Audit Log & Compliance Data | Immutable audit log, PII tagging, export for auditors | MVP | 21 | §3.3, §3.5 |
| EP-08 | Monitoring & Observability | Dashboards, SLO alerting, connector health | MVP | 13 | §3.2 |
| EP-09 | Security & Compliance Hardening | SOC 2 evidence, data retention, encryption review | Post-MVP | 13 | §3.5 |
| EP-10 | Onboarding & Admin UX | Onboarding wizard, tenant setup, empty states | Post-MVP | 8 | §3.6 |
| `[EP-##]` | `[Name]` | `[Description]` | `[MVP/Post]` | `[SP]` | `[Gap]` |

---

## 4. Stories by Epic

### EP-01 — Asset Lifecycle State Machine

| Story ID | User Story | Acceptance Criteria | SP | Depends On | Priority |
|---|---|---|---|---|---|
| EP01-S01 | As an Editor, I want to submit an asset for review so that a Reviewer can approve it before it goes live | 1. Submit button appears when all required fields are valid; 2. Asset transitions to PENDING_REVIEW; 3. Reviewer receives in-app notification; 4. Submitter cannot edit after submission | 5 | EP05-S01 (RBAC) | MVP |
| EP01-S02 | As a Reviewer, I want to approve or reject a submitted asset with a comment so that the asset moves to the correct state | 1. Approve/Reject buttons visible only to Reviewers; 2. Rejection requires a comment; 3. Approved → APPROVED state; 4. Rejected → DRAFT with rejection comment | 5 | EP01-S01 | MVP |
| EP01-S03 | As an Admin, I want to archive an asset so that it is retained for audit but removed from active views | 1. Archive button visible to Admin only; 2. Asset transitions to ARCHIVED; 3. Archived assets appear only in Auditor/Admin views; 4. Audit log entry written | 3 | EP07-S01 (Audit log) | MVP |
| EP01-S04 | As a Compliance Officer, I want to apply and release a legal hold so that frozen assets cannot be modified or archived | 1. Hold applies to any non-ARCHIVED asset; 2. While held, all edit/archive actions return 409; 3. Release requires dual approval (if configured); 4. Hold/release events in audit log | 8 | EP05-S01, EP07-S01 | MVP |
| EP01-S05 | As a System, I want to retry failed connector syncs with exponential backoff so that transient failures self-heal | 1. Retry 3× at 5/10/20 s; 2. Final failure sets SYNC_FAILED state; 3. Admin alert fired; 4. Manual re-sync available | 5 | EP03-S01 (connectors) | MVP |

---

### EP-03 — Connector Integrations

| Story ID | User Story | Acceptance Criteria | SP | Depends On | Priority |
|---|---|---|---|---|---|
| EP03-S01 | As an Admin, I want to connect the accounting system via OAuth 2.0 so that asset valuations sync automatically | 1. OAuth flow completes in < 30 s; 2. Tokens stored encrypted; 3. Sync runs on schedule; 4. Sync status visible on asset detail | 13 | EP05-S01 (RBAC) | MVP |
| EP03-S02 | As the System, I want to receive IoT telemetry via MQTT so that asset condition data is always current | 1. MQTT subscriber connects at startup; 2. Telemetry stored per asset; 3. Stale sensor alert after 24 h offline | 8 | EP02-S01 (asset schema) | MVP |
| EP03-S03 | As an Admin, I want to register outbound webhooks so that external systems receive real-time asset events | 1. Webhook CRUD UI available to Admin; 2. HMAC signature on all deliveries; 3. Retry 3× on non-2xx; 4. Delivery log viewable | 8 | EP02-S01 | MVP |
| EP03-S04 | As an Admin, I want a connector health dashboard so that I can see sync status without reading logs | 1. Shows last sync time per connector; 2. Red/green status indicator; 3. Error details expandable; 4. Manual re-sync button | 5 | EP03-S01 | MVP |

---

### EP-05 — RBAC & Identity

| Story ID | User Story | Acceptance Criteria | SP | Depends On | Priority |
|---|---|---|---|---|---|
| EP05-S01 | As a Tenant Admin, I want to assign roles to users so that access is correctly scoped | 1. Role assignment UI lists all 7 core roles; 2. Admin cannot assign role above their own; 3. Role change triggers audit log event; 4. Changes take effect on next request (< 5 s propagation) | 8 | — | MVP |
| EP05-S02 | As an Enterprise Customer, I want to log in via SSO (OIDC) so that I don't need a separate password | 1. OIDC flow works with Azure AD, Okta, and Auth0; 2. IdP groups map to EAM roles; 3. Unmapped groups default to Viewer; 4. Session lasts 8 h (configurable) | 13 | EP05-S01 | MVP |
| EP05-S03 | As a Tenant Admin, I want to enforce MFA for all users so that my tenant meets security policy | 1. MFA enforcement toggleable per tenant; 2. Users without MFA are redirected to setup on login; 3. MFA bypass requires Admin override (audit logged) | 5 | EP05-S02 | MVP |
| EP05-S04 | As the System, I want every API endpoint to enforce tenant scoping so that cross-tenant data access is impossible | 1. All DB queries include tenant_id filter; 2. Integration tests prove no cross-tenant leak; 3. Penetration test scenario passes | 8 | EP05-S01 | MVP |

---

### EP-06 — Reporting & Data Export

| Story ID | User Story | Acceptance Criteria | SP | Depends On | Priority |
|---|---|---|---|---|---|
| EP06-S01 | As an Estate Manager, I want to generate an asset valuation summary report so that I can share it with beneficiaries | 1. Report filterable by estate, category, date range; 2. Exports to PDF and CSV; 3. Generates in < 15 s for < 1 k rows; 4. Linked to SLO-03 | 8 | EP02-S01 | MVP |
| EP06-S02 | As an Admin, I want to schedule weekly reports to be emailed so that stakeholders stay informed automatically | 1. Scheduler UI: frequency, recipients, report type; 2. Email delivers within 5 min of scheduled time; 3. Failure triggers retry + admin alert | 8 | EP06-S01 | MVP |
| EP06-S03 | As an Auditor, I want to export the full audit log in JSON and CSV so that I can run external compliance analysis | 1. Export scoped to date range and event type; 2. Download starts within 10 s; 3. Includes all fields from §5.1 of Deliverable 03 | 5 | EP07-S01 | MVP |

---

### EP-07 — Audit Log & Compliance Data

| Story ID | User Story | Acceptance Criteria | SP | Depends On | Priority |
|---|---|---|---|---|---|
| EP07-S01 | As the System, I want every RBAC-sensitive action to write an immutable audit log entry so that all changes are traceable | 1. All events in Deliverable 03 §5.2 produce log entries; 2. Log is append-only; 3. Entries include actor, timestamp, before/after state; 4. Shipped to SIEM within 60 s | 13 | EP05-S01 | MVP |
| EP07-S02 | As an Auditor, I want to search and filter audit logs in the UI so that I can investigate specific events | 1. Filter by actor, action, resource, date range; 2. Results paginated (50/page); 3. Export to CSV | 5 | EP07-S01 | MVP |

---

## 5. 8-Week MVP Roadmap

| Week | Sprint | Epics In Progress | Key Deliverables | Exit Criteria |
|---|---|---|---|---|
| 1–2 | Sprint 1 | EP-05, EP-02 | RBAC roles + tenant scoping enforced; core asset CRUD hardened | All role checks pass integration tests; no cross-tenant leak |
| 3–4 | Sprint 2 | EP-01, EP-07, EP-05 | State machine (Draft→Review→Approved→Archived); Audit log v1; OIDC/SSO | State transitions tested; audit log writing to store; SSO login works |
| 5–6 | Sprint 3 | EP-03, EP-04 | Accounting connector OAuth sync; bulk edit UI; mobile breakpoints | Sync runs on schedule; bulk edit < 10 s for 500 records |
| 7 | Sprint 4 | EP-06, EP-08, EP-01 | Reports (valuation summary + scheduled delivery); Legal hold; Monitoring dashboards | Reports generate in < 15 s; SLO dashboards live; legal hold blocks edits |
| 8 | Sprint 5 | All | MVP hardening, performance testing, security review, UAT | All P0/P1 acceptance criteria pass; SLOs measured; no P1 open bugs |

---

## 6. Blank Story Template

```markdown
| [EP##-S##] | As a [role], I want [capability] so that [value] | 1. [AC1]; 2. [AC2]; 3. [AC3] | [SP] | [depends] | [MVP/Post-MVP] |
```

---

*Last updated: 2026-05-28 | Owner: `[Product Manager]` | Review cycle: Each sprint planning*
