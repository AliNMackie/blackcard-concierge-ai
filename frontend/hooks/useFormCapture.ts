/*
  useFormCapture.ts - Level 5 Ambient Intelligence
  A custom React hook to interface with the device camera,
  record a 10-second video clip, and return the Blob for Gemini analysis.
*/
'use client';

import { useState, useRef, useCallback } from 'react';

export const useFormCapture = () => {
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [timeLeft, setTimeLeft] = useState(10);
    const [error, setError] = useState<string | null>(null);
    const [permissionDenied, setPermissionDenied] = useState(false);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<BlobPart[]>([]);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const requestCameraAccess = useCallback(async () => {
        try {
            setError(null);
            setPermissionDenied(false);
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } },
                audio: false // No audio needed for biomechanical audit
            });
            setStream(mediaStream);
        } catch (err: any) {
            console.error('Failed to access camera:', err);
            setPermissionDenied(true);
            if (err.name === 'NotAllowedError') {
                setError('Camera access denied. Please enable camera permissions in your browser settings.');
            } else {
                setError(err.message || 'Failed to initialize the camera.');
            }
        }
    }, []);

    const stopCamera = useCallback(() => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    }, [stream]);

    const startRecording = useCallback((): Promise<Blob> => {
        return new Promise((resolve, reject) => {
            if (!stream) {
                reject(new Error('No active camera stream.'));
                return;
            }

            chunksRef.current = [];
            try {
                // Try to use mp4 if available, fallback to webm
                let mimeType = 'video/webm;codecs=vp9';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'video/webm';
                }

                const mediaRecorder = new MediaRecorder(stream, { mimeType });
                mediaRecorderRef.current = mediaRecorder;

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data && e.data.size > 0) {
                        chunksRef.current.push(e.data);
                    }
                };

                mediaRecorder.onstop = () => {
                    const blob = new Blob(chunksRef.current, { type: mimeType });
                    setIsRecording(false);
                    if (timerRef.current) clearInterval(timerRef.current);
                    resolve(blob);
                };

                mediaRecorder.start(200); // collect 200ms chunks
                setIsRecording(true);
                setTimeLeft(10);

                // Manage the 10-second countdown
                timerRef.current = setInterval(() => {
                    setTimeLeft((prev) => {
                        if (prev <= 1) {
                            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                                mediaRecorderRef.current.stop();
                            }
                            return 0;
                        }
                        return prev - 1;
                    });
                }, 1000);

            } catch (err) {
                console.error('Failed to start recording:', err);
                setIsRecording(false);
                reject(err);
            }
        });
    }, [stream]);

    const cancelRecording = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            // Clear the chunks so a cancelled recording doesn't resolve
            chunksRef.current = [];
        }
        if (timerRef.current) clearInterval(timerRef.current);
        setIsRecording(false);
        setTimeLeft(10);
    }, []);

    return {
        stream,
        isRecording,
        timeLeft,
        error,
        permissionDenied,
        requestCameraAccess,
        stopCamera,
        startRecording,
        cancelRecording
    };
};
