/*
  app/(client)/session/active/page.tsx
  A focused, distraction-free view for an active workout session.
  Integrates the FormScanner inside an animated glassmorphic modal.
*/
import React from 'react';
import { ActiveSessionClient } from './ActiveSessionClient';

export const metadata = {
    title: 'Active Session | Blackcard Concierge',
};

// Next.js 16 Server Component (mocking the session fetch)
export default async function ActiveSessionPage() {
    // Mock fetch for current workout session state
    const mockSession = {
        exercise: 'Barbell Back Squat',
        targetSets: 4,
        currentSet: 3,
        reps: 8,
        weight: '140kg',
        rpeTarget: 8.5
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white selection:bg-rose-500/30 p-6 md:p-12 font-sans tracking-tight">
            <header className="flex justify-between items-center mb-16">
                <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse" />
                    <span className="text-rose-500 font-bold uppercase tracking-widest text-xs">Live Session</span>
                </div>
                <div className="px-4 py-2 rounded-full border border-slate-800 bg-slate-900/50 text-slate-400 text-xs font-bold uppercase tracking-widest">
                    Set {mockSession.currentSet} of {mockSession.targetSets}
                </div>
            </header>

            <main className="max-w-2xl mx-auto flex flex-col items-center justify-center pt-10">
                <h1 className="text-5xl md:text-7xl font-black mb-4 text-center">
                    {mockSession.exercise}
                </h1>
                <div className="flex gap-8 items-center mb-16">
                    <div className="flex flex-col items-center">
                        <span className="text-slate-500 text-[10px] uppercase font-black tracking-widest mb-1">Reps</span>
                        <span className="text-4xl font-black">{mockSession.reps}</span>
                    </div>
                    <div className="w-px h-12 bg-slate-800" />
                    <div className="flex flex-col items-center">
                        <span className="text-slate-500 text-[10px] uppercase font-black tracking-widest mb-1">Weight</span>
                        <span className="text-4xl font-black text-rose-400">{mockSession.weight}</span>
                    </div>
                    <div className="w-px h-12 bg-slate-800" />
                    <div className="flex flex-col items-center">
                        <span className="text-slate-500 text-[10px] uppercase font-black tracking-widest mb-1">Target RPE</span>
                        <span className="text-4xl font-black">{mockSession.rpeTarget}</span>
                    </div>
                </div>

                {/* Client Component handles the interactive modal state */}
                <ActiveSessionClient />
            </main>
        </div>
    );
}
