/*
  AgentSwarmVisualizer.tsx - Level 4 Autonomous Orchestration
  Visualizes the real-time "thinking" process and handoffs between the LangGraph agents.
*/
'use client';

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SwarmEvent } from '@/hooks/useSwarmStream';

interface AgentSwarmVisualizerProps {
    events: SwarmEvent[];
    isActive: boolean;
    finalResult: any | null;
    error: string | null;
}

// Map agent names to elegant, muted colors
const agentColors: Record<string, string> = {
    'Supervisor': 'border-slate-500 text-slate-300',
    'RecoveryAgent': 'border-emerald-500/50 text-emerald-300',
    'PerformanceAgent': 'border-blue-500/50 text-blue-300',
    'NutritionAgent': 'border-amber-500/50 text-amber-300',
};

export const AgentSwarmVisualizer: React.FC<AgentSwarmVisualizerProps> = ({
    events,
    isActive,
    finalResult,
    error,
}) => {
    const endOfListRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to the bottom as new events arrive
    useEffect(() => {
        endOfListRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [events]);

    const activeAgent = isActive && events.length > 0 ? events[events.length - 1].agentName : null;

    return (
        <div className="w-full max-w-2xl mx-auto bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[500px]">
            {/* Header */}
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between z-10">
                <div>
                    <h3 className="text-white font-bold tracking-tight">Concierge Swarm</h3>
                    <p className="text-slate-500 text-xs font-medium uppercase tracking-widest mt-0.5">
                        Multi-Agent Orchestration
                    </p>
                </div>
                {isActive ? (
                    <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                        </span>
                        <span className="text-emerald-400 text-xs font-bold uppercase tracking-widest">Active</span>
                    </div>
                ) : (
                    <div className="flex items-center gap-2">
                        <span className="h-2.5 w-2.5 rounded-full bg-slate-600"></span>
                        <span className="text-slate-500 text-xs font-bold uppercase tracking-widest">Idle</span>
                    </div>
                )}
            </div>

            {/* Event Stream Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 relative">
                <AnimatePresence initial={false}>
                    {events.map((event, i) => {
                        const isLast = i === events.length - 1;
                        const colorClass = agentColors[event.agentName] || agentColors['Supervisor'];

                        return (
                            <motion.div
                                key={event.id}
                                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                className="flex gap-4"
                            >
                                {/* Timeline connector visual */}
                                <div className="flex flex-col items-center">
                                    <div className={`w-2.5 h-2.5 rounded-full border-2 bg-slate-900 z-10 ${colorClass}`} />
                                    {!isLast && <div className="w-px h-full bg-slate-800 my-1 rounded-full" />}
                                </div>

                                <div className="flex-1 pb-4">
                                    <div className="flex items-baseline gap-2 mb-1">
                                        <span className="text-white text-sm font-semibold">{event.agentName}</span>
                                        <span className="text-slate-500 text-[10px] uppercase tracking-wider font-medium">
                                            {event.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </span>
                                    </div>
                                    <div className="bg-slate-800/40 rounded-2xl p-4 border border-slate-700/50">
                                        <p className={`text-sm leading-relaxed ${event.type === 'action' ? 'text-amber-200 font-medium' : 'text-slate-300'}`}>
                                            {event.type === 'action' && <span className="mr-2 opacity-70">⚡</span>}
                                            {event.content}
                                        </p>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>

                {/* Active Thinking Indicator */}
                {isActive && activeAgent && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-4 items-center pl-8 text-slate-500 text-sm font-medium"
                    >
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                        </div>
                        <span>{activeAgent} is thinking...</span>
                    </motion.div>
                )}

                {error && (
                    <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
                        {error}
                    </div>
                )}

                {finalResult && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-6 rounded-3xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 mt-4"
                    >
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-2 bg-indigo-500/20 rounded-xl text-indigo-400">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                            </div>
                            <h4 className="text-white font-bold tracking-tight">Consensus Reached</h4>
                        </div>
                        <p className="text-slate-300 text-sm leading-relaxed mb-4">
                            The Swarm has successfully analyzed the context and finalized the optimal intervention.
                        </p>
                        <pre className="text-indigo-200 text-xs bg-black/30 p-4 rounded-2xl overflow-x-auto font-mono">
                            {JSON.stringify(finalResult, null, 2)}
                        </pre>
                    </motion.div>
                )}

                <div ref={endOfListRef} className="h-4" />
            </div>
        </div>
    );
};
