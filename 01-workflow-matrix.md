# Workflow Matrix
**Estate Asset Manager — Product & Engineering Deliverable 01**

---

## Executive Summary
This document maps every user-initiated action in the Estate Asset Manager to its corresponding system states, valid transitions, error paths, retry logic, and SLA timeouts. Use it as the authoritative source when implementing state machines, designing UI feedback, and writing integration tests.

---

## 1. How to Complete This Template

1. **Identify all user actions** by walking through each feature epic in the backlog (Deliverable 06). List every action a user can take (create, edit, approve, export, sync, etc.).
2. **Map starting state → event → ending state** for each action. A state is a stable condition the system can be in; an event is what triggers a transition.
3. **Define error paths**: for each transition, decide what happens when the external call fails, times out, or returns invalid data. Document the fallback state.
4. **Set SLA timeouts**: agree with stakeholders on p95 latency budgets. Enter them in the `SLA Timeout` column and link to the relevant SLO in Deliverable 04.
5. **Validate completeness**: every state must have at least one exit path (including error). States with no exit are traps — flag them for review.
6. **Link to implementation**: add a `Ticket` column pointing to the relevant story in your backlog so the matrix stays in sync.

> **References**
> - UML State Machine notation: https://www.omg.org/spec/UML/
> - Martin Fowler — Patterns of Enterprise Application Architecture (State pattern)
> - Search: `"state machine" "workflow matrix" template site:martinfowler.com`

---

## 2. State Definitions

| State ID | State Name | Description | Allowed Roles |
|---|---|---|---|
| `S01` | `DRAFT` | Asset record created but not yet validated | Owner, Editor |
| `S02` | `PENDING_REVIEW` | Submitted for manager or compliance review | Reviewer, Admin |
| `S03` | `APPROVED` | Fully validated and live in the registry | All read roles |
| `S04` | `SYNCING` | Outbound sync to accounting/IoT connector in progress | System |
| `S05` | `SYNC_FAILED` | One or more connector calls failed; retries exhausted | Admin, System |
| `S06` | `ARCHIVED` | Soft-deleted; retained for audit | Admin, Auditor |
| `S07` | `LOCKED` | Frozen pending legal hold or compliance review | Compliance, Admin |
| `[S##]` | `[STATE_NAME]` | `[Description]` | `[Roles]` |

---

## 3. Workflow Transition Table

| Action | Actor Role | From State | To State | Trigger Event | Guard Condition | Error State | Retry Policy | SLA Timeout | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Create asset | Owner | — | `S01` DRAFT | `POST /assets` | Auth token valid | 400 Bad Request → client error | No retry | < 2 s p95 | Generates `asset_id` |
| Submit for review | Owner, Editor | `S01` | `S02` | `PATCH /assets/{id}/submit` | All required fields populated | `S01` + validation errors returned | No retry | < 1 s p95 | Triggers reviewer notification |
| Approve asset | Reviewer, Admin | `S02` | `S03` | `PATCH /assets/{id}/approve` | Reviewer ≠ submitter | `S02` + 403 Forbidden | No retry | < 1 s p95 | Audit log entry written |
| Reject asset | Reviewer, Admin | `S02` | `S01` | `PATCH /assets/{id}/reject` | Rejection reason provided | — | No retry | < 1 s p95 | Comment required |
| Trigger sync | System (scheduler) | `S03` | `S04` | Cron / webhook | Connector healthy | `S05` SYNC_FAILED | 3× exp backoff | < 30 s p95 | See §5 retry policy |
| Sync succeeds | System | `S04` | `S03` | Connector 200 OK | Payload checksum valid | `S05` | — | — | Timestamp updated |
| Sync fails (final) | System | `S04` | `S05` | 3rd retry exhausted | — | — | PagerDuty alert | — | Alert runbook §8 |
| Manual re-sync | Admin | `S05` | `S04` | `POST /assets/{id}/sync` | Connector healthy | `S05` | 3× exp backoff | < 30 s p95 | Resets retry counter |
| Archive asset | Admin | `S03` | `S06` | `DELETE /assets/{id}` (soft) | No active legal hold | `S03` + 409 Conflict | No retry | < 1 s p95 | Reversible by Admin |
| Apply legal hold | Compliance | `S03`, `S01` | `S07` | `POST /assets/{id}/hold` | Compliance role required | 403 Forbidden | No retry | < 1 s p95 | Audit entry mandatory |
| Release legal hold | Compliance, Admin | `S07` | `S03` | `DELETE /assets/{id}/hold` | Dual approval if configured | 403 Forbidden | No retry | < 1 s p95 | Returns to pre-hold state |
| Bulk edit | Editor, Admin | `S01`, `S03` | Same | `PATCH /assets/bulk` | ≤ 500 records per call | 422 Partial failure → report | No retry | < 10 s p95 | Partial success allowed |
| Export report | Any | Any | — (read-only) | `GET /reports/{type}` | Read permission on scope | 503 → retry | 2× retry | < 15 s p95 | Async job if > 1 k rows |
| `[Action]` | `[Role]` | `[From]` | `[To]` | `[Event]` | `[Guard]` | `[Error State]` | `[Retry]` | `[SLA]` | `[Notes]` |

