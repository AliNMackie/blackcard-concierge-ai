# Production Infrastructure Plan - Elite Concierge AI

## Overview
This Terraform configuration provisions the foundational infrastructure for the "Elite Concierge AI" platform on Google Cloud Platform (GCP).
It focuses on a serverless, event-driven architecture using Cloud Run, Cloud SQL, and Vertex AI.

## File Structure
*   `main.tf`: Enables required Google Cloud APIs (`run`, `aiplatform`, `sqladmin`, etc.).
*   `compute.tf`: Defines the **Cloud Run** service and the **Artifact Registry** repository.
*   `database.tf`: Provisions the **Cloud SQL** (Postgres) instance, database, user, and secures the password in **Secret Manager**.
*   `iam.tf`: Manages the **Service Account** and core IAM role bindings (Vertex AI, Logging, SQL Client).
*   `variables.tf`: Input variables (`project_id`, `region`, `service_name`).
*   `outputs.tf`: Exports key connection strings and URLs.
*   `versions.tf`: Provider version locking.

## Resources Created

### Core Infrastructure
*   **Networking**: Uses default VPC for MVP simplicity.
*   **Region**: `europe-west2` (London) by default.

### Compute & Serving
*   **Cloud Run Service** (`elite-concierge-api`):
    *   Hosted in `europe-west2`.
    *   Initially deploys a placeholder `hello-world` container.
    *   Configured with Public Ingress (allowing unauthenticated access for webhooks/PWA in MVP).

### Data & storage
*   **Cloud SQL Instance** (Postgres 15):
    *   `db-f1-micro` instance (MVP tier).
    *   Public IP enabled (secured via password + Cloud SQL Proxy/Auth Proxy).
    *   Database: `concierge_db`.
*   **Artifact Registry**: Docker repository for storing backend images.

### Security (IAM)
*   **Service Account** (`elite-concierge-backend-sa`):
    *   Runtime identity for the Cloud Run service.
    *   **Permissions**: `roles/aiplatform.user`, `roles/cloudsql.client`, `roles/storage.objectViewer`, `roles/secretmanager.secretAccessor`, `roles/logging.logWriter`, `roles/monitoring.metricWriter`.

## Deployment Commands

### Prerequisites
*   Google Cloud SDK (`gcloud`) installed and authenticated.
*   Terraform >= 1.0 installed.
*   A GCP Project created with billing enabled.

### 1. Initialize
```bash
cd infra
terraform init
```

### 2. Validate
```bash
terraform validate
```

### 3. Deploy
Replace `YOUR_PROJECT_ID` with your actual GCP Project ID.

```bash
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

## Backend Connection
The backend connects to Cloud SQL using the connection name injected as an environment variable (`DB_INSTANCE_CONNECTION_NAME`).
The password is retrieved from Secret Manager (`DB_SECRET_ID`).
Libraries like `cloud-sql-python-connector` or the Cloud SQL Auth Proxy sidecar are recommended for the actual connection logic.
