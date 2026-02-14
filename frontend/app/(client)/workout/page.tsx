"use client";

import Link from "next/link";
import { Zap, Clock, ChevronRight } from "lucide-react";

const WORKOUTS = [
    {
        id: "session_123",
        name: "Leg Day Destruction",
        duration: "45m",
        intensity: "High",
        exercises: "3 movements",
        icon: "🦵",
        color: "bg-blue-900/40"
    },
    {
        id: "session_456",
        name: "Upper Body Hypertrophy",
        duration: "50m",
        intensity: "Moderate",
        exercises: "5 movements",
        icon: "💪",
        color: "bg-amber-900/40"
    }
];

export default function WorkoutsPage() {
    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            <header className="mb-10 pt-4">
                <h1 className="text-4xl font-bold tracking-tighter mb-2">My Protocols</h1>
                <p className="text-gray-500 text-sm uppercase tracking-widest font-medium">Daily AI-Generated Sessions</p>
            </header>

            <div className="space-y-6">
                <section>
                    <h2 className="text-xs font-bold text-gray-700 uppercase tracking-widest mb-4">Recommended Today</h2>
                    {WORKOUTS.map((workout) => (
                        <Link
                            key={workout.id}
                            href={`/workout/${workout.id}`}
                            className="block group"
                        >
                            <div className={`p-5 rounded-2xl border border-gray-800 ${workout.color} hover:border-gray-600 transition-all flex items-center justify-between`}>
                                <div className="flex items-center gap-4">
                                    <div className="text-3xl">{workout.icon}</div>
                                    <div>
                                        <h3 className="font-bold text-white group-hover:text-amber-400 transition-colors uppercase tracking-tight">{workout.name}</h3>
                                        <div className="flex items-center gap-3 mt-1">
                                            <span className="flex items-center gap-1 text-[10px] text-gray-400 font-bold uppercase">
                                                <Clock size={10} /> {workout.duration}
                                            </span>
                                            <span className="flex items-center gap-1 text-[10px] text-amber-500/80 font-bold uppercase">
                                                <Zap size={10} className="fill-amber-500/80" /> {workout.intensity}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <ChevronRight className="text-gray-600 group-hover:text-white transition" />
                            </div>
                        </Link>
                    ))}
                </section>

                <section>
                    <h2 className="text-xs font-bold text-gray-700 uppercase tracking-widest mb-4">Past Sessions</h2>
                    <div className="bg-zinc-900/30 border border-zinc-800/50 rounded-2xl p-6 text-center">
                        <p className="text-gray-500 text-sm">No historical data found in biometric stream.</p>
                    </div>
                </section>
            </div>
        </div>
    );
}
