# UHNW Pilot Handoff Checklist

**Date**: 14 Feb 2026
**Status**: Conditional GO for 1–3 clients

---

## 🔴 BEFORE First Client (Mandatory)

### 1. Rotate the API Key
The old key (`EliteConcierge2026_GodSecret`) was committed to git. It has been removed from the repo but **must be considered compromised**.

```bash
# 1. Generate a new key (32+ chars, alphanumeric)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update GCP Secret Manager
gcloud secrets versions add ELITE_API_KEY \
  --data-file=- --project=blackcard-concierge-ai <<< "YOUR_NEW_KEY"

# 3. Redeploy backend (or it picks up on next CI deploy)
gcloud run services update elite-concierge-api \
  --region=europe-west2 --project=blackcard-concierge-ai

# 4. Update GitHub Actions secret
# → Settings > Secrets > ELITE_API_KEY → paste new key
```

### 2. Enable DB Backups
Terraform file updated (`infra/database.tf`). Apply it:

```bash
cd infra
terraform init
terraform plan   # Review the changes
terraform apply  # Enable backups
```

Or manually via GCP Console:
- Cloud SQL → `elite-concierge-db-prod` → Edit → Backups → Enable automated backups

### 3. Set Up Uptime Monitoring
In GCP Console:
1. Go to **Monitoring → Uptime Checks → Create**
2. Target: `https://elite-concierge-api-<hash>.europe-west2.run.app/health`
3. Check interval: 5 minutes
4. Alert: Email notification to your inbox

### 4. Update Netlify Environment Variables
You're missing three critical variables in Netlify. You **must** add these to fix the "Missing appId" error and restore auth:

1. Go to **Netlify → Site configuration → Environment variables**
2. **ADD** these missing keys:
   - `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
   - `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
   - `NEXT_PUBLIC_FIREBASE_APP_ID` (Critical: this fixes the 401/Installation error)

3. **Verify** these are also there (you listed them as already present):
   - `NEXT_PUBLIC_FIREBASE_API_KEY`
   - `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
   - `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
   - `NEXT_PUBLIC_BACKEND_URL`
   - `NEXT_PUBLIC_API_KEY` (Your new rotated key)

**Note**: After adding these, Netlify will trigger a new build. Auth will work once that build finishes.

---

## 🟡 First Client & Trainer Onboarding

### Trainer Setup (Cian)
1. Cian signs up at `https://blackcard-concierge.netlify.app/login` using "Sign Up".
2. **Promote him**: Once he has an account, you can promote him by running this command in your terminal:
   ```bash
   curl -X POST https://elite-concierge-api-557456081985.europe-west2.run.app/users/admin/provision-trainer \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_NEW_API_KEY" \
     -d '{"email": "Cd1fit23@gmail.com"}'
   ```

### Account Setup (Client)
1. Client signs up at login page.
2. Firebase creates their auth account automatically.
3. First chat message creates their user record in the DB.

### Trainer Configuration
1. Log into God Mode: `/god-mode` (Trainer Dashboard).
2. Assign the trainer to the client via the dropdown menu.
3. Set the client's `coach_style`.

### Verify It Works
Run through the UAT guide: [uat_guide.md](file:///C:/Users/Alastair%20Mackie/.gemini/antigravity/brain/a944cdba-5edb-483a-a23c-100881b00daa/uat_guide.md)

---

## 🚨 Emergency Runbook

### API is Down
1. Check Cloud Run: `gcloud run services describe elite-concierge-api --region=europe-west2`
2. Check logs: `gcloud logging read "resource.type=cloud_run_revision" --limit=50 --freshness=1h`
3. If crash-looping: redeploy last known good image
   ```bash
   gcloud run deploy elite-concierge-api \
     --image=europe-west2-docker.pkg.dev/blackcard-concierge-ai/elite-concierge-repo/backend:latest \
     --region=europe-west2
   ```

### Database Issues
1. Check status: GCP Console → Cloud SQL → `elite-concierge-db-prod`
2. If corrupted: restore from backup (Console → Backups → Restore)
3. Connection issues: verify Cloud SQL Proxy or connection name in Cloud Run env vars

### Frontend Issues
1. Netlify dashboard: `https://app.netlify.com` → check deploy status
2. Force redeploy: push an empty commit or trigger via Netlify UI
3. Clear service worker: Users can clear via browser DevTools → Application → Service Workers → Unregister

---

## 📋 Remaining Technical Debt (Post-Pilot)

| Item | Priority | Notes |
|:---|:---:|:---|
| Private IP for Cloud SQL | Medium | Move to VPC for defense-in-depth |
| Structured logging | Medium | Switch from `print()` to Cloud Logging JSON |
| Rate limiting | Medium | Add per-user rate limits on chat endpoint |
| Load test execution | Low | Run K6 script before scaling beyond 5 users |
| Git history cleanup | Low | Use `git filter-branch` or BFG to purge old secret from history |
