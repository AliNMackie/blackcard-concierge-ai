'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight, X } from 'lucide-react';
import { DailyInsight } from '@/lib/api';
import { clsx } from 'clsx';

interface ConciergeCardProps {
    insight: DailyInsight | null;
    isLoading: boolean;
    onAccept: () => void;
    onDismiss: () => void;
}

export const ConciergeCard: React.FC<ConciergeCardProps> = ({
    insight,
    isLoading,
    onAccept,
    onDismiss
}) => {
    if (isLoading) {
        return (
            <div className="w-full p-6 bg-neutral-900 border border-white/10 rounded-2xl animate-pulse">
                <div className="h-6 w-1/3 bg-white/5 rounded mb-4" />
                <div className="h-4 w-full bg-white/5 rounded mb-2" />
                <div className="h-4 w-2/3 bg-white/5 rounded" />
            </div>
        );
    }

    if (!insight) return null;

    const isUrgent = insight.suggested_plan_override?.intensity === 'low' ||
        insight.actionable_advice.toLowerCase().includes('recovery') ||
        insight.actionable_advice.toLowerCase().includes('stress');

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className={clsx(
                    "relative overflow-hidden w-full p-6 bg-black border rounded-2xl group transition-all duration-500",
                    isUrgent ? "border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.1)]" : "border-white/10 shadow-2xl"
                )}
            >
                {/* Background Glow */}
                <div className={clsx(
                    "absolute -top-24 -left-24 w-48 h-48 blur-[80px] rounded-full opacity-20 pointer-events-none transition-colors duration-700",
                    isUrgent ? "bg-amber-500" : "bg-blue-500"
                )} />

                <div className="relative z-10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                            <div className={clsx(
                                "p-1.5 rounded-lg transition-colors",
                                isUrgent ? "bg-amber-500/10 text-amber-500" : "bg-white/10 text-white"
                            )}>
                                <Sparkles size={16} />
                            </div>
                            <span className="text-[10px] tracking-[0.2em] uppercase font-bold text-white/40">
                                Proactive Intervention
                            </span>
                        </div>
                        <button
                            onClick={onDismiss}
                            className="text-white/20 hover:text-white transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <h2 className="text-xl md:text-2xl font-semibold text-white mb-3 tracking-tight">
                        {insight.insight_headline}
                    </h2>

                    <p className="text-neutral-400 leading-relaxed text-sm md:text-base mb-6">
                        {insight.actionable_advice}
                    </p>

                    {insight.suggested_plan_override && (
                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={onAccept}
                            className={clsx(
                                "w-full py-5 rounded-xl font-bold text-sm tracking-widest uppercase flex items-center justify-center gap-3 transition-all duration-300",
                                isUrgent
                                    ? "bg-amber-500 text-black hover:bg-amber-400"
                                    : "bg-white text-black hover:bg-neutral-200"
                            )}
                        >
                            Accept Protocol <ArrowRight size={18} />
                        </motion.button>
                    )}
                </div>

                {/* Glassmorphism subtle overlay */}
                <div className="absolute inset-0 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
            </motion.div>
        </AnimatePresence>
    );
};
