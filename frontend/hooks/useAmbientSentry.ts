/*
  useAmbientSentry.ts - Level 5 Ambient Intelligence
  Next.js hook maintaining a persistent WebSocket connection to the Continuous Sentry.
  Silently listens for 'ActionDispatch' events and updates the UI without page refreshes.
*/
'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

export interface AmbientEvent {
    type: 'SENTRY_ALERT' | 'ACTION_DISPATCH' | 'HEARTBEAT';
    message?: string;
    action?: string;
    payload?: any;
}

export const useAmbientSentry = (userId: string | null) => {
    const [ambientEvent, setAmbientEvent] = useState<AmbientEvent | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (!userId) return;

        // Use ws:// for local HTTP, wss:// for HTTPS in production
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Assume backend is on port 8000 for local dev
        const wsUrl = `${protocol}//localhost:8000/api/v1/streams/biometrics/${userId}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            console.log('Ambient Sentry connected.');
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
        };

        ws.onmessage = (event) => {
            try {
                const data: AmbientEvent = JSON.parse(event.data);
                console.log('Ambient Sentry Event Received:', data);
                setAmbientEvent(data);
            } catch (err) {
                console.error('Failed to parse Sentra WS message:', err);
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            console.log('Ambient Sentry disconnected. Reconnecting in 5s...');
            // Exponential backoff or simple timeout for reconnection
            reconnectTimeoutRef.current = setTimeout(connect, 5000);
        };

        ws.onerror = (error) => {
            console.error('Ambient Sentry WS Error:', error);
            ws.close(); // Triggers onclose to handle reconnect
        };
    }, [userId]);

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [connect]);

    // Expose a method for the frontend to simulate sending a wearable packet
    const simulateWearablePacket = (packet: any) => {
        if (wsRef.current && isConnected) {
            wsRef.current.send(JSON.stringify(packet));
        } else {
            console.warn("WebSocket not connected. Cannot send simulation packet.");
        }
    };

    return {
        isConnected,
        ambientEvent,
        simulateWearablePacket,
        clearEvent: () => setAmbientEvent(null),
    };
};
