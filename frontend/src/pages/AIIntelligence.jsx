import React from 'react';
import { motion } from 'framer-motion';
import {
    Brain,
    TrendingUp,
    AlertCircle,
    Zap,
    FileText,
    Download,
    Share2,
    Calendar
} from 'lucide-react';

const InsightCard = ({ title, description, icon: Icon, type }) => {
    const typeStyles = {
        positive: 'border-emerald-500/20 bg-emerald-500/5 text-emerald-400',
        warning: 'border-amber-500/20 bg-amber-500/5 text-amber-400',
        neutral: 'border-blue-500/20 bg-blue-500/5 text-blue-400'
    };

    return (
        <motion.div
            whileHover={{ y: -5 }}
            className={`p-6 rounded-2xl border backdrop-blur-md ${typeStyles[type] || typeStyles.neutral} transition-all duration-300`}
        >
            <div className="flex items-start justify-between mb-4">
                <div className="p-3 rounded-xl bg-white/5">
                    <Icon size={24} />
                </div>
                <div className="text-xs font-medium px-2 py-1 rounded-md bg-white/10 uppercase tracking-wider">
                    {type}
                </div>
            </div>
            <h3 className="text-lg font-semibold mb-2 text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{description}</p>
        </motion.div>
    );
};

const AIIntelligence = () => {
    const insights = [
        {
            title: "Anomaly Detected in Sales Data",
            description: "We've identified a 15% deviation in the 'Electronics' category during Q3. This pattern correlates with the recent logistics shift.",
            icon: AlertCircle,
            type: "warning"
        },
        {
            title: "Growth Forecast: 22% Increase",
            description: "Based on current training sets, we project a significant uptick in customer engagement for the upcoming holiday season.",
            icon: TrendingUp,
            type: "positive"
        },
        {
            title: "Correlation: Weather vs Footfall",
            description: "AI analysis shows a 0.82 correlation between precipitation levels and retail conversion rates in urban centers.",
            icon: Brain,
            type: "neutral"
        }
    ];

    return (
        <div className="space-y-8 pb-20">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight mb-2">AI Intelligence Hub</h1>
                    <p className="text-muted-foreground flex items-center gap-2">
                        <Calendar size={16} />
                        Automated Analysis Report • Last updated 2 hours ago
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all font-medium">
                        <Share2 size={18} />
                        Share Report
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all font-medium">
                        <Download size={18} />
                        Export PDF
                    </button>
                </div>
            </div>

            {/* Top Insights Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {insights.map((insight, index) => (
                    <InsightCard key={index} {...insight} />
                ))}
            </div>

            {/* Main Intelligence Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Executive Summary */}
                <div className="glass-card p-8 rounded-3xl border border-white/10">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 rounded-2xl bg-primary/20 text-primary">
                            <FileText size={24} />
                        </div>
                        <h2 className="text-2xl font-bold text-foreground">Executive Summary</h2>
                    </div>
                    <div className="space-y-4 text-muted-foreground leading-relaxed">
                        <p>
                            The current dataset indicates a robust upward trend in overall operational efficiency. Our models have processed over 2.4 million data points to generate these conclusions.
                        </p>
                        <ul className="space-y-3">
                            <li className="flex gap-3 items-start">
                                <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                                <span>Optimization of resource allocation could yield up to 12% cost savings in the next fiscal quarter.</span>
                            </li>
                            <li className="flex gap-3 items-start">
                                <div className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
                                <span>Customer retention patterns suggest high sensitivity to response times in the support layer.</span>
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Model Status */}
                <div className="glass-card p-8 rounded-3xl border border-white/10">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 rounded-2xl bg-emerald-500/20 text-emerald-400">
                            <Zap size={24} />
                        </div>
                        <h2 className="text-2xl font-bold text-foreground">Model Performance</h2>
                    </div>
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Accuracy (Llama 3.3 Fine-tuned)</span>
                                <span className="font-semibold text-foreground">98.4%</span>
                            </div>
                            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: '98.4%' }}
                                    className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                                />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Confidence Score</span>
                                <span className="font-semibold text-foreground">94.1%</span>
                            </div>
                            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: '94.1%' }}
                                    className="h-full bg-primary shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                />
                            </div>
                        </div>
                        <div className="pt-4 grid grid-cols-2 gap-4">
                            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                <p className="text-xs text-muted-foreground mb-1 uppercase tracking-tight">Latency</p>
                                <p className="text-xl font-bold">142ms</p>
                            </div>
                            <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                                <p className="text-xs text-muted-foreground mb-1 uppercase tracking-tight">Tokens/sec</p>
                                <p className="text-xl font-bold">84</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AIIntelligence;
