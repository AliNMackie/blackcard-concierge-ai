# Elite Concierge AI - Integration Notes

## Overview
This document outlines the external integration points for the Elite Concierge backend.
Currently, we support two primary webhook ingress channels:
1.  **WhatsApp** (via Twilio or Meta Business API)
2.  **Terra** (Wearable Data Aggregation)

## 1. WhatsApp Webhook
**Endpoint**: `POST /webhooks/whatsapp`

### Payload (Twilio Style)
The endpoint expects form-encoded data (standard validation) or a JSON wrapper if using an adapter.
For the MVP, we assume a JSON payload for simplicity:
```json
{
  "From": "whatsapp:+447700900000",
  "Body": "My lower back hurts, can you adjust the plan?",
  "Timestamp": "1716900000"
}
```

### Flow
1.  **Ingest**: Parse `Body` and `From` sender.
2.  **Route**: Wraps as `ChatEvent` and triggers the **Concierge Agent**.
3.  **Response**: Returns 200 OK. The Agent's response is currently committed to the database (`EventLog`).
    *   *TODO*: Implement outbound reply via `twilio-python` or `requests`.

### Security Scope (TODO)
*   Verify `X-Twilio-Signature` header to ensure authenticity.

## 2. Terra Webhook
**Endpoint**: `POST /webhooks/terra`

### Payload (Terra Normalized)
Expects a JSON body typically containing `type` (e.g. `activity`, `daily`, `sleep`) and a `user` object.
```json
{
  "type": "daily",
  "user": {
    "provider": "OURA",
    "user_id": "terra-user-123"
  },
  "data": [
    {
      "metadata": {
        "end_time": "2024-05-28T08:00:00+00:00"
      },
      "scores": {
        "recovery": 45,
        "strain": 12,
        "sleep": 88
      },
      "device_data": {
        "name": "Oura Ring Gen 3"
      }
    }
  ]
}
```

### Flow
1.  **Ingest**: Checks `type` (only `daily` or `activity` for MVP).
2.  **Extract**: Pulls `recovery` from scores.
3.  **Route**: Wraps as `WearableEvent` and triggers **Biometric Sentry**.
4.  **Response**: Returns 200 OK.

### Verification (TODO)
*   Verify `t-signature` header using the Terra Secret.

## Testing Locally
Use `curl` to simulate an inbound webhook:

**WhatsApp:**
```bash
curl -X POST http://localhost:8080/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"From": "+15550001", "Body": "I need a recovery plan"}'
```

**Terra:**
```bash
curl -X POST http://localhost:8080/webhooks/terra \
  -H "Content-Type: application/json" \
  -d '{
    "type": "daily",
    "user": {"provider": "WHOOP"},
    "data": [{"scores": {"recovery": 32}, "device_data": {"name": "Whoop 4.0"}}]
  }'
```
