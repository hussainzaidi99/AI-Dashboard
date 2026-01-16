import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BarChart3,
    LineChart,
    PieChart,
    Search,
    Brain,
    Zap,
    Sparkles,
    FileCode,
    Plus,
    Layers,
    ArrowRight,
    TrendingUp
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useDataset } from '../context/DatasetContext';
import { chartsApi } from '../api/charts';
import { aiApi } from '../api/ai';
import VizWidget from '../components/visualizations/VizWidget';

const VisualAnalysis = () => {
    const { activeFileId, activeSheetIndex, hasActiveDataset, isTextOnly } = useDataset();
    const navigate = useNavigate();
    const [selectedChartType, setSelectedChartType] = useState('bar');
    const [query, setQuery] = useState('');
    const [queryLoading, setQueryLoading] = useState(false);
    const [draftWidget, setDraftWidget] = useState(null);

    // Fetch Recommendations with caching
    const { data: recommendations, isLoading: recsLoading } = useQuery({
        queryKey: ['chart-recommendations', activeFileId, activeSheetIndex],
        queryFn: () => chartsApi.recommend(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset && !isTextOnly,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
    });

    const handleQuerySubmit = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setQueryLoading(true);
        try {
            const result = await aiApi.parseQuery({
                file_id: activeFileId,
                sheet_index: activeSheetIndex,
                query: query,
                use_ai: true
            });

            if (result.chart_config) {
                setDraftWidget({
                    title: `AI Result: ${query}`,
                    description: "Generated via Natural Language Processing",
                    chart: result.chart_config
                });
            }
        } catch (err) {
            console.error("Query failed:", err);
        } finally {
            setQueryLoading(false);
        }
    };

    return (
        <div className="space-y-10 pb-20">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div className="max-w-3xl">
                    <h1 className="text-4xl font-black tracking-tight mb-3">Discovery Canvas</h1>
                    <p className="text-muted-foreground text-lg font-medium">
                        Transform raw data into strategic insights using our neural visualization engine.
                    </p>
                </div>
            </div>

            {hasActiveDataset ? (
                isTextOnly ? (
                    <div className="h-[60vh] glass-card rounded-[3rem] p-12 flex flex-col items-center justify-center text-center space-y-6">
                        <div className="w-24 h-24 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center text-primary/40">
                            <Sparkles size={48} />
                        </div>
                        <div className="max-w-md space-y-2">
                            <h3 className="text-2xl font-bold">Chart Engine Not Applicable</h3>
                            <p className="text-muted-foreground font-medium">
                                This document consists primarily of text content. While we can't generate traditional charts, our AI can provide deep insights and answer your questions in the Intelligence Hub.
                            </p>
                        </div>
                        <button
                            onClick={() => navigate('/intelligence')}
                            className="flex items-center gap-2 px-8 py-3 rounded-2xl bg-white text-black font-bold transition-all shadow-xl hover:bg-neutral-200"
                        >
                            <Brain size={18} />
                            Go to Intelligence Hub
                        </button>
                    </div>
                ) : (
                    <div className="space-y-8">
                        {/* Search / NLP Input */}
                        <form onSubmit={handleQuerySubmit} className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-white/10 to-white/5 rounded-[2.5rem] blur opacity-25 group-focus-within:opacity-100 transition duration-1000"></div>
                            <div className="relative">
                                <div className="absolute left-6 top-1/2 -translate-y-1/2 text-muted-foreground">
                                    <Brain size={24} className="animate-pulse" />
                                </div>
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Ask the Intelligence Engine... e.g., 'Show me revenue trends by region as a bar chart'"
                                    className="w-full h-16 bg-black/40 border border-white/10 rounded-[2rem] pl-16 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all backdrop-blur-xl"
                                    disabled={queryLoading}
                                />
                                <button
                                    type="submit"
                                    disabled={queryLoading || !query.trim()}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 px-6 py-3 bg-white text-black font-bold rounded-2xl shadow-xl hover:bg-neutral-200 transition-all flex items-center gap-2 disabled:opacity-20"
                                >
                                    {queryLoading ? 'Thinking...' : 'Analyze'}
                                </button>
                            </div>
                        </form>

                        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                            {/* Recommendations Sidebar */}
                            <div className="xl:col-span-1 space-y-6">
                                <div className="glass-card rounded-[2.5rem] p-8 space-y-6 border border-white/5">
                                    <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest">
                                        <Zap size={14} />
                                        <span>AI Suggestions</span>
                                    </div>

                                    <div className="space-y-4">
                                        {recsLoading ? (
                                            [1, 2, 3].map(i => <div key={i} className="h-24 rounded-2xl bg-white/5 animate-pulse" />)
                                        ) : recommendations?.recommendations?.map((rec, idx) => (
                                            <button
                                                key={idx}
                                                className="w-full p-5 rounded-[2rem] bg-white/5 border border-white/10 hover:border-primary/50 text-left transition-all group"
                                            >
                                                <div className="flex items-center justify-between mb-2">
                                                    <span className="text-[10px] font-black uppercase text-primary">{rec.chart_type}</span>
                                                    <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-bold">
                                                        {Math.round(rec.confidence * 100)}%
                                                    </span>
                                                </div>
                                                <p className="text-xs font-bold text-white/80 group-hover:text-white leading-relaxed">
                                                    {rec.reasoning.split('.')[0]}.
                                                </p>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Main Canvas */}
                            <div className="xl:col-span-3 space-y-8">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {draftWidget && (
                                        <VizWidget
                                            title={draftWidget.title}
                                            description={draftWidget.description}
                                            config={draftWidget.chart}
                                            isAIResult
                                        />
                                    )}
                                    {recommendations?.recommendations?.slice(0, 4).map((rec, idx) => (
                                        <VizWidget
                                            key={idx}
                                            title={`${rec.chart_type.toUpperCase()} Analysis`}
                                            description={rec.reasoning}
                                            config={rec.config}
                                        />
                                    ))}
                                </div>

                                <div className="h-[200px] border-2 border-dashed border-white/5 rounded-[3rem] flex items-center justify-center group cursor-pointer hover:border-white/10 transition-colors">
                                    <div className="text-center group-hover:scale-105 transition-transform duration-500">
                                        <div className="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4 text-muted-foreground/30 border border-white/5">
                                            <Plus size={32} />
                                        </div>
                                        <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40">Drop new logic node</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )
            ) : (
                <div className="h-[60vh] glass-card rounded-[3rem] p-12 flex flex-col items-center justify-center text-center space-y-6 text-zinc-700">
                    <div className="w-24 h-24 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center">
                        <TrendingUp size={48} />
                    </div>
                    <div className="max-w-sm space-y-2">
                        <h3 className="text-2xl font-bold">Analysis Engine Offline</h3>
                        <p className="text-muted-foreground font-medium">
                            Please upload a dataset to begin visual synthesis. We accommodate Excel, CSV, PDF, and DOCX formats.
                        </p>
                    </div>
                    <button
                        className="group flex items-center gap-2 px-8 py-3 rounded-2xl bg-white text-black font-bold transition-all shadow-xl hover:bg-neutral-200"
                        onClick={() => navigate('/upload')}
                    >
                        Go to Ingestion Zone
                        <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            )}
        </div>
    );
};

export default VisualAnalysis;
