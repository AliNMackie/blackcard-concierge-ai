'use client';

import React, { useMemo } from 'react';
import useSWR from 'swr';
import { fetchTrainerClients, ClientStatus } from '@/lib/api';
import {
    AlertTriangle,
    ChevronRight,
    Users,
    TrendingUp,
    Activity,
    Filter,
    Search,
    Zap
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx } from 'clsx';

export default function TrainerDashboard() {
    const { data: clients, error, isLoading } = useSWR('trainer/clients', fetchTrainerClients, {
        refreshInterval: 30000 // Refresh every 30s for high-velocity triage
    });

    // Aggressive Triage Filter: Hide "Green" clients to prevent cognitive overload
    const triageRoster = useMemo(() => {
        if (!clients) return [];
        return clients.filter(c => c.status === 'RED' || c.status === 'AMBER');
    }, [clients]);

    const stats = useMemo(() => {
        if (!clients) return { total: 0, critical: 0, stable: 0 };
        return {
            total: clients.length,
            critical: clients.filter(c => c.status === 'RED').length,
            stable: clients.filter(c => c.status === 'GREEN').length
        };
    }, [clients]);

    if (error) return (
        <div className="flex items-center justify-center min-h-screen bg-black text-rose-500">
            Error loading triage roster.
        </div>
    );

    return (
        <main className="min-h-screen bg-black text-white p-6 md:p-12 font-sans selection:bg-emerald-500/30">
            {/* Header: Autonomous Scale Context */}
            <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <div className="bg-emerald-500/10 text-emerald-400 p-1 rounded-md">
                            <Zap size={14} />
                        </div>
                        <span className="text-[10px] uppercase tracking-[0.3em] font-black text-white/40">
                            Trainer Command Center v4.3
                        </span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black tracking-tightest">
                        Triage <span className="text-emerald-500">Queue.</span>
                    </h1>
                </div>

                <div className="flex items-center gap-4 bg-white/5 backdrop-blur-xl border border-white/10 p-2 rounded-2xl">
                    <div className="flex -space-x-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="w-10 h-10 rounded-full border-2 border-black bg-neutral-800" />
                        ))}
                    </div>
                    <div className="pr-4">
                        <p className="text-xs font-bold text-white/60">Managed Assets</p>
                        <p className="text-lg font-black">{stats.total.toLocaleString()}</p>
                    </div>
                </div>
            </header>

            {/* Stats Grid */}
            <section className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <StatCard
                    label="Critical (RED)"
                    value={stats.critical}
                    icon={<AlertTriangle className="text-rose-500" />}
                    trend="+12% vs last hour"
                    color="rose"
                />
                <StatCard
                    label="Stable (GREEN)"
                    value={stats.stable}
                    icon={<Activity className="text-emerald-500" />}
                    trend="Automated by AI"
                    color="emerald"
                />
                <StatCard
                    label="1:1,000 Scale"
                    value="99.9%"
                    icon={<TrendingUp className="text-blue-500" />}
                    trend="System Health"
                    color="blue"
                />
            </section>

            {/* Triage Queue */}
            <section className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <Filter size={18} className="text-white/40" />
                        <h2 className="text-xl font-bold">Active Interventions</h2>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" size={16} />
                        <input
                            type="text"
                            placeholder="Search high-risk clients..."
                            className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 ring-emerald-500/50 transition-all w-64"
                        />
                    </div>
                </div>

                <div className="space-y-4">
                    <AnimatePresence mode="popLayout">
                        {isLoading ? (
                            Array(5).fill(0).map((_, i) => <ClientSkeleton key={i} />)
                        ) : triageRoster.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-center py-24 bg-white/5 rounded-3xl border border-dashed border-white/10"
                            >
                                <Users size={48} className="mx-auto mb-4 text-white/20" />
                                <h3 className="text-lg font-bold">Queue Empty</h3>
                                <p className="text-white/40 max-w-xs mx-auto text-sm">
                                    Autonomous Sentry is managing all clients at scale. No manual interventions required.
                                </p>
                            </motion.div>
                        ) : (
                            triageRoster.map((client) => (
                                <ClientRow key={client.id} client={client} />
                            ))
                        )}
                    </AnimatePresence>
                </div>
            </section>
        </main>
    );
}

function StatCard({ label, value, icon, trend, color }: any) {
    return (
        <div className="bg-white/5 border border-white/10 p-6 rounded-3xl hover:border-white/20 transition-all group">
            <div className="flex justify-between items-start mb-4">
                <div className="bg-black/40 p-3 rounded-2xl border border-white/5 group-hover:scale-110 transition-transform">
                    {icon}
                </div>
                <span className="text-[10px] font-black text-white/20 uppercase tracking-widest">{trend}</span>
            </div>
            <p className="text-white/40 text-xs font-bold uppercase tracking-widest mb-1">{label}</p>
            <p className="text-4xl font-black">{value}</p>
        </div>
    );
}

function ClientRow({ client }: { client: ClientStatus }) {
    return (
        <motion.div
            layout
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            whileHover={{ scale: 1.005 }}
            className="group flex flex-col md:flex-row items-start md:items-center justify-between p-6 bg-white/5 border border-white/10 rounded-3xl hover:bg-neutral-900/50 hover:border-emerald-500/30 transition-all cursor-pointer"
        >
            <div className="flex items-center gap-6 mb-4 md:mb-0">
                <div className={clsx(
                    "w-3 h-12 rounded-full",
                    client.status === 'RED' ? "bg-rose-500 shadow-[0_0_20px_rgba(244,63,94,0.4)]" : "bg-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.4)]"
                )} />
                <div>
                    <h3 className="text-xl font-black tracking-tight">{client.full_name}</h3>
                    <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs font-bold text-white/40 uppercase tracking-tighter">ROI Score</span>
                        <span className={clsx(
                            "text-sm font-black",
                            client.status === 'RED' ? "text-rose-500" : "text-amber-500"
                        )}>
                            {(client.roi_score * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-4 md:mb-0">
                {client.risk_flags.map((flag, i) => (
                    <span key={i} className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-[10px] font-bold text-white/60 uppercase">
                        {flag}
                    </span>
                ))}
            </div>

            <div className="flex items-center gap-8">
                <div className="text-right">
                    <p className="text-[10px] font-black text-white/20 uppercase tracking-widest mb-1">Last Sync</p>
                    <p className="text-sm font-bold">{client.last_check_in}</p>
                </div>
                <button className="p-4 bg-emerald-500 text-black rounded-2xl hover:bg-emerald-400 transition-colors group-hover:translate-x-1 duration-300">
                    <ChevronRight size={20} />
                </button>
            </div>
        </motion.div>
    );
}

function ClientSkeleton() {
    return (
        <div className="w-full h-24 bg-white/5 border border-white/10 rounded-3xl animate-pulse" />
    );
}
