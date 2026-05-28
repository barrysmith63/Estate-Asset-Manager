# Data & Reporting Specification
**Estate Asset Manager — Product & Engineering Deliverable 07**

---

## Executive Summary
This document specifies all required reports, their consumers, data sources, export formats, scheduled delivery jobs, retention/archival rules, and sample queries. Use it as the contract between the data engineering and product teams when building the reporting layer.

---

## 1. How to Complete This Template

1. **List all reports** by walking through each role in the RBAC matrix and asking: "What data does this role need to act on their responsibilities?"
2. **Define data sources** for each report: which tables, views, or connector data feeds the report.
3. **Specify export formats** required by each consumer (PDF for executives, CSV for analysts, JSON for integrations).
4. **Design scheduled jobs**: decide on frequency, delivery channel, and failure handling.
5. **Set retention rules**: align with legal hold periods and compliance requirements from Deliverable 09.
6. **Write or validate the sample query**: run against a staging dataset before shipping.

> **References**
> - dbt documentation (data modeling): https://docs.getdbt.com/
> - PostgreSQL query optimization: https://www.postgresql.org/docs/current/performance-tips.html
> - Search: `data reporting specification template enterprise SaaS product`

---

## 2. Report Registry

| Report ID | Report Name | Consumer Roles | Trigger | Export Formats | SLO |
|---|---|---|---|---|---|
| `RPT-01` | Asset Valuation Summary | Estate Mgr, Viewer, Admin | On-demand + scheduled | PDF, CSV, XLSX | SLO-03 (< 15 s) |
| `RPT-02` | Connector Sync Status | Admin, Integration Service | On-demand + real-time | JSON, CSV | SLO-03 |
| `RPT-03` | RBAC & User Access Audit | Auditor, Compliance, Admin | On-demand | CSV, JSON | SLO-03 |
| `RPT-04` | Workflow State Summary | Estate Mgr, Admin, Reviewer | On-demand + weekly | PDF, CSV | SLO-03 |
| `RPT-05` | Audit Event Log Export | Auditor, Compliance | On-demand | CSV, JSON | SLO-03 |
| `RPT-06` | Asset Change History | Any with Read | On-demand | CSV | SLO-03 |
| `RPT-07` | Scheduled Sync Health Digest | Admin | Daily (scheduled) | Email body + CSV attachment | N/A (async) |
| `[RPT-##]` | `[Report Name]` | `[Roles]` | `[Trigger]` | `[Formats]` | `[SLO]` |

---

## 3. Report Specifications

### RPT-01 — Asset Valuation Summary

| Field | Value |
|---|---|
| **Purpose** | Summarize current appraised value of all assets within a scope (estate, category, or tenant) |
| **Primary Consumer** | Estate Manager, Beneficiary Viewer, Admin |
| **Data Sources** | `assets`, `valuations`, `estates`, `categories` tables |
| **Filters Available** | Estate ID, asset category, valuation date range, asset status |
| **Grouping Options** | By estate; by category; by status |
| **Columns** | Asset ID; Asset Name; Category; Estate; Current Value; Currency; Valuation Method; Valuation Date; Status |
| **Totals Row** | Yes — sum of Current Value by currency |
| **Export Formats** | PDF (formatted); CSV (raw); XLSX (with pivot table) |
| **Max Rows Before Async** | 1 000 rows (< 1 k = sync; ≥ 1 k = async job with email delivery) |
| **Async Job Timeout** | 5 min |
| **Permissions** | Viewer: own estates, APPROVED only; Estate Mgr: assigned estates, all states; Admin: all |

#### Sample SQL Query

```sql
-- RPT-01: Asset Valuation Summary
-- Parameters: :estate_id (optional), :category (optional),
--             :date_from (optional), :date_to (optional), :tenant_id (required)
SELECT
    a.id                        AS asset_id,
    a.name                      AS asset_name,
    c.name                      AS category,
    e.name                      AS estate,
    v.amount                    AS current_value,
    v.currency                  AS currency,
    v.method                    AS valuation_method,
    v.effective_date            AS valuation_date,
    a.status                    AS status
FROM assets a
JOIN estates e       ON e.id = a.estate_id AND e.tenant_id = :tenant_id
JOIN categories c    ON c.id = a.category_id
JOIN LATERAL (
    SELECT amount, currency, method, effective_date
    FROM valuations
    WHERE asset_id = a.id
    ORDER BY effective_date DESC
    LIMIT 1
) v ON true
WHERE
    a.tenant_id = :tenant_id
    AND (:estate_id  IS NULL OR a.estate_id  = :estate_id)
    AND (:category   IS NULL OR c.name       = :category)
    AND (:date_from  IS NULL OR v.effective_date >= :date_from)
    AND (:date_to    IS NULL OR v.effective_date <= :date_to)
ORDER BY e.name, c.name, a.name;
```

---

### RPT-02 — Connector Sync Status

| Field | Value |
|---|---|
| **Purpose** | Show current sync health for all connectors: last sync time, status, error count |
| **Primary Consumer** | Admin, Integration Service dashboard |
| **Data Sources** | `sync_jobs`, `connectors`, `assets` tables |
| **Filters Available** | Connector type, status (SYNCED / STALE / FAILED), estate |
| **Columns** | Connector ID; Connector Type; Estate; Last Sync Time; Status; Error Count (last 24 h); Next Scheduled Sync |
| **Export Formats** | JSON (API response); CSV (manual export) |

