# Elite Concierge AI - Frontend PWA

## Overview
This is the Next.js 14 (App Router) PWA for the Elite Concierge platform.
It serves two main personas:
1.  **Clients**: "Black Card" Dashboard (`/dashboard`).
2.  **Trainers**: "God Mode" Dashboard (`/god-mode`).

**Current Architecture (BFF)**:
For this phase, the frontend is decoupled from the backend.
Next.js Route Handlers (`app/api/...`) act as a **BFF (Backend for Frontend)** serving high-fidelity mock data. This allows independent development of the UI flow.

## Setup

### Prerequisites
*   Node.js 18+

### Running Locally
```bash
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000).

### Build & Deploy
```bash
npm run build
npm start
```
*Note: Due to PWA optimizations, `npm run build` forces a webpack build via specific flags.*

## API Routes (Mocked)
*   `GET /api/client/events`: Returns mock `EventLog` items.
*   `POST /api/trainer/override`: Simulates an intervention override action.

## Features
*   **PWA**: Installable on iOS/Android (manifest.json included).
*   **Theme**: Minimalist black/white "Black Card" aesthetic.
*   **Tech Stack**: Next.js 14, Tailwind, TypeScript, Lucide React.

## Netlify Deployment

### Environment Variables

For Netlify (or any production deployment), configure these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_BACKEND_URL` | Cloud Run API base URL | `https://elite-concierge-api-ooquqhlvxa-nw.a.run.app` |
| `NEXT_PUBLIC_API_KEY` | API key for backend authentication | (same as `ELITE_API_KEY` in Cloud Run) |

**In Netlify:**
1. Go to **Site settings → Environment variables**
2. Add both variables with their production values
3. Trigger a new deploy

**For local development**, create a `frontend/.env.local` file:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
NEXT_PUBLIC_API_KEY=dev-test-key-12345
```

### Deployment Guide

See [`docs/NETLIFY_SETUP.md`](../docs/NETLIFY_SETUP.md) for complete deployment instructions, including:
- Base directory configuration (`frontend`)
- Build command and publish directory
- Common troubleshooting steps
- Continuous deployment setup
