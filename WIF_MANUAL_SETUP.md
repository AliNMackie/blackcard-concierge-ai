# Final WIF Setup - Manual Provider Creation

## Current Status

✅ **Successfully Deployed:**
- Cloud SQL database (RUNNABLE)
- Artifact Registry
- Cloud Run service
- Service Accounts with proper IAM roles
- Workload Identity Pool (`github-pool`)
- Service Account IAM binding (GitHub → SA)
- Org Policy fixed (Domain Restricted Sharing = Allow All)

⚠️ **Remaining Step:**
- WIF OIDC Provider creation (must be done manually due to attribute mapping validation)

## Manual Steps to Complete WIF Setup

### Step 1: Create the OIDC Provider in GCP Console

1. Go to: [Workload Identity Federation](https://console.cloud.google.com/iam-admin/workload-identity-pools?project=blackcard-concierge-ai)

2. Click on **`github-pool`**

3. Click **"ADD PROVIDER"** or **"Connect Provider"**

4. Configure as follows:
   - **Provider type**: OpenID Connect (OIDC)
   - **Provider name**: `github-provider`
   - **Issuer (URL)**: `https://token.actions.githubusercontent.com`
   - **Audiences**: Default (leave as-is: `https://iam.googleapis.com/projects/557456081985/locations/global/workloadIdentityPools/github-pool`)
   
5. Under **"Attribute Mapping"**, configure:
   - `google.subject` → `assertion.sub`
   - `attribute.repository` → `assertion.repository`
   
6. Under **"Attribute Conditions"** (optional): Leave blank for now
   
7. Click **"SAVE"**

### Step 2: Get the Provider Resource Name

After creating the provider, click into it and copy the **full resource name**. It should look like:

```
projects/557456081985/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository: https://github.com/AliNMackie/blackcard-concierge-ai/settings/secrets/actions

Add these three secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `blackcard-concierge-ai` |
| `GCP_SERVICE_ACCOUNT` | `github-deploy-sa@blackcard-concierge-ai.iam.gserviceaccount.com` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/557456081985/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |

### Step 4: Verify GitHub Actions Workflow

The workflow `.github/workflows/backend-deploy.yml` should already be configured. On your next push to `main`, it will:

1. Authenticate to GCP using WIF (no keys!)
2. Run backend tests
3. Build Docker image
4. Push to Artifact Registry
5. Deploy to Cloud Run

### Step 5: Test the Setup

Push a small change to trigger the workflow:

```powershell
cd C:\Users\Alastair Mackie\.gemini\antigravity\scratch\elite_concierge_ai
git add .
git commit -m "test: Trigger CI/CD pipeline"
git push origin main
```

Watch the Actions tab in GitHub to verify it works.

## Import Provider to Terraform (Optional - After Manual Creation)

If you successfully created the provider manually and want Terraform to manage it going forward:

```powershell
cd C:\Users\Alastair Mackie\.gemini\antigravity\scratch\elite_concierge_ai\infra
terraform import -var="project_id=blackcard-concierge-ai" -var="region=europe-west2" google_iam_workload_identity_pool_provider.github_provider projects/blackcard-concierge-ai/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

## Troubleshooting

### If GitHub Actions authentication fails:

1. Verify the WIF Provider exists:
   ```powershell
   gcloud iam workload-identity-pools providers list --workload-identity-pool=github-pool --location=global --project=blackcard-concierge-ai
   ```

2. Check the Service Account binding:
   ```powershell
   gcloud iam service-accounts get-iam-policy github-deploy-sa@blackcard-concierge-ai.iam.gserviceaccount.com
   ```
   Should show `roles/iam.workloadIdentityUser` for the GitHub principal.

3. Verify GitHub secrets are set correctly (they're hidden but you can re-add them if needed)

## Next Steps After WIF Works

1. **Enable Public Access** (Optional): Uncomment the IAM binding in `infra/compute.tf` and run `terraform apply` to make the API publicly accessible
2. **Deploy Frontend**: Connect your repo to Vercel/Netlify and configure environment variables
3. **End-to-End Test**: Use `PILOT_CHECKLIST.md` to validate the full deployment
