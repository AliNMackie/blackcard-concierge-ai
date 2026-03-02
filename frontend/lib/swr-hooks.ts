import useSWR from 'swr';
import { fetchEvents, EventLog, fetchTodayInsight, DailyInsight } from './api';
import { useAuth } from './auth-context';

export function useEvents(refreshInterval = 5000) {
    const { user, loading } = useAuth();

    // SWR Fetcher wrapper
    const fetcher = async () => {
        return await fetchEvents();
    };

    const { data, error, isLoading, mutate } = useSWR<EventLog[]>(
        user && !loading ? '/api/events' : null,
        fetcher,
        {
            refreshInterval: refreshInterval,
            revalidateOnFocus: true,
            revalidateOnReconnect: true,
            keepPreviousData: true, // Show stale data while fetching
        }
    );

    return {
        events: data || [],
        isLoading: isLoading || loading,
        isError: error,
        mutate,
    };
}

export function useUnreadCount() {
    // Mock unread count logic for now, or derive from events
    const { events } = useEvents(30000); // Poll slower for count

    // Simple logic: count events from last 24h? Or just return total length for now
    // Taking last 5 as "unread" for demo visual
    // In real app, we'd track last_read_timestamp
    return events.length > 0 ? 3 : 0;
}

export function useTodayInsight() {
    const { user, loading } = useAuth();

    const { data, error, isLoading, mutate } = useSWR<DailyInsight | null>(
        user && !loading ? '/api/concierge/today' : null,
        fetchTodayInsight,
        {
            revalidateOnFocus: true,
            revalidateOnReconnect: true,
            shouldRetryOnError: false
        }
    );

    return {
        insight: data || null,
        isLoading: isLoading || loading,
        isError: error,
        mutate,
    };
}
