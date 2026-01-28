"use client";

import { useState, useEffect } from "react";
import { CheckCircle, Clock, PlayCircle } from "lucide-react";
import { clsx } from "clsx";

export type Exercise = {
    id: string;
    name: string;
    sets: number;
    reps: number; // target reps
    weight: number; // target weight
    videoUrl?: string; // placeholder for video
};

type ExerciseCardProps = {
    exercise: Exercise;
    onComplete: () => void;
    isActive: boolean;
};

export default function ExerciseCard({ exercise, onComplete, isActive }: ExerciseCardProps) {
    const [currentSet, setCurrentSet] = useState(1);
    const [reps, setReps] = useState(exercise.reps);
    const [weight, setWeight] = useState(exercise.weight);
    const [completedSets, setCompletedSets] = useState<number[]>([]);

    // Reset local state when exercise changes
    useEffect(() => {
        setCurrentSet(1);
        setReps(exercise.reps);
        setWeight(exercise.weight);
        setCompletedSets([]);
    }, [exercise.id]);

    const handleLogSet = () => {
        if (completedSets.includes(currentSet)) return;

        const newCompleted = [...completedSets, currentSet];
        setCompletedSets(newCompleted);

        if (newCompleted.length === exercise.sets) {
            onComplete(); // All sets done for this exercise
        } else {
            setCurrentSet(prev => prev + 1);
        }
    };

    if (!isActive) return null;

    return (
        <div className="flex flex-col h-full animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Header */}
            <div className="mb-4">
                <h2 className="text-3xl font-bold uppercase tracking-tighter text-white">{exercise.name}</h2>
                <p className="text-gray-500 text-xs uppercase tracking-widest">
                    Set {currentSet} of {exercise.sets}
                </p>
            </div>

            {/* Video Placeholder */}
            <div className="flex-grow bg-gray-900 rounded-2xl mb-6 relative overflow-hidden border border-gray-800 shadow-2xl">
                <div className="absolute inset-0 flex items-center justify-center">
                    {exercise.videoUrl ? (
                        <div className="text-gray-600 text-xs">Video Loop Loaded</div>
                    ) : (
                        <PlayCircle size={64} className="text-gray-700 opacity-50" />
                    )}
                </div>
                {/* Overlay Gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none"></div>
            </div>

            {/* Inputs */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-1">Weight (KG)</label>
                    <input
                        type="number"
                        value={weight}
                        onChange={(e) => setWeight(Number(e.target.value))}
                        className="bg-transparent text-4xl font-bold text-white w-full outline-none focus:text-blue-400 transition"
                    />
                </div>
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-1">Reps</label>
                    <input
                        type="number"
                        value={reps}
                        onChange={(e) => setReps(Number(e.target.value))}
                        className="bg-transparent text-4xl font-bold text-white w-full outline-none focus:text-blue-400 transition"
                    />
                </div>
            </div>

            {/* Log Button */}
            <button
                onClick={handleLogSet}
                className={clsx(
                    "w-full py-6 rounded-xl font-bold uppercase tracking-widest text-lg transition-all active:scale-95 shadow-lg",
                    "bg-white text-black hover:bg-gray-200"
                )}
            >
                Log Set {currentSet}
            </button>

            {/* Set Indicators */}
            <div className="flex justify-center gap-2 mt-6">
                {Array.from({ length: exercise.sets }).map((_, i) => (
                    <div
                        key={i}
                        className={clsx(
                            "w-2 h-2 rounded-full",
                            completedSets.includes(i + 1) ? "bg-white" : "bg-gray-800"
                        )}
                    />
                ))}
            </div>

        </div>
    );
}
