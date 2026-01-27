$ErrorActionPreference = "Stop"

$PROJECT_ID = "blackcard-concierge-ai"
$PROJECT_NUMBER = "557456081985"
$SERVICE_ACCOUNT = "github-deploy-sa"
$POOL_NAME = "github-pool"
$PROVIDER_NAME = "github-provider"
$REPO = "AliNMackie/blackcard-concierge-ai"

Write-Host "Setting up Workload Identity Federation for $PROJECT_ID..."

# 1. Create Service Account (Ignore if exists)
Write-Host "Creating Service Account..."
try {
    gcloud iam service-accounts create $SERVICE_ACCOUNT --project $PROJECT_ID --display-name "GitHub Actions Deploy SA"
} catch {
    Write-Host "Service Account might already exist, continuing..."
}

# 2. Grant Roles
Write-Host "Granting Roles..."
$SA_EMAIL = "$SERVICE_ACCOUNT@$PROJECT_ID.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:$SA_EMAIL" --role "roles/run.admin" --condition=None
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:$SA_EMAIL" --role "roles/artifactregistry.writer" --condition=None
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:$SA_EMAIL" --role "roles/iam.serviceAccountUser" --condition=None

# 3. Create WIF Pool
Write-Host "Creating Identity Pool..."
try {
    gcloud iam workload-identity-pools create $POOL_NAME --project=$PROJECT_ID --location="global" --display-name="GitHub Actions Pool"
} catch {
    Write-Host "Pool might already exist, continuing..."
}

# 4. Create Provider
Write-Host "Creating Identity Provider..."
try {
    gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME --project=$PROJECT_ID --location="global" --workload-identity-pool=$POOL_NAME --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --issuer-uri="https://token.actions.githubusercontent.com"
} catch {
    Write-Host "Provider might already exist, continuing..."
}

# 5. Bind SA to Repo
Write-Host "Binding Service Account to Repo $REPO..."
gcloud iam service-accounts add-iam-policy-binding $SA_EMAIL --project=$PROJECT_ID --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/attribute.repository/$REPO"

# 6. Output Provider Name
Write-Host "`nSETUP COMPLETE. Use this Provider Name in GitHub Secrets:"
gcloud iam workload-identity-pools providers describe $PROVIDER_NAME --project=$PROJECT_ID --location="global" --workload-identity-pool=$POOL_NAME --format="value(name)"
Write-Host "Service Account: $SA_EMAIL"
