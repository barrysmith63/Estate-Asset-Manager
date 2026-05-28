# Integration Contract Templates
**Estate Asset Manager — Product & Engineering Deliverable 02**

---

## Executive Summary
This document defines the integration contracts for connectors used by the Estate Asset Manager. The accounting connector is fully specified as the canonical example. Two shorter templates follow for IoT sensors and identity providers. Use these contracts to align frontend, backend, and third-party teams before implementation begins.

---

## How to Complete This Template

1. **Fill connector metadata**: name, version, owner team, and SLA classification.
2. **Document all endpoints**: method, path, required headers, request body schema, and response schema.
3. **Provide payload examples**: real or representative JSON for both happy-path and error responses.
4. **Define error semantics**: map every error code the connector can return to a system behavior (retry, alert, user message).
5. **Specify rate limits and retry policy**: copy from Workflow Matrix §5 and adjust per connector.
6. **Write at least 3 test cases**: one happy path, one auth failure, one data-mapping edge case.

> **References**
> - OpenAPI 3.1 spec: https://spec.openapis.org/oas/v3.1.0
> - REST API design best practices: https://restfulapi.net/
> - Search: `integration contract template REST API openapi site:github.com`

---

---

# CONTRACT A — Accounting Connector (Full Specification)

## A.1 Metadata

| Field | Value |
|---|---|
| Connector Name | Accounting Connector |
| Version | `1.0.0` |
| Owner Team | Platform Integrations |
| External System | `[QuickBooks Online / Xero / NetSuite — choose one]` |
| Environment | Production / Staging / Dev |
| SLA Classification | Critical (sync failures trigger P2 alert) |
| Contract Status | `[DRAFT / APPROVED / DEPRECATED]` |
| Last Reviewed | `2026-05-28` |
| Review Cycle | Quarterly |

---

## A.2 Authentication

| Field | Value |
|---|---|
| Auth Method | OAuth 2.0 — Authorization Code + PKCE |
| Token Endpoint | `https://oauth.[provider].com/token` |
| Scopes Required | `accounting.transactions.read accounting.accounts.read` |
| Token Lifetime | 3 600 s (access); 30 days (refresh) |
| Token Storage | Encrypted at rest (AES-256); never logged |
| Refresh Strategy | Refresh at `expiry – 60 s`; if refresh fails, queue sync and alert admin |
| mTLS Required | `[Yes / No]` |

### A.2.1 Auth Flow Diagram

```
EAM Backend ──[Authorization Request]──▶ Provider Auth Server
           ◀──[Authorization Code]──────
           ──[Code + PKCE Verifier]────▶ Token Endpoint
           ◀──[access_token + refresh_token]──
           ──[Bearer access_token]──────▶ Accounting API
```

### A.2.2 Token Request Example

```http
POST /token HTTP/1.1
Host: oauth.[provider].com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=AUTH_CODE_HERE
&redirect_uri=https://app.estateassetmanager.com/oauth/callback
&client_id=CLIENT_ID
&code_verifier=CODE_VERIFIER
```

