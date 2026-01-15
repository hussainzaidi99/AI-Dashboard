import React from 'react';
import {
    LayoutDashboard,
    Upload,
    BarChart3,
    PieChart,
    Database,
    Settings,
    Info,
    MessageSquare,
    LogOut,
    ChevronRight
} from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const SidebarItem = ({ icon: Icon, label, to }) => (
    <NavLink
        to={to}
        className={({ isActive }) => `
            w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 group
            ${isActive
                ? 'bg-white text-black font-bold shadow-[0_0_15px_rgba(255,255,255,0.1)]'
                : 'text-muted-foreground hover:bg-white/5 hover:text-foreground shadow-none'
            }
        `}
    >
        <div className="flex items-center gap-3">
            <Icon size={20} className="group-hover:text-foreground transition-colors" />
            <span className="font-medium">{label}</span>
        </div>
        <ChevronRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity" />
    </NavLink>
);

const Sidebar = () => {
    const { logout } = useAuth();
    const menuItems = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard, to: '/dashboard' },
        { id: 'upload', label: 'Data Upload', icon: Upload, to: '/upload' },
        { id: 'analysis', label: 'Visual Analysis', icon: BarChart3, to: '/analysis' },
        { id: 'intelligence', label: 'AI Insights', icon: PieChart, to: '/intelligence' },
        { id: 'raw-data', label: 'Raw Data', icon: Database, to: '/data' },
    ];

    const footerItems = [
        { id: 'settings', label: 'Settings', icon: Settings, to: '/settings' },
        { id: 'about', label: 'About', icon: Info, to: '/about' },
    ];

    return (
        <aside className="w-64 h-full flex flex-col bg-background/50 backdrop-blur-xl border-r border-white/10 z-20">
            <div className="p-6">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                        <BarChart3 className="text-black" size={24} strokeWidth={2.5} />
                    </div>
                    <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                        AI Analytics
                    </h1>
                </div>

                <nav className="space-y-2">
                    {menuItems.map((item) => (
                        <SidebarItem
                            key={item.id}
                            icon={item.icon}
                            label={item.label}
                            to={item.to}
                        />
                    ))}
                </nav>
            </div>

            <div className="mt-auto p-6 space-y-2">
                <div className="h-px bg-white/10 my-4" />
                {footerItems.map((item) => (
                    <SidebarItem
                        key={item.id}
                        icon={item.icon}
                        label={item.label}
                        to={item.to}
                    />
                ))}

                <button
                    onClick={logout}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-destructive hover:bg-destructive/10 transition-all duration-200 mt-4 group"
                >
                    <LogOut size={20} className="group-hover:rotate-12 transition-transform" />
                    <span className="font-medium">Logout Session</span>
                </button>

                <div className="mt-8 p-4 rounded-2xl glass-card text-xs">
                    <div className="flex items-center gap-2 mb-2 text-white">
                        <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                        <span className="font-semibold uppercase tracking-wider">Premium Plan</span>
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                        Your subscription will renew on May 15.
                    </p>
                    <button className="mt-3 w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors font-medium">
                        Manage Subscription
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
