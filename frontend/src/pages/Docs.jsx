import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
    BookOpen,
    Upload,
    Zap,
    BarChart3,
    Terminal,
    Cpu,
    ArrowRight,
    ArrowLeft,
    CheckCircle2,
    Database,
    Brain,
    Sparkles,
    MousePointer2,
    ChevronRight
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { Link } from 'react-router-dom';
import Footer from '../components/shared/Footer';

const Docs = () => {
    const { theme } = useTheme();
    const [activeSection, setActiveSection] = useState('get-started');

    // Helper Components inside Docs to ensure scope sharing
    const Annotation = ({ children, x, y, arrow = "down" }) => (
        <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
            className="absolute z-20 pointer-events-none"
            style={{ left: x, top: y }}
        >
            <div className="relative flex flex-col items-center">
                {arrow === "up" && (
                    <div className="text-rose-500 mb-1">
                        <MousePointer2 size={24} style={{ transform: 'rotate(135deg)' }} />
                    </div>
                )}
                <div className="px-3 py-1.5 bg-rose-500 text-white font-black text-[10px] uppercase tracking-tighter rounded-lg shadow-xl shadow-rose-500/40 whitespace-nowrap rotate-[-5deg] border-2 border-white/20">
                    {children}
                </div>
                {arrow === "down" && (
                    <motion.div
                        animate={{ y: [0, 5, 0] }}
                        transition={{ repeat: Infinity, duration: 2 }}
                        className="text-rose-500 mt-1"
                    >
                        <ArrowRight size={24} style={{ transform: 'rotate(90deg)' }} />
                    </motion.div>
                )}
            </div>
        </motion.div>
    );

    const BrowserMockup = ({ children, title, active = false }) => (
        <div className={`relative rounded-2xl border transition-all duration-500 overflow-hidden bg-card ${active ? 'border-primary/40 shadow-2xl shadow-primary/10' : 'border-border shadow-sm'}`}>
            <div className="h-8 bg-muted border-b flex items-center px-4 gap-1.5" style={{ background: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}>
                <div className="w-2.5 h-2.5 rounded-full bg-rose-500/40" />
                <div className="w-2.5 h-2.5 rounded-full bg-amber-500/40" />
                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/40" />
                <div className="ml-4 px-3 py-1 bg-background/50 rounded-md text-[9px] font-bold text-muted-foreground w-40 truncate">
                    {title}
                </div>
            </div>
            <div className="p-1 relative min-h-[240px] bg-background/30 backdrop-blur-sm">
                {children}
            </div>
        </div>
    );

    const sections = useMemo(() => [
        {
            id: "get-started",
            title: "Getting Started",
            icon: BookOpen,
            color: "text-blue-500",
            bg: "bg-blue-500/10",
            description: "Go from zero to intelligence in under 3 minutes. Our streamlined onboarding ensures you spend less time configuring and more time discovering.",
            steps: [
                "Authenticate your workspace via Login or Registration.",
                "Access the Ingestion Zone from the sidebar.",
                "Upload a supported dataset (CSV, XLSX, PDF, DOCX).",
                "Execute the Neural Analysis and view your Discovery Canvas."
            ],
            mockup: (
                <div className="p-8 space-y-4">
                    <div className="h-32 rounded-xl border-2 border-dashed border-primary/20 bg-primary/5 flex flex-col items-center justify-center gap-3 relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent" />
                        <Upload size={32} className="text-primary/40" />
                        <div className="h-2 w-24 bg-primary/10 rounded-full" />
                        <Annotation x="50%" y="20%" arrow="down">Drop CSV/Excel Here</Annotation>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                        <div className="h-2 bg-muted rounded-full w-full" />
                        <div className="h-2 bg-muted rounded-full w-2/3" />
                        <div className="h-2 bg-muted rounded-full w-full" />
                    </div>
                </div>
            )
        },
        {
            id: "data-ingestion",
            title: "Data Ingestion",
            icon: Database,
            color: "text-emerald-500",
            bg: "bg-emerald-500/10",
            description: "Our proprietary extraction engine handles the heavy lifting. We automatically identify schemas, normalize entities, and handle temporal data distribution.",
            features: [
                { title: "Smart Normalization", desc: "Automated handling of dates, currencies, and missing values." },
                { title: "Multi-Format Support", desc: "Seamless parsing of structured (Excel/CSV) and semi-structured (PDF/DOCX) data." },
                { title: "Version Control", desc: "Compare different snapshots of your data over time." }
            ],
            mockup: (
                <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="h-4 w-32 bg-foreground/10 rounded-lg" />
                        <div className="h-8 w-8 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                            <CheckCircle2 size={14} />
                        </div>
                    </div>
                    <div className="space-y-3">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-foreground/5 border border-border/50 relative">
                                <div className="w-8 h-8 rounded-lg bg-foreground/10" />
                                <div className="flex-1 space-y-1.5">
                                    <div className="h-2 w-20 bg-foreground/20 rounded-full" />
                                    <div className="h-1.5 w-32 bg-foreground/10 rounded-full" />
                                </div>
                                {i === 1 && <Annotation x="80%" y="-10%" arrow="down">Automated Validation</Annotation>}
                            </div>
                        ))}
                    </div>
                </div>
            )
        },
        {
            id: "intelligence-hub",
            title: "Intelligence Hub",
            icon: Brain,
            color: "text-purple-500",
            bg: "bg-purple-500/10",
            description: "The neural engine scans your data for high-dimensional patterns. It generates natural language summaries and identifies critical anomalies automatically.",
            outcomes: [
                "Executive summaries written by AI for quick digestion.",
                "Pattern recognition across disparate data columns.",
                "Risk identification with severity-weighted observation cards."
            ],
            mockup: (
                <div className="p-6 space-y-4">
                    <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/20 relative">
                        <div className="flex items-center gap-2 mb-3">
                            <Sparkles size={14} className="text-purple-500" />
                            <div className="h-2 w-24 bg-purple-500/30 rounded-full" />
                        </div>
                        <div className="space-y-2">
                            <div className="h-2 w-full bg-foreground/10 rounded-full" />
                            <div className="h-2 w-5/6 bg-foreground/10 rounded-full" />
                        </div>
                        <Annotation x="40%" y="60%" arrow="up">AI Generated Summary</Annotation>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 relative">
                            <div className="h-1.5 w-12 bg-amber-500/40 rounded-full mb-2" />
                            <div className="h-2 w-full bg-foreground/10 rounded-full" />
                            <Annotation x="10%" y="40%" arrow="up">Severity Tag</Annotation>
                        </div>
                        <div className="p-3 rounded-xl bg-blue-500/5 border border-blue-500/20">
                            <div className="h-1.5 w-12 bg-blue-500/40 rounded-full mb-2" />
                            <div className="h-2 w-full bg-foreground/10 rounded-full" />
                        </div>
                    </div>
                </div>
            )
        },
        {
            id: "discovery-canvas",
            title: "Discovery Canvas",
            icon: BarChart3,
            color: "text-amber-500",
            bg: "bg-amber-500/10",
            description: "Interact with your data through natural language. Ask complex questions and receive immediate, high-fidelity visualizations.",
            features: [
                "Natural Language Queries: 'Show me revenue by region'.",
                "Smart Suggestions: AI-driven recommendations for next steps.",
                "Export-Ready: One-click PDF or PNG generation for reports."
            ],
            mockup: (
                <div className="p-6">
                    <div className="h-12 rounded-2xl bg-foreground/5 border border-primary/30 flex items-center px-4 gap-3 relative mb-6 backdrop-blur-md">
                        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
                            <Zap size={16} />
                        </div>
                        <div className="h-2 w-48 bg-foreground/20 rounded-full" />
                        <Annotation x="60%" y="-40%" arrow="down">Ask AI Anything</Annotation>
                    </div>
                    <div className="flex gap-4">
                        <div className="h-24 flex-1 bg-foreground/5 rounded-2xl border border-border flex flex-col justify-end p-4 gap-2">
                            <div className="h-10 w-full bg-primary/20 rounded-lg self-end" />
                            <div className="h-6 w-full bg-primary/10 rounded-lg self-end" />
                        </div>
                        <div className="h-24 flex-1 bg-foreground/5 rounded-2xl border border-border flex flex-col justify-end p-4 gap-2">
                            <div className="h-14 w-full bg-primary/30 rounded-lg self-end" />
                            <div className="h-4 w-full bg-primary/10 rounded-lg self-end" />
                        </div>
                    </div>
                </div>
            )
        }
    ], [theme]);

    useEffect(() => {
        const handleScroll = () => {
            const scrollPosition = window.scrollY + 100;
            for (const section of sections) {
                const element = document.getElementById(section.id);
                if (element) {
                    const { offsetTop, offsetHeight } = element;
                    if (scrollPosition >= offsetTop && scrollPosition < offsetTop + offsetHeight) {
                        setActiveSection(section.id);
                        break;
                    }
                }
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, [sections]);

    const scrollToSection = (id) => {
        const element = document.getElementById(id);
        if (element) {
            window.scrollTo({
                top: element.offsetTop - 40,
                behavior: 'smooth'
            });
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col transition-colors duration-500">
            <div className="flex flex-1 max-w-7xl mx-auto w-full relative">
                {/* Sidebar Navigation */}
                <aside className="hidden lg:block w-72 sticky top-0 h-fit pt-12 pb-20 px-6">
                    <div className="space-y-8">
                        <div>
                            <Link
                                to="/"
                                className="inline-flex items-center gap-2 group text-sm font-bold text-muted-foreground hover:text-foreground transition-colors mb-10"
                            >
                                <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                                Back to Console
                            </Link>
                            <h2 className="text-2xl font-black tracking-tighter mb-1">Documentation</h2>
                            <p className="text-[10px] uppercase tracking-widest font-black text-primary/50">Version 1.4.2 Core</p>
                        </div>

                        <nav className="space-y-2">
                            {sections.map((section) => (
                                <button
                                    key={section.id}
                                    onClick={() => scrollToSection(section.id)}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl transition-all duration-300 group ${activeSection === section.id
                                        ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                                        : 'hover:bg-foreground/5 text-muted-foreground hover:text-foreground'
                                        }`}
                                >
                                    <section.icon size={18} className={activeSection === section.id ? 'text-white' : section.color} />
                                    <span className="text-sm font-black tracking-tight">{section.title}</span>
                                    <ChevronRight
                                        size={14}
                                        className={`ml-auto transition-transform ${activeSection === section.id ? 'translate-x-0' : '-translate-x-2 opacity-0 group-hover:opacity-100'}`}
                                    />
                                </button>
                            ))}
                        </nav>

                        <div className="pt-10">
                            <div className="p-6 rounded-[2rem] bg-foreground/5 border border-border relative overflow-hidden group">
                                <Zap size={40} className="text-primary/10 absolute -right-2 -bottom-2 group-hover:scale-125 transition-transform duration-700" />
                                <h4 className="text-xs font-black uppercase tracking-widest text-primary mb-2">Need API Access?</h4>
                                <p className="text-xs text-muted-foreground font-medium mb-4 leading-relaxed">Connect your pipelines directly to our neural engine.</p>
                                <button className="text-[10px] font-black uppercase tracking-wider text-foreground hover:text-primary underline flex items-center gap-1">
                                    Inquire Now <ArrowRight size={10} />
                                </button>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 px-6 lg:px-12 py-12 lg:py-20 space-y-32">
                    {/* Hero Section */}
                    <section id="hero" className="space-y-6">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-black uppercase tracking-widest text-primary"
                        >
                            <Terminal size={12} />
                            Operation Manual
                        </motion.div>
                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-6xl md:text-8xl font-black tracking-tighter leading-none"
                        >
                            Master the <br />
                            <span className="text-primary">Intelligence Hub.</span>
                        </motion.h1>
                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="text-xl md:text-2xl text-muted-foreground font-medium max-w-2xl leading-relaxed"
                        >
                            A technical deep-dive into navigating, analyzing, and synthesizing high-dimensional data within our neural ecosystem.
                        </motion.p>
                    </section>

                    {/* Dynamic Sections */}
                    {sections.map((section, idx) => (
                        <section key={section.id} id={section.id} className="grid grid-cols-1 xl:grid-cols-2 gap-16 items-start scroll-mt-20">
                            <div className="space-y-8">
                                <div className="flex items-center gap-4">
                                    <div className={`w-16 h-16 rounded-[1.5rem] ${section.bg} ${section.color} flex items-center justify-center`}>
                                        <section.icon size={32} />
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-black tracking-tight">{section.title}</h2>
                                        <p className="text-xs uppercase tracking-[0.2em] font-black opacity-50">Feature Set 0{idx + 1}</p>
                                    </div>
                                </div>
                                <p className="text-lg text-muted-foreground leading-relaxed font-medium">
                                    {section.description}
                                </p>

                                {section.steps && (
                                    <div className="space-y-4 pt-4">
                                        <h4 className="text-xs font-black uppercase tracking-widest text-primary">Integration Sequence</h4>
                                        <div className="grid grid-cols-1 gap-3">
                                            {section.steps.map((step, i) => (
                                                <div key={i} className="flex gap-4 p-4 rounded-2xl bg-foreground/5 border border-border group hover:border-primary/20 transition-all">
                                                    <div className="w-8 h-8 rounded-full bg-background border border-border flex items-center justify-center text-xs font-black shrink-0 group-hover:bg-primary group-hover:text-primary-foreground group-hover:border-primary transition-all">
                                                        {i + 1}
                                                    </div>
                                                    <p className="text-sm font-semibold text-foreground/80 leading-relaxed pt-1.5">{step}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {section.features && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {section.features.map((feat, i) => (
                                            <div key={i} className="p-6 rounded-[2rem] bg-foreground/5 border border-border space-y-2">
                                                <h4 className="text-sm font-black tracking-tight">{feat.title}</h4>
                                                <p className="text-xs text-muted-foreground font-medium leading-relaxed">{feat.desc}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {section.outcomes && (
                                    <div className="space-y-3">
                                        {section.outcomes.map((outcome, i) => (
                                            <div key={i} className="flex items-center gap-3 text-sm font-semibold text-foreground/70">
                                                <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                                                {outcome}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="relative group">
                                <div className="absolute -inset-4 bg-gradient-to-br from-primary/10 via-transparent to-transparent rounded-[3rem] blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                                <BrowserMockup title={`Internal: ${section.title}.view`} active={activeSection === section.id}>
                                    {section.mockup}
                                </BrowserMockup>
                                <div className="mt-4 flex items-center justify-between px-2">
                                    <div className="flex items-center gap-2">
                                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                        <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">Interactive Guide Active</span>
                                    </div>
                                    <div className="text-[10px] font-medium text-muted-foreground italic truncate max-w-[150px]">
                                        Ref: component/guides/{section.id}.js
                                    </div>
                                </div>
                            </div>
                        </section>
                    ))}

                    {/* Footer Support */}
                    <section className="pt-20 text-center space-y-8">
                        <div className="max-w-xl mx-auto space-y-4">
                            <h3 className="text-3xl font-black tracking-tight">Still have questions?</h3>
                            <p className="text-muted-foreground font-medium">Our systems engineers are ready to assist with custom implementations and high-scale deployments.</p>
                        </div>
                        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
                            <a
                                href="mailto:contact@sabasoftgames.com"
                                className="px-8 py-4 rounded-2xl bg-primary text-primary-foreground font-black text-sm uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all"
                            >
                                Contact Systems Lead
                            </a>
                            <button className="px-8 py-4 rounded-2xl bg-foreground/5 border border-border text-foreground font-black text-sm uppercase tracking-widest hover:bg-foreground/10 transition-all">
                                Request Enterprise Demo
                            </button>
                        </div>
                    </section>
                </main>
            </div>
            <Footer />
        </div>
    );
};

export default Docs;
