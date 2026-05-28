# Monitoring, Dashboards & Runbooks
**Estate Asset Manager — Product & Engineering Deliverable 08**

---

## Executive Summary
This document defines the key metrics, dashboard panels, alert definitions, incident response playbooks, and escalation matrix for the Estate Asset Manager in production. Two fully detailed runbooks are included: one for a failed integration sync and one for an SLA breach.

---

## 1. How to Complete This Template

1. **Instrument first**: ensure all metrics below are emitted by the application before configuring alerts.
2. **Set baselines**: run in production for 2 weeks before tightening alert thresholds.
3. **Assign owners**: every alert must have a primary and secondary on-call owner.
4. **Test runbooks**: run a game day for each P1 runbook every quarter.
5. **Link dashboards**: paste the Grafana/DataDog dashboard URL next to each panel definition.
6. **Review after every incident**: update the relevant runbook within 48 h of post-mortem completion.

> **References**
> - Google SRE Workbook — Alerting on SLOs: https://sre.google/workbook/alerting-on-slos/
> - PagerDuty Incident Response Guide: https://response.pagerduty.com/
> - Prometheus alerting rules: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
> - Search: `incident runbook template SRE on-call playbook site:github.com`

---

## 2. Key Metrics

### 2.1 Application Metrics

| Metric Name | Type | Labels | Description | Alert Threshold |
|---|---|---|---|---|
| `http_requests_total` | Counter | `path`, `method`, `status`, `tenant_id` | Total HTTP requests | — (derived) |
| `http_request_duration_seconds` | Histogram | `path`, `method`, `status` | Request latency | p95 > 2 s = P2; p99 > 5 s = P1 |
| `asset_state_transitions_total` | Counter | `from_state`, `to_state`, `tenant_id` | State machine transitions | — |
| `asset_sync_failures_total` | Counter | `connector_type`, `error_code`, `tenant_id` | Sync failures | > 5 / 5 min = P2 |
| `asset_sync_duration_seconds` | Histogram | `connector_type` | Duration of sync job | p95 > 30 s = P2 |
| `eam_assets_stale_pct` | Gauge | `tenant_id` | % assets unsynced > 4 h | > 1 % = P3; > 5 % = P2 |
| `eam_error_budget_remaining_pct` | Gauge | `slo_id` | Error budget remaining | < 25 % = P3; = 0 = P2 |
| `sync_queue_depth` | Gauge | `connector_type` | Pending sync jobs | > 500 = P2 |
| `report_job_duration_seconds` | Histogram | `report_type` | Report generation time | p95 > 15 s = P2 |
| `audit_log_lag_seconds` | Gauge | — | Delay from event to SIEM delivery | > 60 s = P1 |
| `[metric_name]` | `[type]` | `[labels]` | `[description]` | `[threshold]` |

### 2.2 Infrastructure Metrics

| Metric | Source | Alert Threshold |
|---|---|---|
| DB connection pool saturation | PostgreSQL / PgBouncer | > 80 % = P2; > 95 % = P1 |
| DB replication lag | PostgreSQL `pg_replication_slots` | > 10 s = P2; > 60 s = P1 |
| API pod CPU | Kubernetes | > 80 % sustained 5 min = P2 |
| API pod memory | Kubernetes | > 85 % = P2; OOM kill = P1 |
| Sync worker pod restarts | Kubernetes | > 2 restarts / 10 min = P2 |
| Message queue depth (Redis / SQS) | Redis / SQS | > 10 000 messages = P2 |

---

## 3. Dashboard Definitions

| Dashboard Name | Tool | URL | Primary Audience | Panels |
|---|---|---|---|---|
| Asset API Health | Grafana | `[paste URL]` | On-call, Engineering | Request rate; error rate; p50/p95/p99 latency; SLO burn rate |
| Connector Sync Health | Grafana | `[paste URL]` | Admin, On-call | Stale asset %; sync queue depth; sync duration p95; failure rate by connector |
| SLO Overview | Grafana | `[paste URL]` | Engineering, Product | All 3 SLOs — current value vs. target; error budget remaining; burn rate 1h/6h/24h |
| RBAC & Auth Events | Grafana | `[paste URL]` | Security, On-call | Login success/failure rate; role changes; failed permission checks; audit lag |
| Infrastructure | Grafana | `[paste URL]` | DevOps, On-call | DB pool; replication lag; pod CPU/memory; queue depth |
| Report Job Performance | Grafana | `[paste URL]` | Data Engineering | Report p95 duration; async job queue depth; failure rate |

---

## 4. Alert Definitions (Prometheus/Alertmanager)

