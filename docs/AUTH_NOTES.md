# Authentication Notes (Pilot Phase)

## Overview
For the Pilot phase, the Elite Concierge AI uses a **Minimal API Key** strategy for authentication.
This is not a full OAuth solution (e.g., Auth0) but creates a security baseline for the pilot.

## Mechanism (`X-Elite-Key`)
*   **Type**: Static API Key.
*   **Header**: `X-Elite-Key`.
*   **Validation**: Checked against the `ELITE_API_KEY` environment variable in the backend.

## Configuration

### Backend (Cloud Run)
Set the `ELITE_API_KEY` environment variable to a strong random string.
```bash
ELITE_API_KEY="your-secret-pilot-key-123"
```
*   **Protected Endpoints**:
    *   `GET /events` (Trainer Dashboard Data)

### Frontend (Vercel/Netlify)
Set the `NEXT_PUBLIC_API_KEY` environment variable to match the backend key.
```bash
NEXT_PUBLIC_API_KEY="your-secret-pilot-key-123"
```
*   **Usage**: The frontend automatically injects this header into calls to protected endpoints via `lib/api.ts`.
*   **Security Note**: Since this is a Client-Side Env Var (`NEXT_PUBLIC_`), the key is visible in the browser bundle. **This is acceptable for the Pilot (trusted users/trainers) but must be replaced with server-side Auth (Auth0/NextAuth) for Production.**

### Local Development
1.  **Backend**: `ELITE_API_KEY` defaults to `dev-secret-123` if not set.
2.  **Frontend**: Ensure `.env.local` contains `NEXT_PUBLIC_API_KEY=dev-secret-123`.

## Future Roadmap (Post-Pilot)
1.  **Identity Provider**: Integrate Auth0 or Firebase Auth.
2.  **Frontend**: Use `NextAuth.js` for session management.
3.  **Backend**: Replace `get_api_key` with a JWT Bearer Token validator (`VerifyToken` dependency).
