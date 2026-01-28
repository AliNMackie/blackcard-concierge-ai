"use client";

import { useRouter } from "next/navigation";
import { CheckCircle, ArrowRight } from "lucide-react";

export default function OnboardingPage() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto border-x border-gray-900 p-8">
            <header className="mb-12">
                <h1 className="text-4xl font-light tracking-tight mb-2">Welcome to Elite.</h1>
                <p className="text-zinc-500 text-sm italic">"The last fitness protocol you'll ever need."</p>
            </header>

            <main className="flex-grow">
                {/* Task 2: The "Value Ladder" (Service Guarantee) */}
                <div className="bg-zinc-900 p-6 rounded-2xl border border-amber-500/30 mb-8 shadow-2xl">
                    <h3 className="text-amber-500 font-black uppercase tracking-[0.2em] text-[10px] mb-4">Your Elite Access Includes:</h3>
                    <ul className="space-y-4 text-zinc-300">
                        <li className="flex items-center gap-3">
                            <CheckCircle size={18} className="text-amber-500 flex-shrink-0" />
                            <span className="text-sm font-medium tracking-tight">Daily AI-Augmented Protocol</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <CheckCircle size={18} className="text-amber-500 flex-shrink-0" />
                            <span className="text-sm font-medium tracking-tight">24/7 "Ghostwriter" Chat Access</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <CheckCircle size={18} className="text-amber-500 flex-shrink-0" />
                            <span className="text-sm font-medium tracking-tight">Biometric Monitoring (Sleep/HRV)</span>
                        </li>
                        <li className="flex items-center gap-3">
                            <CheckCircle size={18} className="text-amber-500 flex-shrink-0" />
                            <span className="text-sm font-medium tracking-tight">Monthly Strategy Call</span>
                        </li>
                    </ul>
                </div>

                <div className="space-y-4">
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="w-full bg-white text-black font-black uppercase tracking-widest py-5 rounded-2xl flex items-center justify-center gap-2 hover:bg-zinc-200 transition active:scale-95"
                    >
                        Accept Access <ArrowRight size={20} />
                    </button>
                    <p className="text-[10px] text-zinc-600 text-center uppercase tracking-[0.3em]">Invitational Membership Only</p>
                </div>
            </main>

            <footer className="mt-12 text-center text-zinc-800">
                <p className="text-[8px] uppercase tracking-widest">© 2026 Blackcard Concierge Ltd.</p>
            </footer>
        </div>
    );
}
