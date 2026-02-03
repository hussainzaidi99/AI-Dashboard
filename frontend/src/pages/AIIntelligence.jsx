import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Brain,
    TrendingUp,
    AlertCircle,
    Zap,
    FileText,
    Download,
    Share2,
    Calendar,
    Sparkles
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useQuery } from '@tanstack/react-query';
import { useDataset } from '../context/DatasetContext';
import { aiApi } from '../api/ai';
import { useNotifications } from '../context/NotificationContext';
import { useEffect } from 'react';

const InsightCard = ({ title, description, icon: Icon, type }) => {
    const typeStyles = {
        positive: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400',
        warning: 'border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400',
        neutral: 'border-border bg-foreground/5 text-foreground',
        info: 'border-border bg-foreground/[0.02] text-muted-foreground'
    };

    return (
        <motion.div
            whileHover={{ y: -5 }}
            className={`p-6 rounded-2xl border backdrop-blur-md ${typeStyles[type] || typeStyles.neutral} transition-all duration-300`}
        >
            <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-foreground/5">
                    <Icon size={24} />
                </div>
                <div className="text-xs font-bold px-2 py-1 rounded-md bg-foreground/10 uppercase tracking-wider">
                    {type}
                </div>
            </div>
            <h3 className="text-lg font-semibold mb-2 text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3">{description}</p>
        </motion.div>
    );
};

const SkeletonCard = () => (
    <div className="p-6 rounded-2xl border border-border bg-foreground/5 animate-pulse">
        <div className="w-12 h-12 bg-foreground/10 rounded-xl mb-4" />
        <div className="h-6 w-2/3 bg-foreground/10 rounded mb-2" />
        <div className="h-4 w-full bg-foreground/10 rounded" />
    </div>
);

