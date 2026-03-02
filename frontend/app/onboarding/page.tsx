"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { updateUserProfile, UserProfilePayload } from "@/lib/api";
import { Loader2, ArrowRight, ArrowLeft, Target, Activity, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

export default function OnboardingPage() {
    const router = useRouter();
    const [step, setStep] = useState(1);
    const [isSaving, setIsSaving] = useState(false);

    // Form State
    const [formData, setFormData] = useState<UserProfilePayload>({
        height: "",
        weight: "",
        age: undefined,
        gender: "Prefer not to say",
        primary_goal: "Hypertrophy",
        injuries: "None",
        days_per_week: 4
    });

    const updateData = (field: keyof UserProfilePayload, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleNext = () => setStep(prev => prev + 1);
    const handleBack = () => setStep(prev => prev - 1);

    const handleComplete = async () => {
        setIsSaving(true);
        try {
            await updateUserProfile(formData);
            router.push('/dashboard');
        } catch (error) {
            console.error(error);
            setIsSaving(false);
        }
    };

    return (
        <div className="min-h-screen bg-black text-white p-6 flex flex-col items-center justify-center relative overflow-hidden">

            {/* Background Accent */}
            <div className="absolute top-1/4 -right-20 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
            <div className="absolute bottom-1/4 -left-20 w-80 h-80 bg-amber-600/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="w-full max-w-md z-10 flex flex-col h-[80vh]">

                {/* Header */}
                <div className="flex justify-between items-center mb-12">
                    {step > 1 ? (
                        <button onClick={handleBack} className="text-gray-500 hover:text-white p-2 -ml-2 transition-colors">
                            <ArrowLeft size={24} />
                        </button>
                    ) : <div className="w-10" />}

                    <div className="flex gap-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className={clsx("h-1 w-8 rounded-full transition-all", step >= i ? "bg-white" : "bg-gray-800")} />
                        ))}
                    </div>
                    <div className="w-10" />
                </div>

                {/* Step 1: Baseline Metrics */}
                {step === 1 && (
                    <div className="flex-grow animate-in fade-in slide-in-from-right-4 duration-300">
                        <Activity size={40} className="text-blue-500 mb-6" />
                        <h1 className="text-4xl font-black uppercase tracking-tighter mb-2">Build Your<br />Baseline</h1>
                        <p className="text-gray-400 mb-8 text-sm leading-relaxed">Let's establish your starting metrics so Elite AI can tailor your exact progression.</p>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-2">Height</label>
                                    <input type="text" placeholder="e.g. 180cm" value={formData.height} onChange={(e) => updateData('height', e.target.value)} className="bg-transparent text-white w-full outline-none font-bold placeholder-gray-700" />
                                </div>
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-2">Weight</label>
                                    <input type="text" placeholder="e.g. 85kg" value={formData.weight} onChange={(e) => updateData('weight', e.target.value)} className="bg-transparent text-white w-full outline-none font-bold placeholder-gray-700" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-2">Age</label>
                                    <input type="number" placeholder="28" value={formData.age || ''} onChange={(e) => updateData('age', Number(e.target.value))} className="bg-transparent text-white w-full outline-none font-bold placeholder-gray-700" />
                                </div>
                                <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-2">Gender</label>
                                    <select value={formData.gender} onChange={(e) => updateData('gender', e.target.value)} className="bg-transparent text-white w-full outline-none font-bold appearance-none">
                                        <option value="Male">Male</option>
                                        <option value="Female">Female</option>
                                        <option value="Prefer not to say">Prefer not to say</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 2: Primary Goal */}
                {step === 2 && (
                    <div className="flex-grow animate-in fade-in slide-in-from-right-4 duration-300">
                        <Target size={40} className="text-amber-500 mb-6" />
                        <h1 className="text-4xl font-black uppercase tracking-tighter mb-2">Define Your<br />Target</h1>
                        <p className="text-gray-400 mb-8 text-sm leading-relaxed">What represents a successful block of training for you?</p>

                        <div className="space-y-3">
                            {['Hypertrophy', 'Strength', 'Fat Loss', 'Hyrox Competitor'].map(goal => (
                                <button
                                    key={goal}
                                    onClick={() => updateData('primary_goal', goal)}
                                    className={clsx(
                                        "w-full p-5 rounded-xl border flex items-center justify-between transition-all",
                                        formData.primary_goal === goal ? "bg-white text-black border-white" : "bg-gray-900 border-gray-800 text-gray-400 hover:border-gray-600"
                                    )}
                                >
                                    <span className="font-bold uppercase tracking-widest">{goal}</span>
                                    {formData.primary_goal === goal && <CheckCircle size={20} />}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Step 3: Crucial Context */}
                {step === 3 && (
                    <div className="flex-grow animate-in fade-in slide-in-from-right-4 duration-300">
                        <Activity size={40} className="text-red-500 mb-6" />
                        <h1 className="text-4xl font-black uppercase tracking-tighter mb-2">Final<br />Calibration</h1>
                        <p className="text-gray-400 mb-8 text-sm leading-relaxed">Provide the guardrails for your AI Coach.</p>

                        <div className="space-y-6">
                            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-3">Training Days Per Week</label>
                                <div className="flex justify-between px-2">
                                    {[2, 3, 4, 5, 6].map(days => (
                                        <button
                                            key={days}
                                            onClick={() => updateData('days_per_week', days)}
                                            className={clsx(
                                                "w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all",
                                                formData.days_per_week === days ? "bg-white text-black scale-110" : "bg-gray-800 text-gray-500"
                                            )}
                                        >
                                            {days}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                                <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-2">Pre-existing Injuries or Pain</label>
                                <textarea
                                    placeholder="e.g. Right shoulder pain during overhead presses..."
                                    value={formData.injuries}
                                    onChange={(e) => updateData('injuries', e.target.value)}
                                    className="bg-transparent text-white w-full outline-none text-sm placeholder-gray-700 min-h-[100px] resize-none"
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Footer Action */}
                <div className="mt-auto pt-6">
                    {step < 3 ? (
                        <button
                            onClick={handleNext}
                            className="w-full py-5 rounded-xl bg-white text-black font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-gray-200 transition-all active:scale-95 shadow-lg"
                        >
                            Next Step <ArrowRight size={20} />
                        </button>
                    ) : (
                        <button
                            onClick={handleComplete}
                            disabled={isSaving}
                            className="w-full py-5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-black uppercase tracking-widest flex items-center justify-center gap-2 hover:opacity-90 transition-all active:scale-95 shadow-lg"
                        >
                            {isSaving ? (
                                <><Loader2 className="animate-spin" size={20} /> Generating Intel...</>
                            ) : (
                                "Initialize AI Coach"
                            )}
                        </button>
                    )}
                </div>

            </div>
        </div>
    );
}
