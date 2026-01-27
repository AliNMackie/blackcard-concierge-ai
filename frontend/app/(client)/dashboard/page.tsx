"use client";

import { useEffect, useState } from 'react';
import { fetchEvents, EventLog } from '@/lib/api';
import { Activity, Heart, Camera, MessageSquare } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function ClientDashboard() {
    const [events, setEvents] = useState<EventLog[]>([]);

    useEffect(() => {
        fetchEvents(10).then(setEvents);
    }, []);

    return (
        <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-gray-900">

            {/* Header */}
            <div className="p-8 pb-4">
                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-500 mb-1">Elite Concierge</h2>
                <h1 className="text-4xl font-light tracking-tight text-white">Hello, Alastair.</h1>
            </div>

            {/* Main Status Card */}
            <div className="px-6 mb-8">
                <div className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
                    <div className="relative z-10">
                        <div className="text-gray-400 text-xs uppercase tracking-wider mb-2">Readiness Status</div>
                        <div className="text-3xl font-medium text-white mb-1">Optimal</div>
                        <div className="text-sm text-gray-500">Recovery score trending upward.</div>
                    </div>
                </div>
            </div>

            {/* Activity Feed */}
            <div className="px-6 space-y-4">
                <h3 className="text-sm font-bold text-gray-700 uppercase tracking-widest mb-4">Recent Activity</h3>

                {events.map((evt) => (
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

                {events.length === 0 && (
                    <div className="text-center py-10 text-gray-700 text-sm">
                        Waiting for biometric stream...
                    </div>
                )}

            </div>

            {/* Tab Bar Placeholder */}
            <div className="fixed bottom-0 left-0 right-0 border-t border-gray-900 bg-black/90 backdrop-blur pb-6 pt-4 flex justify-around text-gray-500 max-w-md mx-auto">
                <Activity size={24} className="text-white" />
                <MessageSquare size={24} />
            </div>

        </div>
    );
}
