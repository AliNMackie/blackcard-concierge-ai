"use client";

import { useState } from 'react';
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, ArrowLeft, Target, Dumbbell, Shield, Calendar } from "lucide-react";
import { submitOnboarding } from '@/lib/api';

const GOALS = [
    { id: "hypertrophy", label: "Hypertrophy", desc: "Maximum muscle growth" },
    { id: "strength", label: "Strength", desc: "Peak force production" },
    { id: "longevity", label: "Longevity", desc: "Healthspan optimization" },
    { id: "fat_loss", label: "Fat Loss", desc: "Body recomposition" },
];

export default function OnboardingPage() {
    const router = useRouter();
    const [step, setStep] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [form, setForm] = useState({
        age: '',
        gender: '',
        current_weight: '',
        target_weight: '',
        goal: '',
        injuries: '',
        days_per_week: 4,
    });

    const updateField = (key: string, value: string | number) => {
        setForm(prev => ({ ...prev, [key]: value }));
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            await submitOnboarding({
                age: parseInt(form.age),
                gender: form.gender,
                current_weight: form.current_weight,
                target_weight: form.target_weight,
                goal: form.goal,
                injuries: form.injuries || undefined,
                days_per_week: form.days_per_week,
            });
            router.push('/dashboard');
        } catch (error) {
            console.error("Onboarding failed:", error);
            setIsSubmitting(false);
        }
    };

    const steps = [
        // Step 0: Baseline
        <div key="baseline" className="space-y-6">
            <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2 font-bold">Age</label>
                <input
                    type="number"
                    value={form.age}
                    onChange={e => updateField('age', e.target.value)}
                    placeholder="35"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-white/20 focus:border-amber-500/50 focus:outline-none transition-colors"
                />
            </div>
            <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2 font-bold">Gender</label>
                <div className="grid grid-cols-2 gap-3">
                    {['Male', 'Female'].map(g => (
                        <button
                            key={g}
                            onClick={() => updateField('gender', g)}
                            className={`py-3.5 rounded-xl border text-sm font-bold tracking-wide transition-all ${form.gender === g
                                    ? 'bg-white text-black border-white'
                                    : 'bg-white/5 text-white/60 border-white/10 hover:border-white/30'
                                }`}
                        >
                            {g}
                        </button>
                    ))}
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2 font-bold">Current (kg)</label>
                    <input
                        type="text"
                        value={form.current_weight}
                        onChange={e => updateField('current_weight', e.target.value)}
                        placeholder="85"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-white/20 focus:border-amber-500/50 focus:outline-none transition-colors"
                    />
                </div>
                <div>
                    <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2 font-bold">Target (kg)</label>
                    <input
                        type="text"
                        value={form.target_weight}
                        onChange={e => updateField('target_weight', e.target.value)}
                        placeholder="80"
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-white/20 focus:border-amber-500/50 focus:outline-none transition-colors"
                    />
                </div>
            </div>
        </div>,

        // Step 1: Goal
        <div key="goal" className="space-y-3">
            {GOALS.map(g => (
                <button
                    key={g.id}
                    onClick={() => updateField('goal', g.id)}
                    className={`w-full p-4 rounded-2xl border text-left transition-all group ${form.goal === g.id
                            ? 'bg-white/10 border-amber-500/60'
                            : 'bg-white/5 border-white/5 hover:border-white/20'
                        }`}
                >
                    <div className="flex items-center gap-4">
                        <Target size={20} className={form.goal === g.id ? 'text-amber-500' : 'text-white/40'} />
                        <div>
                            <div className="text-sm font-bold text-white">{g.label}</div>
                            <div className="text-xs text-white/30">{g.desc}</div>
                        </div>
                    </div>
                </button>
            ))}
        </div>,

        // Step 2: Constraints
        <div key="constraints" className="space-y-6">
            <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-2 font-bold">Injuries / Limitations</label>
                <textarea
                    value={form.injuries}
                    onChange={e => updateField('injuries', e.target.value)}
                    placeholder="e.g., Lower back pain, recovering ACL..."
                    rows={3}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder-white/20 focus:border-amber-500/50 focus:outline-none transition-colors resize-none"
                />
            </div>
            <div>
                <label className="block text-[10px] uppercase tracking-[0.2em] text-white/40 mb-3 font-bold">Days Per Week</label>
                <div className="flex gap-2">
                    {[2, 3, 4, 5, 6].map(d => (
                        <button
                            key={d}
                            onClick={() => updateField('days_per_week', d)}
                            className={`flex-1 py-3.5 rounded-xl border text-sm font-bold transition-all ${form.days_per_week === d
                                    ? 'bg-white text-black border-white'
                                    : 'bg-white/5 text-white/60 border-white/10 hover:border-white/30'
                                }`}
                        >
                            {d}
                        </button>
                    ))}
                </div>
            </div>
        </div>,
    ];

    const titles = [
        { title: "Your Baseline", subtitle: "We need your physiology to calibrate the AI." },
        { title: "Your Mission", subtitle: "What are we optimizing for?" },
        { title: "Your Constraints", subtitle: "So we never program against you." },
    ];

    const canAdvance = step === 0 ? (form.age && form.gender && form.current_weight)
        : step === 1 ? form.goal
            : true;

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto border-x border-neutral-900">
            {/* Progress Bar */}
            <div className="h-1 bg-neutral-900">
                <motion.div
                    className="h-full bg-gradient-to-r from-amber-500 to-amber-400"
                    animate={{ width: `${((step + 1) / 3) * 100}%` }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                />
            </div>

            <div className="p-8 flex-grow flex flex-col">
                {/* Header */}
                <div className="mb-10">
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-amber-500 mb-2">
                        Step {step + 1} of 3
                    </h2>
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={step}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.25 }}
                        >
                            <h1 className="text-3xl font-light tracking-tight mb-1">{titles[step].title}</h1>
                            <p className="text-white/30 text-sm">{titles[step].subtitle}</p>
                        </motion.div>
                    </AnimatePresence>
                </div>

                {/* Step Content */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={step}
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.25 }}
                        className="flex-grow"
                    >
                        {steps[step]}
                    </motion.div>
                </AnimatePresence>

                {/* Navigation */}
                <div className="mt-8 flex gap-3">
                    {step > 0 && (
                        <button
                            onClick={() => setStep(s => s - 1)}
                            className="px-6 py-4 rounded-2xl border border-white/10 text-white/60 hover:border-white/30 transition-all"
                        >
                            <ArrowLeft size={18} />
                        </button>
                    )}
                    <button
                        onClick={() => step < 2 ? setStep(s => s + 1) : handleSubmit()}
                        disabled={!canAdvance || isSubmitting}
                        className={`flex-1 py-4 rounded-2xl font-black uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all active:scale-95 ${canAdvance && !isSubmitting
                                ? 'bg-white text-black hover:bg-neutral-200'
                                : 'bg-white/10 text-white/20 cursor-not-allowed'
                            }`}
                    >
                        {isSubmitting ? (
                            <span className="animate-pulse">Calibrating AI...</span>
                        ) : step < 2 ? (
                            <>Continue <ArrowRight size={16} /></>
                        ) : (
                            <>Initialize Protocol <ArrowRight size={16} /></>
                        )}
                    </button>
                </div>
            </div>

            <footer className="p-8 pt-0 text-center">
                <p className="text-[8px] uppercase tracking-widest text-neutral-800">© 2026 Blackcard Concierge Ltd.</p>
            </footer>
        </div>
    );
}
