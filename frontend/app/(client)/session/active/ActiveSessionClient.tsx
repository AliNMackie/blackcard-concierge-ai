'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FormScanner } from '@/components/biomechanics/FormScanner';

export const ActiveSessionClient: React.FC = () => {
    const [isScannerOpen, setIsScannerOpen] = useState(false);

    return (
        <>
            <button
                onClick={() => setIsScannerOpen(true)}
                className="w-full max-w-sm py-6 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-[2rem] font-black uppercase tracking-widest text-lg transition-transform hover:scale-105 active:scale-95 shadow-[0_0_50px_-15px_rgba(52,211,153,0.6)] flex flex-col items-center gap-1"
            >
                <span>Initialize Form Check</span>
                <span className="text-[10px] font-bold opacity-70 tracking-[0.2em] uppercase">Biomechanics Audit</span>
            </button>

            <AnimatePresence>
                {isScannerOpen && (
                    <motion.div
                        initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
                        animate={{ opacity: 1, backdropFilter: 'blur(24px)' }}
                        exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-slate-950/80"
                    >
                        {/* Modal Container */}
                        <motion.div
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.9, y: 20 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                            className="relative w-full max-w-lg"
                        >
                            {/* Close Button */}
                            <button
                                onClick={() => setIsScannerOpen(false)}
                                className="absolute -top-12 right-0 md:-right-12 md:top-0 w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-700 transition-colors z-[60]"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18" /><path d="m6 6 12 12" /></svg>
                            </button>

                            <FormScanner />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};
