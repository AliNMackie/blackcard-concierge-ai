"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ExerciseCard, { Exercise } from "@/components/workout/ExerciseCard";
import { Timer, CheckCircle, ArrowLeft } from "lucide-react";
import { clsx } from "clsx";

// Mock Data for "Leg Day Destruction"
const MOCK_SESSION = {
    id: "session_123",
    name: "Leg Day Destruction",
    exercises: [
        { id: "ex_1", name: "Barbell Back Squat", sets: 3, reps: 5, weight: 100 },
        { id: "ex_2", name: "Bulgarian Split Squat", sets: 3, reps: 8, weight: 24 }, // Dumbbells
        { id: "ex_3", name: "Romanian Deadlift", sets: 3, reps: 10, weight: 80 },
    ] as Exercise[]
};

export default function WorkoutSessionPage() {
    const params = useParams();
    const router = useRouter();
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);
    const [isResting, setIsResting] = useState(false);
    const [isComplete, setIsComplete] = useState(false);

    const currentExercise = MOCK_SESSION.exercises[currentExerciseIndex];

    const handleExerciseComplete = () => {
        setIsResting(true);
        // In a real app, we'd start a timer here
        setTimeout(() => {
            setIsResting(false);
            if (currentExerciseIndex < MOCK_SESSION.exercises.length - 1) {
                setCurrentExerciseIndex(prev => prev + 1);
            } else {
                setIsComplete(true);
            }
        }, 3000); // Mock 3s rest for demo flow
    };

    const handleSkipRest = () => {
        setIsResting(false);
        if (currentExerciseIndex < MOCK_SESSION.exercises.length - 1) {
            setCurrentExerciseIndex(prev => prev + 1);
        } else {
            setIsComplete(true);
        }
    };

    if (isComplete) {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6 text-center animate-in zoom-in-95 duration-500">
                <CheckCircle size={64} className="text-green-500 mb-6" />
                <h1 className="text-4xl font-bold uppercase tracking-tighter mb-2">Workout Complete</h1>
                <p className="text-gray-500 mb-8">Great job, Alastair. Recovery protocol generated.</p>
                <button
                    onClick={() => router.push('/dashboard')}
                    className="bg-white text-black px-8 py-4 rounded-xl font-bold uppercase tracking-widest hover:bg-gray-200 transition"
                >
                    Return to Dashboard
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto relative overflow-hidden">

            {/* Top Bar */}
            <header className="p-6 flex justify-between items-center z-10">
                <button onClick={() => router.back()} className="text-gray-500 hover:text-white">
                    <ArrowLeft />
                </button>
                <div className="text-xs font-bold uppercase tracking-widest text-gray-500">
                    {MOCK_SESSION.name}
                </div>
                <div className="w-6" /> {/* Spacer */}
            </header>

            {/* Main Content Area */}
            <main className="flex-grow p-6 flex flex-col relative">

                {/* Progress Bar */}
                <div className="flex gap-1 mb-8">
                    {MOCK_SESSION.exercises.map((ex, idx) => (
                        <div
                            key={ex.id}
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
