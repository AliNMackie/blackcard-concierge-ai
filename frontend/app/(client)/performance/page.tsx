"use client";

import { useEffect, useState } from 'react';
import {
    LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import {
    ArrowUpRight, ArrowDownRight, Minus, Activity, Trophy, Zap, Calendar as CalendarIcon,
    Dumbbell, MessageSquare, Menu, Users, ChevronDown, Loader2, Plus, X
} from 'lucide-react';
import Link from 'next/link';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchAnalytics, logPerformanceMetric } from '@/lib/api';

// --- Mock Data (Retained for Sections Not Yet Connected) ---
const CONSISTENCY_DATA = Array.from({ length: 28 }, (_, i) => ({
    day: i + 1,
    status: Math.random() > 0.3 ? 'complete' : Math.random() > 0.5 ? 'rest' : 'missed',
    intensity: Math.floor(Math.random() * 3) + 1
}));

const BODY_DATA = [
    { date: 'Jan', weight: 82.5, bodyFat: 18 },
    { date: 'Feb', weight: 81.8, bodyFat: 17.5 },
    { date: 'Mar', weight: 81.2, bodyFat: 16.8 },
    { date: 'Apr', weight: 80.5, bodyFat: 15.5 },
    { date: 'May', weight: 80.0, bodyFat: 15.0 },
    { date: 'Jun', weight: 79.5, bodyFat: 14.2 },
];

const BENCHMARK_DATA = [
    { date: 'Jan', k1: "4:00", k5: "22:30", k10: "48:00", val1k: 240, val5k: 1350, val10k: 2880 },
    { date: 'Mar', k1: "3:55", k5: "21:45", k10: "46:30", val1k: 235, val5k: 1305, val10k: 2790 },
    { date: 'May', k1: "3:50", k5: "21:15", k10: "45:45", val1k: 230, val5k: 1275, val10k: 2745 },
    { date: 'Jun', k1: "3:45", k5: "20:30", k10: "44:00", val1k: 225, val5k: 1230, val10k: 2640 },
];

