# Deployment Notes - Elite Concierge AI

## "Golden Path" Deployment

### 1. Infrastructure (Terraform)
We manage infrastructure manually via Terraform to control state changes.

**One-Time Setup**:
See [PROJECT_SETUP.md](infra/PROJECT_SETUP.md) for initial provisioning of Project `blackcard-concierge-ai`.

**Updates**:
If you change `infra/*.tf` files:
```bash
cd infra
terraform init
terraform apply -var="project_id=blackcard-concierge-ai" -var="region=europe-west2"
```

### 2. Backend (GitHub Actions)
Backend deployments are **automated**.

**Trigger**:
*   Merge a Pull Request to `main`.
*   OR Manually run the "Backend CI/CD" workflow from the GitHub Actions tab.

**Prerequisites**:
*   GitHub Secrets must be configured. See [CI_CD_SETUP.md](CI_CD_SETUP.md).

**Manual Fallback**:
If CI/CD is broken, use the script (requires `gcloud login`):
```bash
./deploy_backend.sh blackcard-concierge-ai
```

### 3. Frontend (Vercel/Netlify)
The frontend is deployed via Vercel/Netlify integration.

**Configuration**:
*   **Build Command**: `cd frontend && npm install && npm run build`
*   **Output Directory**: `frontend/.next` (or default)
*   **Env Vars**:
    *   `NEXT_PUBLIC_BACKEND_URL`: `https://elite-concierge-api-[hash].europe-west2.run.app` (Get this from Cloud Run console or Terraform output)
    *   `NEXT_PUBLIC_API_KEY`: Matching your backend secret.

### 4. Verification
Run through `PILOT_CHECKLIST.md` to confirm the full loop.
