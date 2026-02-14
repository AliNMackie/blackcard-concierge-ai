import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom Metrics
const errorRate = new Rate('errors');
const chatDuration = new Trend('chat_duration');
const eventsDuration = new Trend('events_duration');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'https://elite-concierge-api-xxxx.run.app';
const API_KEY = __ENV.API_KEY || '';

export const options = {
    stages: [
        { duration: '30s', target: 50 },    // Ramp-up to 50 users
        { duration: '1m', target: 200 },     // Ramp-up to 200
        { duration: '2m', target: 500 },     // Ramp-up to 500
        { duration: '3m', target: 1000 },    // Peak: 1000 concurrent users
        { duration: '1m', target: 500 },     // Scale down
        { duration: '30s', target: 0 },      // Ramp-down
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'],  // 95% of requests < 2s
        http_req_failed: ['rate<0.05'],      // Error rate < 5%
        errors: ['rate<0.05'],
    },
};

const headers = {
    'Content-Type': 'application/json',
    'X-Elite-Key': API_KEY,
};

// --- Scenarios ---

export default function () {
    const scenario = Math.random();

    if (scenario < 0.4) {
        testHealthCheck();
    } else if (scenario < 0.7) {
        testListEvents();
    } else if (scenario < 0.85) {
        testChatEvent();
    } else {
        testWearableEvent();
    }

    sleep(Math.random() * 2 + 0.5); // 0.5-2.5s think time
}

function testHealthCheck() {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
        'health: status 200': (r) => r.status === 200,
        'health: db connected': (r) => JSON.parse(r.body as string).db === 'connected',
    }) || errorRate.add(1);
}

function testListEvents() {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/events?limit=20`, { headers });
    eventsDuration.add(Date.now() - start);

    check(res, {
        'events: status 200': (r) => r.status === 200,
        'events: returns array': (r) => Array.isArray(JSON.parse(r.body as string)),
    }) || errorRate.add(1);
}

function testChatEvent() {
    const messages = [
        "What's my recovery score today?",
        "Suggest a workout for today",
        "How did I sleep last night?",
        "Am I ready for HIIT today?",
        "What supplements should I take?",
    ];

    const payload = JSON.stringify({
        user_id: `loadtest-user-${__VU}`,
        message: messages[Math.floor(Math.random() * messages.length)],
    });

    const start = Date.now();
    const res = http.post(`${BASE_URL}/events/chat`, payload, { headers });
    chatDuration.add(Date.now() - start);

    check(res, {
        'chat: status 200': (r) => r.status === 200,
        'chat: has response': (r) => {
            const body = JSON.parse(r.body as string);
            return body.message && body.message.length > 0;
        },
    }) || errorRate.add(1);
}

function testWearableEvent() {
    const payload = JSON.stringify({
        device_type: 'whoop',
        recovery_score: Math.floor(Math.random() * 100),
        hrv: Math.floor(Math.random() * 80) + 20,
        resting_hr: Math.floor(Math.random() * 30) + 45,
        sleep_hours: Math.round((Math.random() * 4 + 4.5) * 10) / 10,
    });

    const res = http.post(`${BASE_URL}/events/wearable`, payload, { headers });

    check(res, {
        'wearable: status 200': (r) => r.status === 200,
    }) || errorRate.add(1);
}
