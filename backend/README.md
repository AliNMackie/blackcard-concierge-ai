# Elite Concierge AI - Backend

## Overview
This is the backend service for the Elite Concierge AI platform.
It uses **FastAPI** for the web layer, **LangGraph** for agents, and **Cloud SQL** (Postgres) for persistence.

## Setup

### Prerequisites
*   Python 3.11+
*   Environment Variables (Optional for Dev, Required for Prod)

### Environment Variables
| Variable | Description | Default (Dev) |
| :--- | :--- | :--- |
| `PROJECT_ID` | GCP Project ID | `mock-project-id` |
| `GCP_REGION` | GCP Region | `europe-west2` |
| `DB_INSTANCE_CONNECTION_NAME` | Cloud SQL Connect String | `None` (Disables persistence) |
| `DB_USER` | Database User | `elite-concierge-user` |
| `DB_PASS` | Database Password | `None` |
| `DB_NAME` | Database Name | `concierge_db` |
| `DATABASE_URL` | Async Postgres URL (Dev Override) | `None` |

### Running Locally (No DB)
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Server**:
    ```bash
    uvicorn app.main:app --reload
    ```
    *Note: Calls to `/events` will process logic but log "No Database Configured" if env vars are missing.*

### Running Locally (With DB)
You can point to a local Docker Postgres or a Cloud SQL instance.
Example `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/concierge_db
```

### Running Tests
```bash
python -m pytest
```
Tests mock the LLM and bypass the Database layer to verify Agent logic speed and correctness.

## Endpoints

### 1. Wearable Event (Low Recovery)
```bash
curl -X POST http://localhost:8000/events/wearable \
  -H "Content-Type: application/json" \
  -d '{"device_type": "whoop", "recovery_score": 32}'
```

### 2. Vision Event
```bash
curl -X POST http://localhost:8000/events/vision \
  -H "Content-Type: application/json" \
  -d '{"detected_equipment": ["Kettlebells"], "user_query": "HIIT flow"}'
```
