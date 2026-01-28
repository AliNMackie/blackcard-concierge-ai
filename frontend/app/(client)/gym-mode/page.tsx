"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import ExerciseCard, { Exercise } from "@/components/workout/ExerciseCard";
import { getApiUrl } from "@/lib/api";
import { Timer, ArrowLeft, Loader2, CheckCircle } from "lucide-react";
import { clsx } from "clsx";

export default function GymModePage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [session, setSession] = useState<any>(null);
    const [exercises, setExercises] = useState<Exercise[]>([]);

    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [isResting, setIsResting] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

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

                <ExerciseCard
                    key={currentExercise.id}
                    exercise={currentExercise}
                    isActive={!isResting}
                    onComplete={handleExerciseComplete}
                />

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

        </div>
    );
}
