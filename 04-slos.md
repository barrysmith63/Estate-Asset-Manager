# Production SLOs — Service Level Objectives
**Estate Asset Manager — Product & Engineering Deliverable 04**

---

## Executive Summary
This document defines three production SLOs for the Estate Asset Manager, with rationale, measurement methodology, alerting thresholds, and runbook snippets. SLOs are the primary tool for balancing reliability investment against feature velocity. Add new SLOs using the template in §5.

---

## 1. How to Complete This Template

1. **Define the SLI (Service Level Indicator)**: choose a measurable signal — request success rate, latency percentile, or data freshness. Be precise.
2. **Set the SLO target**: agree with product and stakeholders. Start conservatively; tighten after baseline data is collected.
3. **Define the error budget**: `1 – SLO target`. Calculate the allowable downtime/errors per rolling 30-day window.
4. **Set burn-rate alerts**: fast burn (last 1 h) for paging; slow burn (last 6 h) for tickets. Google SRE recommends 2 % burn rate over 1 h as a page threshold.
5. **Write runbook snippets**: link to the full runbooks in Deliverable 08.
6. **Review monthly**: if error budget is always full, the SLO may be too loose. If it's always exhausted, it's too tight or requires an engineering investment.

> **References**
> - Google SRE Workbook — SLO chapter: https://sre.google/workbook/implementing-slos/
> - Google SRE Book — Chapter 4: https://sre.google/sre-book/service-level-objectives/
> - Atlassian — Error budget policy: https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli
> - Search: `SLO error budget burn rate alerting Prometheus site:sre.google`

---

## 2. SLO Definitions

### SLO-01 — Asset API Availability & Correctness

| Field | Value |
|---|---|
| **SLO Name** | Asset API Availability & Correctness |
| **SLO ID** | `SLO-01` |
| **Owner** | Backend Engineering |
| **SLI Type** | Request success rate |
| **SLI Definition** | `(HTTP 2xx responses to /assets/* endpoints) ÷ (all non-healthcheck requests to /assets/*)` measured at the load balancer over a rolling 30-day window |
| **SLO Target** | **99.5 %** |
| **Error Budget** | 0.5 % ≈ **3.6 hours** of full outage per 30-day window |
| **Measurement Tool** | Prometheus `nginx_http_requests_total` + custom label filter |
| **Reporting Cadence** | Real-time dashboard; weekly report to engineering; monthly review with product |
| **Effective Date** | `2026-06-01` |
| **Review Date** | `2026-09-01` |

#### SLI Prometheus Query

```promql
# SLI: 30-day rolling success rate for /assets/* endpoints
sum(rate(http_requests_total{path=~"/assets.*", status=~"2.."}[30d]))
/
sum(rate(http_requests_total{path=~"/assets.*", status!~"4.."}[30d]))
```

> Note: 4xx errors (client faults) are excluded from the denominator — they do not count against the SLO.

#### Error Budget Calculation

| Window | Total Requests (est.) | Allowed Failures | Minutes of Downtime |
|---|---|---|---|
| 30 days | ~4 320 000 | ≤ 21 600 | ≤ 216 min |
| 7 days | ~1 008 000 | ≤ 5 040 | ≤ 50 min |
| 1 day | ~144 000 | ≤ 720 | ≤ 7 min |

#### Alerting Thresholds

| Alert Name | Condition | Severity | Action |
|---|---|---|---|
| `SLO01_FastBurn` | Burn rate > 14.4× over last 1 h (consumes 2 % budget/h) | P1 — Page on-call | Runbook §SLO-01-FB |
| `SLO01_SlowBurn` | Burn rate > 6× over last 6 h | P2 — Ticket + Slack alert | Runbook §SLO-01-SB |
| `SLO01_BudgetLow` | < 25 % error budget remaining | P3 — Engineering meeting | Review deployment history |
| `SLO01_BudgetExhausted` | Error budget = 0 | P2 — Feature freeze | Freeze non-critical deploys |

#### Runbook Snippet — SLO-01 Fast Burn

