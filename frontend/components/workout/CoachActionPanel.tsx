"use client";

import { useState } from "react";
import { Zap, Clock, ShieldAlert, Dumbbell } from "lucide-react";
import { clsx } from "clsx";

type CoachActionPanelProps = {
    onAction: (feedback: string) => void;
    isAnalyzing: boolean;
};

export default function CoachActionPanel({ onAction, isAnalyzing }: CoachActionPanelProps) {
    const actions = [
        { id: "too_heavy", label: "Too Heavy", icon: Dumbbell, feedback: "This is too heavy for me today." },
        { id: "swap", label: "Swap Exercise", icon: Zap, feedback: "I can't do this exercise, please swap it." },
        { id: "short_time", label: "Short on Time", icon: Clock, feedback: "I am short on time, let's speed this up." },
        { id: "equipment", label: "Equipment Taken", icon: ShieldAlert, feedback: "The equipment for this is taken." },
    ];

    return (
        <div className="mt-6 mb-2">
            <h3 className="text-gray-500 text-[10px] uppercase tracking-widest mb-3 font-bold border-b border-gray-800 pb-2">Coach Overrides</h3>
            <div className="grid grid-cols-2 gap-3">
                {actions.map((action) => {
                    const Icon = action.icon;
                    return (
                        <button
                            key={action.id}
                            onClick={() => onAction(action.feedback)}
                            disabled={isAnalyzing}
                            className={clsx(
                                "flex flex-col items-center justify-center p-4 rounded-xl border transition-all active:scale-95 text-center",
                                isAnalyzing
                                    ? "bg-gray-900 border-gray-800 text-gray-600 cursor-not-allowed opacity-50"
                                    : "bg-gray-900/50 border-gray-800 text-gray-400 hover:text-white hover:border-gray-600 hover:bg-gray-800"
                            )}
                        >
                            <Icon size={24} className={clsx("mb-2", !isAnalyzing && "text-amber-500/80")} />
                            <span className="text-xs font-bold uppercase tracking-wider">{action.label}</span>
                        </button>
                    )
                })}
            </div>
        </div>
    );
}