### A.2.3 Token Response Example

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpc...",
  "scope": "accounting.transactions.read accounting.accounts.read"
}
```

---

## A.3 Endpoints

### A.3.1 Endpoint Registry

| ID | Method | Path | Purpose | Auth Required | Rate Limit Bucket |
|---|---|---|---|---|---|
| `ACC-EP-01` | `GET` | `/accounts` | List chart of accounts | Bearer token | Standard |
| `ACC-EP-02` | `GET` | `/accounts/{id}` | Get single account | Bearer token | Standard |
| `ACC-EP-03` | `GET` | `/transactions` | List transactions (paginated) | Bearer token | Standard |
| `ACC-EP-04` | `POST` | `/transactions` | Create transaction entry | Bearer token | Write |
| `ACC-EP-05` | `POST` | `/assets/sync` | Push asset valuation update | Bearer token | Write |
| `ACC-EP-06` | `GET` | `/webhooks` | List registered webhooks | Bearer token | Standard |
| `ACC-EP-07` | `POST` | `/webhooks` | Register EAM webhook endpoint | Bearer token | Standard |

---

### A.3.2 GET /accounts — List Accounts

**Request**

```http
GET /accounts?limit=100&offset=0 HTTP/1.1
Host: api.[provider].com
Authorization: Bearer {access_token}
Accept: application/json
X-Request-ID: {uuid}
```

**Request Parameters**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | No | Records per page (default 100, max 500) |
| `offset` | integer | No | Pagination offset |
| `account_type` | string | No | Filter: `ASSET`, `LIABILITY`, `EQUITY`, `REVENUE`, `EXPENSE` |

**Happy-Path Response (200)**

```json
{
  "accounts": [
    {
      "id": "acc_01JA2B3C",
      "name": "Fixed Assets",
      "code": "1500",
      "type": "ASSET",
      "currency": "USD",
      "balance": 1250000.00,
      "updated_at": "2026-05-01T12:00:00Z"
    }
  ],
  "total": 42,
  "limit": 100,
  "offset": 0
}
```

---

### A.3.3 POST /assets/sync — Push Asset Valuation

**Request**

```http
POST /assets/sync HTTP/1.1
Host: api.[provider].com
Authorization: Bearer {access_token}
Content-Type: application/json
X-Request-ID: {uuid}
X-Idempotency-Key: {asset_id}-{sync_timestamp}
```

**Request Body**

```json
{
  "asset_id": "est_asset_9182",
  "account_id": "acc_01JA2B3C",
  "valuation": {
    "amount": 95000.00,
    "currency": "USD",
    "method": "APPRAISAL",
    "effective_date": "2026-04-30"
  },
  "description": "Q1 2026 appraisal — 123 Main St property",
  "tags": ["real_estate", "primary_residence"]
}
```

**Happy-Path Response (201)**

```json
{
  "sync_id": "sync_83kd9",
  "status": "ACCEPTED",
  "provider_transaction_id": "txn_7788abc",
  "created_at": "2026-05-28T11:30:00Z"
}
```

---

## A.4 Data Mapping

| EAM Field | Accounting Field | Type | Transformation | Notes |
|---|---|---|---|---|
| `asset.id` | `asset_id` | string | Direct | UUID |
| `asset.valuation.current_value` | `valuation.amount` | decimal | Direct | 2 decimal places |
| `asset.valuation.currency` | `valuation.currency` | string | ISO 4217 | Default USD |
| `asset.category` | `account_id` | string | Lookup table | Map category → account |
| `asset.effective_date` | `valuation.effective_date` | date | ISO 8601 | YYYY-MM-DD |
| `asset.notes` | `description` | string | Truncate to 255 chars | Strip HTML |
| `asset.tags` | `tags` | array of strings | Direct | Max 10 tags |
| `[EAM field]` | `[Accounting field]` | `[type]` | `[transformation]` | `[notes]` |

---

## A.5 Error Semantics

| HTTP Code | Provider Error Code | Meaning | EAM Behavior | User-Facing Message |
|---|---|---|---|---|
| 400 | `INVALID_PAYLOAD` | Malformed request | Log + alert engineer; do not retry | "Sync failed: data format error." |
| 401 | `TOKEN_EXPIRED` | Access token expired | Refresh token silently; retry once | Transparent to user |
| 401 | `TOKEN_INVALID` | Token revoked | Alert admin; pause sync | "Re-authorize accounting connector." |
| 403 | `INSUFFICIENT_SCOPE` | Missing OAuth scope | Alert admin; log | "Accounting permissions need update." |
| 404 | `ACCOUNT_NOT_FOUND` | Mapped account missing | Alert engineer; skip record | "Account mapping error. Contact admin." |
| 409 | `DUPLICATE_TRANSACTION` | Idempotency key reused | Treat as success; log warning | Transparent to user |
| 422 | `VALIDATION_ERROR` | Business rule violated | Log details; do not retry | "Sync rejected: see error details." |
| 429 | `RATE_LIMITED` | Too many requests | Wait `Retry-After` seconds; re-queue | Transparent to user |
| 500 | `INTERNAL_ERROR` | Provider fault | Retry 3× exp backoff; alert if exhausted | "Accounting sync temporarily unavailable." |
| 503 | `SERVICE_UNAVAILABLE` | Planned maintenance | Check status page; retry after window | "Accounting system under maintenance." |

---

## A.6 Rate Limits

| Bucket | Limit | Window | Scope | Enforcement |
|---|---|---|---|---|
| Standard (reads) | 500 requests | 60 s | Per OAuth app | 429 + `Retry-After` header |
| Write | 100 requests | 60 s | Per OAuth app | 429 + `Retry-After` header |
| Daily quota | 50 000 requests | 24 h | Per OAuth app | 429 after quota exhausted |

**EAM strategy**: batch asset syncs into groups of 50 per cycle; stagger connectors by 5 s to avoid concurrent bursts.

---

## A.7 Retry Policy

| Condition | Retries | Initial Delay | Multiplier | Max Delay | Jitter |
|---|---|---|---|---|---|
| 429 Rate limited | Unlimited (until window) | `Retry-After` value | 1× | — | None |
| 500 / 503 transient | 3 | 5 s | 2× | 60 s | ±20 % |
| 401 Token expired | 1 (after refresh) | 0 s | — | — | None |
| Network timeout | 2 | 3 s | 2× | 15 s | ±10 % |
| 400 / 422 client error | 0 | — | — | — | Never retry client errors |

---

## A.8 Webhook Contract

EAM registers a webhook to receive push notifications of account changes:

**Registration Request**

```json
{
  "url": "https://api.estateassetmanager.com/webhooks/accounting",
  "events": ["account.balance_changed", "transaction.created"],
  "secret": "[HMAC-SHA256 secret — stored in secrets manager]"
}
```

**Incoming Webhook Payload**

```json
{
  "event": "account.balance_changed",
  "account_id": "acc_01JA2B3C",
  "previous_balance": 1200000.00,
  "new_balance": 1250000.00,
  "timestamp": "2026-05-28T11:00:00Z",
  "signature": "sha256=abc123..."
}
```

**Signature Validation**: `HMAC-SHA256(secret, raw_body)` — reject if mismatch. Respond 200 within 5 s or provider retries.

---

## A.9 Test Cases

| ID | Name | Input | Expected Response | Pass Criteria |
|---|---|---|---|---|
| `TC-ACC-01` | Happy path asset sync | Valid payload, valid token | 201 + `sync_id` | `sync_id` present; DB updated |
| `TC-ACC-02` | Expired access token | Expired token, valid refresh | 401 → refresh → 201 | Transparent retry; no user error |
| `TC-ACC-03` | Invalid account mapping | `account_id` not in provider | 404 | Alert fired; record skipped; no crash |
| `TC-ACC-04` | Rate limit hit | 101st write in 60 s | 429 + `Retry-After: 30` | Queue paused 30 s; retried successfully |
| `TC-ACC-05` | Duplicate idempotency key | Same key sent twice | 409 | Treated as success; no duplicate record |
| `TC-ACC-06` | Webhook HMAC mismatch | Tampered payload | EAM returns 400 | Webhook rejected; security log entry |
| `[TC-ACC-##]` | `[Name]` | `[Input]` | `[Expected]` | `[Pass criteria]` |

---

---

# CONTRACT B — IoT Sensors Connector (Short Template)

## B.1 Metadata

| Field | Value |
|---|---|
| Connector Name | IoT Sensors Connector |
| Version | `1.0.0` |
| Owner Team | `[Platform Integrations]` |
| External System | `[AWS IoT Core / Azure IoT Hub / Custom MQTT Broker]` |
| SLA Classification | `[Standard / Critical]` |
| Contract Status | `DRAFT` |

## B.2 Authentication

| Field | Value |
|---|---|
| Auth Method | `[X.509 certificates / API key / IAM role]` |
| Key/Cert Storage | Secrets Manager; rotate every 90 days |
| mTLS Required | `[Yes / No]` |

## B.3 Key Endpoints / Topics

| Method / Topic | Path / MQTT Topic | Purpose |
|---|---|---|
| `SUBSCRIBE` | `estates/{estate_id}/sensors/#` | Receive all sensor readings |
| `PUBLISH` | `estates/{estate_id}/commands/{sensor_id}` | Send commands to sensor |
| `GET` | `/devices/{id}/telemetry` | Pull last N readings via REST |

## B.4 Payload Example

```json
{
  "sensor_id": "sensor_8821",
  "asset_id": "est_asset_9182",
  "type": "TEMPERATURE",
  "value": 68.5,
  "unit": "F",
  "timestamp": "2026-05-28T10:00:00Z",
  "battery_pct": 82
}
```

## B.5 Data Mapping

| Sensor Field | EAM Field | Transformation |
|---|---|---|
| `sensor_id` | `asset.iot_device_id` | Direct |
| `asset_id` | `asset.id` | Direct |
| `value` | `asset.telemetry.latest_reading` | Store with unit |
| `timestamp` | `asset.telemetry.last_seen_at` | ISO 8601 |
| `[field]` | `[EAM field]` | `[transform]` |

## B.6 Error Semantics

| Condition | EAM Behavior |
|---|---|
| Sensor offline > 24 h | Alert admin; flag asset with `SENSOR_OFFLINE` tag |
| Invalid payload schema | Log and discard; increment error counter |
| Broker unreachable | Reconnect with 30 s exp backoff; alert after 5 min |

## B.7 Test Cases

| ID | Scenario | Pass Criteria |
|---|---|---|
| `TC-IOT-01` | Valid telemetry received | Asset telemetry record updated |
| `TC-IOT-02` | Sensor offline 25 h | Alert generated; asset flagged |
| `TC-IOT-03` | Malformed JSON payload | Discarded; error counter +1; no crash |

---

---

# CONTRACT C — Identity Provider Connector (Short Template)

## C.1 Metadata

| Field | Value |
|---|---|
| Connector Name | Identity Provider (IdP) Connector |
| Version | `1.0.0` |
| Owner Team | `[Security / Platform]` |
| External System | `[Azure AD / Okta / Auth0 / AWS Cognito]` |
| SLA Classification | Critical (auth failures block all users) |
| Contract Status | `DRAFT` |

## C.2 Authentication Protocol

| Field | Value |
|---|---|
| Protocol | OIDC 1.0 + OAuth 2.0 |
| Discovery URL | `https://[provider]/.well-known/openid-configuration` |
| Scopes | `openid profile email groups` |
| Token Validation | JWT signature + `iss` + `aud` + `exp` checks |
| Session Duration | 8 h (configurable per tenant) |
| MFA Required | `[Yes / No — per tenant policy]` |

## C.3 Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/.well-known/openid-configuration` | OIDC discovery |
| `GET` | `/authorize` | Initiate login |
| `POST` | `/token` | Exchange code for tokens |
| `GET` | `/userinfo` | Fetch user profile |
| `POST` | `/token/revoke` | Logout / revoke session |
| `GET` | `/jwks` | Public keys for JWT validation |

## C.4 Claims Mapping

| OIDC Claim | EAM Field | Notes |
|---|---|---|
| `sub` | `user.external_id` | Stable identifier |
| `email` | `user.email` | Normalize to lowercase |
| `name` | `user.display_name` | Display only |
| `groups` | `user.roles` | Map IdP groups to EAM RBAC roles |
| `[claim]` | `[EAM field]` | `[notes]` |

## C.5 Error Semantics

| Condition | EAM Behavior |
|---|---|
| `invalid_token` | Redirect to login; log event |
| `account_disabled` | Return 403; alert admin |
| IdP unreachable | Return 503; show maintenance page |
| Group mapping fails | Assign default `Viewer` role; alert admin |

## C.6 Test Cases

| ID | Scenario | Pass Criteria |
|---|---|---|
| `TC-IDP-01` | Valid OIDC login | User authenticated; session created; role assigned |
| `TC-IDP-02` | Token expired mid-session | Silent refresh or redirect to login |
| `TC-IDP-03` | Unknown group claim | `Viewer` role assigned; admin alerted |
| `TC-IDP-04` | IdP returns 503 | User sees maintenance page; no stack trace exposed |

---

*Last updated: 2026-05-28 | Owner: `[Platform Integrations Lead]` | Review cycle: Quarterly*
