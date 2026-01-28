"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ExerciseCard, { Exercise } from "@/components/workout/ExerciseCard";
import { getApiUrl } from "@/lib/api";
import { Timer, ArrowLeft, Loader2, CheckCircle, PlayCircle, ChevronDown, Info } from "lucide-react";
import { clsx } from "clsx";

export default function GymModePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [session, setSession] = useState<any>(null);
    const [exercises, setExercises] = useState<Exercise[]>([]);

    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [isResting, setIsResting] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [showSubs, setShowSubs] = useState(false);

    useEffect(() => {
        async function fetchWorkout() {
            try {
                // Fetch Demo Workout for "auth0|bob" (Mock ID)
                const res = await fetch(`${getApiUrl()}/workouts/demo/auth0|bob`);
                if (!res.ok) throw new Error("Failed to fetch workout");
                const data = await res.json();

                setSession(data);
                setExercises(data.exercises);
            } catch (error) {
                console.error("Error loading workout:", error);
            } finally {
                setLoading(false);
            }
        }
        fetchWorkout();
    }, []);

    const handleExerciseComplete = () => {
        setIsResting(true);
        console.log(`Completed Exercise ${currentExerciseIndex + 1}/${exercises.length} - Saved to DB (Mock)`);

        setTimeout(() => {
            setIsResting(false);
            if (currentExerciseIndex < exercises.length - 1) {
                setCurrentExerciseIndex(prev => prev + 1);
            } else {
                setIsComplete(true);
            }
        }, 3000);
    };

    const handleSkipRest = () => {
        setIsResting(false);
        if (currentExerciseIndex < exercises.length - 1) {
            setCurrentExerciseIndex(prev => prev + 1);
        } else {
            setIsComplete(true);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-black flex items-center justify-center text-white">
                <Loader2 className="animate-spin text-blue-500" size={48} />
                <span className="ml-4 text-sm uppercase tracking-widest text-gray-500">Loading Protocol...</span>
            </div>
        );
    }

    if (isComplete) {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center animate-in zoom-in-95 duration-500">
                <CheckCircle size={64} className="text-green-500 mb-6" />
                <h1 className="text-4xl font-bold uppercase tracking-tighter mb-2">Detailed Log Saved</h1>
                <p className="text-gray-500 mb-8">System is analyzing your performance.</p>
                <button
                    onClick={() => router.push('/dashboard')}
                    className="bg-white text-black px-8 py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition"
                >
                    Return to Dashboard
                </button>
            </div>
        );
    }

    if (!session || exercises.length === 0) {
        return <div className="text-white p-10">No workout found. Please contact support.</div>;
    }

    const currentExercise = exercises[currentExerciseIndex];

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto relative overflow-hidden">

            {/* Top Bar */}
            <header className="p-6 flex justify-between items-center z-10">
                <button onClick={() => router.back()} className="text-gray-500 hover:text-white">
                    <ArrowLeft />
                </button>
                <div className="text-xs font-bold uppercase tracking-widest text-gray-500">
                    {session.name}
                </div>
                <div className="w-6" />
            </header>

            {/* Main Content Area */}
            <main className="flex-grow p-6 flex flex-col relative">

                {/* Progress Bar */}
                <div className="flex gap-1 mb-8">
                    {exercises.map((ex, idx) => (
                        <div
                            key={idx}
                            className={clsx(
                                "h-1 flex-1 rounded-full transition-all duration-300",
                                idx < currentExerciseIndex ? "bg-green-500" :
                                    idx === currentExerciseIndex ? "bg-white" : "bg-gray-800"
                            )}
                        />
                    ))}
                </div>

                {/* Coach's Briefing (Phase 1: Coach's Note) */}
                {currentExerciseIndex === 0 && !isResting && (
                    <div className="mb-8 animate-in fade-in slide-in-from-top-4 duration-700">
                        <div className="bg-zinc-900 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-lg flex gap-4 items-start">
                            <div className="w-10 h-10 rounded-full bg-zinc-800 border border-zinc-700 flex-shrink-0 flex items-center justify-center font-black text-xs text-zinc-500">
                                COACH
                            </div>
                            <div>
                                <p className="text-zinc-200 text-sm leading-relaxed italic">
                                    "I saw your sleep was low (45), so I've swapped the heavy squats for Sled Pushes. Keep the intensity high, but save your lower back. You've got this."
                                </p>
                                <div className="mt-3 flex items-center gap-3">
                                    <button className="flex items-center gap-2 bg-amber-500 text-black text-[10px] font-black uppercase px-3 py-1.5 rounded-lg hover:bg-amber-400 transition">
                                        <PlayCircle size={14} />
                                        Listen to Briefing (0:45)
                                    </button>
                                    <p className="text-[10px] text-zinc-600 uppercase tracking-widest font-bold">Today's Protocol Adjustment</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                <ExerciseCard
                    key={currentExercise.id}
                    exercise={currentExercise}
                    isActive={!isResting}
                    onComplete={handleExerciseComplete}
                />

                {/* Task 4: The "Objection Handler" (Equipment Subs) */}
                <div className="mt-8">
                    <button
                        onClick={() => setShowSubs(!showSubs)}
                        className="w-full bg-zinc-900 border border-zinc-800 p-4 rounded-xl flex items-center justify-between group transition-all"
                    >
                        <div className="flex items-center gap-2">
                            <Info size={16} className="text-zinc-500" />
                            <span className="text-xs font-bold uppercase tracking-widest text-zinc-400">Not at your usual gym?</span>
                        </div>
                        <ChevronDown size={16} className={clsx("text-zinc-600 transition-transform duration-300", showSubs && "rotate-180")} />
                    </button>

                    <div className={clsx(
                        "overflow-hidden transition-all duration-300 ease-in-out",
                        showSubs ? "max-h-40 mt-2 opacity-100" : "max-h-0 opacity-0"
                    )}>
                        <div className="bg-zinc-900/50 border border-zinc-800 p-4 rounded-xl text-zinc-500 text-[10px] leading-relaxed uppercase tracking-wider font-medium">
                            <p className="mb-2 mb-1 border-b border-zinc-800 pb-2">Common Substitutions:</p>
                            <ul className="space-y-2">
                                <li className="flex justify-between">
                                    <span>No Sled?</span>
                                    <span className="text-zinc-400">Treadmill Push (Off)</span>
                                </li>
                                <li className="flex justify-between">
                                    <span>No SkiErg?</span>
                                    <span className="text-zinc-400">KB Swings</span>
                                </li>
                                <li className="flex justify-between">
                                    <span>No Dumbbells?</span>
                                    <span className="text-zinc-400">Bands / Bodyweight</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Rest Timer Overlay */}
                {isResting && (
                    <div className="absolute inset-0 bg-black/95 backdrop-blur-sm z-50 flex flex-col items-center justify-center animate-in fade-in duration-300">
                        <Timer size={48} className="text-blue-500 mb-4 animate-pulse" />
                        <h2 className="text-4xl font-bold text-white mb-2">REST</h2>
                        <p className="text-gray-500 text-sm uppercase tracking-widest mb-8">Recover for next movement</p>

                        <button
                            onClick={handleSkipRest}
                            className="border border-gray-700 text-gray-300 px-6 py-3 rounded-full text-sm font-bold uppercase tracking-widest hover:bg-gray-900 transition"
                        >
                            Skip Rest
                        </button>
                    </div>
                )}
            </main>

            {/* Session Report Modal (Phase 3: Feedback) */}
            {isComplete && (
                <div className="fixed inset-0 bg-black z-[100] flex flex-col p-8 animate-in slide-in-from-bottom duration-500">
                    <header className="mb-10 text-center">
                        <CheckCircle size={64} className="text-green-500 mx-auto mb-6" />
                        <h1 className="text-3xl font-bold uppercase tracking-tighter">Session Complete</h1>
                        <p className="text-zinc-500 text-xs uppercase tracking-widest mt-2">Personal Training Log</p>
                    </header>

                    <div className="space-y-8 flex-grow">
                        <div>
                            <label className="text-zinc-500 text-xs uppercase tracking-[0.2em] block mb-4">How hard was that? (RPE)</label>
                            <input type="range" min="1" max="10" className="w-full accent-amber-500 h-2 bg-zinc-900 rounded-lg appearance-none cursor-pointer" />
                            <div className="flex justify-between text-[10px] text-zinc-600 mt-2 font-bold uppercase tracking-widest">
                                <span>Easy</span>
                                <span>Moderate</span>
                                <span>Max Effort</span>
                            </div>
                        </div>

                        <div>
                            <label className="text-zinc-500 text-xs uppercase tracking-[0.2em] block mb-2">Pain or Issues?</label>
                            <textarea
                                placeholder="Any tightness or form concerns..."
                                className="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-sm text-white focus:border-amber-500 transition-all outline-none"
                                rows={3}
                            />
                        </div>

                        <div>
                            <label className="text-zinc-500 text-xs uppercase tracking-[0.2em] block mb-2">Form Check Videos</label>
                            <div className="border-2 border-dashed border-zinc-800 rounded-xl py-6 flex flex-col items-center text-zinc-600 hover:border-zinc-700 cursor-pointer transition">
                                <span className="text-sm font-medium">Drop clips here</span>
                                <span className="text-[10px] uppercase tracking-widest mt-1 opacity-50">Async Review Enabled</span>
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={() => router.push('/dashboard')}
                        className="bg-white text-black py-5 rounded-2xl font-black uppercase tracking-widest hover:bg-zinc-200 transition active:scale-95 shadow-xl mb-6"
                    >
                        Submit Report
                    </button>
                </div>
            )}

        </div>
    );
}
