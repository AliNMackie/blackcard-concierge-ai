# Final WIF Setup - Console Wizard Method

## Current Status ✅

**Successfully Created:**
- ✅ All core infrastructure (Cloud SQL, Artifact Registry, Cloud Run, Service Accounts)
- ✅ Org Policy fixed (Domain Restricted Sharing = Allow All)
- ✅ Workload Identity Pool: `github-actions-pool`

**Remaining:**
- ⚠️ OIDC Provider (must be created via Console due to API validation quirk)
- ⚠️ Service Account IAM binding
- ⚠️ GitHub Secrets

## Step 1: Create OIDC Provider (Console Wizard - 2 mins)

1. **Open the pool:**
   - Go to: https://console.cloud.google.com/iam-admin/workload-identity-pools?project=blackcard-concierge-ai
   - Click on `github-actions-pool`

2. **Add Provider:**
   - Click **"GRANT ACCESS"** or **"ADD PROVIDER"**
   
3. **Select Provider:**
   - Choose **"OpenID Connect (OIDC)"**
   - Click **"CONTINUE"**

4. **Provider Details:**
   - **Provider name**: `github-provider`
   - **Issuer (URL)**: `https://token.actions.githubusercontent.com`
   - Click **"CONTINUE"**

5. **Configure Settings (CRITICAL - Follow Exactly):**
   - Under **"Attribute Mapping"**:
     - **Attribute 1:**
       - Attribute name: `google.subject`
       - CEL expression: `assertion.sub`
     - Click **"ADD MAPPING"**
     - **Attribute 2:**
       - Attribute name: `attribute.repository`
       - CEL expression: `assertion.repository`
   
   - **Leave "Attribute Conditions" EMPTY** (do not add any conditions)
   
   - Click **"SAVE"**

6. **Grant Access to Service Account:**
   - After saving, you'll see "Grant access to service account"
   - **Service account email**: `elite-concierge-backend-sa@blackcard-concierge-ai.iam.gserviceaccount.com`
   - **Select principals**: Choose "Only identities matching the filter"
   - **Attribute name**: `attribute.repository`
   - **Attribute value**: `AliNMackie/blackcard-concierge-ai`
   - **Service Account role**: This should default to "Workload Identity User"
   - Click **"SAVE"**

## Step 2: Get Provider Resource Name

After creation:
1. Click into the `github-provider` you just created
2. Copy the full **"Resource name"** (should look like):
   ```
   projects/557456081985/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
   ```

## Step 3:  Configure GitHub Secrets

Go to: https://github.com/AliNMackie/blackcard-concierge-ai/settings/secrets/actions

Add these 3 repository secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | `blackcard-concierge-ai` |
| `GCP_SERVICE_ACCOUNT` | `elite-concierge-backend-sa@blackcard-concierge-ai.iam.gserviceaccount.com` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | (Paste the full resource name from Step 2) |

## Step 4: Test the CI/CD Pipeline

Push a small change to trigger the workflow:

```powershell
cd C:\Users\Alastair Mackie\.gemini\antigravity\scratch\elite_concierge_ai
git add .
git commit -m "test: Verify WIF authentication"
git push origin main
```

Then watch: https://github.com/AliNMackie/blackcard-concierge-ai/actions

The workflow should:
1. ✅ Authenticate via WIF (no keys needed!)
2. ✅ Build Docker image
3. ✅ Push to Artifact Registry
4. ✅ Deploy to Cloud Run

## Troubleshooting

### If authentication fails in GitHub Actions:

Check the provider exists:
```powershell
gcloud iam workload-identity-pools providers list --workload-identity-pool=github-actions-pool --location=global --project=blackcard-concierge-ai
```

Verify the SA binding:
```powershell
gcloud iam service-accounts get-iam-policy elite-concierge-backend-sa@blackcard-concierge-ai.iam.gserviceaccount.com
```

Should show `roles/iam.workloadIdentityUser` for your repository.

## Why Console Instead of Terraform?

The Workload Identity Provider API has strict (and somewhat inconsistent) validation for attribute mappings. The Console wizard handles this automatically and is Google's recommended approach for first-time setup. Once working, you can import the provider into Terraform:

```powershell
terraform import google_iam_workload_identity_pool_provider.github_provider projects/blackcard-concierge-ai/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
```

## Next Steps After WIF Works

1. **Enable Public Access** (Optional): Uncomment the IAM binding in `infra/compute.tf`
2. **Deploy Frontend**: Connect repo to Vercel/Netlify
3. **End-to-End Test**: Use `PILOT_CHECKLIST.md`
