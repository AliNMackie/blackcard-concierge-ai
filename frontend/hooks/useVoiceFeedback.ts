'use client';

import { useRef, useCallback } from 'react';
import { Landmark, PoseStandardizer } from '@/lib/pose-standardizer';

interface VoiceFeedbackOptions {
    debounceMs?: number;
    volume?: number;
    rate?: number;
}

export const useVoiceFeedback = (options: VoiceFeedbackOptions = {}) => {
    const { debounceMs = 3000, volume = 1, rate = 1 } = options;
    const lastSpeakTimeRef = useRef<number>(0);

    const speak = useCallback((message: string) => {
        const now = Date.now();
        if (now - lastSpeakTimeRef.current < debounceMs) return;

        if (typeof window !== 'undefined' && window.speechSynthesis) {
            // Cancel any pending speech to avoid backlog
            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(message);
            utterance.volume = volume;
            utterance.rate = rate;
            window.speechSynthesis.speak(utterance);
            lastSpeakTimeRef.current = now;
        }
    }, [debounceMs, volume, rate]);

    const analyzeAndSpeak = useCallback((landmarks: Landmark[]) => {
        if (landmarks.length < 33) return;

        // 1. Knee Valgus Logic (Simple heuristic)
        // Check if knees (25, 26) are closer together than hips (23, 24)
        const hipWidth = Math.abs(landmarks[23].x - landmarks[24].x);
        const kneeWidth = Math.abs(landmarks[25].x - landmarks[26].x);

        if (kneeWidth < hipWidth * 0.8) {
            speak("Knees out");
            return;
        }

        // 2. Squat Depth (Hips relative to knees)
        // If hip y is close to knee y, they are hitting parallel
        // If hip is much higher than knee during a descent, "Hips down"
        const leftHip = landmarks[23];
        const leftKnee = landmarks[25];
        const leftAnkle = landmarks[27];

        const hipKneeAngle = PoseStandardizer.calculateAngle(landmarks[11], landmarks[23], landmarks[25]);

        // If hip-knee-ankle angle is decreasing (squatting) but hip y is still high
        const kneeAngle = PoseStandardizer.calculateAngle(landmarks[23], landmarks[25], landmarks[27]);

        if (kneeAngle < 120 && leftHip.y < leftKnee.y - 0.1) {
            // This is a rough heuristic for "not deep enough"
            // speak("Hips down");
        }

        // 3. Posture (Shoulders vs Hips)
        const leftShoulder = landmarks[11];
        const rightShoulder = landmarks[12];
        const midShoulderY = (leftShoulder.y + rightShoulder.y) / 2;
        const midHipY = (landmarks[23].y + landmarks[24].y) / 2;

        // If shoulders are dropping too far forward
        if (midShoulderY > midHipY - 0.2) {
            // speak("Chest up");
        }

    }, [speak]);

    return { analyzeAndSpeak, speak };
};
