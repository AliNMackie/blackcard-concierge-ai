'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plane, Dumbbell, User, Check } from 'lucide-react';
import { clsx } from 'clsx';

interface TravelModeToggleProps {
    isTraveling: boolean;
    currentConstraint: string;
    onToggle: (isTraveling: boolean, constraint: string) => void;
}

export const TravelModeToggle: React.FC<TravelModeToggleProps> = ({
    isTraveling,
    currentConstraint,
    onToggle
}) => {
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleToggleClick = () => {
        if (!isTraveling) {
            setIsModalOpen(true);
        } else {
            onToggle(false, "Full Gym");
        }
    };

    const selectConstraint = (constraint: string) => {
        onToggle(true, constraint);
        setIsModalOpen(false);
    };

    return (
        <>
            <div className="flex items-center gap-3">
                <span className={clsx(
                    "text-[10px] uppercase tracking-[0.2em] font-bold transition-colors duration-300",
                    isTraveling ? "text-amber-500" : "text-white/20"
                )}>
                    Travel Mode
                </span>
                <button
                    onClick={handleToggleClick}
                    className={clsx(
                        "relative w-12 h-6 rounded-full transition-colors duration-500 flex items-center px-1",
                        isTraveling ? "bg-amber-500" : "bg-neutral-800"
                    )}
                >
                    <motion.div
                        animate={{ x: isTraveling ? 24 : 0 }}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                        className="w-4 h-4 bg-white rounded-full shadow-lg flex items-center justify-center"
                    >
                        {isTraveling && <Plane size={10} className="text-amber-500" />}
                    </motion.div>
                </button>
            </div>

            <AnimatePresence>
                {isModalOpen && (
                    <div className="fixed inset-0 z-[100] flex items-end justify-center px-4 pb-10 sm:p-0">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setIsModalOpen(false)}
                            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                        />

                        <motion.div
                            initial={{ y: "100%" }}
                            animate={{ y: 0 }}
                            exit={{ y: "100%" }}
                            transition={{ type: "spring", damping: 25, stiffness: 200 }}
                            className="relative w-full max-w-sm bg-neutral-900 border border-white/10 rounded-3xl overflow-hidden shadow-2xl"
                        >
                            <div className="p-8">
                                <h3 className="text-xl font-semibold text-white mb-2">Environment Pivot</h3>
                                <p className="text-white/40 text-sm mb-8 leading-relaxed">
                                    Select your current equipment landscape. I will rewrite your protocol instantly.
                                </p>

                                <div className="space-y-3">
                                    {[
                                        { id: "Hotel Gym (Dumbbells Only)", label: "Hotel Gym", icon: Dumbbell, desc: "Limited to dumbbells and bench." },
                                        { id: "Bodyweight Only", label: "Pure Bodyweight", icon: User, desc: "No equipment, hotel room session." }
                                    ].map((opt) => (
                                        <button
                                            key={opt.id}
                                            onClick={() => selectConstraint(opt.id)}
                                            className="w-full p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-white/20 hover:bg-white/10 transition-all flex items-center justify-between group"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className="p-2.5 rounded-xl bg-white/5 text-white/60 group-hover:text-white transition-colors">
                                                    <opt.icon size={20} />
                                                </div>
                                                <div className="text-left">
                                                    <div className="text-sm font-bold text-white tracking-wide">{opt.label}</div>
                                                    <div className="text-xs text-white/30">{opt.desc}</div>
                                                </div>
                                            </div>
                                            <div className="w-6 h-6 rounded-full border border-white/10 flex items-center justify-center group-hover:border-white/40">
                                                <Check size={14} className="text-white opacity-0 group-hover:opacity-100" />
                                            </div>
                                        </button>
                                    ))}
                                </div>

                                <button
                                    onClick={() => setIsModalOpen(false)}
                                    className="w-full mt-6 py-4 text-white/40 text-sm font-medium hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>

                            <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </>
    );
};
