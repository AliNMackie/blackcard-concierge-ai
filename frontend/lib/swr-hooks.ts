import useSWR from 'swr';
import { fetchEvents, EventLog } from './api';

// SWR Fetcher wrapper
const fetcher = async () => {
    return await fetchEvents();
};

export function useEvents(refreshInterval = 5000) {
    const { data, error, isLoading, mutate } = useSWR<EventLog[]>('/api/events', fetcher, {
        refreshInterval: refreshInterval,
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        keepPreviousData: true, // Show stale data while fetching
    });

    return {
        events: data || [],
        isLoading,
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
