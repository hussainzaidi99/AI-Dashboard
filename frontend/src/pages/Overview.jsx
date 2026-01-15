import React from 'react';
import {
    TrendingUp,
    Users,
    Activity,
    MousePointer2,
    ArrowUpRight,
    ArrowDownRight,
    BarChart3,
    Sparkles,
    FileSearch,
    Zap
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useDataset } from '../context/DatasetContext';
import { dataApi } from '../api/data';
import { aiApi } from '../api/ai';
import { chartsApi } from '../api/charts';
import { processingApi } from '../api/processing';
import VizWidget from '../components/visualizations/VizWidget';
import { motion } from 'framer-motion';

const StatCard = ({ title, value, change, trend, icon: Icon, color, loading }) => (
    <div className="glass-card p-6 rounded-[2rem] flex flex-col justify-between hover:scale-[1.02] transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/70 group-hover:bg-white group-hover:text-black transition-all">
                {loading ? <div className="w-5 h-5 border-2 border-current/20 border-t-current rounded-full animate-spin" /> : <Icon size={24} />}
            </div>
            {!loading && (
                <div className={`flex items-center gap-1 text-sm font-bold ${trend === 'up' ? 'text-white' : 'text-white/40'}`}>
                    {trend === 'up' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                    {change}%
                </div>
            )}
        </div>
        <div>
            <p className="text-muted-foreground text-sm font-medium mb-1">{title}</p>
            {loading ? (
                <div className="h-8 w-24 bg-white/5 animate-pulse rounded-lg" />
            ) : (
                <h3 className="text-3xl font-bold tracking-tight">{value}</h3>
            )}
        </div>
    </div>
);

const Overview = () => {
    const { activeFileId, activeSheetIndex, hasActiveDataset } = useDataset();

    // Fetch Statistics with caching
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['stats', activeFileId, activeSheetIndex],
        queryFn: () => dataApi.getStatistics(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
    });

    // Fetch Insights with caching
    const { data: insights, isLoading: insightsLoading } = useQuery({
        queryKey: ['insights', activeFileId, activeSheetIndex],
        queryFn: () => aiApi.getInsights(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
        retry: 1, // Only retry once on failure
    });

    // Fetch Quality Report with caching
    const { data: quality, isLoading: qualityLoading } = useQuery({
        queryKey: ['quality', activeFileId, activeSheetIndex],
        queryFn: () => dataApi.getQuality(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
    });

    // Fetch Dashboard with caching
    const { data: dashboard, isLoading: dashboardLoading } = useQuery({
        queryKey: ['dashboard', activeFileId, activeSheetIndex],
        queryFn: () => chartsApi.getDashboard(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
    });

    return (
        <div className="space-y-12 pb-20">
            {/* Dashboard Header - Workspace Focused */}
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-2 border-b border-white/5">
                <div>
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 rounded-lg bg-white/10 text-white">
                            <Sparkles size={18} />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-widest text-white/60">Intelligence Core Active</span>
                    </div>
                    <h1 className="text-4xl font-bold tracking-tight mb-2 text-white/90">
                        {hasActiveDataset ? 'Intelligence Snapshot' : 'Global Operations Hub'}
                    </h1>
                    <p className="text-zinc-400 font-medium text-lg">
                        {hasActiveDataset
                            ? "Neural discovery engines are processing your dataset in real-time."
                            : "Ready to ingest new intelligence. Connect a data source to begin."}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="h-12 px-5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all font-semibold flex items-center gap-2">
                        <Zap size={18} className="text-amber-400" />
                        Live Status
                    </button>
                    <button className="h-12 px-6 rounded-xl bg-primary text-primary-foreground font-bold shadow-lg shadow-white/5 hover:bg-neutral-200 active:scale-95 transition-all flex items-center gap-2">
                        <FileSearch size={20} />
                        Global Search
                    </button>
                </div>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Global Rows"
                    value={stats?.total_rows?.toLocaleString() || '---'}
                    change={25} trend="up" icon={Users} color="blue-400"
                    loading={statsLoading}
                />
                <StatCard
                    title="Data Entities"
                    value={stats?.total_columns || '---'}
                    change={12} trend="up" icon={Activity} color="rose-400"
                    loading={statsLoading}
                />
                <StatCard
                    title="Missing Cells"
                    value={stats?.null_counts_sum || '0'}
                    change={stats?.null_percent?.toFixed(1) || '0'} trend="down" icon={TrendingUp} color="emerald-400"
                    loading={statsLoading}
                />
                <StatCard
                    title="Completeness"
                    value={quality?.scores?.completeness ? `${(quality.scores.completeness * 100).toFixed(1)}%` : '---'}
                    change={Math.round((quality?.scores?.completeness || 0) * 100)} trend="up" icon={MousePointer2} color="amber-400"
                    loading={qualityLoading}
                />
            </div>

            {/* Main Analysis Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Chart Slot */}
                <div className="lg:col-span-2">
                    {hasActiveDataset ? (
                        <VizWidget
                            title={dashboard?.widgets?.[0]?.title || "Main Discovery Engine"}
                            description={dashboard?.widgets?.[0]?.description || "Deep pattern analysis of your primary dataset."}
                            config={dashboard?.widgets?.[0]?.chart}
                            loading={dashboardLoading}
                        />
                    ) : (
                        <div className="h-[500px] glass-card rounded-[2.5rem] p-8 flex flex-col items-center justify-center border-2 border-dashed border-white/5 group cursor-pointer hover:border-primary/20 transition-all">
                            <div className="text-center group-hover:scale-105 transition-transform duration-500">
                                <div className="w-20 h-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-6 text-primary shadow-[0_0_30px_rgba(59,130,246,0.1)]">
                                    <TrendingUp size={36} />
                                </div>
                                <h3 className="text-xl font-bold mb-2">Waiting for Data Pipeline</h3>
                                <p className="text-muted-foreground max-w-xs mx-auto">
                                    Upload a dataset in the ingestion zone to activate world-class visualizations.
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* AI Discovery Sidebar */}
                <div className="glass-card rounded-[2.5rem] p-8 flex flex-col">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-xl font-bold flex items-center gap-2">
                            <Sparkles className="text-amber-400" size={20} />
                            AI Insights
                        </h3>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[9px] font-bold border border-emerald-500/20 uppercase tracking-widest">Active</span>
                    </div>

                    <div className="space-y-4 flex-1 overflow-y-auto custom-scrollbar pr-2">
                        {!hasActiveDataset ? (
                            [1, 2, 3].map((i) => (
                                <div key={i} className="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-3 opacity-40">
                                    <div className="h-4 w-1/3 bg-white/10 rounded" />
                                    <div className="h-12 w-full bg-white/5 rounded-xl" />
                                </div>
                            ))
                        ) : insightsLoading ? (
                            <div className="flex flex-col items-center justify-center h-48 space-y-4">
                                <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin" />
                                <p className="text-xs font-bold text-muted-foreground uppercase">Reasoning...</p>
                            </div>
                        ) : insights?.insights?.length > 0 ? (
                            insights.insights.map((insight, idx) => (
                                <motion.div
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    key={idx}
                                    className="p-5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
                                >
                                    <div className="flex items-center gap-3 mb-3">
                                        <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center text-white/70 group-hover:bg-white group-hover:text-black transition-all">
                                            <TrendingUp size={16} />
                                        </div>
                                        <span className="text-[10px] font-bold uppercase tracking-widest text-white/50">{insight.title || 'Discovery'}</span>
                                    </div>
                                    <p className="text-sm text-foreground/80 leading-relaxed font-medium">
                                        {insight.description || insight}
                                    </p>
                                </motion.div>
                            ))
                        ) : (
                            <p className="text-center text-muted-foreground text-sm py-10 italic">No automated insights available for this segment.</p>
                        )}
                    </div>

                    <button className="mt-8 w-full py-4 bg-primary text-primary-foreground font-bold rounded-2xl shadow-lg shadow-white/5 hover:bg-neutral-200 transition-all flex items-center justify-center gap-2">
                        <Sparkles size={18} />
                        Generate Custom Insight
                    </button>
                </div>
            </div>

            {/* Secondary Row Slots */}
            {hasActiveDataset && dashboard?.widgets?.length > 1 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {dashboard.widgets.slice(1, 3).map((widget, idx) => (
                        <VizWidget
                            key={idx}
                            title={widget.title}
                            description={widget.description}
                            config={widget.chart}
                            loading={dashboardLoading}
                        />
                    ))}
                </div>
            )}
        </div>
    );
};

export default Overview;
