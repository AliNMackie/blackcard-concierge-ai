"use client";

import { CheckCircle } from "lucide-react";
import { clsx } from "clsx";

interface ClientCardProps {
    name: string;
    adherence: number;
    lastActive: string;
    status: "RED" | "GREEN" | "AMBER";
}

export default function ClientCard({ name, adherence, lastActive, status }: ClientCardProps) {
    return (
        <div className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl shadow-xl flex justify-between items-center group hover:border-zinc-700 transition-all">
            <div className="flex items-center gap-4">
                <div className={clsx(
                    "w-3 h-3 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)]",
                    status === "GREEN" ? "bg-green-500 shadow-green-500/20" :
                        status === "RED" ? "bg-red-500 shadow-red-500/20" : "bg-amber-500 shadow-amber-500/20"
                )} />
                <div>
                    <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold text-white">{name}</h3>
                        {/* Task 3: The "Social Proof" (Compliance Badge) */}
                        <div className="bg-green-500/10 text-green-500 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest border border-green-500/20">
                            {adherence}% Adherence
                        </div>
                    </div>
                    <p className="text-[10px] text-zinc-500 uppercase tracking-widest mt-1">
                        Active {lastActive}
                    </p>
                </div>
            </div>
            <button className="text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-white transition">
                View Detail
            </button>
        </div>
    );
}
