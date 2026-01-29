"use client";

import { useEffect, useState } from 'react';
import { clsx } from 'clsx';
import { fetchEvents, EventLog, toggleTravel, fetchTravelStatus } from '@/lib/api';
import { Activity, Heart, Camera, MessageSquare, Plane, Users, Trophy } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

export default function ClientDashboard() {
    const [events, setEvents] = useState<EventLog[]>([]);
    const [loading, setLoading] = useState(false);
    const [isTraveling, setIsTraveling] = useState(false);

    useEffect(() => {
        loadData();
        checkTravelStatus();
    }, []);

    async function loadData() {
        setLoading(true);
        const data = await fetchEvents(10);
        setEvents(data);
        setLoading(false);
    }

    async function checkTravelStatus() {
        try {
            const status = await fetchTravelStatus();
            setIsTraveling(status.is_traveling);
        } catch (e) {
            console.error("Failed to fetch travel status", e);
        }
    }

    async function handleToggleTravel() {
        try {
            const status = await toggleTravel();
            setIsTraveling(status.is_traveling);
        } catch (e) {
            alert("Failed to update travel status");
        }
    }

    return (
        <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-gray-900">

            {/* Header */}
            <div className="p-8 pb-4">
                <div className="flex justify-between items-start mb-4">
                    <div className="flex flex-col gap-1 items-start">
                        <button
                            onClick={handleToggleTravel}
                            className={clsx(
                                "flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest transition-all",
                                isTraveling ? "bg-blue-500 text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]" : "bg-zinc-800 text-zinc-500 hover:text-white"
                            )}
                        >
                            <Plane size={12} className={isTraveling ? "animate-pulse" : ""} />
                            {isTraveling ? "Travel mode ON" : "Travel mode OFF"}
                        </button>
                    </div>
                    <button
                        onClick={loadData}
                        disabled={loading}
                        className="text-xs font-bold uppercase tracking-wider text-gray-600 hover:text-white transition disabled:opacity-50"
                    >
                        {loading ? 'Syncing...' : 'Refresh'}
                    </button>
                </div>
                <div>
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-500 mb-1 flex items-center gap-2">
                        Elite Concierge
                        <span className="bg-green-500/10 text-green-500 px-2 py-0.5 rounded text-[8px] tracking-widest border border-green-500/20">
                            ⌚ Apple Watch: Connected
                        </span>
                    </h2>
                    <h1 className="text-4xl font-light tracking-tight text-white">Hello, Alastair.</h1>
                </div>
            </div>

            {/* Main Status Card */}
            <div className="px-6 mb-2">
                <div className="bg-gradient-to-br from-zinc-900 to-black border border-zinc-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
                    <div className="relative z-10">
                        <div className="text-zinc-500 text-xs uppercase tracking-wider mb-2">Readiness Status</div>
                        <div className="text-3xl font-medium text-amber-500 mb-1">Low / Recovery Mode</div>
                        <div className="text-sm text-zinc-500 font-light">Sleep score 45 requires active recovery.</div>
                    </div>
                </div>
            </div>

            {/* The Active Protocol Card */}
            <div className="px-6 mb-8">
                <div className="bg-zinc-900 border border-amber-500/20 p-6 rounded-2xl shadow-xl flex justify-between items-center group hover:border-amber-500/40 transition-all">
                    <div>
                        <h3 className="text-zinc-500 text-[10px] uppercase tracking-[0.2em] font-bold">Today's Objective</h3>
                        <p className="text-xl font-bold text-white mt-1">Sled Push & Stability</p>
                        <p className="text-[10px] text-zinc-400 mt-1 uppercase tracking-wider opacity-60">45 Mins • Low Impact • Recovery Focus</p>
                    </div>
                    <Link
                        href="/gym-mode"
                        className="bg-amber-500 text-black font-black px-8 py-3 rounded-xl hover:bg-amber-400 transition active:scale-95 shadow-[0_0_20px_rgba(245,158,11,0.2)]"
                    >
                        START
                    </Link>
                </div>
            </div>

            {/* Activity Feed */}
            <div className="px-6 space-y-4">
                <h3 className="text-sm font-bold text-gray-700 uppercase tracking-widest mb-4">Recent Activity</h3>

                {loading && events.length === 0 ? (
                    <div className="text-center py-10 text-gray-700 text-xs animate-pulse">Syncing biometric data...</div>
                ) : events.map((evt) => (
                    <div key={evt.id} className="flex gap-4 items-start py-3 border-b border-gray-900/50">
                        <div className="mt-1">
                            {evt.event_type === 'wearable' && <Heart className="text-red-500" size={20} />}
                            {evt.event_type === 'vision' && <Camera className="text-blue-500" size={20} />}
                            {evt.event_type === 'chat' && <MessageSquare className="text-white" size={20} />}
                        </div>
                        <div>
                            <div className="text-sm font-medium text-gray-200">
                                {evt.event_type === 'wearable' ? 'Biometric Analysis' :
                                    evt.event_type === 'vision' ? 'Visual Analysis' : 'Concierge Chat'}
                            </div>
                            <p className="text-xs text-gray-500 leading-snug mt-1 line-clamp-2">
                                {evt.agent_message}
                            </p>
                            <div className="text-[10px] text-gray-600 mt-2 font-mono uppercase">
                                {formatDistanceToNow(new Date(evt.created_at))} ago
                            </div>
                        </div>
                    </div>
                ))}

                {!loading && events.length === 0 && (
                    <div className="text-center py-10 text-gray-700 text-sm">
                        Waiting for biometric stream...
                    </div>
                )}

            </div>

            {/* Tab Bar Placeholder */}
            <div className="fixed bottom-0 left-0 right-0 border-t border-gray-900 bg-black/90 backdrop-blur pb-6 pt-4 flex justify-around text-gray-500 max-w-md mx-auto">
                <Link href="/dashboard"><Activity size={24} className="text-white" /></Link>
                <Link href="/personas"><Users size={24} className="hover:text-white transition" /></Link>
                <Link href="/performance"><Trophy size={24} className="hover:text-white transition" /></Link>
                <Link href="/messages"><MessageSquare size={24} className="hover:text-white transition" /></Link>
            </div>

        </div>
    );
}
