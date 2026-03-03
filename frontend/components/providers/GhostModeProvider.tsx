'use client';

/**
 * GhostModeProvider.tsx
 *
 * A Client Component wrapper that handles the spatial awareness layer.
 * 1. Checks `is_traveling` state from user profile / geolocator.
 * 2. Injects `.theme-ghost-mode` CSS class to shift app to amber palette.
 * 3. Surafces the "Scan Hotel Gym" FAB for the Vision Mapper.
 */

import React, { useEffect, useState, useRef } from 'react';
import { Camera, MapPin, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { getApiUrl } from '@/lib/api';
import { getIdToken } from '@/lib/firebase';

interface GhostModeProviderProps {
    children: React.ReactNode;
    initialIsTraveling?: boolean;
}

export function GhostModeProvider({ children, initialIsTraveling = false }: GhostModeProviderProps) {
    const [isTraveling, setIsTraveling] = useState(initialIsTraveling);
    const [isFabOpen, setIsFabOpen] = useState(false);
    const [isScanning, setIsScanning] = useState(false);
    const [locationError, setLocationError] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // 1. Theme Injection
    useEffect(() => {
        if (isTraveling) {
            document.documentElement.classList.add('theme-ghost-mode');
        } else {
            document.documentElement.classList.remove('theme-ghost-mode');
        }

        return () => {
            document.documentElement.classList.remove('theme-ghost-mode');
        };
    }, [isTraveling]);

    // 2. Geolocation Sync (Haversine Check)
    useEffect(() => {
        // Only verify location if authorized
        if (!navigator.geolocation) return;

        const checkLocation = async (pos: GeolocationPosition) => {
            try {
                const token = await getIdToken();
                const headers: HeadersInit = { 'Content-Type': 'application/json' };
                if (token) {
                    headers['Authorization'] = `Bearer ${token}`;
                } else if (process.env.NEXT_PUBLIC_API_KEY) {
                    headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;
                }

                const res = await fetch(`${getApiUrl()}/spatial/check-location`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({
                        latitude: pos.coords.latitude,
                        longitude: pos.coords.longitude,
                    }),
                });

                if (res.ok) {
                    const data = await res.json();
                    setIsTraveling(data.is_traveling);
                }
            } catch (err) {
                console.error('Spatial check failed', err);
            }
        };

        // Note: In production you would probably only poll this occasionally,
        // or trigger it on app foreground. For MVP, we evaluate once on mount.
        navigator.geolocation.getCurrentPosition(
            checkLocation,
            (err) => setLocationError(err.message),
            { maximumAge: 60000, timeout: 10000 }
        );
    }, []);

    // 3. File Upload Handler -> Vision Mapper
    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsScanning(true);
        setIsFabOpen(false); // Close menu while scanning

        try {
            // Convert to Base64
            const reader = new FileReader();
            reader.onloadend = async () => {
                const base64String = reader.result as string;

                const token = await getIdToken();
                const headers: HeadersInit = { 'Content-Type': 'application/json' };
                if (token) headers['Authorization'] = `Bearer ${token}`;
                if (process.env.NEXT_PUBLIC_API_KEY) headers['X-Elite-Key'] = process.env.NEXT_PUBLIC_API_KEY;

                const res = await fetch(`${getApiUrl()}/vision/scan-gym`, {
                    method: 'POST',
                    headers,
                    body: JSON.stringify({ image_base64: base64String }),
                });

                if (res.ok) {
                    // Vision endpoint mutates session and writes a DailyInsight.
                    // In a real app we'd dispatch a refresh event or invalidate queries here.
                    alert("Gym scanned successfully! Your session has been adapted.");
                } else {
                    alert("Scan failed. Please try again.");
                }
                setIsScanning(false);
            };
            reader.readAsDataURL(file);
        } catch (err) {
            console.error(err);
            setIsScanning(false);
            alert("Error reading file.");
        }
    };

    return (
        <>
            <style dangerouslySetInnerHTML={{
                __html: `
        /* Injectable Global Variables for Ghost Mode */
        html.theme-ghost-mode {
          /* Swap standard elite silver/blue for warm amber */
          --ghost-primary: #f59e0b; 
          --ghost-primary-glow: rgba(245,158,11,0.2);
          --ghost-bg: #1a1405; /* Warm dark background */
        }
        
        html.theme-ghost-mode body {
          background-color: var(--ghost-bg);
          color: #fce7f3; /* Softer text */
        }
        
        /* Example: Any component using these vars will auto-shift */
        .ghost-border {
          border-color: var(--ghost-primary, rgba(255,255,255,0.1));
        }
      `}} />

            {/* Main App Content */}
            <div className={isTraveling ? 'ghost-border transition-colors duration-1000' : ''}>
                {children}
            </div>

            {/* Floating Action Button (rendered only in Ghost Mode) */}
            <AnimatePresence>
                {isTraveling && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8, y: 50 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.8, y: 50 }}
                        className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3"
                    >
                        {/* Modal Menu */}
                        <AnimatePresence>
                            {isFabOpen && (
                                <motion.div
                                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    className="bg-neutral-900 border border-amber-500/30 rounded-2xl p-4 shadow-[0_10px_40px_rgba(245,158,11,0.15)] mb-2 flex flex-col gap-2 w-48"
                                >
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        disabled={isScanning}
                                        className="flex items-center gap-3 p-3 text-sm text-neutral-200 hover:bg-amber-500/10 hover:text-amber-400 rounded-xl transition-colors text-left"
                                    >
                                        <Camera size={18} />
                                        {isScanning ? 'Scanning...' : 'Scan Gym'}
                                    </button>
                                    <div className="h-px w-full bg-white/5 my-1" />
                                    <div className="px-2 py-1 flex items-start gap-2 text-xs text-neutral-500">
                                        <MapPin size={12} className="mt-0.5" />
                                        <p>Ghost Mode Active</p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Hidden File Input */}
                        <input
                            type="file"
                            accept="image/*"
                            capture="environment" /* Prefer back camera on mobile */
                            ref={fileInputRef}
                            className="hidden"
                            onChange={handleFileUpload}
                        />

                        {/* FAB Trigger */}
                        <button
                            onClick={() => setIsFabOpen(!isFabOpen)}
                            className="group relative flex items-center justify-center w-14 h-14 bg-amber-500 text-black rounded-full shadow-[0_0_20px_rgba(245,158,11,0.3)] hover:scale-105 active:scale-95 transition-all overflow-hidden"
                        >
                            {/* Outer pulse */}
                            <div className="absolute inset-0 rounded-full animate-ping bg-amber-500/40" style={{ animationDuration: '3s' }} />

                            <div className="relative z-10 flex items-center justify-center w-full h-full bg-amber-500 rounded-full">
                                {isScanning ? (
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ repeat: Infinity, ease: "linear", duration: 1 }}
                                    >
                                        <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full" />
                                    </motion.div>
                                ) : isFabOpen ? (
                                    <X size={24} />
                                ) : (
                                    <Camera size={24} />
                                )}
                            </div>
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
