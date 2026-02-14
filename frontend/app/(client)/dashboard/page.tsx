"use client";

import { useEffect } from 'react';
import { fetchEvents, EventLog } from '@/lib/api';
import { useEvents } from '@/lib/swr-hooks';
import { Activity, Heart, Camera, MessageSquare, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { requestNotificationPermission } from '@/lib/firebase-messaging';
import { getIdToken } from '@/lib/firebase';

export default function ClientDashboard() {
    const { events, isLoading } = useEvents(5000); // Poll every 5s

    // Notification Registration
    useEffect(() => {
        const registerForPush = async () => {
            if (typeof window !== 'undefined' && 'Notification' in window) {
                const token = await requestNotificationPermission();
                if (token) {
                    // Send to Backend
                    try {
                        const idToken = await getIdToken();
                        const { getApiUrl } = await import('@/lib/api');
                        const API_BASE = getApiUrl();

                        await fetch(`${API_BASE}/notifications/subscribe`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${idToken}`
                            },
                            body: JSON.stringify({ token })
                        });
                        console.log('Subscribed to Push Notifications');
                    } catch (e) {
                        console.error('Failed to subscribe to push', e);
                    }
                }
            }
        };
        registerForPush();
    }, []);

    return (
        <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-gray-900">

            {/* Header */}
            <div className="p-8 pb-4 flex justify-between items-end">
                <div>
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-500 mb-1">Elite Concierge</h2>
                    <h1 className="text-4xl font-light tracking-tight text-white">Hello, Alastair.</h1>
                </div>
                {/* Live Indicator */}
                {!isLoading && (
                    <div className="flex items-center gap-1.5 mb-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        <span className="text-[10px] uppercase font-bold text-green-500 tracking-wider">Live</span>
                    </div>
                )}
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

        </div>
    );
}
