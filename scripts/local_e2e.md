# Local End-to-End (E2E) Testing Guide

This guide specifically tests the flow:
`Webhook -> Backend Logic -> Database -> Frontend Dashboard`

## 1. Start the Backend
Runs at `http://localhost:8080`.
```bash
cd backend
# Windows:
$env:DB_INSTANCE_CONNECTION_NAME=""; $env:DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/concierge_db" 
# (Or rely on your .env defaults if setup)
uvicorn app.main:app --reload --port 8080
```
*Note: Ensure you have a local DB running or the app handles missing DB gracefully.*

## 2. Start the Frontend
Runs at `http://localhost:3000`.
Ensure `frontend/.env.local` points to the backend:
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
```

Start app:
```bash
cd frontend
npm run dev
```

## 3. Trigger Test Events
We have a helper script to send sample Webhook payloads (Terra & WhatsApp).

In a new terminal root:
```bash
python scripts/send_test_events.py
```

## 4. Verify Results
1.  **Backend Logs**: Should show "Webhook (Terra)... mapped to WearableEvent" and "Webhook (WhatsApp)..."
2.  **Trainer Dashboard** (`http://localhost:3000/god-mode`):
    *   Click "Refresh Data".
    *   You should see new rows for "Wearable" (Recovery Score 25) and "Chat".
3.  **Client Dashboard** (`http://localhost:3000/dashboard`):
    *   You should see cards for "Biometric Analysis" and "Concierge Chat".
