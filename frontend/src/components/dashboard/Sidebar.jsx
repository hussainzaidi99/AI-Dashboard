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
    ChevronRight,
    ChevronLeft,
    Menu
} from 'lucide-react';
import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const SidebarItem = ({ icon: Icon, label, to, isCollapsed }) => (
    <NavLink
        to={to}
        className={({ isActive }) => `
            w-full flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} px-4 py-3 rounded-xl transition-all duration-200 group
            ${isActive
                ? 'bg-primary text-primary-foreground font-bold shadow-lg shadow-primary/10'
                : 'text-muted-foreground hover:bg-foreground/5 hover:text-foreground shadow-none'
            }
        `}
    >
        <div className="flex items-center gap-3">
            <Icon size={isCollapsed ? 24 : 20} className="group-hover:text-foreground transition-colors" />
            {!isCollapsed && <span className="font-medium text-sm">{label}</span>}
        </div>
        {!isCollapsed && <ChevronRight size={16} className="opacity-0 group-hover:opacity-100 transition-opacity" />}
    </NavLink>
);

const Sidebar = ({ isCollapsed, setIsCollapsed }) => {
    const { logout } = useAuth();
    const menuItems = [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard, to: '/dashboard' },
        { id: 'upload', label: 'Data Upload', icon: Upload, to: '/upload' },
        { id: 'intelligence', label: 'AI Insights', icon: PieChart, to: '/intelligence' },
        { id: 'raw-data', label: 'Raw Data', icon: Database, to: '/data' },
        { id: 'pricing', label: 'Pricing', icon: MessageSquare, to: '/pricing' },
    ];

    const footerItems = [
        { id: 'settings', label: 'Settings', icon: Settings, to: '/settings' },
        { id: 'about', label: 'About', icon: Info, to: '/about' },
    ];

    return (
        <aside className={`${isCollapsed ? 'w-20' : 'w-64'} h-full flex flex-col bg-background/95 backdrop-blur-3xl border-r border-border z-20 transition-all duration-300 relative`}>
            {/* Toggle Button */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center shadow-lg hover:scale-110 transition-all z-30"
            >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            <div className={`p-6 ${isCollapsed ? 'px-4' : ''}`}>
                <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center mb-6' : 'mb-8'}`}>
                    <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20 shrink-0">
                        <BarChart3 className="text-primary-foreground" size={24} strokeWidth={2.5} />
                    </div>
                    {!isCollapsed && (
                        <h1 className="text-xl font-bold tracking-tight text-foreground truncate">
                            AI Analytics
                        </h1>
                    )}
                </div>

                <nav className="space-y-2">
                    {menuItems.map((item) => (
                        <SidebarItem
                            key={item.id}
                            icon={item.icon}
                            label={item.label}
                            to={item.to}
                            isCollapsed={isCollapsed}
                        />
                    ))}
                </nav>
            </div>

            <div className={`mt-auto p-6 ${isCollapsed ? 'px-4' : ''} space-y-2`}>
                <div className="h-px bg-border my-4" />
                {footerItems.map((item) => (
                    <SidebarItem
                        key={item.id}
                        icon={item.icon}
                        label={item.label}
                        to={item.to}
                        isCollapsed={isCollapsed}
                    />
                ))}

                <button
                    onClick={logout}
                    className={`w-full flex items-center ${isCollapsed ? 'justify-center' : 'gap-3 px-4'} py-3 rounded-xl text-red-400 hover:bg-red-400/10 transition-all duration-200 mt-4 group`}
                >
                    <LogOut size={20} className="group-hover:rotate-12 transition-transform" />
                    {!isCollapsed && <span className="font-medium text-sm">Logout Session</span>}
                </button>

                <div className="mt-8 p-4 rounded-2xl glass-card text-xs">
                    <div className="flex items-center gap-2 mb-2 text-foreground">
                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                        <span className="font-semibold uppercase tracking-wider">Premium Plan</span>
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                        Your subscription will renew based on the expiry date of your current plan.
                    </p>
                    <Link to="/pricing" className="mt-3 w-full py-2 bg-foreground/5 hover:bg-foreground/10 rounded-lg transition-colors font-medium flex items-center justify-center text-foreground">
                        Manage Credits
                    </Link>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
