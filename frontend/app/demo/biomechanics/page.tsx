/*
  Biomechanics Demo Page — Level 5 Showcase
  Demonstrates the "900-Frame Audit" by triggering a mock biomechanical analysis
  and rendering the SVG kinetic overlays.
*/
'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { BiomechanicalVisualizer } from '@/components/biomechanics/BiomechanicalVisualizer';
import { useBiomechanics } from '@/lib/use-biomechanics';

const MOCK_FRAMES = [
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
];

const DEFAULT_SVG = `
<svg width="100%" height="100%" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <path d="M50 10 L50 90" stroke="rgba(52, 211, 153, 0.5)" stroke-width="2" stroke-dasharray="2,2" fill="none" />
  <circle cx="50" cy="90" r="3" fill="#34d399" />
  <text x="55" y="88" fill="#34d399" font-size="3" font-weight="bold">HEEL STRIKE</text>
</svg>
`;

export default function BiomechanicsDemoPage() {
    const { runBiomechanicalAudit, auditResult, isLoading, error } = useBiomechanics();
    const [isTravelMode, setIsTravelMode] = useState(false);

    const handleStartAudit = () => {
        // Movement: Barbell Squat
        runBiomechanicalAudit('barbell_squat', MOCK_FRAMES);
    };

    return (
        <div className="min-h-screen bg-slate-950 text-white p-8 md:p-16 selection:bg-rose-500/30">
            <div className="max-w-4xl mx-auto">
                <header className="mb-12">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="px-3 py-1 bg-rose-500/10 text-rose-500 text-[10px] font-black uppercase tracking-widest rounded-full border border-rose-500/20">
                            Stage 5: Ambient Intelligence
                        </span>
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                        <span className="text-slate-500 text-[10px] font-black uppercase tracking-widest">
                            Multimodal Biomechanics
                        </span>
                    </div>
                    <h1 className="text-5xl md:text-6xl font-black tracking-tightest mb-6">
                        The 900-Frame <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-white to-slate-500">
                            Kinetic Audit
                        </span>
                    </h1>
                    <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
                        Continuous Situational Inference in action. Gemini 3.1 Pro analyzes
                        high-fidelity movement frames and generates dynamic SVG joint-path
                        overlays to correct form in real-time.
                    </p>
                </header>

                <section className="space-y-8">
                    {/* Main Visualizer Container */}
                    <BiomechanicalVisualizer
                        svgOverlay={auditResult?.svg_overlay || DEFAULT_SVG}
                        interventionCue={auditResult?.intervention_cue}
                        driftScore={auditResult?.drift_score}
                        isLoading={isLoading}
                        isTravelMode={isTravelMode}
                    />

                    {/* Controls Container */}
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-8 rounded-3xl bg-slate-900/50 border border-slate-800 backdrop-blur-sm">
                        <div className="flex items-center gap-6">
                            <button
                                onClick={handleStartAudit}
                                disabled={isLoading}
                                className="px-8 py-4 bg-white text-slate-950 rounded-2xl font-black text-sm uppercase tracking-widest hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
                            >
                                {isLoading ? 'Analyzing...' : 'Trigger Audit'}
                            </button>

                            <div className="flex items-center gap-3">
                                <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Travel Mode</label>
                                <button
                                    onClick={() => setIsTravelMode(!isTravelMode)}
                                    className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 ${isTravelMode ? 'bg-amber-400' : 'bg-slate-700'}`}
                                >
                                    <div className={`w-4 h-4 bg-white rounded-full transition-transform duration-300 ${isTravelMode ? 'translate-x-6' : 'translate-x-0'}`} />
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="flex items-center gap-3 text-rose-400 text-xs font-bold bg-rose-400/10 px-4 py-2 rounded-xl border border-rose-400/20">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                                {error}
                            </div>
                        )}

                        {!auditResult && !isLoading && !error && (
                            <p className="text-slate-500 text-xs italic">
                                Tap trigger to simulate a Gemini biomechanical analysis.
                            </p>
                        )}
                    </div>

                    {/* Technical Specs Overlay */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-6 rounded-3xl bg-slate-900/30 border border-slate-800/50">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Inference Mode</span>
                            <p className="text-white font-bold">Vector Similarity (pgvector)</p>
                        </div>
                        <div className="p-6 rounded-3xl bg-slate-900/30 border border-slate-800/50">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Vision Model</span>
                            <p className="text-white font-bold">Gemini 3.1 Pro (Multimodal)</p>
                        </div>
                        <div className="p-6 rounded-3xl bg-slate-900/30 border border-slate-800/50">
                            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 block">Rendering Latency</span>
                            <p className="text-white font-bold">&lt; 2.8s (SVG Native)</p>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
