'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, Brain, Trophy, Sparkles, ArrowRight } from 'lucide-react';

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-black via-zinc-900 to-black">
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-amber-600/20 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>
      </div>

      {/* Noise texture overlay */}
      <div className="absolute inset-0 opacity-[0.015] mix-blend-overlay pointer-events-none">
        <div className="absolute inset-0 bg-repeat" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noise\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.65\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noise)\'/%3E%3C/svg%3E")' }} />
      </div>

      <main className="relative z-10">
        {/* Navigation */}
        <nav className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-black/50 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-amber-700 rounded-md flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-black" />
                </div>
                <span className="text-xl font-bold tracking-tight">Elite Concierge</span>
              </div>
              <div className="flex items-center gap-4">
                <Link
                  href="/dashboard"
                  className="text-sm text-zinc-400 hover:text-white transition-colors"
                >
                  Client Portal
                </Link>
                <Link
                  href="/god-mode"
                  className="text-sm text-zinc-400 hover:text-white transition-colors"
                >
                  Trainer Access
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className={`max-w-4xl transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/20 mb-8">
                <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                <span className="text-sm text-amber-200 font-medium">AI-Powered Wellness Concierge</span>
              </div>

              {/* Main Headline */}
              <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-tight">
                Your Personal
                <br />
                <span className="bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200 bg-clip-text text-transparent">
                  Performance Partner
                </span>
              </h1>

              {/* Subheadline */}
              <p className="text-xl md:text-2xl text-zinc-400 mb-12 max-w-2xl leading-relaxed">
                Elite-level wellness intelligence for discerning individuals.
                AI-driven insights, contextual coaching, and biometric mastery—curated exclusively for you.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/dashboard"
                  className="group relative px-8 py-4 bg-gradient-to-r from-amber-500 to-amber-600 text-black font-semibold rounded-full overflow-hidden transition-all hover:shadow-2xl hover:shadow-amber-500/50 hover:scale-105"
                >
                  <span className="relative z-10 flex items-center justify-center gap-2">
                    Access Your Dashboard
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <div className="absolute inset-0 bg-gradient-to-r from-amber-400 to-amber-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                </Link>

                <Link
                  href="/god-mode"
                  className="group px-8 py-4 bg-white/5 backdrop-blur border border-white/10 text-white font-semibold rounded-full hover:bg-white/10 transition-all hover:border-white/20"
                >
                  <span className="flex items-center justify-center gap-2">
                    Trainer Portal
                    <Brain className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                  </span>
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6 lg:px-8 border-t border-white/10">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-3 gap-8">
              {/* Feature 1 */}
              <div className={`group p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 hover:border-amber-500/50 transition-all duration-500 hover:shadow-xl hover:shadow-amber-500/10 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`} style={{ transitionDelay: '200ms' }}>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-6 group-hover:bg-amber-500/20 transition-colors">
                  <Activity className="w-6 h-6 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">Biometric Intelligence</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Real-time analysis of your Terra-connected wearables. Sleep, HRV, recovery—decoded by AI.
                </p>
              </div>

              {/* Feature 2 */}
              <div className={`group p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 hover:border-amber-500/50 transition-all duration-500 hover:shadow-xl hover:shadow-amber-500/10 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`} style={{ transitionDelay: '400ms' }}>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-6 group-hover:bg-amber-500/20 transition-colors">
                  <Brain className="w-6 h-6 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">Contextual Coaching</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Gemini-powered agents understand your goals, context, and constraints—delivering precise guidance.
                </p>
              </div>

              {/* Feature 3 */}
              <div className={`group p-8 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 hover:border-amber-500/50 transition-all duration-500 hover:shadow-xl hover:shadow-amber-500/10 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`} style={{ transitionDelay: '600ms' }}>
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center mb-6 group-hover:bg-amber-500/20 transition-colors">
                  <Trophy className="w-6 h-6 text-amber-400" />
                </div>
                <h3 className="text-xl font-bold mb-3">Elite Oversight</h3>
                <p className="text-zinc-400 leading-relaxed">
                  Your trainer monitors, intervenes, and optimizes via God Mode—ensuring peak performance.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-20 px-6 lg:px-8 border-t border-white/10">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8 text-center">
              <div>
                <div className="text-4xl font-bold bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent mb-2">24/7</div>
                <div className="text-zinc-500 text-sm uppercase tracking-wider">AI Monitoring</div>
              </div>
              <div>
                <div className="text-4xl font-bold bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent mb-2">&lt;60s</div>
                <div className="text-zinc-500 text-sm uppercase tracking-wider">Response Time</div>
              </div>
              <div>
                <div className="text-4xl font-bold bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent mb-2">100%</div>
                <div className="text-zinc-500 text-sm uppercase tracking-wider">Personalized</div>
              </div>
              <div>
                <div className="text-4xl font-bold bg-gradient-to-r from-amber-200 to-amber-400 bg-clip-text text-transparent mb-2">∞</div>
                <div className="text-zinc-500 text-sm uppercase tracking-wider">Potential</div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 py-12 px-6 lg:px-8">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-zinc-500">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span>Elite Concierge AI © 2026</span>
            </div>
            <div className="flex gap-6">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