```
INCIDENT: SLO-01 Asset API Fast Burn
SEVERITY: P1
TRIGGERED BY: http error rate > 0.5% sustained for > 5 min

Step 1 — Triage (< 5 min)
  • Check Grafana dashboard "Asset API Health" for error rate spike.
  • Identify error codes: 5xx = server-side; 4xx spike = client/upstream issue.
  • Check recent deployments: `kubectl rollout history deployment/asset-api`

Step 2 — Contain (< 15 min)
  • If latest deploy is culpable: `kubectl rollout undo deployment/asset-api`
  • If database: check connection pool saturation — `db_pool_active / db_pool_max`
  • If connector: check integration health dashboard (see SLO-02).

Step 3 — Communicate
  • Post in #incidents: "P1 — Asset API degraded. [Error rate X%]. Investigating."
  • Update status page within 10 min of detection.

Step 4 — Resolve & Post-mortem
  • Confirm error rate < 0.1% for 15 min before closing.
  • File post-mortem within 48 h.
  → Full runbook: Deliverable 08, §INC-01
```

---

### SLO-02 — Connector Sync Freshness

| Field | Value |
|---|---|
| **SLO Name** | Connector Sync Freshness |
| **SLO ID** | `SLO-02` |
| **Owner** | Platform Integrations |
| **SLI Type** | Data freshness (time since last successful sync) |
| **SLI Definition** | `% of active assets where last_synced_at < NOW() – 4h` — measured every 5 min across all tenants |
| **SLO Target** | **≥ 99 %** of assets synced within the 4-hour window |
| **Error Budget** | 1 % of assets may be stale at any measurement point ≈ allows ~7 h of sync downtime per 30 days |
| **Measurement Tool** | Custom DB query + Prometheus pushgateway; alert on gauge `eam_assets_stale_pct` |
| **Reporting Cadence** | Real-time dashboard; weekly report; monthly review |
| **Effective Date** | `2026-06-01` |
| **Review Date** | `2026-09-01` |

#### SLI SQL Query (Measurement Job)

```sql
-- Run every 5 min; push result to Prometheus pushgateway
SELECT
  COUNT(*) FILTER (WHERE last_synced_at < NOW() - INTERVAL '4 hours') AS stale_count,
  COUNT(*) AS total_active,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE last_synced_at >= NOW() - INTERVAL '4 hours') / COUNT(*),
    2
  ) AS fresh_pct
FROM assets
WHERE status = 'APPROVED'
  AND connector_sync_enabled = true;
```

#### Alerting Thresholds

| Alert Name | Condition | Severity | Action |
|---|---|---|---|
| `SLO02_HighStaleness` | `eam_assets_stale_pct > 5%` for > 15 min | P2 — Page on-call | Runbook §SLO-02-HS |
| `SLO02_ModerateStaleness` | `eam_assets_stale_pct > 1%` for > 30 min | P3 — Slack alert | Check connector logs |
| `SLO02_SyncQueueDepth` | Sync queue depth > 500 pending jobs | P2 | Scale sync workers |
| `SLO02_BudgetLow` | Stale % threshold breached > 6 h this month | P3 | Engineering review |

#### Runbook Snippet — SLO-02 High Staleness

```
INCIDENT: SLO-02 Connector Sync Freshness Breach
SEVERITY: P2
TRIGGERED BY: eam_assets_stale_pct > 5% for > 15 min

Step 1 — Identify affected connector(s)
  • Dashboard: "Connector Sync Health" → filter by connector_type
  • Query: SELECT connector_type, COUNT(*) FROM assets WHERE stale GROUP BY 1;

Step 2 — Check connector status
  • Accounting: check provider status page and OAuth token validity
  • IoT: check MQTT broker connectivity and device heartbeats
  • Run: `kubectl logs deployment/sync-worker --tail=100 | grep ERROR`

Step 3 — Remediate
  • Token expired: trigger re-auth flow; tokens auto-refresh if service account healthy
  • Connector down: pause affected connector; set asset flag SYNC_PAUSED
  • Worker crash: `kubectl rollout restart deployment/sync-worker`

Step 4 — Verify recovery
  • Confirm stale % drops below 1% within 30 min of fix.
  • Update status page.
  → Full runbook: Deliverable 08, §INC-02
```

---

### SLO-03 — Report Generation Latency

