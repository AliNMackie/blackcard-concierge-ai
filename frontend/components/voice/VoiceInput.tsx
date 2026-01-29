"use client";

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { sendChatMessage } from '@/lib/api';

type VoiceInputProps = {
    onMessageSent?: (message: string) => void;
    onResponseReceived?: (response: string) => void;
};

export default function VoiceInput({ onMessageSent, onResponseReceived }: VoiceInputProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [processing, setProcessing] = useState(false);

    // Refs for Speech API
    const recognitionRef = useRef<any>(null);
    const synthRef = useRef<SpeechSynthesis | null>(null);

    useEffect(() => {
        // Initialize Speech Recognition
        if (typeof window !== 'undefined') {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            if (SpeechRecognition) {
                const recognition = new SpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onstart = () => setIsListening(true);
                recognition.onend = () => setIsListening(false);

                recognition.onresult = async (event: any) => {
                    const text = event.results[0][0].transcript;
                    console.log("Transcript:", text);
                    setTranscript(text);
                    if (onMessageSent) onMessageSent(text);

                    await handleVoiceCommand(text);
                };

                recognitionRef.current = recognition;
            }

            synthRef.current = window.speechSynthesis;
        }
    }, []);

    const speak = (text: string) => {
        if (!synthRef.current) return;

        // Cancel any ongoing speech
        synthRef.current.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Try to find a nice premium voice (e.g. Google UK English Male)
        const voices = synthRef.current.getVoices();
        const premiumVoice = voices.find(v => v.name.includes('Google UK English Male') || v.name.includes('Daniel'));
        if (premiumVoice) utterance.voice = premiumVoice;

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);

        synthRef.current.speak(utterance);
    };

    const handleVoiceCommand = async (text: string) => {
        setProcessing(true);
        try {
            // Send to Backend (Gemini)
            // Hardcoding user ID for demo
            const response = await sendChatMessage("auth0|bob", text);
            const aiMessage = response.message;

            if (onResponseReceived) onResponseReceived(aiMessage);

            // Speak Response
            speak(aiMessage);

        } catch (error) {
            console.error("Voice command failed:", error);
            speak("I'm having trouble connecting to the concierge.");
        } finally {
            setProcessing(false);
        }
    };

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
        } else {
            recognitionRef.current?.start();
        }
    };

    if (!recognitionRef.current) return null; // Hide if not supported

    return (
        <div className="fixed bottom-24 right-6 z-50 flex flex-col items-end gap-2">

            {/* Context/Status Bubble */}
            {(transcript || isSpeaking || processing) && (
                <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-2xl rounded-br-none shadow-2xl max-w-[200px] mb-2 animate-in fade-in slide-in-from-bottom-2">
                    {processing && <div className="text-zinc-500 text-xs flex items-center gap-2"><Loader2 size={12} className="animate-spin" /> Thinking...</div>}
                    {isSpeaking && <div className="text-amber-500 text-xs flex items-center gap-2"><Volume2 size={12} className="animate-pulse" /> Speaking...</div>}
                    {!processing && !isSpeaking && <div className="text-white text-xs italic">"{transcript}"</div>}
                </div>
            )}

            {/* FAB */}
            <button
                onClick={toggleListening}
                className={clsx(
                    "w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all active:scale-90",
                    isListening ? "bg-red-500 animate-pulse shadow-red-500/50" :
                        processing ? "bg-zinc-700 animate-spin-slow" :
                            "bg-gradient-to-br from-amber-400 to-amber-600 shadow-amber-500/30 hover:scale-105"
                )}
            >
                {isListening ? (
                    <MicOff className="text-white" size={24} />
                ) : processing ? (
                    <Loader2 className="text-white/50" size={24} />
                ) : (
                    <Mic className="text-black" size={24} />
                )}
            </button>
        </div>
    );
}