---

## 4. State Transition Diagram (ASCII)

```
           ┌──────────────────────────────────────────────┐
           │                                              │
  [CREATE] │        [SUBMIT]        [APPROVE]            │
     ──────▶  DRAFT  ──────▶  PENDING_REVIEW  ──────▶  APPROVED
             │   ◀──────                        │   ◀──────────────────
             │  [REJECT]                        │ [SYNC triggers]
             │                                  ▼
             │                               SYNCING ──(success)──▶ APPROVED
             │                                  │
             │                            (fail × 3)
             │                                  ▼
             │                            SYNC_FAILED ──(manual re-sync)──▶ SYNCING
             │
     ──────────────────────────────── ARCHIVE ──▶ ARCHIVED
     ──────────────────────────────── HOLD    ──▶ LOCKED ──(release)──▶ APPROVED
```

---

## 5. Retry & Backoff Policy

| Scenario | Max Attempts | Initial Delay | Backoff Multiplier | Max Delay | Jitter |
|---|---|---|---|---|---|
| Connector sync (transient 5xx) | 3 | 5 s | 2× | 60 s | ±20 % |
| Report export (queue timeout) | 2 | 10 s | 1.5× | 30 s | ±10 % |
| Notification delivery | 5 | 2 s | 2× | 120 s | ±30 % |
| Webhook outbound | 3 | 3 s | 2× | 30 s | ±15 % |

> **Reference**: AWS Architecture Blog — Exponential Backoff and Jitter: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/

---

## 6. Error Path Summary

| HTTP Status | Meaning | System Behavior | User Message |
|---|---|---|---|
| 400 | Bad request / validation failure | Return field-level errors; stay in current state | "Please correct the highlighted fields." |
| 401 | Unauthenticated | Redirect to login; preserve deep link | "Your session has expired. Please sign in." |
| 403 | Forbidden (RBAC) | Log attempt; return 403 | "You don't have permission to perform this action." |
| 404 | Resource not found | Return 404; log if unexpected | "This record no longer exists." |
| 409 | Conflict (e.g., legal hold) | Explain conflict; do not mutate state | "This record is locked. Contact compliance." |
| 422 | Partial bulk failure | Return per-record result array | "X of Y records updated. See details." |
| 429 | Rate limited | Respect `Retry-After` header; queue | "System is busy. Retrying automatically." |
| 500/503 | Server/connector error | Retry policy §5; alert if exhausted | "A system error occurred. Our team has been notified." |

---

## 7. SLA Timeout Thresholds

| Operation | p50 Target | p95 Target | p99 Target | SLO Reference |
|---|---|---|---|---|
| Asset CRUD (single record) | < 300 ms | < 2 s | < 5 s | SLO-01 |
| Sync job (per connector) | < 10 s | < 30 s | < 60 s | SLO-02 |
| Report generation (< 1 k rows) | < 3 s | < 15 s | < 30 s | SLO-03 |
| Bulk edit (≤ 500 records) | < 3 s | < 10 s | < 20 s | SLO-01 |

---

## 8. Blank Template Row

Copy and paste for each new action:

```markdown
| [Action Name] | [Role] | [From State] | [To State] | [Trigger Event / API endpoint] | [Guard Condition] | [Error State + code] | [Retry policy or "No retry"] | [SLA timeout] | [Notes] |
```

---

*Last updated: 2026-05-28 | Owner: `[Engineering Lead]` | Review cycle: Each sprint*