#### Sample SQL Query

```sql
-- RPT-02: Connector Sync Status (last sync per connector per estate)
SELECT
    c.id                        AS connector_id,
    c.connector_type,
    e.name                      AS estate,
    MAX(sj.completed_at)        AS last_sync_time,
    CASE
        WHEN MAX(sj.completed_at) >= NOW() - INTERVAL '4 hours' THEN 'SYNCED'
        WHEN MAX(sj.completed_at) >= NOW() - INTERVAL '24 hours' THEN 'STALE'
        ELSE 'FAILED'
    END                         AS status,
    COUNT(*) FILTER (WHERE sj.status = 'FAILED'
                       AND sj.created_at >= NOW() - INTERVAL '24 hours')
                                AS error_count_24h,
    MIN(sj.scheduled_at) FILTER (WHERE sj.status = 'PENDING')
                                AS next_scheduled_sync
FROM connectors c
JOIN estates e   ON e.id = c.estate_id AND e.tenant_id = :tenant_id
LEFT JOIN sync_jobs sj ON sj.connector_id = c.id
GROUP BY c.id, c.connector_type, e.name
ORDER BY status DESC, last_sync_time ASC;
```

---

### RPT-05 — Audit Event Log Export

| Field | Value |
|---|---|
| **Purpose** | Export audit events for external compliance analysis or SIEM ingestion |
| **Primary Consumer** | Auditor, Compliance Officer |
| **Data Sources** | `audit_events` (append-only table) |
| **Filters Available** | Date range (required); actor user_id; action type; resource type; outcome |
| **Columns** | All fields from Deliverable 03 §5.1 schema |
| **Export Formats** | JSON (newline-delimited); CSV |
| **Max Date Range** | 90 days per export (larger ranges require Admin approval + async job) |
| **Permission** | Auditor (R07), Compliance (R08) only |

#### Sample SQL Query

```sql
-- RPT-05: Audit Event Log Export
SELECT
    ae.event_id,
    ae.timestamp,
    ae.tenant_id,
    ae.actor_user_id,
    ae.actor_role,
    ae.actor_ip,
    ae.action,
    ae.resource_type,
    ae.resource_id,
    ae.outcome,
    ae.changes_before,
    ae.changes_after,
    ae.request_id
FROM audit_events ae
WHERE
    ae.tenant_id = :tenant_id
    AND ae.timestamp BETWEEN :date_from AND :date_to
    AND (:actor_id     IS NULL OR ae.actor_user_id = :actor_id)
    AND (:action_type  IS NULL OR ae.action        = :action_type)
    AND (:resource     IS NULL OR ae.resource_type = :resource)
ORDER BY ae.timestamp ASC;
```

---

## 4. Scheduled Jobs

| Job ID | Report | Schedule (cron) | Delivery Channel | Recipients | Failure Behavior |
|---|---|---|---|---|---|
| `JOB-01` | RPT-07 Sync Health Digest | `0 7 * * *` (07:00 daily) | Email + Slack webhook | Tenant Admins | Retry 2×; alert on-call after 3rd failure |
| `JOB-02` | RPT-01 Weekly Valuation | `0 8 * * 1` (08:00 Monday) | Email (PDF attachment) | Estate Managers (per tenant config) | Retry 2×; log failure; no alert |
| `JOB-03` | RPT-04 Workflow Summary | `0 9 * * 5` (09:00 Friday) | Email | Estate Managers, Reviewers | Retry 1×; log failure |
| `JOB-04` | Audit log archival | `0 2 1 * *` (02:00, 1st of month) | S3 cold storage | N/A — automated | Alert on failure; manual rerun documented |
| `[JOB-##]` | `[Report]` | `[cron]` | `[Channel]` | `[Recipients]` | `[Failure behavior]` |

---

## 5. Data Retention & Archival Rules

| Data Type | Hot Storage | Warm Archive | Cold Archive | Deletion |
|---|---|---|---|---|
| Asset records (active) | Indefinite | N/A | N/A | On tenant offboarding (90-day grace) |
| Asset records (archived) | 1 year | 6 years cold (S3 Glacier) | N/A | After 7-year retention period |
| Audit events (standard) | 1 year | 6 years cold | N/A | After 7-year retention period |
| Audit events (critical) | 1 year | 9 years cold | N/A | After 10-year retention period |
| Sync job logs | 90 days | N/A | N/A | Auto-purge after 90 days |
| Report export files | 7 days (download link) | N/A | N/A | Auto-delete after 7 days |
| Legal hold assets | Indefinite (while held) | N/A | N/A | Only after hold released + 7 years |

---

## 6. New Report Template

```markdown
### RPT-XX — [Report Name]

| Field | Value |
|---|---|
| **Purpose** | [What decision does this report support?] |
| **Primary Consumer** | [Role(s)] |
| **Data Sources** | [Tables / views / connector data] |
| **Filters Available** | [List of filter parameters] |
| **Columns** | [Column names and descriptions] |
| **Export Formats** | [PDF / CSV / XLSX / JSON] |
| **Max Rows Before Async** | [Row count threshold] |
| **Permissions** | [Which roles can access; any row-level scoping] |

#### Sample SQL Query
[SQL here]
```

---

*Last updated: 2026-05-28 | Owner: `[Data Engineering Lead]` | Review cycle: Each reporting sprint*
