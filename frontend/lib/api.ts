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

export type DailyInsight = {

    id: string;
    user_id: string;
    date: string;
    insight_headline: string;
    actionable_advice: string;
    suggested_plan_override: any;
};


import { getIdToken } from './firebase';
import { mutate as globalMutate } from 'swr';

// Custom error for paywall interception
export class PaywallError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'PaywallError';
    }
}


const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL;
// If BACKEND_URL is set, use it with the /api/v1 prefix. Otherwise use internal BFF (/api/client).
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api/v1` : '/api/client';

export async function fetchEvents(limit = 50): Promise<EventLog[]> {
    try {
        const url = BACKEND_URL ? `${BACKEND_URL}/events?limit=${limit}` : `${API_BASE}/events`;
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

export type WorkoutData = {
    session_id: string;
    exercise_name: string;
    sets: number;
    reps: number;
    weight_kg: number;
};

export async function logWorkoutSession(data: WorkoutData): Promise<void> {
    const endpoint = `${API_BASE}/telemetry/session`;
    const headers = await getAuthHeaders();

    // Optimistic Update: Update the local cache immediately
    const cacheKey = `/api/v1/telemetry/history?session_id=${data.session_id}`;

    await globalMutate(
        cacheKey,
        async (currentData: any) => {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers,
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error('Failed to log workout session');
            return res.json();
        },
        {
            optimisticData: (currentData: any) => {
                const updated = currentData ? [...currentData] : [];
                updated.unshift({ ...data, id: 'temp-id', created_at: new Date().toISOString() });
                return updated;
            },
            rollbackOnError: true,
            populateCache: true,
            revalidate: false,
        }
    );
}

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

export type UserProfilePayload = {
    height?: string;
    weight?: string;
    age?: number;
    gender?: string;
    primary_goal?: string;
    injuries?: string;
    days_per_week?: number;
};

export async function updateUserProfile(payload: UserProfilePayload): Promise<any> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/users/profile`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
        if (!res.ok) {
            throw new Error('Failed to update profile');
        }
        return res.json();
    } catch (error) {
        console.error('Profile update error:', error);
        throw error;
    }
}

export type CoachAdaptPayload = {
    current_workout_plan?: any;
    user_feedback?: string;
    context?: string;
    trigger?: string;
    user_id?: string;
};


export type CoachAdaptResponse = {
    coaching_cue: string;
    adapted_plan: any;
};

export async function adaptWorkout(payload: CoachAdaptPayload): Promise<CoachAdaptResponse> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/coach/adapt`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
        if (res.status === 403) {
            const body = await res.json();
            if (body?.detail?.code === 'paywall_required') {
                throw new PaywallError(body.detail.message);
            }
        }
        if (!res.ok) throw new Error('Coach adaptation failed');
        return res.json();
    } catch (error) {
        console.error('Coach adapt error:', error);
        throw error;
    }
}


export async function updateTravelStatus(isTraveling: boolean, constraint: string): Promise<any> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/users/travel-status`, {
            method: 'PATCH',
            headers,
            body: JSON.stringify({ is_traveling: isTraveling, equipment_constraint: constraint }),
        });
        if (res.status === 403) {
            const body = await res.json();
            if (body?.detail?.code === 'paywall_required') {
                throw new PaywallError(body.detail.message);
            }
        }
        if (!res.ok) throw new Error('Failed to update travel status');
        return res.json();
    } catch (error) {
        console.error('Update travel status error:', error);
        throw error;
    }
}

export type OnboardingPayload = {
    age: number;
    gender: string;
    current_weight: string;
    target_weight: string;
    goal: string;
    injuries?: string;
    days_per_week: number;
};

export async function submitOnboarding(payload: OnboardingPayload): Promise<any> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/users/onboard`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Onboarding failed');
        return res.json();
    } catch (error) {
        console.error('Onboarding error:', error);
        throw error;
    }
}


export async function fetchUserProfile(): Promise<any> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/users/me`, { headers });
        if (!res.ok) throw new Error('Failed to fetch user profile');
        return res.json();
    } catch (error) {
        console.error('Fetch profile error:', error);
        return null;
    }
}


export async function fetchTodayInsight(): Promise<DailyInsight | null> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/concierge/today`, { headers });
        if (res.status === 404) return null;
        if (!res.ok) throw new Error('Failed to fetch daily insight');
        return res.json();
    } catch (error) {
        console.error('Fetch today insight error:', error);
        return null;
    }
}


// ---------------------------------------------------------------------------
// Sentry Graph — Autonomous biometric intervention
// ---------------------------------------------------------------------------
export type SessionMutation = {
    headline: string;
    advice: string;
    original_exercises_replaced: string[];
    replacement_exercises: string[];
    intensity_cap_percent: number;
    volume_reduction_percent: number;
    session_type_override: string;
};

export type SentryResult = {
    user_id: string;
    recovery_status: 'RED' | 'AMBER' | 'GREEN';
    intervention_triggered: boolean;
    session_mutation: SessionMutation | null;
    notification_payload: Record<string, unknown> | null;
    actions_taken: string[];
};

/** Manually trigger the Biometric Sentry for the current user. */
export async function triggerSentry(): Promise<SentryResult | null> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/sentry/run`, {
            method: 'POST',
            headers,
        });
        if (!res.ok) throw new Error('Sentry trigger failed');
        return res.json();
    } catch (error) {
        console.error('Sentry trigger error:', error);
        return null;
    }
}

/** Generic biomechanical audit for multi-frame kinetic analysis. */
export async function submitBiomechanicsAudit(payload: {
    movement_type: string;
    frames_b64?: string[];
    video_base64?: string;
    vectors?: number[];
    fps?: number;
}): Promise<any> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/biomechanics/audit`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Biomechanical Audit failed');
        return res.json();
    } catch (error) {
        console.error('Biomechanics audit error:', error);
        throw error;
    }
}

// ---------------------------------------------------------------------------
// Trainer Command Center (TCC) — Multi-Tenant Scale Triage
// ---------------------------------------------------------------------------
export type ClientStatus = {
    id: string;
    full_name: string;
    roi_score: number;
    last_check_in: string;
    status: 'RED' | 'AMBER' | 'GREEN';
    risk_flags: string[];
};

export async function fetchTrainerClients(): Promise<ClientStatus[]> {
    try {
        const headers = await getAuthHeaders();
        const res = await fetch(`${API_BASE}/coach/clients`, { headers });
        if (!res.ok) throw new Error('Failed to fetch trainer clients');
        return res.json();
    } catch (error) {
        console.error('Fetch trainer clients error:', error);
        return [];
    }
}

