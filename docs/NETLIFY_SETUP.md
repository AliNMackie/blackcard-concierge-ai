# Netlify Deployment Guide

## Quick Setup

**Repository**: `AliNMackie/blackcard-concierge-ai`  
**Framework**: Next.js 14 (App Router) with PWA support  
**Deployment Platform**: Netlify

## Netlify Configuration

### 1. Create New Site

1. Go to [Netlify](https://app.netlify.com/)
2. Click **"Add new site"** → **"Import an existing project"**
3. Choose **GitHub** → Select `AliNMackie/blackcard-concierge-ai`

### 2. Build Settings

Configure these settings in the deploy configuration screen:

| Setting | Value |
|---------|-------|
| **Base directory** | `frontend` |
| **Build command** | `npm install && npm run build` |
| **Publish directory** | `frontend/.next` |

> **Note**: The `netlify.toml` in the repo root already contains these settings, so Netlify should auto-detect them.

### 3. Environment Variables

Before deploying, add these environment variables in **Site settings → Environment variables**:

| Variable Name | Value | Example |
|---------------|-------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Your Cloud Run API URL | `https://elite-concierge-api-ooquqhlvxa-nw.a.run.app` |
| `NEXT_PUBLIC_API_KEY` | Your backend API key | (same as `ELITE_API_KEY` in backend) |
| `NODE_VERSION` | `20` | `20` |

**To add environment variables:**
1. Go to **Site settings** → **Environment variables**
2. Click **"Add a variable"**
3. Add each variable with "All scopes" selected
4. Click **"Deploy site"**

### 4. Deploy

1. Click **"Deploy site"**
2. Watch the deploy logs to ensure build succeeds
3. Once deployed, visit your site URL (e.g., `https://your-site.netlify.app`)

## Common Issues

### ❌ Build fails: "No package.json found"

**Cause**: Base directory is not set to `frontend`  
**Fix**: In **Site settings → Build & deploy → Build settings**, set **Base directory** to `frontend`

### ❌ Build succeeds but API calls fail (404/CORS errors)

**Cause**: Missing environment variables  
**Fix**: 
1. Go to **Site settings → Environment variables**
2. Verify `NEXT_PUBLIC_BACKEND_URL` and `NEXT_PUBLIC_API_KEY` are set
3. Trigger a new deploy from **Deploys → Trigger deploy → Deploy site**

### ❌ PWA service worker not registering

**Cause**: Service worker is disabled in development mode  
**Fix**: This is expected. PWA features only work in production builds on Netlify.

### ❌ Backend returns 403 Forbidden

**Cause**: API key mismatch  
**Fix**: Ensure `NEXT_PUBLIC_API_KEY` in Netlify matches `ELITE_API_KEY` in your Cloud Run backend environment variables.

## Local Development vs Netlify

| Aspect | Local (`npm run dev`) | Netlify Production |
|--------|----------------------|-------------------|
| Base URL | `http://localhost:8080` | Cloud Run URL |
| API Key | Dev key in `.env.local` | Production key (Netlify env var) |
| PWA | Disabled | Enabled |
| Service Worker | Not registered | Registered |

## Updating Environment Variables

If you need to update the backend URL or API key:

1. Go to **Site settings → Environment variables**
2. Click on the variable name
3. Update the value
4. Save changes
5. Trigger a new deploy: **Deploys → Trigger deploy → Clear cache and deploy site**

## Continuous Deployment

Netlify is now connected to your GitHub repository. Any push to `main` will trigger an automatic deployment:

1. Make changes to `frontend/`
2. Commit and push to `main`
3. Netlify automatically builds and deploys
4. Check deploy status at your Netlify dashboard

## Custom Domain (Optional)

To add a custom domain:

1. Go to **Site settings → Domain management**
2. Click **"Add custom domain"**
3. Follow Netlify's DNS configuration instructions
4. Once verified, your site will be available at your custom domain

## Next Steps

After successful deployment:

1. ✅ Verify the PWA installs correctly on mobile (Add to Home Screen)
2. ✅ Test backend API calls work (check Network tab in DevTools)
3. ✅ Confirm authentication flows function correctly
4. ✅ Run through `PILOT_CHECKLIST.md` for end-to-end validation

## Troubleshooting Checklist

- [ ] Base directory is set to `frontend`
- [ ] Build command is `npm install && npm run build`
- [ ] Publish directory is `frontend/.next`
- [ ] `NEXT_PUBLIC_BACKEND_URL` environment variable is set
- [ ] `NEXT_PUBLIC_API_KEY` environment variable is set
- [ ] `NODE_VERSION` is set to `20`
- [ ] Backend Cloud Run service is publicly accessible (or CORS configured)
- [ ] API key matches between frontend and backend

## Support

If you encounter issues not covered here:
1. Check Netlify deploy logs for specific error messages
2. Review backend Cloud Run logs for API errors
3. Verify environment variables in both Netlify and Cloud Run
4. Test the backend URL directly via `curl` or Postman
