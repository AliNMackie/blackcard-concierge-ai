"use client";

import { useEffect, useState } from 'react';
import { fetchEvents, EventLog, triggerIntervention, adminUpdateUser } from '@/lib/api';
import { Activity, Zap, CheckCircle, AlertTriangle, UserCog, RefreshCw } from 'lucide-react';
import { clsx } from 'clsx';
import { formatDistanceToNow } from 'date-fns';

const PERSONAS = [
    { id: 'hyrox_competitor', label: 'Hyrox Athlete' },
    { id: 'empowered_mum', label: 'Empowered Mum' },
    { id: 'muscle_architect', label: 'Muscle Architect' },
    { id: 'bio_optimizer', label: 'Bio-Optimizer' }
];

export default function GodModePage() {
    const [events, setEvents] = useState<EventLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activePersona, setActivePersona] = useState<string>("hyrox_competitor"); // Default state for demo

    useEffect(() => {
        loadData();
    }, []);

    async function loadData() {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchEvents();
            setEvents(data);
            // In a real app, we'd fetch all users. For MVP, we assume User "1" is the main demo.
        } catch (err: any) {
            if (err.message === 'AUTH_ERROR') {
                setError('AUTH');
            } else {
                setError('NETWORK');
            }
        }
        setLoading(false);
    }

    async function handlePersonaChange(newStyle: string) {
        // Optimistic UI update
        setActivePersona(newStyle);
        try {
            await adminUpdateUser("1", { coach_style: newStyle });
            alert(`Client Persona forced to: ${newStyle}`);
        } catch (e) {
            alert("Failed to override persona");
        }
    }

    async function handleIntervention(clientId: string) {
        setLoading(true);
        try {
            await triggerIntervention(clientId);
            await loadData();
        } catch (err) {
            alert("Ghostwriter failed to engage. Check logs.");
        }
        setLoading(false);
    }

    return (
        <div className="min-h-screen bg-black text-white p-6 font-sans">
            <header className="mb-10 flex justify-between items-start border-b border-gray-800 pb-6">
                <div>
                    <h1 className="text-3xl font-bold tracking-tighter text-white">GOD MODE</h1>
                    <p className="text-gray-500 text-sm tracking-widest uppercase mb-4">Elite Concierge Overview</p>

                    {/* Active Client Control (MVP: Hardcoded for Demo Client) */}
                    <div className="flex items-center gap-4 bg-zinc-900 border border-zinc-800 p-3 rounded-lg">
                        <UserCog size={20} className="text-blue-400" />
                        <div>
                            <p className="text-[10px] text-gray-500 uppercase font-bold">Client: Alastair (Demo)</p>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-300">Force Persona:</span>
                                <select
                                    value={activePersona}
                                    onChange={(e) => handlePersonaChange(e.target.value)}
                                    className="bg-black border border-gray-700 text-xs rounded px-2 py-1 text-white focus:outline-none focus:border-blue-500"
                                >
                                    {PERSONAS.map(p => (
                                        <option key={p.id} value={p.id}>{p.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <a
                        href="/personas"
                        className="flex items-center gap-2 bg-zinc-800 text-white px-4 py-2 text-sm font-bold uppercase tracking-wider hover:bg-zinc-700 transition rounded-sm border border-zinc-700"
                    >
                        <UserCog size={16} /> View Personas
                    </a>
                    <button
                        onClick={loadData}
                        className="flex items-center gap-2 bg-white text-black px-4 py-2 text-sm font-bold uppercase tracking-wider hover:bg-gray-200 transition rounded-sm"
                    >
                        <RefreshCw size={16} /> Refresh Stream
                    </button>
                </div>
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
                <div className="space-y-4">
                    {/* Desktop Table: Hidden on Mobile */}
                    <div className="hidden md:block overflow-x-auto rounded-xl border border-gray-800">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-zinc-900/50 text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                                    <th className="py-4 pl-6 font-normal">Timestamp</th>
                                    <th className="py-4 font-normal">Client</th>
                                    <th className="py-4 font-normal">Event Type</th>
                                    <th className="py-4 font-normal">Agent Decision</th>
                                    <th className="py-4 font-normal">AI Message</th>
                                    <th className="py-4 pr-6 font-normal text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-900">
                                {events.map((event) => (
                                    <tr key={event.id} className="group hover:bg-gray-900/50 transition duration-150">
                                        <td className="py-4 pl-6 text-sm text-gray-400 font-mono">
                                            {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                                        </td>
                                        <td className="py-4 text-sm font-mono text-blue-400/80">
                                            {event.user_id}
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
                                        <td className="py-4 text-sm text-gray-400 max-w-xs truncate">
                                            {event.agent_message}
                                        </td>
                                        <td className="py-4 pr-6 text-right">
                                            <button
                                                onClick={() => handleIntervention(event.user_id)}
                                                className="bg-blue-600/10 text-blue-400 border border-blue-600/20 px-3 py-1 rounded text-[10px] font-black uppercase tracking-tighter hover:bg-blue-600 hover:text-white transition"
                                            >
                                                Intervene
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Mobile Card Feed: Visible on Mobile */}
                    <div className="md:hidden space-y-4">
                        {events.map((event) => (
                            <div key={event.id} className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg relative overflow-hidden">
                                {/* Top Badges */}
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex gap-2 items-center">
                                        <span className={clsx(
                                            "w-2 h-2 rounded-full",
                                            event.event_type === 'wearable' ? "bg-red-500" :
                                                event.event_type === 'vision' ? "bg-blue-500" : "bg-white"
                                        )} />
                                        <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-widest">
                                            {event.event_type} • {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                                        </span>
                                    </div>
                                    <div className="text-[10px] font-black uppercase tracking-widest bg-black/50 px-2 py-1 rounded text-zinc-300 border border-zinc-700">
                                        {event.agent_decision}
                                    </div>
                                </div>

                                {/* Main Content */}
                                <div className="mb-4">
                                    <p className="text-sm text-zinc-300 leading-relaxed font-medium">
                                        "{event.agent_message}"
                                    </p>
                                </div>

                                {/* Detailed Footer */}
                                <div className="pt-4 border-t border-zinc-800 flex justify-between items-center">
                                    <div className="text-[10px] text-zinc-600 font-mono">
                                        ID: {event.user_id}
                                    </div>
                                    <button
                                        onClick={() => handleIntervention(event.user_id)}
                                        className="flex items-center gap-2 bg-blue-500/10 text-blue-400 px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 hover:text-white transition border border-blue-500/20"
                                    >
                                        <Zap size={12} /> Trigger Intervention
                                    </button>
                                </div>

                                {/* Decor */}
                                {event.agent_decision === "RED" && <div className="absolute right-0 top-0 w-20 h-20 bg-red-500/10 blur-2xl pointer-events-none" />}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
