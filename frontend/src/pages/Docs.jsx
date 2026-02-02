import React from 'react';
import { motion } from 'framer-motion';
import {
    BookOpen,
    Upload,
    Zap,
    BarChart3,
    Shield,
    Terminal,
    Cpu,
    Globe,
    Layers,
    ArrowRight
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Docs = () => {
    const { theme } = useTheme();
    const sections = [
        {
            title: "Getting Started",
            icon: BookOpen,
            content: "Welcome to AI Analytics Dashboard. This platform is designed to transform your raw data into actionable intelligence using advanced machine learning models and high-performance visualizations.",
            steps: [
                "Navigate to the Data Upload section.",
                "Upload your CSV or Excel files.",
                "Wait for the system to synchronize and process the dataset.",
                "Explore the Intelligence Snapshot for immediate insights."
            ]
        },
        {
            title: "Data Intelligence",
            icon: Cpu,
            content: "Our neural engine scans your data for patterns, anomalies, and correlations that aren't visible to the naked eye.",
            features: [
                "Automated Segment Analysis",
                "Anomaly Detection",
                "Predictive Trend Mapping",
                "Natural Language Summaries"
            ]
        },
        {
            title: "Credits System",
            icon: Zap,
            content: "The system uses a token-based credit system for processing complex analytical tasks.",
            info: "1 Credit is approximately equivalent to 70,000 processed tokens. Credits are consumed during data upload and AI analysis requests."
        }
    ];

    return (
        <div className="max-w-6xl mx-auto pb-20 space-y-12">
            {/* Header */}
            <header className={`relative py-16 px-8 rounded-[3rem] overflow-hidden transition-all duration-500 shadow-2xl ${theme === 'dark'
                    ? 'bg-[#0a0a0a] border border-white/5 shadow-white/5'
                    : 'bg-primary text-primary-foreground shadow-primary/20'
                }`}>
                <div className={`absolute inset-0 opacity-50 ${theme === 'dark'
                        ? 'bg-gradient-to-br from-blue-900/20 via-transparent to-purple-900/20'
                        : 'bg-gradient-to-br from-primary via-primary to-blue-600'
                    }`} />
                <div className="relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-[10px] font-black uppercase tracking-widest mb-6"
                    >
                        <Terminal size={12} />
                        AI Analytics Documentation 
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-7xl font-black tracking-tighter mb-6"
                    >
                        Master the <br />
                        <span className="text-blue-300">Intelligence Core.</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className={`text-xl max-w-2xl font-medium ${theme === 'dark' ? 'text-muted-foreground' : 'text-primary-foreground/70'
                            }`}
                    >
                        Comprehensive guide to navigating, analyzing, and synthesizing high-dimensional data within our neural ecosystem.
                    </motion.p>
                </div>
            </header>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {sections.map((section, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: idx * 0.1 + 0.3 }}
                        className="glass-card rounded-[2.5rem] p-10 border border-border group hover:border-primary/20 transition-all duration-500"
                    >
                        <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-8 group-hover:scale-110 transition-transform duration-500">
                            <section.icon size={28} />
                        </div>
                        <h3 className="text-2xl font-black mb-4 text-foreground tracking-tight">{section.title}</h3>
                        <p className="text-muted-foreground leading-relaxed mb-6 font-medium">
                            {section.content}
                        </p>

                        {section.steps && (
                            <ul className="space-y-4">
                                {section.steps.map((step, i) => (
                                    <li key={i} className="flex items-start gap-3 text-sm font-semibold text-foreground/80">
                                        <div className="mt-1 w-5 h-5 rounded-full bg-primary/10 flex items-center justify-center text-[10px] text-primary shrink-0">
                                            {i + 1}
                                        </div>
                                        {step}
                                    </li>
                                ))}
                            </ul>
                        )}

                        {section.features && (
                            <div className="grid grid-cols-2 gap-3 mt-4">
                                {section.features.map((feat, i) => (
                                    <div key={i} className="px-4 py-2 rounded-xl bg-foreground/5 border border-border text-[10px] font-black uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                                        <Layers size={12} className="text-primary" />
                                        {feat}
                                    </div>
                                ))}
                            </div>
                        )}

                        {section.info && (
                            <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/20 text-xs font-medium text-blue-500/80 italic">
                                {section.info}
                            </div>
                        )}
                    </motion.div>
                ))}

                {/* Integration Card */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.6 }}
                    className="glass-card rounded-[2.5rem] p-10 border border-border bg-gradient-to-br from-primary/5 to-transparent relative overflow-hidden flex flex-col justify-between"
                >
                    <div>
                        <div className="flex items-center gap-3 mb-8">
                            <Globe size={32} className="text-primary" />
                            <div className="h-px flex-1 bg-border" />
                        </div>
                        <h3 className="text-2xl font-black mb-4 text-foreground tracking-tight">API Integration</h3>
                        <p className="text-muted-foreground leading-relaxed font-medium">
                            Connect your external data pipelines directly to our analytics core for real-time synthesis. We are working on making this feature available soon.
                        </p>
                    </div>
                    <button className="mt-8 flex items-center gap-2 text-primary font-black text-sm uppercase tracking-widest hover:gap-4 transition-all w-fit">
                        Explore SDK <ArrowRight size={16} />
                    </button>
                </motion.div>
            </div>

            {/* Footer Note */}
            <div className="text-center pt-12">
                <p className="text-sm text-muted-foreground font-medium">
                    Facing issues? Contact our systems engineer at <a href="mailto:contact@sabasoftgames.com" className="text-primary font-bold hover:underline">contact@sabasoftgames.com</a>
                </p>
            </div>
        </div>
    );
};

export default Docs;
