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

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
// If BACKEND_URL is set, use it. Otherwise use internal BFF (/api/client).
const API_BASE = BACKEND_URL ? `${BACKEND_URL}` : '/api/client';

export function getApiUrl() {
    return API_BASE;
}

/**
 * Get authorization headers for API requests.
 * Uses Firebase ID token if available, falls back to API key for backwards compatibility.
 */
async function getAuthHeaders(): Promise<HeadersInit> {
    const headers: HeadersInit = {};

    // Try to get Firebase token first (client-side only)
    if (typeof window !== 'undefined') {
        try {
            const { getIdToken } = await import('./firebase');
            const token = await getIdToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
                return headers;
            }
        } catch {
            // Firebase not configured, fall through to API key
        }
    }

    // Fallback to API key for backwards compatibility
    // Fallback to API key for backwards compatibility
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
        headers['Authorization'] = `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`;
    }

    return headers;
}

export async function fetchEvents(limit = 50): Promise<EventLog[]> {
    try {
        const url = BACKEND_URL ? `${API_BASE}/events?limit=${limit}` : `${API_BASE}/events`;
        const headers = await getAuthHeaders();

        const res = await fetch(url, { headers, cache: 'no-store' });
        if (res.status === 403) throw new Error('AUTH_ERROR');
        if (!res.ok) throw new Error('Failed to fetch events');
        return res.json();
    } catch (error) {
        console.error(error);
        return [];
    }
}

export async function triggerIntervention(clientId: string) {
    const url = `${API_BASE}/events/intervention/${clientId}`;
    const headers: HeadersInit = {};
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }

    const res = await fetch(url, {
        method: 'POST',
        headers
    });
    if (!res.ok) throw new Error('Failed to trigger intervention');
    return res.json();
}

export async function toggleTravel() {
    const url = `${API_BASE}/users/me/toggle-travel`;
    const headers: HeadersInit = {};
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }
    const res = await fetch(url, { method: 'POST', headers });
    if (!res.ok) throw new Error('Failed to toggle travel');
    return res.json();
}

export async function fetchTravelStatus() {
    const url = `${API_BASE}/users/me/travel-status`;
    const headers: HeadersInit = {};
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Failed to fetch travel status');
    return res.json();
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

    const res = await fetch('/api/trainer/override', {
        method: 'POST',
        body: JSON.stringify({ clientId: userId, action }),
    });
    return res.json();
}

export async function adminUpdateUser(userId: string, data: { coach_style?: string, is_traveling?: boolean }) {
    const url = `${API_BASE}/admin/users/${userId}`;
    const headers: HeadersInit = {
        'Content-Type': 'application/json'
    };
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }

    const res = await fetch(url, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(data)
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: 'Failed to update user' }));
        throw new Error(error.detail || 'Failed to update user');
    }

    return res.json();
}

// Vision API (Supports Image & Video)
export async function analyzeVision(mediaBase64: string, isVideo = false) {
    // Basic cleaning if header is present
    const cleanBase64 = mediaBase64.replace(/^data:(image|video)\/\w+;base64,/, "");

    const payload: any = {
        detected_equipment: [],
        user_query: isVideo ? "Check my form" : "Identify gym equipment and suggest a workout"
    };

    if (isVideo) {
        payload.video_base64 = cleanBase64;
    } else {
        payload.image_base64 = cleanBase64;
    }

    const url = `${API_BASE}/events/vision`;

    const headers: HeadersInit = {
        'Content-Type': 'application/json'
    };
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }

    const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Analysis failed');
    return res.json();
}

// Chat API for Voice/Text
export async function sendChatMessage(userId: string, message: string) {
    const url = `${API_BASE}/events/chat`;
    const headers: HeadersInit = {
        'Content-Type': 'application/json'
    };
    if (process.env.NEXT_PUBLIC_API_KEY) {
        headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
    }

    const payload = {
        user_id: userId,
        message: message
    };

    const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error('Failed to send chat message');
    return res.json();
}

// Trainer -> Client Direct Messaging
export async function sendTrainerMessage(clientId: string, message: string, sendWhatsApp = false) {
    const url = `${API_BASE}/users/clients/${clientId}/message`;
    const authHeaders = await getAuthHeaders();

    const res = await fetch(url, {
        method: 'POST',
        headers: {
            ...authHeaders,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message, send_whatsapp: sendWhatsApp })
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Failed to send message' }));
        throw new Error(err.detail);
    }
    return res.json();
}

// Get messages for a specific client
export async function getClientMessages(clientId: string, limit = 20) {
    const url = `${API_BASE}/users/clients/${clientId}/messages?limit=${limit}`;
    const headers = await getAuthHeaders();

    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
}
