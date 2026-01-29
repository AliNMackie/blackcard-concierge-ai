"use client";

import { useState, useRef, useCallback } from "react";
import Webcam from "react-webcam";
import { useRouter } from "next/navigation";
import { analyzeVision, getApiUrl } from "@/lib/api";
import { ArrowLeft, Camera, Loader2, RefreshCcw, Zap, CheckCircle } from "lucide-react";
import { clsx } from "clsx";
import ExerciseCard, { Exercise } from "@/components/workout/ExerciseCard";

export default function GymModePage() {
    const router = useRouter();
    const webcamRef = useRef<Webcam>(null);

    // States: 'camera' | 'analyzing' | 'workout'
    const [mode, setMode] = useState<'camera' | 'analyzing' | 'workout'>('camera');
    const [imgSrc, setImgSrc] = useState<string | null>(null);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [exercises, setExercises] = useState<Exercise[]>([]);
    const [currentExerciseIndex, setCurrentExerciseIndex] = useState(0);

    const capture = useCallback(() => {
        if (webcamRef.current) {
            const imageSrc = webcamRef.current.getScreenshot();
            setImgSrc(imageSrc);
        }
    }, [webcamRef]);

    const handleAnalyze = async () => {
        if (!imgSrc) return;
        setMode('analyzing');

        try {
            // Call Gemini Vision API
            const response = await analyzeVision(imgSrc);
            console.log("Vision Response:", response); // Debug

            const aiMessage = response.message;

            // Mock "Parsing" of AI response into playable workout
            // Ideally, we'd ask Gemini to output JSON. For now, static mock based on "Visual Analysis" context
            const generatedExercises: Exercise[] = [
                { id: "v1", name: "AI: Sled Push (Heavy)", sets: 3, reps: 10, weight: 100 },
                { id: "v2", name: "AI: Kettlebell Swings", sets: 3, reps: 15, weight: 24 },
                { id: "v3", name: "AI: Assault Bike Sprints", sets: 4, reps: 10, weight: 0 } // rep = cals?
            ];

            setExercises(generatedExercises);
            setAnalysisResult(aiMessage);
            setMode('workout');

        } catch (error) {
            console.error(error);
            alert("Failed to analyze image. Try again.");
            setMode('camera');
        }
    };

    const retake = () => {
        setImgSrc(null);
    };

    // --- RENDER: CAMERA MODE ---
    if (mode === 'camera') {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col relative">
                {/* Header Overlay */}
                <div className="absolute top-0 left-0 right-0 p-6 z-20 flex justify-between items-center bg-gradient-to-b from-black/80 to-transparent">
                    <button onClick={() => router.back()} className="text-white">
                        <ArrowLeft />
                    </button>
                    <span className="text-xs font-bold uppercase tracking-widest text-amber-500 flex items-center gap-2">
                        <Zap size={14} className="fill-amber-500" />
                        Vision AI Active
                    </span>
                    <div className="w-6" />
                </div>

                {/* Camera Viewport */}
                <div className="flex-grow relative bg-zinc-900 flex items-center justify-center overflow-hidden">
                    {!imgSrc ? (
                        <Webcam
                            audio={false}
                            ref={webcamRef}
                            screenshotFormat="image/jpeg"
                            videoConstraints={{ facingMode: "environment" }}
                            className="absolute inset-0 w-full h-full object-cover"
                        />
                    ) : (
                        <img src={imgSrc} alt="Captured" className="absolute inset-0 w-full h-full object-cover" />
                    )}

                    {/* Guidelines Overlay */}
                    {!imgSrc && (
                        <div className="absolute inset-0 border-[32px] border-black/40 pointer-events-none flex items-center justify-center">
                            <div className="border border-white/20 w-64 h-64 rounded-xl flex items-center justify-center">
                                <span className="text-white/50 text-[10px] uppercase tracking-widest bg-black/50 px-2 py-1 rounded">Scan Equipment</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Controls */}
                <div className="bg-black p-8 pb-12 flex justify-center items-center gap-8 relative z-20">
                    {!imgSrc ? (
                        <button
                            onClick={capture}
                            className="w-20 h-20 rounded-full border-4 border-white flex items-center justify-center bg-white/10 active:scale-95 transition"
                        >
                            <div className="w-16 h-16 bg-white rounded-full" />
                        </button>
                    ) : (
                        <>
                            <button onClick={retake} className="flex flex-col items-center text-zinc-500 gap-2">
                                <div className="w-12 h-12 rounded-full bg-zinc-900 flex items-center justify-center border border-zinc-800">
                                    <RefreshCcw size={20} />
                                </div>
                                <span className="text-[10px] uppercase tracking-widest">Retake</span>
                            </button>

                            <button onClick={handleAnalyze} className="flex flex-col items-center text-amber-500 gap-2">
                                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-900/50 animate-pulse">
                                    <Zap size={32} className="text-black fill-black" />
                                </div>
                                <span className="text-[10px] uppercase tracking-widest font-bold">Analyze</span>
                            </button>
                        </>
                    )}
                </div>
            </div>
        );
    }

    // --- RENDER: ANALYZING ---
    if (mode === 'analyzing') {
        return (
            <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center text-center p-8">
                <div className="relative mb-8">
                    <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 animate-pulse"></div>
                    <Loader2 size={64} className="text-blue-500 animate-spin relative z-10" />
                </div>
                <h2 className="text-2xl font-bold uppercase tracking-tight mb-2">Analyzing Environment...</h2>
                <p className="text-zinc-500 text-xs uppercase tracking-widest">Gemini Vision is identifying equipment</p>

                <div className="mt-12 text-left max-w-xs w-full space-y-2">
                    <div className="flex items-center gap-3 text-zinc-400 text-sm">
                        <CheckCircle size={16} className="text-green-500" /> Scanning visual feed...
                    </div>
                    <div className="flex items-center gap-3 text-zinc-400 text-sm animate-pulse delay-75">
                        <CheckCircle size={16} className="text-zinc-700" /> Identifying objects...
                    </div>
                    <div className="flex items-center gap-3 text-zinc-400 text-sm opacity-50">
                        <CheckCircle size={16} className="text-zinc-700" /> Generating protocol...
                    </div>
                </div>
            </div>
        );
    }

    // --- RENDER: WORKOUT (Compact view) ---
    return (
        <div className="min-h-screen bg-black text-white p-6 pb-24">
            <header className="flex justify-between items-center mb-8">
                <button onClick={() => setMode('camera')} className="text-gray-500 hover:text-white">
                    <ArrowLeft />
                </button>
                <div className="text-xs font-bold uppercase tracking-widest text-amber-500">
                    AI Generated Protocol
                </div>
                <div className="w-6" />
            </header>

            <div className="mb-6 bg-zinc-900 border border-zinc-800 p-4 rounded-xl">
                <h3 className="text-sm font-bold text-white mb-2">Agent Analysis</h3>
                <p className="text-xs text-zinc-400 leading-relaxed italic">"{analysisResult}"</p>
            </div>

            <div className="space-y-4">
                {exercises.map((ex, idx) => (
                    <ExerciseCard
                        key={idx}
                        exercise={ex}
                        isActive={idx === currentExerciseIndex}
                        onComplete={() => setCurrentExerciseIndex(i => Math.min(i + 1, exercises.length - 1))}
                    />
                ))}
            </div>

            <div className="mt-8 text-center text-zinc-600 text-xs">
                Vision AI v1.0 • Gemini 2.5 Flash
            </div>
        </div>
    );
}
