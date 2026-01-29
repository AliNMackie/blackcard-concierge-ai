"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { CheckCircle, PlayCircle, Camera, X, Zap, Loader2, Video } from "lucide-react";
import { clsx } from "clsx";
import Webcam from "react-webcam";
import { analyzeVision } from "@/lib/api";

export type Exercise = {
    id: string;
    name: string;
    sets: number;
    reps: number;
    weight: number;
    videoUrl?: string;
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

    // Camera / AI State
    const [showCamera, setShowCamera] = useState(false);
    const [recording, setRecording] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    const [feedback, setFeedback] = useState<string | null>(null);

    const webcamRef = useRef<Webcam>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    useEffect(() => {
        setCurrentSet(1);
        setReps(exercise.reps);
        setWeight(exercise.weight);
        setCompletedSets([]);
        setFeedback(null);
    }, [exercise.id]);

    const handleLogSet = () => {
        if (completedSets.includes(currentSet)) return;
        const newCompleted = [...completedSets, currentSet];
        setCompletedSets(newCompleted);

        if (newCompleted.length === exercise.sets) {
            onComplete();
        } else {
            setCurrentSet(prev => prev + 1);
        }
    };

    // --- Video Recording Logic ---
    const startRecording = useCallback(() => {
        setRecording(true);
        chunksRef.current = [];

        if (webcamRef.current && webcamRef.current.stream) {
            const stream = webcamRef.current.stream;
            const mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm" });

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: "video/webm" });
                setRecording(false);
                setAnalyzing(true);
                await processVideo(blob);
            };

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start();

            // Auto-stop after 5 seconds
            setTimeout(() => {
                if (mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                }
            }, 5000);
        }
    }, [webcamRef]);

    const processVideo = async (blob: Blob) => {
        // Convert Blob to Base64
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = async () => {
            const base64data = reader.result as string;
            try {
                // Send to backend
                const result = await analyzeVision(base64data, true);
                setFeedback(result.message);
            } catch (e) {
                console.error(e);
                setFeedback("Failed to analyze video. Try again.");
            } finally {
                setAnalyzing(false);
            }
        };
    };

    if (!isActive) return null;

    return (
        <div className="flex flex-col h-full animate-in fade-in slide-in-from-bottom-4 duration-500 relative">

            {/* Header */}
            <div className="mb-4 flex justify-between items-start">
                <div>
                    <h2 className="text-3xl font-bold uppercase tracking-tighter text-white">{exercise.name}</h2>
                    <p className="text-gray-500 text-xs uppercase tracking-widest">
                        Set {currentSet} of {exercise.sets}
                    </p>
                </div>
                <button
                    onClick={() => setShowCamera(true)}
                    className="flex flex-col items-center gap-1 text-zinc-600 hover:text-amber-500 transition-colors group"
                >
                    <div className="p-3 rounded-full bg-zinc-900 border border-zinc-800 group-hover:border-amber-500/50">
                        <Camera size={20} />
                    </div>
                    <span className="text-[8px] uppercase font-black tracking-widest">Check Form</span>
                </button>
            </div>

            {/* Video Placeholder / Feedback Area */}
            <div className="flex-grow bg-gray-900 rounded-2xl mb-6 relative overflow-hidden border border-gray-800 shadow-2xl group">
                {feedback ? (
                    <div className="absolute inset-0 bg-black/90 p-6 flex flex-col items-center justify-center text-center animate-in fade-in">
                        <CheckCircle size={48} className="text-green-500 mb-4" />
                        <h3 className="text-amber-500 uppercase font-black tracking-widest text-sm mb-2">Form Analysis</h3>
                        <p className="text-white text-sm italic leading-relaxed">"{feedback}"</p>
                        <button onClick={() => setFeedback(null)} className="mt-6 text-zinc-500 text-xs hover:text-white uppercase tracking-wider">Dismiss</button>
                    </div>
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                        {exercise.videoUrl ? (
                            <div className="text-gray-600 text-xs">Video Loop Loaded</div>
                        ) : (
                            <PlayCircle size={64} className="text-gray-700 opacity-50" />
                        )}
                    </div>
                )}

                {/* Overlay Gradient */}
                {!feedback && <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none"></div>}
            </div>

            {/* Inputs */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-1">Weight (KG)</label>
                    <input type="number" value={weight} onChange={(e) => setWeight(Number(e.target.value))} className="bg-transparent text-4xl font-bold text-white w-full outline-none focus:text-blue-400 transition" />
                </div>
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <label className="text-gray-500 text-[10px] uppercase tracking-widest block mb-1">Reps</label>
                    <input type="number" value={reps} onChange={(e) => setReps(Number(e.target.value))} className="bg-transparent text-4xl font-bold text-white w-full outline-none focus:text-blue-400 transition" />
                </div>
            </div>

            {/* Log Button */}
            <button onClick={handleLogSet} className={clsx("w-full py-6 rounded-xl font-bold uppercase tracking-widest text-lg transition-all active:scale-95 shadow-lg", "bg-white text-black hover:bg-gray-200")}>
                Log Set {currentSet}
            </button>

            {/* Set Indicators */}
            <div className="flex justify-center gap-2 mt-6">
                {Array.from({ length: exercise.sets }).map((_, i) => (
                    <div key={i} className={clsx("w-2 h-2 rounded-full", completedSets.includes(i + 1) ? "bg-white" : "bg-gray-800")} />
                ))}
            </div>

            {/* CAMERA OVERLAY */}
            {showCamera && (
                <div className="fixed inset-0 z-50 bg-black flex flex-col">
                    <div className="absolute top-0 left-0 right-0 p-6 flex justify-between z-10">
                        <span className="text-xs font-bold uppercase tracking-widest text-white/50 flex items-center gap-2"><Video size={14} /> Form Check Mode</span>
                        <button onClick={() => setShowCamera(false)} className="bg-white/10 p-2 rounded-full text-white"><X size={20} /></button>
                    </div>

                    <div className="flex-grow relative flex items-center justify-center bg-zinc-900">
                        {analyzing ? (
                            <div className="text-center">
                                <Loader2 size={48} className="text-blue-500 animate-spin mx-auto mb-4" />
                                <div className="text-white font-bold uppercase tracking-widest text-sm">Analyzing Mechanics...</div>
                            </div>
                        ) : (
                            <Webcam
                                ref={webcamRef}
                                audio={false}
                                className="w-full h-full object-cover"
                                videoConstraints={{ facingMode: "user" }}
                            />
                        )}

                        {recording && (
                            <div className="absolute top-8 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-red-500/80 px-4 py-1 rounded-full text-white text-xs font-bold uppercase tracking-widest animate-pulse">
                                <div className="w-2 h-2 bg-white rounded-full" /> Recording
                            </div>
                        )}
                    </div>

                    {!analyzing && (
                        <div className="p-12 pb-24 flex justify-center bg-black">
                            <button
                                onClick={startRecording}
                                disabled={recording}
                                className={clsx(
                                    "w-20 h-20 rounded-full border-4 flex items-center justify-center transition-all",
                                    recording ? "border-red-500 bg-red-500/20 scale-110" : "border-white bg-white/10 active:scale-95"
                                )}
                            >
                                <div className={clsx("bg-white transition-all duration-300", recording ? "w-8 h-8 rounded-md" : "w-16 h-16 rounded-full")} />
                            </button>
                        </div>
                    )}
                </div>
            )}

        </div>
    );
}
