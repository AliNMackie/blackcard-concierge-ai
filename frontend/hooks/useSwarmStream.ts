/*
  useSwarmStream.ts - Level 4 Autonomous Orchestration
  Custom hook to consume the NDJSON stream from the Multi-Agent Swarm endpoint.
*/
'use client';

import { useState, useCallback } from 'react';

// Expected shape from the backend stream
export interface SwarmStreamChunk {
    agent_name: string;
    scratchpad?: string;
    tool_call?: string;
    is_final?: boolean;
    output?: any;
}

export interface SwarmEvent {
    id: string;
    agentName: string;
    content: string;
    type: 'thought' | 'action' | 'result';
    timestamp: Date;
}

export const useSwarmStream = () => {
    const [events, setEvents] = useState<SwarmEvent[]>([]);
    const [isActive, setIsActive] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [finalResult, setFinalResult] = useState<any | null>(null);

    const triggerSwarm = useCallback(async (userId: string, eventType: string, payload: any) => {
        setIsActive(true);
        setError(null);
        setEvents([]);
        setFinalResult(null);

        try {
            const response = await fetch('/api/v1/swarm/trigger/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'Authorization': `Bearer ${token}` // Assuming AuthContext provides this in a real setting
                },
                body: JSON.stringify({
                    user_id: userId,
                    event_type: eventType,
                    event_payload: payload,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            if (!response.body) {
                throw new Error('ReadableStream not yet supported in this browser.');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');

                // Keep the last partial line in the buffer
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.trim() === '') continue;

                    try {
                        const chunk: SwarmStreamChunk = JSON.parse(line);

                        if (chunk.is_final) {
                            setFinalResult(chunk.output);
                            // We don't add the final result to the events timeline directly here,
                            // let the UI handle the finalResult state.
                        } else {
                            const newEvent: SwarmEvent = {
                                id: crypto.randomUUID(),
                                agentName: chunk.agent_name,
                                content: chunk.tool_call || chunk.scratchpad || 'Analyzing...',
                                type: chunk.tool_call ? 'action' : 'thought',
                                timestamp: new Date(),
                            };

                            setEvents((prev) => [...prev, newEvent]);
                        }
                    } catch (e) {
                        console.error('Failed to parse NDJSON chunk:', line, e);
                    }
                }
            }
        } catch (err: any) {
            console.error('Swarm stream error:', err);
            setError(err.message || 'Connection to the Swarm lost.');
        } finally {
            setIsActive(false);
        }
    }, []);

    return {
        events,
        isActive,
        finalResult,
        error,
        triggerSwarm,
    };
};