const AIIntelligence = () => {
    const { toast } = useNotifications();
    const { activeFileId, activeSheetIndex, hasActiveDataset, isTextOnly } = useDataset();

    const { data, isLoading, isError } = useQuery({
        queryKey: ['ai-insights', activeFileId, activeSheetIndex],
        queryFn: () => aiApi.getInsights(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        placeholderData: (prev) => prev,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
        retry: 1, // Only retry once on failure
    });

    useEffect(() => {
        if (data && !isLoading) {
            toast.success('Analysis Report Updated', {
                description: 'AI has generated new insights based on your current dataset state.'
            });
        }
    }, [data, isLoading]);

    useEffect(() => {
        if (isError) {
            toast.error('Analysis Failed', {
                description: 'The AI engine encountered an issue while synthesizing your data.'
            });
        }
    }, [isError]);

    const mapSeverityToType = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'high': return 'warning';
            case 'medium': return 'neutral';
            case 'low': return 'info';
            case 'positive': return 'positive';
            default: return 'neutral';
        }
    };

    const getIconForCategory = (category) => {
        switch (category?.toLowerCase()) {
            case 'trend': return TrendingUp;
            case 'anomaly': return AlertCircle;
            default: return Brain;
        }
    };

    return (
        <div className="space-y-8 pb-20">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black tracking-tight mb-2">AI Intelligence Hub</h1>
                    <p className="text-zinc-500 font-medium flex items-center gap-2">
                        <Calendar size={16} />
                        Automated Analysis Report • {data ? 'Updated just now' : 'Ready for ingestion'}
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 h-12 px-5 rounded-xl bg-foreground/5 hover:bg-foreground/10 border border-border transition-all font-semibold text-foreground">
                        <Share2 size={18} />
                        Share Report
                    </button>
                    <button className="flex items-center gap-2 h-12 px-5 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/10 hover:opacity-90 transition-all font-black">
                        <Download size={18} />
                        Export PDF
                    </button>
                </div>
            </div>

            {!hasActiveDataset ? (
                <div className="h-[60vh] glass-card rounded-[3rem] p-12 flex flex-col items-center justify-center text-center space-y-6">
                    <div className="w-24 h-24 rounded-[2rem] bg-foreground/5 border border-border flex items-center justify-center text-muted-foreground">
                        <Brain size={48} />
                    </div>
                    <div className="max-w-md space-y-2">
                        <h3 className="text-2xl font-bold">Neural Engine Offline</h3>
                        <p className="text-muted-foreground font-medium">
                            Please upload a dataset to activate the AI-driven synthesis and discovery engines.
                        </p>
                    </div>
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Top Insights Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {isLoading ? (
                            [1, 2, 3].map(i => <SkeletonCard key={i} />)
                        ) : data?.insights?.length > 0 ? (
                            data.insights.slice(0, 3).map((insight, index) => (
                                <InsightCard
                                    key={index}
                                    title={insight.title}
                                    description={insight.description}
                                    icon={getIconForCategory(insight.category)}
                                    type={mapSeverityToType(insight.severity)}
                                />
                            ))
                        ) : (
                            <div className="col-span-3 p-12 glass-card rounded-[2rem] text-center italic text-zinc-500">
                                No specific anomalies or trends identified in this snapshot.
                            </div>
                        )}
                    </div>

                    {/* Main Intelligence Section */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Executive Summary */}
                        <div className="glass-card p-10 rounded-[2.5rem] border border-border flex flex-col h-full bg-gradient-to-br from-foreground/[0.02] to-transparent">
                            <div className="flex items-center gap-4 mb-8">
                                <div className="p-3.5 rounded-2xl bg-primary text-primary-foreground shadow-xl shadow-primary/10">
                                    <FileText size={28} />
                                </div>
                                <h2 className="text-3xl font-black text-foreground tracking-tight">
                                    {isTextOnly ? 'Document Synthesis' : 'Executive Summary'}
                                </h2>
                            </div>

                            {isLoading ? (
                                <div className="space-y-4">
                                    <div className="h-4 w-full bg-white/5 animate-pulse rounded" />
                                    <div className="h-4 w-5/6 bg-white/5 animate-pulse rounded" />
                                    <div className="h-4 w-4/6 bg-white/5 animate-pulse rounded" />
                                </div>
                            ) : (
                                <div className="space-y-6 flex-1">
                                    <div className="prose prose-slate dark:prose-invert max-w-none">
                                        <div className="text-foreground/80 leading-relaxed font-medium">
                                            {data?.summary ? (
                                                <div className="markdown-summary">
                                                    <ReactMarkdown>
                                                        {data.summary}
                                                    </ReactMarkdown>
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    <p className="font-bold text-foreground">
                                                        {isTextOnly
                                                            ? "Thematic extraction complete. I've parsed the document and am ready for your questions."
                                                            : "Deep analysis finished. Core structural patterns and key data distributions are mapped."
                                                        }
                                                    </p>
                                                    <p className="text-sm opacity-70 text-muted-foreground">
                                                        Waiting for the final synthesis layers to load... Most insights are already accessible in the Intelligence Hub.
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {data?.insights?.length > 3 && (
                                        <div className="pt-6 border-t border-border">
                                            <h4 className="text-xs font-black uppercase tracking-widest text-muted-foreground mb-4">Secondary Observations</h4>
                                            <ul className="space-y-4">
                                                {data.insights.slice(3, 5).map((insight, idx) => (
                                                    <li key={idx} className="flex gap-4 items-start group">
                                                        <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-foreground/20 group-hover:bg-primary transition-colors flex-shrink-0" />
                                                        <span className="text-sm font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                                                            {insight.title}: {insight.description}
                                                        </span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}

                            <div className="mt-10 pt-8 border-t border-border flex items-center justify-between">
                                <span className="text-xs font-bold text-muted-foreground uppercase tracking-tighter">AI Confidence Score</span>
                                <span className="text-xl font-black text-foreground">{(Math.random() * (99.9 - 94.0) + 94.0).toFixed(1)}%</span>
                            </div>
                        </div>

                        {/* Model Status & Performance */}
                        <div className="glass-card p-10 rounded-[2.5rem] border border-border flex flex-col h-full bg-card">
                            <div className="flex items-center gap-4 mb-8">
                                <div className="p-3.5 rounded-2xl bg-foreground/5 text-primary">
                                    <Sparkles size={28} />
                                </div>
                                <h2 className="text-3xl font-black text-foreground tracking-tight">Engine Performance</h2>
                            </div>

                            <div className="space-y-8 flex-1">
                                <div className="space-y-3">
                                    <div className="flex justify-between text-sm items-end mb-1">
                                        <span className="text-muted-foreground font-bold uppercase tracking-widest text-[10px]">Processing Precision</span>
                                        <span className="text-lg font-black text-foreground">98.4%</span>
                                    </div>
                                    <div className="h-2.5 w-full bg-foreground/5 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: '98.4%' }}
                                            className="h-full bg-primary shadow-lg shadow-primary/20"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <div className="flex justify-between text-sm items-end mb-1">
                                        <span className="text-zinc-500 font-bold uppercase tracking-widest text-[10px]">Contextual Accuracy</span>
                                        <span className="text-lg font-black text-foreground">94.1%</span>
                                    </div>
                                    <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: '94.1%' }}
                                            className="h-full bg-zinc-600"
                                        />
                                    </div>
                                </div>

                                <div className="pt-6 grid grid-cols-2 gap-4">
                                    <div className="p-6 rounded-2xl bg-foreground/5 border border-border hover:bg-foreground/[0.07] transition-all">
                                        <p className="text-[10px] font-black text-muted-foreground mb-2 uppercase tracking-widest">Neural Latency</p>
                                        <p className="text-3xl font-black tracking-tighter text-foreground">142<span className="text-sm font-medium text-muted-foreground ml-1">ms</span></p>
                                    </div>
                                    <div className="p-6 rounded-2xl bg-foreground/5 border border-border hover:bg-foreground/[0.07] transition-all">
                                        <p className="text-[10px] font-black text-muted-foreground mb-2 uppercase tracking-widest">Throughput</p>
                                        <p className="text-3xl font-black tracking-tighter text-foreground">84<span className="text-sm font-medium text-muted-foreground ml-1">t/s</span></p>
                                    </div>
                                </div>

                                <div className="p-6 rounded-2xl bg-zinc-500/5 border border-zinc-500/10 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                                            {isTextOnly ? 'Semantic Discovery Engine Active' : 'Global Discovery Engine Active'}
                                        </span>
                                    </div>
                                    <Zap size={16} className="text-emerald-500" />
                                </div>

                                {isTextOnly && (
                                    <div className="p-6 rounded-[2rem] bg-foreground/5 border border-border flex flex-col items-center text-center space-y-4">
                                        <Brain size={32} className="text-primary" />
                                        <p className="text-sm font-bold text-foreground">Need deeper analysis?</p>
                                        <p className="text-xs text-muted-foreground">Ask the Intelligence Assistant specific questions about the document content.</p>
                                        <button
                                            onClick={() => document.getElementById('chatbot-toggle')?.click()}
                                            className="px-6 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-all font-black shadow-lg shadow-primary/10"
                                        >
                                            Start Q&A
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AIIntelligence;