export default function PerformancePage() {
    const [timeRange, setTimeRange] = useState<'4W' | '3M' | '6M' | '12M'>('3M');
    const [activeMetric, setActiveMetric] = useState<'strength' | 'engine' | 'readiness' | 'body' | 'benchmarks'>('strength');

    // Real Data State
    const [strength, setStrength] = useState<any>(null);
    const [engine, setEngine] = useState<any>(null);
    const [readiness, setReadiness] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    // Manual Input State
    const [isLogModalOpen, setIsLogModalOpen] = useState(false);
    const [logValue, setLogValue] = useState('');
    const [submitting, setSubmitting] = useState(false);

    async function loadMetrics() {
        setLoading(true);
        try {
            const [s, e, r] = await Promise.all([
                fetchAnalytics('strength').catch(e => null),
                fetchAnalytics('engine').catch(e => null),
                fetchAnalytics('readiness').catch(e => null)
            ]);
            setStrength(s);
            setEngine(e);
            setReadiness(r);
        } catch (err) {
            console.error("Failed to load analytics", err);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadMetrics();
    }, []);

    const handleLogSubmit = async () => {
        if (!logValue) return;
        setSubmitting(true);
        try {
            await logPerformanceMetric({
                category: activeMetric,
                name: activeMetric === 'strength' ? 'Squat' : activeMetric, // Defaulting for simple MVP
                value: parseFloat(logValue),
                unit: activeMetric === 'strength' ? 'kg' : activeMetric === 'engine' ? 'min/km' : 'score',
                timestamp: new Date().toISOString()
            });
            setIsLogModalOpen(false);
            setLogValue('');
            // Refresh data
            await loadMetrics();
        } catch (err) {
            alert("Failed to log metric");
        } finally {
            setSubmitting(false);
        }
    };

    // Formatters for display
    const fmtStrength = strength ? `${strength.estimated_1rm}kg` : '-';
    const fmtEngine = engine ? `${engine.ftp}` : '-'; // e.g. "4:05" or watts
    const fmtReadiness = readiness ? `${readiness.score}/100` : '-';

    return (
        <div className="min-h-screen bg-black text-white font-sans pb-24 max-w-md mx-auto border-x border-gray-900">

            {/* Header */}
            <header className="p-6 pb-2 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-light tracking-tight text-white mb-1">Performance</h1>
                    <p className="text-zinc-500 text-xs uppercase tracking-widest">Long-term Progress Analysis</p>
                </div>
                <button
                    onClick={() => setIsLogModalOpen(true)}
                    className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-700 transition"
                >
                    <Plus size={20} />
                </button>
            </header>

            {/* Log Modal */}
            <AnimatePresence>
                {isLogModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
                        <motion.div
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                            onClick={() => setIsLogModalOpen(false)}
                        />
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl w-full max-w-xs relative z-10 shadow-2xl"
                        >
                            <h3 className="text-lg font-bold mb-1 capitalize">Log {activeMetric}</h3>
                            <p className="text-xs text-zinc-500 mb-4">Enter today's value for this metric.</p>

                            <input
                                type="number"
                                value={logValue}
                                onChange={(e) => setLogValue(e.target.value)}
                                placeholder="Value..."
                                className="w-full bg-black border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-amber-500 mb-4"
                                autoFocus
                            />

                            <div className="flex gap-2">
                                <button
                                    onClick={() => setIsLogModalOpen(false)}
                                    className="flex-1 py-3 rounded-lg bg-zinc-800 text-sm font-medium hover:bg-zinc-700"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleLogSubmit}
                                    disabled={submitting}
                                    className="flex-1 py-3 rounded-lg bg-white text-black text-sm font-bold hover:bg-gray-200 disabled:opacity-50"
                                >
                                    {submitting ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Global Time Selector */}
            <div className="px-6 mb-6">
                <div className="bg-zinc-900/50 p-1 rounded-lg flex justify-between text-xs font-medium">
                    {['4W', '3M', '6M', '12M'].map((range) => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range as any)}
                            className={clsx(
                                "px-4 py-1.5 rounded-md transition-all",
                                timeRange === range ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-500 hover:text-zinc-300"
                            )}
                        >
                            {range}
                        </button>
                    ))}
                </div>
            </div>

            {/* KPI Cards */}
            <div className="px-6 grid grid-cols-2 gap-3 mb-8">
                {loading ? (
                    <div className="col-span-2 flex justify-center py-4"><Loader2 className="animate-spin text-zinc-600" /></div>
                ) : (
                    <>
                        <KPICard
                            title="Strength (1RM)"
                            value={fmtStrength}
                            trend={strength?.trend || 'flat'}
                            icon={<Dumbbell size={14} />}
                            isActive={activeMetric === 'strength'}
                            onClick={() => setActiveMetric('strength')}
                        />
                        <KPICard
                            title="Engine (Pace)"
                            value={fmtEngine}
                            trend="up" // TODO: Real trend
                            icon={<Zap size={14} />}
                            isActive={activeMetric === 'engine'}
                            onClick={() => setActiveMetric('engine')}
                        />
                        {/* Keep Body/Benchmarks Static for now or until route implemented */}
                        <KPICard
                            title="Ready Score"
                            value={fmtReadiness}
                            trend="flat"
                            icon={<Activity size={14} />}
                            isActive={activeMetric === 'readiness'}
                            onClick={() => setActiveMetric('readiness')}
                        />
                        <KPICard
                            title="Body Fat"
                            value="14.2%"
                            trend="down"
                            icon={<Activity size={14} />}
                            isActive={activeMetric === 'body'}
                            onClick={() => setActiveMetric('body')}
                        />
                        <KPICard
                            title="10K Time"
                            value="44:00"
                            trend="up"
                            icon={<Trophy size={14} />}
                            isActive={activeMetric === 'benchmarks'}
                            onClick={() => setActiveMetric('benchmarks')}
                        />
                        <KPICard
                            title="Consistency"
                            value="88%"
                            trend="down"
                            icon={<CalendarIcon size={14} />}
                        />
                    </>
                )}
            </div>

            {/* Main Charts Section */}
            <div className="px-6 space-y-10">

                {/* Section 1: Strength Trends */}
                <section className={clsx("transition-opacity duration-500", activeMetric !== 'strength' && "opacity-40 hover:opacity-100")}>
                    <div className="flex justify-between items-end mb-4">
                        <div>
                            <h2 className="text-lg font-bold">Strength & Power</h2>
                            <p className="text-xs text-zinc-500">Estimated 1RM Progression</p>
                        </div>
                    </div>
                    <div className="h-64 w-full bg-zinc-900/30 rounded-2xl p-4 border border-zinc-800/50 relative">
                        <ResponsiveContainer width="100%" height="100%" aspect={1.5}>
                            <LineChart data={strength?.history || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="date" stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#666" fontSize={10} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                {/* For simple MVP of generic Strength, just plot 'value' */}
                                <Line type="monotone" dataKey="value" stroke="#fbbf24" strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                            </LineChart>
                        </ResponsiveContainer>
                        <div className="absolute top-4 right-4 flex flex-col gap-1 text-[10px] text-zinc-400">
                            <span className="text-amber-400">● {strength?.exercise || 'Strength'}</span>
                        </div>
                    </div>
                </section>

                {/* Section 2: Body Composition (NEW) */}
                <section className={clsx("transition-opacity duration-500", activeMetric !== 'body' && "opacity-40 hover:opacity-100")}>
                    <div className="mb-4">
                        <h2 className="text-lg font-bold">Body Composition</h2>
                        <p className="text-xs text-zinc-500">Weight (kg) vs Body Fat (%)</p>
                    </div>
                    <div className="h-64 w-full bg-zinc-900/30 rounded-2xl p-4 border border-zinc-800/50 relative">
                        <ResponsiveContainer width="100%" height="100%" aspect={1.5}>
                            <LineChart data={BODY_DATA}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="date" stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis yAxisId="left" stroke="#9ca3af" fontSize={10} tickLine={false} axisLine={false} domain={['dataMin - 1', 'dataMax + 1']} />
                                <YAxis yAxisId="right" orientation="right" stroke="#f43f5e" fontSize={10} tickLine={false} axisLine={false} domain={['dataMin - 1', 'dataMax + 1']} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Line yAxisId="left" type="monotone" dataKey="weight" stroke="#e4e4e7" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                                <Line yAxisId="right" type="monotone" dataKey="bodyFat" stroke="#f43f5e" strokeWidth={2} dot={{ r: 3 }} />
                            </LineChart>
                        </ResponsiveContainer>
                        <div className="absolute top-4 right-4 flex flex-col gap-1 text-[10px] text-zinc-400">
                            <span className="text-gray-200">● Weight</span>
                            <span className="text-rose-500">● BF%</span>
                        </div>
                    </div>
                </section>


                {/* Section 3: Benchmarks (NEW) */}
                <section className={clsx("transition-opacity duration-500", activeMetric !== 'benchmarks' && "opacity-40 hover:opacity-100")}>
                    <div className="mb-4">
                        <h2 className="text-lg font-bold">Benchmark Times</h2>
                        <p className="text-xs text-zinc-500">Race Pace Progression</p>
                    </div>
                    <div className="h-64 w-full bg-zinc-900/30 rounded-2xl p-4 border border-zinc-800/50">
                        <ResponsiveContainer width="100%" height="100%" aspect={1.5}>
                            <LineChart data={BENCHMARK_DATA}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="date" stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#666" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(val) => `${Math.round(val / 60)}m`} domain={['dataMin', 'dataMax']} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }}
                                    formatter={(value: any, name: string | undefined) => {
                                        // A bit hacky to find the original string, but for visual demo:
                                        if (value > 2000) return [(value / 60).toFixed(1) + ' min', name];
                                        return [value, name];
                                    }}
                                />
                                <Line type="monotone" dataKey="val5k" name="5K Time" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
                                <Line type="monotone" dataKey="val10k" name="10K Time" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
                        <Badge label="New 10k PB (44:00)" color="text-purple-400 bg-purple-400/10" />
                        <Badge label="Sub-21 5k" color="text-blue-400 bg-blue-400/10" />
                    </div>
                </section>

                {/* Section 4: Engine & Conditioning */}
                <section className={clsx("transition-opacity duration-500", activeMetric !== 'engine' && "opacity-40 hover:opacity-100")}>
                    <div className="mb-4">
                        <h2 className="text-lg font-bold">Engine Capacity</h2>
                        <p className="text-xs text-zinc-500">Avg Pace (min/km) vs Time</p>
                    </div>
                    <div className="h-48 w-full bg-zinc-900/30 rounded-2xl p-4 border border-zinc-800/50">
                        <ResponsiveContainer width="100%" height="100%" aspect={2}>
                            <AreaChart data={engine?.history || []}>
                                <defs>
                                    <linearGradient id="colorRun" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid stroke="#333" vertical={false} />
                                <XAxis dataKey="date" stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                <YAxis stroke="#666" fontSize={10} tickLine={false} axisLine={false} domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                                <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }} />
                                <Area type="monotone" dataKey="value" stroke="#10b981" fillOpacity={1} fill="url(#colorRun)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex gap-2 mt-3 overflow-x-auto pb-2">
                        <Badge label="New 5k PB" color="text-green-400 bg-green-400/10" />
                        <Badge label="Fastest Sled Push" color="text-amber-400 bg-amber-400/10" />
                    </div>
                </section>

                {/* Section 5: Readiness & Recovery */}
                <section>
                    <div className="mb-4">
                        <h2 className="text-lg font-bold">Readiness vs Load</h2>
                        <p className="text-xs text-zinc-500">Recovery Score (Line) vs Training Volume (Bar)</p>
                    </div>
                    <div className="h-48 w-full bg-zinc-900/30 rounded-2xl p-4 border border-zinc-800/50">
                        <ResponsiveContainer width="100%" height="100%" aspect={2}>
                            <BarChart data={readiness?.history || []}>
                                <XAxis dataKey="date" stroke="#666" fontSize={10} tickLine={false} axisLine={false} />
                                <Tooltip
                                    cursor={{ fill: '#27272a' }}
                                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', fontSize: '12px' }}
                                />
                                <Bar dataKey="value" fill="#3f3f46" radius={[2, 2, 0, 0]} />
                                {/* <Line type="step" dataKey="score" stroke="#fff" strokeWidth={2} dot={{ r: 3 }} /> */}
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-2 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg">
                        <p className="text-[10px] text-rose-400 leading-snug">
                            <span className="font-bold">Insight:</span> Low readiness on Wednesday (45) correlated with high load (800) on Tuesday. Consider lighter active recovery post-heavy sessions.
                        </p>
                    </div>
                </section>

                {/* Section 6: Consistency Heatmap */}
                <section>
                    <h2 className="text-lg font-bold mb-4">Consistency</h2>
                    <div className="grid grid-cols-7 gap-1">
                        {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map(d => (
                            <div key={d} className="text-center text-[10px] text-zinc-600 font-bold mb-1">{d}</div>
                        ))}
                        {CONSISTENCY_DATA.map((day, i) => (
                            <div
                                key={i}
                                className={clsx(
                                    "aspect-square rounded-sm",
                                    day.status === 'complete' ? (day.intensity === 3 ? "bg-amber-500" : day.intensity === 2 ? "bg-amber-500/70" : "bg-amber-500/40") :
                                        day.status === 'rest' ? "bg-zinc-800" : "bg-zinc-900 border border-zinc-800"
                                )}
                            />
                        ))}
                    </div>
                    <p className="text-center text-xs text-zinc-500 mt-4">
                        <span className="text-white font-bold">18 days</span> trained in last 4 weeks.
                    </p>
                </section>

            </div>

        </div>
    );
}

// --- Components ---

function KPICard({ title, value, trend, icon, isActive, onClick }: any) {
    return (
        <div
            onClick={onClick}
            className={clsx(
                "bg-zinc-900 border p-4 rounded-xl cursor-pointer transition-all",
                isActive ? "border-amber-500/50 bg-zinc-800" : "border-zinc-800 hover:border-zinc-700"
            )}
        >
            <div className="flex justify-between items-start mb-2">
                <span className="text-zinc-500 text-[10px] uppercase tracking-wider font-bold">{title}</span>
                <span className={clsx("text-zinc-400", isActive && "text-amber-500")}>{icon}</span>
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold text-white">{value}</span>
                {trend === 'up' && <ArrowUpRight size={12} className="text-green-500" />}
                {trend === 'down' && <ArrowDownRight size={12} className="text-rose-500" />}
                {trend === 'flat' && <Minus size={12} className="text-zinc-500" />}
            </div>
        </div>
    );
}

function Badge({ label, color }: { label: string, color: string }) {
    return (
        <span className={clsx("text-[10px] px-2 py-1 rounded-full font-medium whitespace-nowrap", color)}>
            {label}
        </span>
    );
}
