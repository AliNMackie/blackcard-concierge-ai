"use client";

import { useEffect, useState } from 'react';
import { fetchEvents, EventLog, triggerOverride } from '@/lib/api';
import { Activity, Zap, CheckCircle, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import { formatDistanceToNow } from 'date-fns';

export default function GodModePage() {
    const [events, setEvents] = useState<EventLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchEvents();
            setEvents(data);
        } catch (err: any) {
            if (err.message === 'AUTH_ERROR') {
                setError('AUTH');
            } else {
                setError('NETWORK');
            }
        }
        setLoading(false);
    }

    async function handleOverride(id: number) {
        if (confirm("Confirm Manual Intervention Override?")) {
            await triggerOverride(id.toString(), "MANUAL_INTERVENTION");
            alert("Intervention Protocol Initiated.");
        }
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 font-sans">
            <header className="mb-10 flex justify-between items-center border-b border-gray-800 pb-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter">GOD MODE</h1>
                    <p className="text-gray-500 text-sm tracking-widest uppercase">Elite Concierge Overview</p>
                </div>
                <button
                    onClick={loadData}
                    className="bg-white text-black px-4 py-2 text-sm font-bold uppercase tracking-wider hover:bg-gray-200 transition"
                >
                    Refresh Data
                </button>
            </header>

            {error === 'AUTH' ? (
                <div className="flex flex-col items-center justify-center py-20 text-red-500 animate-in fade-in">
                    <AlertTriangle size={48} className="mb-4" />
                    <h2 className="text-2xl font-bold tracking-widest uppercase">Access Denied</h2>
                    <p className="text-gray-500 mt-2">Biometric clearance level insufficient.</p>
                    <p className="text-xs text-gray-700 mt-4 font-mono">ERR_CODE: 403_FORBIDDEN</p>
                </div>
            ) : loading ? (
                <div className="flex justify-center py-20 animate-pulse text-gray-500">
                    Connecting to Biometric Stream...
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                                <th className="py-4 font-normal">Timestamp</th>
                                <th className="py-4 font-normal">Event Type</th>
                                <th className="py-4 font-normal">Agent Decision</th>
                                <th className="py-4 font-normal">AI Message</th>
                                <th className="py-4 font-normal text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-900">
                            {events.map((event) => (
                                <tr key={event.id} className="group hover:bg-gray-900/50 transition duration-150">
                                    <td className="py-4 text-sm text-gray-400">
                                        {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                                    </td>
                                    <td className="py-4">
                                        <span className={clsx(
                                            "px-2 py-1 rounded text-xs font-bold uppercase tracking-wide border",
                                            event.event_type === 'wearable' ? "bg-red-900/20 text-red-400 border-red-900/30" :
                                                event.event_type === 'vision' ? "bg-blue-900/20 text-blue-400 border-blue-900/30" :
                                                    "bg-gray-800 text-gray-400 border-gray-700"
                                        )}>
                                            {event.event_type}
                                        </span>
                                    </td>
                                    <td className="py-4 text-sm font-medium">
                                        {event.agent_decision === "RED" && <span className="text-red-500 flex items-center gap-2"><AlertTriangle size={14} /> RED ALERT</span>}
                                        {event.agent_decision === "GREEN" && <span className="text-green-500 flex items-center gap-2"><CheckCircle size={14} /> OPTIMAL</span>}
                                        {event.agent_decision === "WORKOUT_GENERATED" && <span className="text-blue-400 flex items-center gap-2"><Activity size={14} /> PLAN READY</span>}
                                        {!["RED", "GREEN", "WORKOUT_GENERATED"].includes(event.agent_decision || "") && event.agent_decision}
                                    </td>
                                    <td className="py-4 text-sm text-gray-400 max-w-md truncate">
                                        {event.agent_message}
                                    </td>
                                    <td className="py-4 text-right">
                                        <button
                                            onClick={() => handleOverride(event.id)}
                                            className="text-xs uppercase font-bold text-gray-600 hover:text-white transition group-hover:visible"
                                        >
                                            Override
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {events.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="py-10 text-center text-gray-600">
                                        No events detected. Platform is quiet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
