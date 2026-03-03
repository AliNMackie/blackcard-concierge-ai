/*
  SVGOverlay.tsx - Level 5 Ambient Intelligence
  Securely layers the raw 'svg_overlay' string returned by Gemini 3.1 Pro
  directly on top of a Video element, maintaining perfect scale alignment.
*/
'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface SVGOverlayProps {
    svgOverlay: string;
    coachingCue?: string;
}

export const SVGOverlay: React.FC<SVGOverlayProps> = ({ svgOverlay, coachingCue }) => {
    return (
        <>
            {/* 
        The absolute positioned container for the SVG.
        It must occupy the exact identical bounds as its parent video container.
        Using blend modes to make it pop over the video.
      */}
            <div
                className="absolute inset-0 z-20 pointer-events-none mix-blend-screen"
                dangerouslySetInnerHTML={{ __html: svgOverlay }}
            />

            {/* Animated Scanning Grid (Subtle Ambient effect) */}
            <div className="absolute inset-0 z-10 pointer-events-none opacity-20 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:40px_40px]" />

            {/* The Coaching Cue */}
            {coachingCue && (
                <motion.div
                    initial={{ y: 50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    className="absolute bottom-8 left-1/2 -translate-x-1/2 z-30 w-[90%] max-w-lg"
                >
                    <div className="p-5 rounded-2xl backdrop-blur-xl bg-slate-900/60 border border-slate-700/50 shadow-2xl flex items-start gap-4">
                        <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" /><path d="m9 12 2 2 4-4" /></svg>
                        </div>
                        <div>
                            <h4 className="text-white font-bold tracking-tight mb-1 text-sm uppercase">Form Correction</h4>
                            <p className="text-slate-300 text-sm leading-relaxed">
                                {coachingCue}
                            </p>
                        </div>
                    </div>
                </motion.div>
            )}
        </>
    );
};