| Field | Value |
|---|---|
| **SLO Name** | Report Generation Latency |
| **SLO ID** | `SLO-03` |
| **Owner** | Data & Reporting Team |
| **SLI Type** | Latency (p95 request duration) |
| **SLI Definition** | 95th-percentile response time for `GET /reports/{type}` where result set < 1 000 rows, measured over a rolling 30-day window |
| **SLO Target** | p95 ≤ **15 seconds** |
| **Error Budget** | Up to 5 % of report requests may exceed 15 s per 30-day window |
| **Measurement Tool** | Prometheus histogram `http_request_duration_seconds_bucket{path="/reports/.*"}` |
| **Reporting Cadence** | Real-time dashboard; weekly report |
| **Effective Date** | `2026-06-01` |
| **Review Date** | `2026-09-01` |

#### SLI Prometheus Query

```promql
# p95 latency for report endpoints, 30-day rolling
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{path=~"/reports/.*"}[30d]))
  by (le)
)
```

#### Alerting Thresholds

| Alert Name | Condition | Severity | Action |
|---|---|---|---|
| `SLO03_P95Breach` | p95 > 15 s for > 10 min | P2 — Slack alert + ticket | Runbook §SLO-03-LB |
| `SLO03_P99Breach` | p99 > 30 s for > 5 min | P1 — Page on-call | Investigate query plan |
| `SLO03_AsyncQueue` | Async report queue depth > 50 pending | P3 | Scale report workers |

#### Runbook Snippet — SLO-03 Latency Breach

```
INCIDENT: SLO-03 Report Latency Breach
SEVERITY: P2 (P1 if p99 > 30s)

Step 1 — Identify slow reports
  • Query: SELECT report_type, AVG(duration_ms) FROM report_jobs
            WHERE created_at > NOW() - INTERVAL '1h' GROUP BY 1 ORDER BY 2 DESC;

Step 2 — Check database
  • Run EXPLAIN ANALYZE on the slowest report query.
  • Check for missing indexes: `pg_stat_user_indexes` — look for seq scans on assets.
  • Check DB CPU / connection pool saturation.

Step 3 — Remediate
  • If query plan degraded: force index hint or add missing index.
  • If report worker OOM: `kubectl top pods -l app=report-worker` → scale up.
  • If tenant isolation issue: add tenant_id filter to query.

Step 4 — Verify
  • Confirm p95 < 15s for 15 consecutive minutes.
  → Full runbook: Deliverable 08, §INC-03
```

---

## 3. Error Budget Policy

| Budget Remaining | Policy |
|---|---|
| > 75 % | Normal operations; deploy freely |
| 25 %–75 % | Standard change management; review risky deploys |
| < 25 % | Engineering prioritizes reliability work over features |
| 0 % | Feature freeze; all engineering focuses on reliability; exec escalation |

---

## 4. SLO Dashboard Requirements

| Panel | Metric | Visualization |
|---|---|---|
| SLO-01 Availability | 30-day rolling success rate | Gauge (target line at 99.5 %) |
| SLO-01 Error Budget | % remaining this month | Burn-down bar chart |
| SLO-02 Sync Freshness | % assets synced within window | Gauge (target line at 99 %) |
| SLO-02 Stale Assets | Count by connector type | Stacked bar, time-series |
| SLO-03 Report p95 Latency | Rolling p95 | Time-series with threshold line at 15 s |
| Error Budget Burn Rate | All SLOs, burn rate over 1 h / 6 h / 24 h | Multi-line time-series |

---

## 5. New SLO Template

Copy and paste this block to define additional SLOs:

```markdown
### SLO-XX — [Name]

| Field | Value |
|---|---|
| **SLO Name** | [Name] |
| **SLO ID** | `SLO-XX` |
| **Owner** | [Team] |
| **SLI Type** | [Availability / Latency / Freshness / Correctness] |
| **SLI Definition** | [Precise definition of what is measured and how] |
| **SLO Target** | [X.XX %] |
| **Error Budget** | [1 – target × window] |
| **Measurement Tool** | [Prometheus / SQL job / synthetic monitor] |
| **Reporting Cadence** | [Real-time / Weekly / Monthly] |
| **Effective Date** | [YYYY-MM-DD] |
| **Review Date** | [YYYY-MM-DD] |

#### SLI Query
[Prometheus / SQL query]

#### Alerting Thresholds
| Alert Name | Condition | Severity | Action |
|---|---|---|---|
| `SLO-XX_Alert` | [condition] | [P1/P2/P3] | [action] |

#### Runbook Snippet
[3–5 step runbook]
```

---

*Last updated: 2026-05-28 | Owner: `[SRE Lead]` | Review cycle: Monthly error budget review + quarterly target review*
