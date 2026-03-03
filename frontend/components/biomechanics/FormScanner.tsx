/*
  FormScanner.tsx - Level 5 Ambient Intelligence
  The primary viewfinder UI for the Biomechanical Form Audit.
  Handles camera preview, capture initiation, and rendering the Gemini SVG overlay.
*/
'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFormCapture } from '@/hooks/useFormCapture';
import { SVGOverlay } from './SVGOverlay';

interface AuditResult {
    svg_overlay: string;
    coaching_cue: string;
}

export const FormScanner: React.FC = () => {
    const {
        stream,
        isRecording,
        timeLeft,
        error: cameraError,
        permissionDenied,
        requestCameraAccess,
        stopCamera,
        startRecording,
    } = useFormCapture();

    const videoRef = useRef<HTMLVideoElement>(null);

    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
    const [capturedVideoUrl, setCapturedVideoUrl] = useState<string | null>(null);
    const [apiError, setApiError] = useState<string | null>(null);

    // Attach the camera stream to the video element
    useEffect(() => {
        if (videoRef.current && stream && !capturedVideoUrl) {
            videoRef.current.srcObject = stream;
        }
    }, [stream, capturedVideoUrl]);

    // Cleanup stream on unmount
    useEffect(() => {
        return () => {
            stopCamera();
            if (capturedVideoUrl) {
                URL.revokeObjectURL(capturedVideoUrl);
            }
        };
    }, [stopCamera, capturedVideoUrl]);

    const handleStartAuthentication = async () => {
        if (!stream) {
            await requestCameraAccess();
        }
    };

    const handleRecordAndAnalyze = async () => {
        setApiError(null);
        setAuditResult(null);
        if (capturedVideoUrl) {
            URL.revokeObjectURL(capturedVideoUrl);
            setCapturedVideoUrl(null);
        }

        try {
            const videoBlob = await startRecording();

            // Stop live preview and show the recorded video looping
            stopCamera();
            const localUrl = URL.createObjectURL(videoBlob);
            setCapturedVideoUrl(localUrl);

            // Begin backend analysis
            setIsAnalyzing(true);

            const formData = new FormData();
            formData.append('video', videoBlob, 'audit.webm');
            formData.append('movement_type', 'unknown'); // Let Gemini determine it, or could be passed via props

            const response = await fetch('/api/v1/biomechanics/audit', {
                method: 'POST',
                // 'Authorization': `Bearer ${token}`
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Analysis failed. Please try again.');
            }

            const data = await response.json();
            setAuditResult({
                svg_overlay: data.svg_overlay,
                coaching_cue: data.coaching_cue || data.intervention_cue,
            });

        } catch (err: any) {
            console.error(err);
            setApiError(err.message || 'An error occurred during analysis.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const resetScanner = async () => {
        setAuditResult(null);
        setApiError(null);
        if (capturedVideoUrl) {
            URL.revokeObjectURL(capturedVideoUrl);
            setCapturedVideoUrl(null);
        }
        await requestCameraAccess();
    };

    return (
        <div className="relative w-full max-w-lg mx-auto aspect-[9/16] md:aspect-video bg-slate-900 rounded-[2.5rem] overflow-hidden shadow-2xl border-4 border-slate-800">

            {/* 1. Camera / Video Layer */}
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                loop={!!capturedVideoUrl}
                src={capturedVideoUrl || undefined}
                className="absolute inset-0 w-full h-full object-cover"
            />

            {/* 2. SVG Biomechanics Layer (Only visible when audit is complete) */}
            {auditResult && (
                <SVGOverlay
                    svgOverlay={auditResult.svg_overlay}
                    coachingCue={auditResult.coaching_cue}
                />
            )}

            {/* 3. UI Overlay Layer */}
            <div className="absolute inset-0 z-30 flex flex-col justify-between p-6">

                {/* Header Status */}
                <div className="flex justify-between items-start">
                    <div className="bg-slate-900/60 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${stream ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
                        <span className="text-white text-xs font-bold uppercase tracking-widest">
                            {isRecording ? 'Capturing' : (capturedVideoUrl ? 'Playback' : 'Scanner Ready')}
                        </span>
                    </div>

                    {isRecording && (
                        <div className="bg-rose-500/20 backdrop-blur-md px-4 py-2 rounded-full border border-rose-500/30 text-rose-400 font-black tabular-nums">
                            00:{timeLeft.toString().padStart(2, '0')}
                        </div>
                    )}
                </div>

                {/* Center Loading State */}
                <AnimatePresence>
                    {isAnalyzing && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.1 }}
                            className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 backdrop-blur-xl z-40"
                        >
                            <div className="w-16 h-16 border-4 border-slate-800 border-t-emerald-400 border-r-emerald-400 rounded-full animate-spin mb-6" />
                            <h3 className="text-white font-black tracking-tight text-xl mb-2">Analyzing Vector Drift</h3>
                            <p className="text-slate-400 text-sm font-medium">Gemini 3.1 Pro is computing biomechanical signatures...</p>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Bottom Controls */}
                <div className="flex flex-col items-center gap-4 mt-auto">
                    {cameraError || apiError ? (
                        <div className="w-full bg-rose-500/10 backdrop-blur-md border border-rose-500/20 p-4 rounded-2xl text-rose-400 text-sm text-center">
                            {cameraError || apiError}
                        </div>
                    ) : null}

                    {!stream && !capturedVideoUrl && (
                        <button
                            onClick={handleStartAuthentication}
                            className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black uppercase tracking-widest rounded-2xl transition-all shadow-[0_0_40px_-10px_rgba(52,211,153,0.5)]"
                        >
                            Enable Camera
                        </button>
                    )}

                    {stream && !isRecording && !capturedVideoUrl && (
                        <div className="bg-slate-900/40 p-2 rounded-full backdrop-blur-md border border-white/10">
                            <button
                                onClick={handleRecordAndAnalyze}
                                className="w-20 h-20 bg-rose-500 rounded-full border-4 border-slate-900 flex items-center justify-center hover:scale-105 active:scale-95 transition-all focus:outline-none focus:ring-4 ring-rose-500/30 shadow-[0_0_40px_rgba(244,63,94,0.4)]"
                            >
                                <span className="w-8 h-8 rounded-sm bg-white" />
                            </button>
                        </div>
                    )}

                    {auditResult && (
                        <button
                            onClick={resetScanner}
                            className="w-full py-4 bg-white hover:bg-slate-200 text-slate-950 font-black uppercase tracking-widest rounded-2xl transition-colors"
                        >
                            Start New Audit
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};
