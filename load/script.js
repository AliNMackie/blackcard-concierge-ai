import http from 'k6/http';
import { check, sleep } from 'k6';

// --- Load Model & Configuration ---
// Ramp up to 50 Virtual Users over 30s, stay for 1m, ramp down.
export const options = {
    stages: [
        { duration: '30s', target: 50 }, // Ramp up
        { duration: '1m', target: 50 },  // Steady state
        { duration: '30s', target: 0 },  // Ramp down
    ],
    thresholds: {
        // SLOs: 95% of requests must complete below 500ms
        http_req_duration: ['p(95)<500'],
        // Error rate should be less than 1%
        http_req_failed: ['rate<0.01'],
    },
};

// Base URL defaults to production but can be overridden via environment variable
const BASE_URL = __ENV.BASE_URL || 'https://elite-concierge-api-451634571436.europe-west2.run.app';
// Note: Ideally construct this from the actual URL or pass via CLI

export default function () {
    // 1. Health Check (Lightweight)
    const resHealth = http.get(`${BASE_URL}/health`);
    check(resHealth, { 'status is 200': (r) => r.status === 200 });

    // 2. Access "God Mode" Events (Database Read)
    // We use a query param or header if needed. For now, we assume public or simple auth if configured.
    // Warning: If auth is required, we need to pass headers.
    // Using a simplified check for now assuming open or dev mode key.

    // const params = { headers: { 'X-Elite-Key': 'dev-secret-123' } };
    // const resEvents = http.get(`${BASE_URL}/events?limit=10`, params);
    // check(resEvents, { 'events status is 200': (r) => r.status === 200 });

    sleep(1);
}