```yaml
# alert-rules.yaml
groups:
  - name: eam.slo
    rules:
      - alert: SLO01_FastBurn
        expr: |
          sum(rate(http_requests_total{path=~"/assets.*", status=~"5.."}[1h]))
          / sum(rate(http_requests_total{path=~"/assets.*"}[1h])) > 0.144
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "SLO-01 fast burn: error rate exceeding 14.4× budget burn rate"
          runbook_url: "https://runbooks.internal/SLO-01-FastBurn"

      - alert: SLO02_HighStaleness
        expr: eam_assets_stale_pct > 5
        for: 15m
        labels:
          severity: critical
          team: integrations
        annotations:
          summary: "SLO-02: > 5% of assets stale for > 15 min"
          runbook_url: "https://runbooks.internal/SLO-02-HighStaleness"

      - alert: SLO03_P95LatencyBreach
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket{path=~"/reports/.*"}[10m]))
            by (le)) > 15
        for: 10m
        labels:
          severity: warning
          team: data
        annotations:
          summary: "SLO-03: report p95 latency > 15s"
          runbook_url: "https://runbooks.internal/SLO-03-Latency"

  - name: eam.integrations
    rules:
      - alert: ConnectorSyncFailureSpike
        expr: increase(asset_sync_failures_total[5m]) > 5
        for: 0m
        labels:
          severity: warning
          team: integrations
        annotations:
          summary: "Connector sync failure spike: > 5 failures in 5 min"
          runbook_url: "https://runbooks.internal/INC-02"

      - alert: AuditLogLagHigh
        expr: audit_log_lag_seconds > 60
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Audit log delivery to SIEM lagging > 60 s"
          runbook_url: "https://runbooks.internal/INC-04"
```

---

## 5. Escalation Matrix

| Severity | Response Time | Initial Action | Escalation Path | Communication Channel |
|---|---|---|---|---|
| P1 — Critical | < 15 min | On-call engineer pages immediately | Eng Lead → VP Eng (if > 30 min unresolved) | PagerDuty + #incidents Slack |
| P2 — High | < 1 h | On-call engineer creates ticket; investigates | Eng Lead (if > 2 h unresolved) | Slack #alerts + Jira ticket |
| P3 — Medium | < 4 h business hours | Ticket created; scheduled in next sprint | Product + Eng Lead review | Jira + weekly SLO review |
| P4 — Low | Next sprint | Backlog item | — | Jira |

### On-Call Rotation

| Role | Owner | Backup | Contact |
|---|---|---|---|
| Backend On-Call | `[Name]` | `[Name]` | PagerDuty schedule: `[link]` |
| Integrations On-Call | `[Name]` | `[Name]` | PagerDuty schedule: `[link]` |
| Security On-Call | `[Name]` | `[Name]` | PagerDuty schedule: `[link]` |
| Incident Commander | `[Name — Eng Lead or Sr Engineer]` | `[Name]` | Auto-assigned for P1 |

---

## 6. Runbook — INC-02: Failed Integration Sync

```
RUNBOOK: INC-02 — Failed Integration / Connector Sync
SEVERITY: P2 (escalates to P1 if > 50% assets stale or data loss risk)
ALERT: ConnectorSyncFailureSpike OR SLO02_HighStaleness
OWNER: Integrations On-Call

═══════════════════════════════════════════════
STEP 1 — ASSESS (< 5 min)
═══════════════════════════════════════════════
1a. Open dashboard: "Connector Sync Health"
    • Which connector(s) are failing? (accounting / IoT / webhook)
    • How many assets are affected?
    • What error code is most frequent?

1b. Pull recent error logs:
    kubectl logs deployment/sync-worker --tail=200 | grep -E "ERROR|WARN"

1c. Identify failure mode:
    • HTTP 401 → token expired or revoked (go to Step 2a)
    • HTTP 429 → rate limited (go to Step 2b)
    • HTTP 5xx → provider outage (go to Step 2c)
    • Network timeout → infra issue (go to Step 2d)
    • Schema/parsing error → data issue (go to Step 2e)

═══════════════════════════════════════════════
STEP 2 — CONTAIN & REMEDIATE
═══════════════════════════════════════════════
2a. TOKEN EXPIRED / REVOKED
    • Check token TTL: SELECT expires_at FROM connector_tokens WHERE connector_type='accounting';
    • If expired: trigger re-auth flow
      curl -X POST https://api.internal/connectors/accounting/reauth
    • If revoked: alert Tenant Admin; pause connector until re-authorized
      UPDATE connectors SET status='PAUSED' WHERE connector_type='accounting' AND tenant_id=:id;

2b. RATE LIMITED (429)
    • Check Retry-After header in logs
    • Pause sync scheduler for affected connector: duration = Retry-After + 30 s
    • Do NOT manually re-trigger — queue will resume automatically

2c. PROVIDER OUTAGE (5xx)
    • Check provider status page (bookmark in team wiki)
    • If confirmed outage: set connector status to DEGRADED; suppress alerts for 2 h
      UPDATE connectors SET status='DEGRADED', degraded_reason='provider_outage' ...;
    • Post in #incidents: "Accounting provider outage confirmed. Sync paused. Will retry at HH:MM."

2d. NETWORK / INFRA ISSUE
    • Check pod networking: kubectl exec -it sync-worker-pod -- curl https://api.[provider].com/health
    • Check DNS: kubectl exec -it sync-worker-pod -- nslookup api.[provider].com
    • If pod networking broken: kubectl rollout restart deployment/sync-worker

2e. SCHEMA / PARSING ERROR
    • Get failing payload: SELECT raw_response FROM sync_jobs WHERE status='FAILED' ORDER BY created_at DESC LIMIT 5;
    • Check if provider changed their API (compare with Contract A, Deliverable 02)
    • If schema changed: disable sync; file P1 ticket for connector update; notify Admin

═══════════════════════════════════════════════
STEP 3 — VERIFY RECOVERY (< 30 min after fix)
═══════════════════════════════════════════════
• Confirm sync queue clears: SELECT COUNT(*) FROM sync_jobs WHERE status='PENDING';
• Confirm stale asset % drops below 1%: (use RPT-02 SQL from Deliverable 07)
• Confirm no new error alerts firing for 15 min

═══════════════════════════════════════════════
STEP 4 — COMMUNICATE & CLOSE
═══════════════════════════════════════════════
• Update status page: "Connector sync restored at HH:MM. All assets now current."
• File post-mortem within 48 h if incident lasted > 1 h or affected > 10% of assets
• Update this runbook with any new failure modes discovered

POST-MORTEM TEMPLATE: https://postmortems.internal/template
```

