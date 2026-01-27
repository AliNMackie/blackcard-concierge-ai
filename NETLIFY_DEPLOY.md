# Netlify Deployment Summary for `AliNMackie/blackcard-concierge-ai`

## Configuration

### Netlify UI Settings

When setting up the site in Netlify, use these exact values:

| Setting | Value |
|---------|-------|
| **Base directory** | `frontend` |
| **Build command** | `npm install && npm run build` |
| **Publish directory** | `frontend/.next` |

> **Note**: These are also defined in `netlify.toml` at the repo root and should auto-populate.

### Environment Variables

Add these in **Site settings → Environment variables**:

| Variable Name | Value | Where to Get It |
|---------------|-------|----------------|
| `NEXT_PUBLIC_BACKEND_URL` | `https://elite-concierge-api-ooquqhlvxa-nw.a.run.app` | Cloud Run service URL (from `terraform output`) |
| `NEXT_PUBLIC_API_KEY` | (your production API key) | Same value as `ELITE_API_KEY` in Cloud Run environment |
| `NODE_VERSION` | `20` | (fixed value) |

## Common Failure Modes

### 1. Build fails with "No package.json found"
**Cause**: Base directory not set to `frontend`  
**Fix**: Set **Base directory** to `frontend` in Site settings

### 2. Build succeeds but API calls fail (404/CORS)
**Cause**: Missing `NEXT_PUBLIC_BACKEND_URL` or `NEXT_PUBLIC_API_KEY`  
**Fix**: Add environment variables and redeploy

### 3. Backend returns 403 Forbidden
**Cause**: API key mismatch  
**Fix**: Ensure `NEXT_PUBLIC_API_KEY` in Netlify matches `ELITE_API_KEY` in Cloud Run

### 4. PWA not installing on mobile
**Cause**: Service worker disabled (development mode)  
**Fix**: This is expected locally; works in production Netlify builds

## Deployment Flow

1. **Connect GitHub**: Netlify → New site → GitHub → Select `AliNMackie/blackcard-concierge-ai`
2. **Configure**: Verify base dir, build command, publish dir (should auto-populate from `netlify.toml`)
3. **Add Env Vars**: Site settings → Environment variables → Add 3 variables above
4. **Deploy**: Click "Deploy site"
5. **Verify**: Test API calls work, PWA installs correctly

## Links

- **Setup Guide**: [`docs/NETLIFY_SETUP.md`](docs/NETLIFY_SETUP.md)
- **Frontend README**: [`frontend/README.md`](frontend/README.md)
- **Cloud Run Backend**: https://elite-concierge-api-ooquqhlvxa-nw.a.run.app

## Next Steps After Deploy

1. ✅ Test PWA installation on mobile
2. ✅ Verify backend API calls (check DevTools Network tab)
3. ✅ Run through `PILOT_CHECKLIST.md` for E2E validation
