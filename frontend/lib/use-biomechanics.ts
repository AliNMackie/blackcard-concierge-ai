/*
  use-biomechanics.ts — Level 5 Ambient Intelligence Data Hook
  Interacts with the /api/v1/biomechanics/audit endpoint to 
  perform multi-frame kinetic analysis using Gemini 3.1 Pro.
*/
'use client';

import { useState } from 'react';
import { submitBiomechanicsAudit } from '@/lib/api';

interface AuditResponse {
    user_id: string;
    movement_type: string;
    intervention_cue: string;
    svg_overlay: string;
    drift_score: number;
}

export const useBiomechanics = () => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [auditResult, setAuditResult] = useState<AuditResponse | null>(null);

    const runBiomechanicalAudit = async (movementType: string, framesB64: string[]) => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await submitBiomechanicsAudit({
                movement_type: movementType,
                frames_b64: framesB64,
                fps: 30
            });

            setAuditResult(data);
        } catch (err: any) {
            console.error('Biomechanical Audit failed:', err);
            setError(err?.message || 'Failed to analyze biomechanics. Ensure your session is active.');
        } finally {
            setIsLoading(false);
        }
    };

    const resetAudit = () => {
        setAuditResult(null);
        setError(null);
    };

    return {
        runBiomechanicalAudit,
        auditResult,
        isLoading,
        error,
        resetAudit
    };
};