---

## 7. Runbook — INC-03: SLA Breach (Report Latency)

```
RUNBOOK: INC-03 — SLO-03 Report Generation SLA Breach
SEVERITY: P2 (P1 if p99 > 30 s or reports completely unavailable)
ALERT: SLO03_P95LatencyBreach OR SLO03_P99Breach
OWNER: Data Engineering On-Call

═══════════════════════════════════════════════
STEP 1 — ASSESS (< 5 min)
═══════════════════════════════════════════════
1a. Identify which reports are slow:
    SELECT report_type, AVG(duration_ms), COUNT(*) as count,
           PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95
    FROM report_jobs
    WHERE created_at > NOW() - INTERVAL '1 hour'
    GROUP BY report_type ORDER BY p95 DESC;

1b. Check async job queue:
    SELECT COUNT(*) FROM report_jobs WHERE status = 'PENDING';
    (> 50 = queue backup; > 200 = worker likely down)

1c. Check report workers:
    kubectl get pods -l app=report-worker
    kubectl top pods -l app=report-worker

═══════════════════════════════════════════════
STEP 2 — CONTAIN & REMEDIATE
═══════════════════════════════════════════════
2a. SLOW QUERY (most common cause)
    • Get the slowest report job ID:
      SELECT id, report_type, duration_ms FROM report_jobs ORDER BY duration_ms DESC LIMIT 1;
    • Replay EXPLAIN ANALYZE on its query (use parameterized values from report_jobs.params)
    • Look for: Sequential scans on large tables; missing tenant_id index; missing valuation date index
    • Add missing index (non-blocking):
      CREATE INDEX CONCURRENTLY idx_assets_tenant_estate ON assets(tenant_id, estate_id);
    • If query plan regressed after a deploy: roll back the relevant migration

2b. WORKER DOWN / OOM
    • kubectl describe pod [crashed-pod-name] (look for OOM in Events)
    • Scale up workers: kubectl scale deployment/report-worker --replicas=4
    • If persistent OOM: review query memory allocation; add LIMIT to unbounded queries

2c. DB SATURATION
    • Check connection pool: SELECT count(*) FROM pg_stat_activity WHERE state='active';
    • Check slow queries: SELECT query, total_exec_time FROM pg_stat_statements
                           ORDER BY total_exec_time DESC LIMIT 10;
    • If pool exhausted: increase PgBouncer pool_size by 20%; alert DBA

2d. QUEUE BACKUP
    • Check if workers are processing: kubectl logs deployment/report-worker --tail=50
    • If workers idle despite queue depth: restart workers
      kubectl rollout restart deployment/report-worker

═══════════════════════════════════════════════
STEP 3 — VERIFY RECOVERY
═══════════════════════════════════════════════
• Confirm p95 < 15 s for 15 consecutive minutes in Grafana
• Confirm async queue drains to < 10 pending jobs
• Run a test report (RPT-01, 100-row dataset) and time it manually

═══════════════════════════════════════════════
STEP 4 — COMMUNICATE & CLOSE
═══════════════════════════════════════════════
• Notify affected users via in-app banner if latency exceeded 5 min
• Update status page
• File post-mortem if p99 > 30 s or users reported errors

POST-MORTEM TEMPLATE: https://postmortems.internal/template
```

---

## 8. Runbook Blank Template

```
RUNBOOK: [INC-##] — [Incident Name]
SEVERITY: [P1 / P2 / P3]
ALERT: [Alert rule name]
OWNER: [Team / on-call role]

STEP 1 — ASSESS (< X min)
  [How to determine scope and impact]

STEP 2 — CONTAIN & REMEDIATE
  [Step-by-step fix, including commands]

STEP 3 — VERIFY RECOVERY
  [How to confirm the issue is resolved]

STEP 4 — COMMUNICATE & CLOSE
  [Status page update; post-mortem threshold]
```

---

*Last updated: 2026-05-28 | Owner: `[SRE / DevOps Lead]` | Review cycle: After every P1 incident; quarterly game day*
