import React from 'react';
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
import { motion, AnimatePresence } from 'framer-motion';

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [isProfileOpen, setIsProfileOpen] = React.useState(false);

    const initials = user?.email?.substring(0, 2).toUpperCase() || 'AI';

    return (
        <header className="h-20 flex items-center justify-between px-8 bg-background/30 backdrop-blur-xl border-b border-white/10 z-30 sticky top-0">
            {/* Search Section */}
            <div className="flex items-center gap-8 flex-1">
                <div className="relative w-full max-w-md group">
                    <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search analytics, files, insights..."
                        className="w-full h-11 pl-10 pr-4 bg-white/5 border border-white/10 rounded-2xl focus:outline-none focus:ring-2 focus:ring-white/20 transition-all text-sm placeholder:text-muted-foreground"
                    />
                </div>

                {/* Navigation Links */}
                <nav className="hidden xl:flex items-center gap-6">
                    <Link to="/pricing" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Pricing</Link>
                    <Link to="/templates" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">Dashboard Templates</Link>
                </nav>
            </div>

            <div className="flex items-center gap-6">
                {/* Notifications & Date */}
                <div className="flex items-center gap-3">
                    <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm font-medium text-muted-foreground">
                        <Calendar size={16} />
                        <span>{new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                    </div>

                    <button className="p-3 rounded-2xl bg-white/5 border border-white/10 text-muted-foreground hover:bg-white/10 hover:text-foreground transition-all relative">
                        <Bell size={20} />
                        <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-white rounded-full border-2 border-background" />
                    </button>
                </div>

                <div className="h-8 w-px bg-white/10" />

                {/* Profile Section */}
                <div className="relative z-50">
                    <button
                        onClick={() => setIsProfileOpen(!isProfileOpen)}
                        className="flex items-center gap-3 p-1.5 pl-2 rounded-2xl hover:bg-white/5 transition-all group border border-transparent hover:border-white/10"
                    >
                        <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center text-black font-black text-sm shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all group-hover:bg-neutral-200">
                            {initials}
                        </div>
                        <div className="hidden lg:block text-left mr-1">
                            <p className="text-sm font-semibold leading-none text-white/80">{user?.email?.split('@')[0] || 'User'}</p>
                            <p className="text-[10px] text-zinc-500 font-bold mt-1 uppercase tracking-wider">{user?.role || 'Pro Plan'}</p>
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
                                    className="absolute right-0 mt-3 w-64 glass-card rounded-2xl border border-white/10 p-2 shadow-2xl z-[70] overflow-hidden"
                                >
                                    <div className="p-4 border-b border-white/5 mb-2">
                                        <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">Authenticated Account</p>
                                        <p className="text-sm font-medium truncate">{user?.email}</p>
                                    </div>

                                    <div className="space-y-1">
                                        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors text-sm font-medium">
                                            <User size={18} className="text-white/60" />
                                            View Profile
                                        </button>
                                        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors text-sm font-medium">
                                            <Settings size={18} className="text-muted-foreground" />
                                            Account Settings
                                        </button>
                                        <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 transition-colors text-sm font-medium text-destructive active:scale-95" onClick={logout}>
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
        </header>
    );
};

export default Navbar;
