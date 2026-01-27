# CI/CD Setup: GitHub Actions + GCP

This guide documents the **one-time setup** required to enable automated deployments from GitHub to Google Cloud.

## 1. GCP Setup (Workload Identity Federation)
Instead of exporting long-lived keys, we use Workload Identity Federation (WIF).

### A. Define Variables
```bash
export PROJECT_ID="blackcard-concierge-ai"
export PROJECT_NUMBER="557456081985"
export SERVICE_ACCOUNT="github-deploy-sa"
export POOL_NAME="github-pool"
export PROVIDER_NAME="github-provider"
export REPO="AliNMackie/blackcard-concierge-ai"
```

### B. Create Service Account
```bash
gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
  --project "${PROJECT_ID}" \
  --display-name "GitHub Actions Deploy SA"

# Grant permissions (Cloud Run, Artifact Registry, Storage, Service Account User)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/run.admin"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role "roles/iam.serviceAccountUser"
```

### C. Configure Workload Identity Pool
```bash
gcloud iam workload-identity-pools create "${POOL_NAME}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_NAME}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="${POOL_NAME}" \
  --display-name="GitHub Actions Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### D. Bind Service Account to Repo
```bash
gcloud iam service-accounts add-iam-policy-binding "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO}"
```

### E. Get the Provider Name
You will need the full Provider resource name for the GitHub Secret.
```bash
gcloud iam workload-identity-pools providers describe "${PROVIDER_NAME}" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="${POOL_NAME}" \
  --format="value(name)"
```
*   **Format**: `projects/557456081985/locations/global/workloadIdentityPools/github-pool/providers/github-provider`

## 2. GitHub Secrets Setup
Go to your GitHub Repo -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following:

| Secret Name | Value Example |
| :--- | :--- |
| `GCP_PROJECT_ID` | `blackcard-concierge-ai` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Output from step 1.E (the long `projects/...` string) |
| `GCP_SERVICE_ACCOUNT` | `github-deploy-sa@blackcard-concierge-ai.iam.gserviceaccount.com` |

## 3. Verification
1.  Push a commit to `main`.
2.  Go to the **Actions** tab in GitHub.
3.  Verify the `Backend CI/CD` workflow runs successfully.
