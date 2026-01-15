import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    BarChart3,
    Settings2,
    Download,
    Share2,
    Layout,
    Move,
    Plus
} from 'lucide-react';
import { useDataset } from '../context/DatasetContext';
import { dataApi } from '../api/data';
import VizWidget from '../components/visualizations/VizWidget';

const VisualAnalysis = () => {
    const { activeFileId, activeSheetIndex, hasActiveDataset } = useDataset();
    const [selectedChartType, setSelectedChartType] = useState('bar');
    const [query, setQuery] = useState('');
    const [queryLoading, setQueryLoading] = useState(false);

    const handleInquiry = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setQueryLoading(true);
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/ai/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                },
                body: JSON.stringify({ file_id: activeFileId, query: query, sheet_index: activeSheetIndex })
            });
            const data = await response.json();
            console.log('AI Query Result:', data);
            // In a real app, we would add this new widget to our recommendations or state
            alert("AI has parsed your query! New visualization logic would be injected here.");
        } catch (err) {
            console.error('Inquiry error:', err);
        } finally {
            setQueryLoading(false);
        }
    };

    // Fetch Recommended Charts
    const { data: recommendations, isLoading: recsLoading } = useQuery({
        queryKey: ['recommendations', activeFileId, activeSheetIndex],
        queryFn: async () => {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/charts/recommend?file_id=${activeFileId}&sheet_index=${activeSheetIndex}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
                }
            });
            return response.json();
        },
        enabled: hasActiveDataset
    });

    return (
        <div className="space-y-8 pb-20">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Visual Analysis</h2>
                    <p className="text-muted-foreground mt-1">Deep dive into your dataset with AI-powered visualization tools.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="px-4 py-2 rounded-xl border border-white/10 hover:bg-white/5 transition-all text-sm font-medium flex items-center gap-2">
                        <Settings2 size={16} />
                        Configure View
                    </button>
                    <button className="px-4 py-2 rounded-xl bg-primary text-white font-bold text-sm shadow-lg shadow-primary/20 hover:bg-blue-600 transition-all flex items-center gap-2">
                        <Plus size={16} />
                        Add Custom Widget
                    </button>
                </div>
            </div>

            {!hasActiveDataset ? (
                <div className="h-[60vh] glass-card rounded-[3rem] p-12 flex flex-col items-center justify-center text-center space-y-6">
                    <div className="w-24 h-24 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center text-muted-foreground/30">
                        <BarChart3 size={48} />
                    </div>
                    <div className="max-w-md space-y-2">
                        <h3 className="text-2xl font-bold">Analysis Engine Offline</h3>
                        <p className="text-muted-foreground">
                            Please ingest a dataset first to activate the multi-dimensional visual analysis engine.
                        </p>
                    </div>
                    <button className="px-8 py-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 font-bold transition-all">
                        Go to Ingestion Zone
                    </button>
                </div>
            ) : (
                <div className="space-y-8">
                    {/* Intelligence Inquiry Bar */}
                    <form onSubmit={handleInquiry} className="glass-card p-6 rounded-[2rem] border-primary/20 shadow-[0_0_40px_rgba(59,130,246,0.1)]">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                {queryLoading ? <div className="w-6 h-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin" /> : <BarChart3 size={24} />}
                            </div>
                            <div className="flex-1 relative group">
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Ask the Intelligence Engine... e.g., 'Show me revenue trends by region as a bar chart'"
                                    className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl pl-4 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-muted-foreground/50"
                                    disabled={queryLoading}
                                />
                                <button
                                    type="submit"
                                    disabled={queryLoading || !query.trim()}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 bg-primary text-white font-bold rounded-xl shadow-lg shadow-primary/20 hover:bg-blue-600 transition-all flex items-center gap-2 disabled:opacity-50"
                                >
                                    {queryLoading ? 'Processing...' : 'Ask AI'}
                                </button>
                            </div>
                        </div>
                    </form>

                    <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
                        {/* Controls / Recommendations Sidebar */}
                        <div className="xl:col-span-1 space-y-6">
                            <div className="glass-card rounded-[2rem] p-6 space-y-6">
                                <h3 className="font-bold text-sm uppercase tracking-widest text-muted-foreground">AI Intelligence</h3>

                                <div className="space-y-3">
                                    <p className="text-xs font-medium text-white/50">Suggested Visualizations</p>
                                    {recsLoading ? (
                                        [1, 2, 3].map(i => <div key={i} className="h-20 rounded-2xl bg-white/5 animate-pulse" />)
                                    ) : recommendations?.recommendations?.map((rec, idx) => (
                                        <button
                                            key={idx}
                                            className="w-full p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-primary/50 text-left transition-all group"
                                        >
                                            <div className="flex items-center justify-between mb-2">
                                                <span className="text-[10px] font-bold uppercase tracking-tighter text-primary">{rec.chart_type}</span>
                                                <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                                                    {Math.round(rec.confidence * 100)}% Match
                                                </span>
                                            </div>
                                            <p className="text-xs font-semibold text-white/80 group-hover:text-white transition-colors">
                                                {rec.reasoning.split('.')[0]}.
                                            </p>
                                        </button>
                                    ))}
                                </div>

                                <div className="pt-6 border-t border-white/5">
                                    <button className="w-full p-4 rounded-2xl bg-primary/10 hover:bg-primary/20 text-primary font-bold text-sm transition-all flex items-center justify-center gap-2">
                                        <Layout size={16} />
                                        Auto-Layout Dashboard
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Visualization Canvas */}
                        <div className="xl:col-span-3 space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {recommendations?.recommendations?.slice(0, 4).map((rec, idx) => (
                                    <VizWidget
                                        key={idx}
                                        title={`${rec.chart_type.toUpperCase()} Analysis`}
                                        description={rec.reasoning}
                                        config={rec.config}
                                    />
                                ))}
                            </div>

                            <div className="h-[200px] border-2 border-dashed border-white/5 rounded-[2.5rem] flex items-center justify-center group cursor-pointer hover:border-white/10 transition-colors">
                                <div className="text-center group-hover:scale-105 transition-transform duration-500">
                                    <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mx-auto mb-3 text-muted-foreground/50">
                                        <Plus size={24} />
                                    </div>
                                    <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground/60">Drop new chart here</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VisualAnalysis;
