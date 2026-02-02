import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    Search as SearchIcon,
    Bell,
    Calendar,
    ChevronDown,
    User,
    Settings,
    LogOut,
    CreditCard,
    Layout as LayoutIcon
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { motion, AnimatePresence } from 'framer-motion';
import ThemeToggle from '../shared/ThemeToggle';

const Navbar = () => {
    const { user, logout, activeBalance } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [isProfileOpen, setIsProfileOpen] = useState(false);

    const initials = user?.email?.substring(0, 2).toUpperCase() || 'AI';

    // Calculate display credits (1 Credit = 70,000 tokens)
    const credits = (activeBalance || 0) / 70000;

    // Color Logic
    let creditColor = "text-emerald-400"; // Good
    if (credits < 10) creditColor = "text-yellow-400"; // Warning
    if (credits < 2) creditColor = "text-red-500"; // Critical

    return (
        <header className="h-20 flex items-center justify-between px-8 bg-background/80 backdrop-blur-xl border-b border-border z-30 sticky top-0 transition-all duration-500">
            {/* Search Section */}
            <div className="flex items-center gap-8 flex-1">
                <div className="relative w-full max-w-md group">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search analytics, files, insights..."
                        className="w-full h-11 pl-10 pr-4 bg-foreground/5 border border-border rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all text-sm placeholder:text-muted-foreground text-foreground"
                    />
                </div>

                {/* Navigation Links */}
                <nav className="hidden xl:flex items-center gap-6">
                </nav>
            </div>

            <div className="flex items-center gap-6">

                {/* Credits Badge */}
                <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl bg-foreground/5 border border-border backdrop-blur-md shadow-inner">
                    <div className={`w-2 h-2 rounded-full ${credits > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className={`text-sm font-bold font-mono ${creditColor}`}>{credits.toFixed(2)}</span>
                    <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider ml-1">Credits</span>
                </div>

                {/* Theme Toggle & Notifications & Date */}
                <div className="flex items-center gap-3">
                    <ThemeToggle className="p-3 bg-foreground/5 border border-border" />

                    <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl bg-foreground/5 border border-border text-sm font-medium text-muted-foreground">
                        <Calendar size={16} />
                        <span>{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>

                        <button className="p-3 rounded-2xl bg-foreground/5 border border-border text-muted-foreground hover:bg-foreground/10 hover:text-foreground transition-all relative">
                            <Bell size={20} />
                            <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-primary rounded-full border-2 border-background" />
                        </button>
                    </div>

                    <div className="h-8 w-px bg-border" />

                    {/* Profile Section */}
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
                                <p className="text-[10px] text-muted-foreground font-bold mt-1 uppercase tracking-wider">{user?.role || 'Pro Plan'}</p>
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
                                                onClick={() => {
                                                    logout();
                                                    navigate('/');
                                                }}
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
                </div>
            </div>
        </header>
    );
};

export default Navbar;
