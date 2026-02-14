'use client';

import Link from 'next/link';
import { Activity, Brain, Trophy, Sparkles, ArrowRight, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Subtle background gradient */}
      <div className="fixed inset-0 bg-gradient-to-b from-zinc-900 via-black to-black pointer-events-none" />

      {/* Ambient glow effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-80 h-80 bg-amber-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative">
        {/* Simple Nav */}
        <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-black/80 backdrop-blur-xl">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-black" strokeWidth={2.5} />
              </div>
              <span className="font-bold text-lg">Elite Concierge</span>
            </div>
            <div className="flex items-center gap-6">
              <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-white transition">
                Client
              </Link>
              <Link href="/god-mode" className="text-sm text-zinc-400 hover:text-white transition">
                Trainer
              </Link>
            </div>
          </div>
        </nav>

        {/* Hero */}
        <section className="pt-40 pb-24 px-6">
          <div className="max-w-4xl mx-auto">
            {/* Status badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 mb-8">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-xs font-medium text-amber-200 uppercase tracking-wider">AI-Powered Wellness</span>
            </div>

            {/* Main headline */}
            <h1 className="text-6xl md:text-7xl font-bold mb-6 tracking-tight">
              Elite Performance.
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-amber-400 to-amber-500">
                Intelligent Guidance.
              </span>
            </h1>

            {/* Subheading */}
            <p className="text-xl text-zinc-400 mb-10 max-w-2xl leading-relaxed">
              Personalized wellness intelligence for discerning individuals.
              Real-time biometrics, AI-driven insights, and expert oversight—exclusively curated for your peak performance.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4">
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-r from-amber-500 to-amber-600 text-black font-semibold rounded-lg hover:shadow-lg hover:shadow-amber-500/50 transition-all"
              >
                Access Dashboard
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                href="/god-mode"
                className="inline-flex items-center gap-2 px-6 py-3.5 bg-white/5 border border-white/10 font-semibold rounded-lg hover:bg-white/10 transition-all"
              >
                <Brain className="w-4 h-4" />
                Trainer Portal
              </Link>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-20 px-6 border-t border-white/5">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-3 gap-6">
              {/* Feature 1 */}
              <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5 hover:border-amber-500/30 transition-all duration-300">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-5">
                    <Activity className="w-6 h-6 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">Biometric Intelligence</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Terra-connected wearables analyzed in real-time. Sleep, HRV, recovery—decoded by AI.
                  </p>
                </div>
              </div>

              {/* Feature 2 */}
              <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5 hover:border-amber-500/30 transition-all duration-300">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-5">
                    <Zap className="w-6 h-6 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">Contextual Coaching</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Gemini-powered agents deliver precise guidance based on your goals and constraints.
                  </p>
                </div>
              </div>

              {/* Feature 3 */}
              <div className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/5 to-transparent border border-white/5 hover:border-amber-500/30 transition-all duration-300">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-amber-500/0 to-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-5">
                    <Trophy className="w-6 h-6 text-amber-400" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">Elite Oversight</h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    Your trainer monitors and optimizes via God Mode—ensuring sustained peak performance.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="py-20 px-6 border-t border-white/5">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <div className="text-center">
                <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-400 mb-2">24/7</div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider">Monitoring</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-400 mb-2">&lt;60s</div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider">Response</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-400 mb-2">100%</div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider">Personal</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-400 mb-2">∞</div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider">Potential</div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/5 py-8 px-6">
          <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <Sparkles className="w-3 h-3 text-amber-500" />
              <span>Elite Concierge AI © 2026</span>
            </div>
            <div className="flex gap-6 text-sm text-zinc-500">
              <a href="#" className="hover:text-white transition">Privacy</a>
              <a href="#" className="hover:text-white transition">Terms</a>
              <a href="#" className="hover:text-white transition">Support</a>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
