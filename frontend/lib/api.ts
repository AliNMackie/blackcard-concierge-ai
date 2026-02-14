export type AgentResponse = {
    agent_name: string;
    message: string;
    suggested_action: string;
};

export type EventLog = {
    id: number;
    user_id: string;
    event_type: string;
    payload: any;
    agent_decision?: string;
    agent_message?: string;
    created_at: string;
};

import { getIdToken } from './firebase';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
// If BACKEND_URL is set, use it. Otherwise use internal BFF (/api/client).
const API_BASE = BACKEND_URL ? `${BACKEND_URL}` : '/api/client';

export async function fetchEvents(limit = 50): Promise<EventLog[]> {
    try {
        const url = BACKEND_URL ? `${API_BASE}/events?limit=${limit}` : `${API_BASE}/events`;
        const headers: HeadersInit = {};

        const token = await getIdToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        } else if (typeof window !== 'undefined' && window.localStorage.getItem('E2E_BYPASS')) {
            if (process.env.NEXT_PUBLIC_API_KEY) {
                headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
            }
        }

        const res = await fetch(url, { headers });
        if (res.status === 403) throw new Error('AUTH_ERROR');
        if (!res.ok) throw new Error('Failed to fetch events');
        return res.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function triggerOverride(userId: string, action: string) {
    const url = BACKEND_URL ? `${API_BASE}/events/override` : `/api/trainer/override`;

    // Note: Variable url for override logic if backend supports it in future.
    // For now, backend doesn't have an override endpoint, so we might want to keep mocking it 
    // OR create a stub in backend.
    // Let's stick to the BFF mock for override unless BACKEND_URL is set *and* we implement it there.
    // For this step, we'll keep override mocked in BFF or logged in console if using real backend.

    if (BACKEND_URL) {
        console.log("Training override sent to backend (stub):", action);
        return { success: true };
    }

    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    const token = await getIdToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    } else if (typeof window !== 'undefined' && window.localStorage.getItem('E2E_BYPASS')) {
        if (process.env.NEXT_PUBLIC_API_KEY) {
            headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
        }
    }

    const res = await fetch('/api/trainer/override', {
        method: 'POST',
        headers,
        body: JSON.stringify({ clientId: userId, action }),
    });
    return res.json();
}

export function getApiUrl(): string {
    return API_BASE;
}

async function getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = { 'Content-Type': 'application/json' };
    const token = await getIdToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    } else if (typeof window !== 'undefined' && window.localStorage.getItem('E2E_BYPASS')) {
        if (process.env.NEXT_PUBLIC_API_KEY) {
            headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
        }
    }
    return headers;
}

export async function analyzeVision(imageBase64: string, _liveMode?: boolean): Promise<AgentResponse> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/events/vision`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                detected_equipment: [],
                image_base64: imageBase64,
            }),
        });
        if (!res.ok) throw new Error('Vision analysis failed');
        return res.json();
    } catch (error) {
        console.error('Vision analysis error:', error);
        return { agent_name: 'System', message: 'Vision analysis unavailable.', suggested_action: 'ERROR' };
    }
}

export async function sendChatMessage(userId: string, message: string): Promise<AgentResponse> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/events/chat`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ user_id: userId, message }),
        });
        if (!res.ok) throw new Error('Chat send failed');
        return res.json();
    } catch (error) {
        console.error('Chat error:', error);
        return { agent_name: 'System', message: 'Unable to send message. Please try again.', suggested_action: 'ERROR' };
    }
}

export type AnalyticsData = {
    labels: string[];
    datasets: { label: string; data: number[] }[];
};

export async function fetchAnalytics(category: string, period = '7d'): Promise<AnalyticsData | null> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/analytics/${category}?period=${period}`, { headers });
        if (!res.ok) return null;
        return res.json();
    } catch (error) {
        console.error('Analytics fetch error:', error);
        return null;
    }
}

export type PerformanceMetricInput = {
    category: string;
    name: string;
    value: number;
    unit: string;
    timestamp: string;
};

export async function logPerformanceMetric(data: PerformanceMetricInput): Promise<void> {
    try {
        const headers = await getAuthHeaders();
        await fetch(`${API_BASE}/analytics/metrics`, {
            method: 'POST',
            headers,
            body: JSON.stringify(data),
        });
    } catch (error) {
        console.error('Metric log error:', error);
    }
}

