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
