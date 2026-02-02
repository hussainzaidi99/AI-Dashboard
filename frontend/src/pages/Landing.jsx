import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowUpRight, BarChart3, Search, Activity, Zap, User, Settings, LogOut, ChevronDown } from 'lucide-react';
import LightRays from '../components/backgrounds/LightRays';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import ThemeToggle from '../components/shared/ThemeToggle';
import Footer from '../components/shared/Footer';

const Landing = () => {
    const navigate = useNavigate();
    const { isAuthenticated, user, logout } = useAuth();
    const { theme } = useTheme();
    const [isProfileOpen, setIsProfileOpen] = React.useState(false);

    const initials = user?.email?.substring(0, 2).toUpperCase() || 'AI';

    return (
        <div className="relative min-h-screen bg-background text-foreground overflow-hidden font-sans selection:bg-primary/20 transition-colors duration-500">
            {/* Background Effect - Dynamic Theme Glow */}
            <div className="fixed inset-0 z-0 opacity-95">
                <LightRays
                    raysOrigin="top-center"
                    raysColor={theme === 'dark' ? "#f8fafc" : "#64748b"}
                    raysSpeed={theme === 'dark' ? 0.4 : 0.2}
                    lightSpread={0.8}
                    rayLength={2.5}
                    followMouse={true}
                    mouseInfluence={0.03}
                    pulsating={true}
                />
            </div>

            {/* Public Header */}
            <header className="relative z-20 h-20 flex items-center justify-between px-8 md:px-16 glass border-b border-border mx-6 mt-4 rounded-3xl transition-all duration-500">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/10">
                        <BarChart3 className="text-primary-foreground" size={24} strokeWidth={2.5} />
                    </div>
                    <h1 className="text-xl font-black font-heading tracking-tight text-foreground">
                        AI Analytics
                    </h1>
                </div>

                <nav className="hidden md:flex items-center gap-10">
                </nav>

                <div className="flex items-center gap-6">
                    <ThemeToggle className="bg-foreground/5 border border-border" />

                    {isAuthenticated ? (
                        /* Profile Dropdown for Authenticated Users */
                        <div className="relative z-50">
                            <button
                                onClick={() => setIsProfileOpen(!isProfileOpen)}
                                className="flex items-center gap-3 p-1.5 pl-2 rounded-2xl hover:bg-foreground/5 transition-all group border border-transparent hover:border-border"
                            >
                                <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-black text-sm shadow-lg shadow-primary/10 transition-all group-hover:bg-primary/90">
                                    {initials}
                                </div>
                                <div className="hidden lg:block text-left mr-1">
                                    <p className="text-sm font-semibold leading-none text-foreground">{user?.email?.split('@')[0] || 'User'}</p>
                                    <p className="text-[10px] text-muted-foreground font-bold mt-1 uppercase tracking-wider">USER</p>
                                </div>
                                <ChevronDown size={14} className={`text-muted-foreground transition-transform duration-300 ${isProfileOpen ? 'rotate-180' : ''}`} />
                            </button>

                            <AnimatePresence>
                                {isProfileOpen && (
                                    <>
                                        <div
                                            className="fixed inset-0 z-[60]"
                                            onClick={() => setIsProfileOpen(false)}
                                        />
                                        <motion.div
                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                            className="absolute right-0 mt-3 w-64 glass-card rounded-2xl border border-border p-2 shadow-2xl z-[70] overflow-hidden"
                                        >
                                            <div className="p-4 border-b border-border mb-2">
                                                <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">Authenticated Account</p>
                                                <p className="text-sm font-medium truncate text-foreground">{user?.email}</p>
                                            </div>

                                            <div className="space-y-1">
                                                <button
                                                    onClick={() => navigate('/dashboard')}
                                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-foreground/5 transition-colors text-sm font-medium text-foreground"
                                                >
                                                    <BarChart3 size={18} className="text-muted-foreground" />
                                                    Go to Dashboard
                                                </button>
                                                <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-foreground/5 transition-colors text-sm font-medium text-foreground">
                                                    <User size={18} className="text-muted-foreground" />
                                                    View Profile
                                                </button>
                                                <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-foreground/5 transition-colors text-sm font-medium text-foreground">
                                                    <Settings size={18} className="text-muted-foreground" />
                                                    Account Settings
                                                </button>
                                                <button
                                                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-foreground/5 transition-colors text-sm font-medium text-destructive active:scale-95"
                                                    onClick={logout}
                                                >
                                                    <LogOut size={18} />
                                                    Sign Out
                                                </button>
                                            </div>
                                        </motion.div>
                                    </>
                                )}
                            </AnimatePresence>
                        </div>
                    ) : (
                        /* Sign In / Get Started for Guests */
                        <>
                            <button
                                onClick={() => navigate('/login')}
                                className="text-sm font-bold text-muted-foreground hover:text-foreground transition-colors"
                            >
                                Sign In
                            </button>
                            <button
                                onClick={() => navigate('/register')}
                                className="h-11 px-6 rounded-2xl bg-primary text-primary-foreground font-extrabold shadow-lg shadow-primary/10 hover:opacity-90 active:scale-95 transition-all text-sm"
                            >
                                Get Started
                            </button>
                        </>
                    )}
                </div>
            </header>

            {/* Hero Section */}
            <main className="relative z-10 pt-28 pb-40 px-4">
                <div className="max-w-6xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-[0.2em] mb-10 mx-auto">
                            <Sparkles size={12} className="opacity-80" />
                            Next-Gen Intelligence Engine
                        </div>

                        <h1 className="text-5xl md:text-7xl lg:text-[5.5rem] font-black font-heading tracking-tighter mb-8 leading-[0.95] text-foreground transition-colors duration-500">
                            Generate <span className="text-transparent bg-clip-text bg-gradient-to-b from-foreground to-foreground/30">monolithic insights</span> <br />
                            of your Data in seconds.
                        </h1>

                        <p className="text-xl md:text-2xl text-muted-foreground mb-14 max-w-2xl mx-auto leading-relaxed font-medium transition-colors duration-500">
                            The ultimate analytical core. Our discovery engine
                            distills raw information into surgical intelligence instantly.
                        </p>

                        <div className="flex flex-wrap items-center justify-center gap-5">
                            <button
                                onClick={() => navigate(isAuthenticated ? '/dashboard' : '/register')}
                                className="h-16 px-10 rounded-2xl bg-primary text-primary-foreground text-lg font-black shadow-xl shadow-primary/10 hover:shadow-primary/20 hover:opacity-95 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-3"
                            >
                                {isAuthenticated ? 'Go to Dashboard' : 'Start for Free'}
                                <ArrowUpRight size={22} strokeWidth={3} />
                            </button>
                            <button className="h-16 px-10 rounded-2xl bg-foreground/5 border border-border text-foreground text-lg font-bold hover:bg-foreground/10 transition-all backdrop-blur-sm">
                                Watch Preview
                            </button>
                        </div>
                    </motion.div>

                    {/* Dashboard Preview / Feature Cards */}
                    <div className="mt-40 grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard
                            icon={Search}
                            title="Deep Discovery"
                            description="AI-driven scanning that uncovers hidden patterns and anomalies automatically."
                        />
                        <FeatureCard
                            icon={Activity}
                            title="Live Intelligence"
                            description="Real-time visualizations that transform dynamically as your data scale grows."
                        />
                        <FeatureCard
                            icon={Zap}
                            title="Neural Reports"
                            description="Generate executive-level summaries and briefings using advanced LLM models."
                        />
                    </div>
                </div>
            </main>

            {/* Footer */}
            <Footer />
        </div>
    );
};

const FeatureCard = ({ icon: Icon, title, description }) => (
    <div className="p-10 rounded-[2.5rem] glass border border-border hover:border-primary/20 hover:-translate-y-2 transition-all duration-500 group text-left">
        <div className="w-16 h-16 rounded-2xl bg-foreground/5 flex items-center justify-center text-foreground mb-8 group-hover:bg-primary group-hover:text-primary-foreground transition-all duration-500 shadow-inner">
            <Icon size={32} strokeWidth={1.5} />
        </div>
        <h3 className="text-2xl font-black font-heading mb-4 text-foreground">{title}</h3>
        <p className="text-muted-foreground leading-relaxed font-medium text-lg">{description}</p>
    </div>
);

export default Landing;
