'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Crown, X, Zap, Globe, Brain, Shield } from 'lucide-react';

interface UpgradeModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const FEATURES = [
    { icon: Brain, label: "Unlimited AI Coaching", desc: "No limits on workout adaptations" },
    { icon: Globe, label: "Travel Mode", desc: "Seamless environment pivots" },
    { icon: Zap, label: "Proactive Briefings", desc: "Daily AI-generated insights" },
    { icon: Shield, label: "Priority Support", desc: "White-glove concierge access" },
];

export const UpgradeModal: React.FC<UpgradeModalProps> = ({ isOpen, onClose }) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/90 backdrop-blur-md"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        transition={{ type: "spring", damping: 25, stiffness: 250 }}
                        className="relative w-full max-w-sm bg-neutral-950 border border-amber-500/20 rounded-3xl overflow-hidden shadow-2xl"
                    >
                        {/* Glow line */}
                        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

                        {/* Close */}
                        <button
                            onClick={onClose}
                            className="absolute top-4 right-4 p-2 text-white/30 hover:text-white transition-colors z-10"
                        >
                            <X size={18} />
                        </button>

                        <div className="p-8 pt-10">
                            {/* Crown */}
                            <div className="flex justify-center mb-6">
                                <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/20">
                                    <Crown size={32} className="text-amber-500" />
                                </div>
                            </div>

                            {/* Copy */}
                            <h2 className="text-xl font-semibold text-white text-center mb-2">
                                Upgrade to Blackcard
                            </h2>
                            <p className="text-white/40 text-sm text-center leading-relaxed mb-8">
                                You've reached your Concierge limit for the month.
                                Unlock unlimited proactive coaching, travel mode,
                                and elite routine adaptation.
                            </p>

                            {/* Features */}
                            <div className="space-y-3 mb-8">
                                {FEATURES.map(f => (
                                    <div key={f.label} className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                                        <f.icon size={16} className="text-amber-500 flex-shrink-0" />
                                        <div>
                                            <div className="text-xs font-bold text-white">{f.label}</div>
                                            <div className="text-[10px] text-white/30">{f.desc}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* CTA */}
                            <button
                                onClick={() => {
                                    // Stripe integration placeholder
                                    console.log("Stripe checkout triggered");
                                }}
                                className="w-full py-4 rounded-2xl bg-gradient-to-r from-amber-500 to-amber-600 text-black font-black uppercase tracking-widest text-sm hover:from-amber-400 hover:to-amber-500 transition-all active:scale-95"
                            >
                                Upgrade Now
                            </button>

                            <p className="text-[10px] text-white/20 text-center mt-4 uppercase tracking-[0.2em]">
                                Cancel anytime · Billed monthly
                            </p>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
};
