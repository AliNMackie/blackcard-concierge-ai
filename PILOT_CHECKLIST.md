# Pilot Smoke Test Checklist

## Overview
This checklist ensures the Cloud Deployment (Cloud Run + Vercel/Netlify) is ready for the pilot.

## 1. Environment Setup
*   [ ] **Backend**: Cloud Run Service `elite-concierge-api` is Active.
*   [ ] **Frontend**: Deployed to Vercel/Netlify.
*   [ ] **Config**:
    *   Backend Env: `DB_INSTANCE_CONNECTION_NAME` set, `ELITE_API_KEY` set.
    *   Frontend Env: `NEXT_PUBLIC_BACKEND_URL` set to Cloud Run URL, `NEXT_PUBLIC_API_KEY` set.

## 2. Connect & Verify
1.  **Health Check**:
    ```bash
    curl https://YOUR-CLOUD-RUN-URL/health
    # Expect: {"status":"ok", ...}
    ```
2.  **Frontend Load**:
    *   Open Frontend URL.
    *   Verify "Black Card" dashboard loads (no network errors in console).

## 3. Data Flow Test (Simulation)
Use `curl` or Postman to simulate webhooks hitting the **Cloud Backend**.

### A. Terra Event (Wearable)
```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/webhooks/terra \
     -H "Content-Type: application/json" \
     -d '{
       "type": "daily",
       "user": {"provider": "OURA", "user_id": "pilot-user-1"},
       "data": [{"scores": {"recovery": 30}, "device_data": {"name": "Oura"}}]
     }'
```
*   **Verify**: Check Trainer Dashboard (`/god-mode`). A new row for "Wearable" with score 30 should appear.

### B. WhatsApp Event (Chat)
```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/webhooks/whatsapp \
     -H "Content-Type: application/json" \
     -d '{
       "From": "whatsapp:+dummy", 
       "Body": "Pilot test message: My knee hurts."
     }'
```
*   **Verify**: Check Trainer Dashboard. New "Chat" row should appear.

## 4. Trainer Override
1.  On `/god-mode`, click "Override" on any event.
2.  Verify the Toast/Console confirms the action.
