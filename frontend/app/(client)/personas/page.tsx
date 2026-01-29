'use client';

import PersonasPage from '../../../src/pages/Personas'; // Importing the component I just made, assuming a src/pages pattern, but looking at structure, I might need to adjust.
// Actually, I should just write the component directly into the app router file for simplicity if `src/pages` isn't the pattern.
// Let me check structure again.
// The list_dir showed `app/(client)/gym-mode/page.tsx`.
// So valid path is `frontend/app/(client)/personas/page.tsx`.

// Re-writing content for the App Router file directly:
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';

const PERSONAS = [
    {
        id: 'hyrox_competitor',
        name: 'Alex Carter',
        role: 'Hybrid Competitor Coach',
        tagline: 'Train like you mean to podium.',
        subline: 'HYROX and hybrid performance, built on data not guesswork.',
        bio: 'Alex blends strength, engine work, and movement efficiency so athletes can move faster for longer. From sleds to interval runs, he turns metrics into momentum.',
        badges: ['HYROX', 'Hybrid Athlete', 'Race Simulation'],
        color: 'bg-slate-900',
        accent: 'text-lime-400',
        icon: '⚡'
    },
    {
        id: 'empowered_mum',
        name: 'Sarah Blake',
        role: 'Empowered Mum Trainer',
        tagline: 'Strong from the inside out.',
        subline: 'Post-baby strength and energy, built around your real life.',
        bio: 'Sarah focuses on rebuilding strength, confidence, and energy with sessions that respect busy schedules. No guilt. Just progress you can feel.',
        badges: ['Mum-Focused', 'Postnatal-Aware', 'Quick Sessions'],
        color: 'bg-stone-100',
        accent: 'text-rose-500',
        textColor: 'text-gray-800',
        icon: '🌿'
    },
    {
        id: 'muscle_architect',
        name: 'Rico Vega',
        role: 'Muscle Architect',
        tagline: 'Build strength that shows.',
        subline: 'Structured hypertrophy and recovery, engineered for visible change.',
        bio: 'Rico treats your body like a long-term design project. He combines advanced hypertrophy programming and recovery science to add lean, visible muscle.',
        badges: ['Muscle Gain', 'Hypertrophy', 'Physique Focus'],
        color: 'bg-slate-800',
        accent: 'text-amber-400',
        icon: '🏗️'
    },
    {
        id: 'bio_optimizer',
        name: 'Dr. Maya Lin',
        role: 'Bio-Optimization Coach',
        tagline: 'Elevate the system.',
        subline: 'Longevity and performance, driven by your biometrics.',
        bio: 'Dr. Maya syncs strength, Zone 2, mobility, and breathwork with your wearables. Small inputs, big compounding returns for accurate longevity.',
        badges: ['Longevity', 'Wearable-Driven', 'Stress-Smart'],
        color: 'bg-white border-2 border-gray-100',
        accent: 'text-teal-500',
        textColor: 'text-gray-900',
        icon: '🧬'
    }
];

export default function Personas() {
    const router = useRouter();
    const [selected, setSelected] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const handleSelect = async (id: string) => {
        setSelected(id);
        setLoading(true);

        try {
            const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080';
            const res = await fetch(`${API_URL}/users/me`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Elite-Key': 'dev-secret-123'
                },
                body: JSON.stringify({ coach_style: id })
            });

            if (res.ok) {
                setTimeout(() => {
                    router.push('/dashboard');
                }, 800);
            } else {
                console.error("Failed to update persona");
                setLoading(false);
            }
        } catch (e) {
            console.error(e);
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-white text-gray-900 font-sans p-6 pb-24">
            <header className="mb-12 mt-4 max-w-7xl mx-auto text-center md:text-left">
                <h1 className="text-4xl font-light tracking-tight text-gray-900 mb-2">Choose Your Coach</h1>
                <p className="text-gray-500 text-lg">Select the specialist AI persona that aligns with your current goals.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
                {PERSONAS.map((persona) => (
                    <motion.div
                        key={persona.id}
                        whileHover={{ y: -8 }}
                        onClick={() => handleSelect(persona.id)}
                        className={`
              relative cursor-pointer overflow-hidden rounded-xl shadow-sm flex flex-col h-full transition-all duration-300
              ${persona.color} 
              ${selected === persona.id ? 'ring-4 ring-black ring-offset-2' : 'hover:shadow-xl'}
            `}
                    >
                        {/* Header / Image Area Placeholder */}
                        <div className={`p-6 pb-2 ${persona.textColor || 'text-white'}`}>
                            <div className="flex justify-between items-start mb-4">
                                <div className="text-3xl">{persona.icon}</div>
                                {selected === persona.id && <div className="bg-white text-black text-xs font-bold px-2 py-1 rounded-full">ACTIVE</div>}
                            </div>

                            <h3 className="text-2xl font-bold tracking-tight mb-1">{persona.name}</h3>
                            <p className={`text-sm opacity-80 uppercase tracking-wider font-semibold ${persona.accent}`}>{persona.role}</p>
                        </div>

                        {/* Content Body */}
                        <div className={`p-6 pt-2 flex-grow flex flex-col ${persona.textColor || 'text-gray-300'}`}>
                            <p className="font-serif italic text-lg opacity-90 mb-4">"{persona.tagline}"</p>

                            <p className="text-sm leading-relaxed opacity-80 mb-6 flex-grow">
                                {persona.bio}
                            </p>

                            {/* Badges */}
                            <div className="flex flex-wrap gap-2 mb-6">
                                {persona.badges.map(b => (
                                    <span key={b} className={`text-[10px] uppercase tracking-wider px-2 py-1 rounded border border-current opacity-60`}>
                                        {b}
                                    </span>
                                ))}
                            </div>

                            <div className="mt-auto">
                                <button
                                    disabled={loading}
                                    className={`w-full py-3 rounded-lg text-sm font-bold tracking-wide transition-all uppercase
                            ${selected === persona.id
                                            ? 'bg-white text-black'
                                            : `bg-white/10 hover:bg-white/20 backdrop-blur-md ${persona.textColor ? 'border border-gray-200' : ''}`
                                        }
                        `}
                                >
                                    {selected === persona.id ? (loading ? 'Updating...' : 'Selected') : 'Select Profile'}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
