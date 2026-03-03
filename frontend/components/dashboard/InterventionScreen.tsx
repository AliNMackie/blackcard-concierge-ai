/**
 * InterventionScreen — Next.js 16 Server Component
 *
 * Fetches the user's latest DailyInsight server-side.
 * If the recovery status is RED, it bypasses the normal dashboard
 * and renders a full-screen "Recovery Protocol" takeover UI.
 *
 * If GREEN or AMBER (or no insight), it returns null — the normal
 * dashboard renders unobstructed beneath it.
 *
 * Usage: Place above the main dashboard content in the (client) layout
 * or dashboard page. It renders as a React Server Component (RSC),
 * so data is fetched at request time with zero client-side waterfall.
 */

import { cookies, headers } from 'next/headers';
import { Wind, Footprints, Moon, ShieldAlert, ArrowRight } from 'lucide-react';
import type { DailyInsight } from '@/lib/api';

// ---------------------------------------------------------------------------
// Server-side data fetch (RSC — runs on the server, never in the browser)
// ---------------------------------------------------------------------------
async function getDailyInsight(): Promise<DailyInsight | null> {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!backendUrl) return null;

    // Forward the Authorization header from the incoming request
    // (Next.js 16 App Router: headers() is available in Server Components)
    const incomingHeaders = await headers();
    const authHeader = incomingHeaders.get('authorization');

    try {
        const res = await fetch(`${backendUrl}/api/v1/concierge/today`, {
            headers: {
                ...(authHeader ? { Authorization: authHeader } : {}),
                'Content-Type': 'application/json',
            },
            // Revalidate every 5 minutes — the sentry runs on cron, not per-request
            next: { revalidate: 300 },
        });

        if (res.status === 404 || !res.ok) return null;
        return res.json() as Promise<DailyInsight>;
    } catch {
        return null;
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function isRedStatus(insight: DailyInsight): boolean {
    const override = insight.suggested_plan_override;
    if (!override) return false;

    // Sentry graph sets session_type_override to "recovery_protocol" on RED
    if (override.session_type_override === 'recovery_protocol') return true;
    // Fallback: intensity cap of 0 means full RED protocol
    if (typeof override.intensity_cap_percent === 'number' && override.intensity_cap_percent === 0) return true;

    return false;
}

// ---------------------------------------------------------------------------
// Recovery Protocol Action Cards
// ---------------------------------------------------------------------------
const RECOVERY_ACTIONS = [
    {
        id: 'breathwork',
        icon: Wind,
        label: 'Breathwork',
        sublabel: '5 min — Physiological Sighs',
        description: 'Double inhale through the nose, long slow exhale. Activates the parasympathetic system.',
        href: '/dashboard/recovery/breathwork',
    },
    {
        id: 'walk',
        icon: Footprints,
        label: 'Zone 1 Walk',
        sublabel: '20 min — Low heart rate',
        description: 'Outdoor walk at a conversational pace. Keep heart rate below 120 BPM.',
        href: '/dashboard/recovery/walk',
    },
    {
        id: 'sleep',
        icon: Moon,
        label: 'Sleep Protocol',
        sublabel: 'Tonight — Optimise recovery',
        description: '18°C room · 400mg Magnesium · 200mg L-Theanine · 30 min before bed.',
        href: '/dashboard/recovery/sleep',
    },
] as const;

// ---------------------------------------------------------------------------
// Main Server Component
// ---------------------------------------------------------------------------
export default async function InterventionScreen() {
    const insight = await getDailyInsight();

    // Only intercept on confirmed RED status
    if (!insight || !isRedStatus(insight)) {
        return null;
    }

    return (
        <div
            className="fixed inset-0 z-50 flex flex-col overflow-y-auto"
            style={{
                background: 'radial-gradient(ellipse 120% 80% at 50% 0%, rgba(127,0,0,0.35) 0%, #080808 60%)',
            }}
            aria-label="Recovery Protocol Active"
        >
            {/* Ambient pulse ring */}
            <div
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 overflow-hidden"
            >
                <div
                    className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10"
                    style={{
                        background: 'radial-gradient(circle, rgb(200,0,0) 0%, transparent 70%)',
                        animation: 'pulse 4s ease-in-out infinite',
                    }}
                />
            </div>

            <div className="relative flex flex-col min-h-full px-6 py-10 max-w-lg mx-auto w-full">

                {/* Header */}
                <div className="flex items-center gap-3 mb-10">
                    <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-red-900/50 border border-red-500/30">
                        <ShieldAlert size={20} className="text-red-400" />
                    </div>
                    <div>
                        <p className="text-[10px] tracking-[0.25em] uppercase font-bold text-red-500/70">
                            Blackcard Concierge
                        </p>
                        <p className="text-[10px] tracking-[0.2em] uppercase text-white/30">
                            Recovery Protocol Active
                        </p>
                    </div>
                </div>

                {/* Headline */}
                <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight leading-tight mb-4">
                    {insight.insight_headline}
                </h1>

                {/* Concierge advice */}
                <p className="text-neutral-400 leading-relaxed text-sm md:text-base mb-10">
                    {insight.actionable_advice}
                </p>

                {/* Divider */}
                <div className="flex items-center gap-4 mb-8">
                    <div className="flex-1 h-px bg-white/5" />
                    <span className="text-[10px] tracking-[0.2em] uppercase text-white/20">
                        Choose your protocol
                    </span>
                    <div className="flex-1 h-px bg-white/5" />
                </div>

                {/* Recovery Action Fat Buttons */}
                <div className="flex flex-col gap-4 mb-10">
                    {RECOVERY_ACTIONS.map((action) => {
                        const Icon = action.icon;
                        return (
                            <a
                                key={action.id}
                                href={action.href}
                                id={`recovery-action-${action.id}`}
                                className="group relative flex items-center gap-5 p-5 rounded-2xl border border-white/8 bg-white/2 backdrop-blur-sm hover:border-red-500/40 hover:bg-red-950/20 transition-all duration-300 active:scale-[0.98]"
                            >
                                {/* Icon */}
                                <div className="flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-xl bg-white/5 border border-white/8 text-white/50 group-hover:text-red-400 group-hover:border-red-500/30 group-hover:bg-red-950/30 transition-all duration-300">
                                    <Icon size={22} />
                                </div>

                                {/* Text */}
                                <div className="flex-1 min-w-0">
                                    <p className="text-white font-semibold text-sm tracking-tight">
                                        {action.label}
                                    </p>
                                    <p className="text-white/40 text-xs mt-0.5">
                                        {action.sublabel}
                                    </p>
                                    <p className="text-white/25 text-xs mt-1 leading-relaxed hidden md:block">
                                        {action.description}
                                    </p>
                                </div>

                                {/* Arrow */}
                                <ArrowRight
                                    size={16}
                                    className="flex-shrink-0 text-white/20 group-hover:text-red-400 group-hover:translate-x-1 transition-all duration-300"
                                />
                            </a>
                        );
                    })}
                </div>

                {/* Override escape hatch — deliberate friction by design */}
                <div className="mt-auto text-center">
                    <a
                        href="/dashboard?override=true"
                        id="recovery-override-link"
                        className="inline-block text-xs text-white/20 hover:text-white/40 transition-colors underline underline-offset-4 decoration-white/10"
                    >
                        I understand the risk — proceed to my original session
                    </a>
                </div>

            </div>

            <style>{`
        @keyframes pulse {
          0%, 100% { transform: translateX(-50%) translateY(-50%) scale(1); opacity: 0.10; }
          50% { transform: translateX(-50%) translateY(-50%) scale(1.15); opacity: 0.18; }
        }
      `}</style>
        </div>
    );
}
