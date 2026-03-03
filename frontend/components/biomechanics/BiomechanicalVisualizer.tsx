/*
  BiomechanicalVisualizer.tsx — Level 5 Ambient Intelligence UI
  Renders a high-fidelity SVG overlay representing joint paths and 
  mechanical drift provided by Gemini 3.1 Pro via the Biomechanics Audit API.
*/
'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface BiomechanicalVisualizerProps {
    svgOverlay: string; // The raw <svg> string from the backend
    interventionCue?: string;
    driftScore?: number;
    isLoading?: boolean;
    className?: string;
    isTravelMode?: boolean;
}

export const BiomechanicalVisualizer: React.FC<BiomechanicalVisualizerProps> = ({
    svgOverlay,
    interventionCue,
    driftScore = 0,
    isLoading = false,
    className = '',
    isTravelMode = false,
}) => {
    // Determine if it's a high-drift (red) or low-drift (green) movement
    const isHighDrift = driftScore > 0.15;
    const accentColor = isTravelMode ? 'text-amber-400' : (isHighDrift ? 'text-rose-400' : 'text-emerald-400');
    const gradientColor = isTravelMode ? 'from-amber-500/20' : (isHighDrift ? 'from-rose-500/20' : 'from-emerald-500/20');

    return (
        <div className={`relative w-full aspect-video rounded-3xl overflow-hidden bg-slate-900 shadow-2xl ${className}`}>
            {/* 1. Loading State */}
            <AnimatePresence>
                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-slate-900/80 backdrop-blur-md"
                    >
                        <div className="w-12 h-12 border-4 border-slate-700 border-t-white rounded-full animate-spin mb-4" />
                        <p className="text-white/60 font-medium tracking-tight">Gemini analyzing biomechanics...</p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* 2. The Biomechanical SVG Overlay Layer */}
            <div
                className="absolute inset-0 z-20 pointer-events-none mix-blend-screen"
                dangerouslySetInnerHTML={{ __html: svgOverlay }}
            />

            {/* Background image placeholder (In production, this would be a <video> or <img>) */}
            <div className="absolute inset-0 z-10 opacity-30 bg-[url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center" />

            {/* 3. Ambient Scan Line Animation */}
            <motion.div
                animate={{ translateY: ['0%', '100%', '0%'] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                className={`absolute inset-x-0 h-1 z-30 bg-gradient-to-r from-transparent ${isTravelMode ? 'via-amber-400/50' : 'via-white/30'} to-transparent`}
            />

            {/* 4. The Intervention Cue (Bottom Overlay) */}
            {interventionCue && (
                <motion.div
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className={`absolute bottom-6 left-6 right-6 z-40 p-6 rounded-2xl backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl`}
                >
                    <div className="flex items-start gap-4">
                        <div className={`mt-1 p-2 rounded-lg bg-white/10 ${accentColor}`}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m16 6-4 4-4-4" /><path d="M12 2v8" /><rect width="20" height="12" x="2" y="10" rx="2" /></svg>
                        </div>
                        <div>
                            <h4 className="text-white font-bold text-lg mb-1 tracking-tight">Intervention Cue</h4>
                            <p className="text-white/70 text-sm leading-relaxed max-w-md">
                                {interventionCue}
                            </p>
                        </div>
                        <div className="ml-auto flex flex-col items-end">
                            <span className="text-white/40 text-[10px] uppercase font-black tracking-widest mb-1">Mechanical Drift</span>
                            <div className={`text-2xl font-black tabular-nums ${accentColor}`}>
                                {(driftScore * 100).toFixed(1)}%
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* 5. Top Status Badge */}
            <div className="absolute top-6 left-6 z-40 flex gap-2">
                <div className={`px-4 py-2 rounded-full backdrop-blur-md bg-white/10 border border-white/10 flex items-center gap-2`}>
                    <div className={`w-2 h-2 rounded-full animate-pulse ${isHighDrift ? 'bg-rose-400' : 'bg-emerald-400'}`} />
                    <span className="text-white text-xs font-bold uppercase tracking-widest">
                        {isHighDrift ? 'Kinetic Deviation' : 'Optimal Path'}
                    </span>
                </div>
                {isTravelMode && (
                    <div className="px-4 py-2 rounded-full backdrop-blur-md bg-amber-500/20 border border-amber-500/30 text-amber-400 text-xs font-bold uppercase tracking-widest">
                        Travel Logic Active
                    </div>
                )}
            </div>
        </div>
    );
};
