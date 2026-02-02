import React from 'react';
import { motion } from 'framer-motion';
import {
    Settings as SettingsIcon,
    User,
    Bell,
    Shield,
    Palette,
    Zap,
    Key,
    Save
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Settings = () => {
    const { theme } = useTheme();

    const sections = [
        {
            title: "Account Settings",
            icon: User,
            fields: ["Display Name", "Email Address", "Profile Image"]
        },
        {
            title: "Appearance",
            icon: Palette,
            content: `Active Theme: ${theme.toUpperCase()}`,
            info: "Theme synchronization is managed via the global toggle in the navbar."
        },
        {
            title: "API & Security",
            icon: Key,
            fields: ["Master API Key", "Webhooks", "SSH Access"]
        },
        {
            title: "Notification Flow",
            icon: Bell,
            fields: ["Email Alerts", "Browser Push", "System Status"]
        }
    ];

    return (
        <div className="max-w-4xl mx-auto pb-20 space-y-8">
            <header className="flex items-center justify-between mb-12">
                <div>
                    <h1 className="text-4xl font-black text-foreground tracking-tighter">Control Center</h1>
                    <p className="text-muted-foreground font-medium mt-1">Configure your neural workspace environment.</p>
                </div>
                <div className="p-3 rounded-2xl bg-foreground/5 border border-border">
                    <SettingsIcon size={24} className="text-primary animate-spin-slow" />
                </div>
            </header>

            <div className="grid grid-cols-1 gap-6">
                {sections.map((section, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="glass-card rounded-3xl p-8 border border-border group hover:border-primary/20 transition-all duration-300"
                    >
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                                <section.icon size={20} />
                            </div>
                            <h3 className="text-lg font-bold text-foreground">{section.title}</h3>
                        </div>

                        {section.fields && (
                            <div className="space-y-4">
                                {section.fields.map((field, i) => (
                                    <div key={i} className="flex items-center justify-between p-4 rounded-2xl bg-foreground/[0.02] border border-border/50 group/item hover:bg-foreground/[0.04] transition-all">
                                        <span className="text-sm font-semibold text-muted-foreground group-hover/item:text-foreground transition-colors">{field}</span>
                                        <button className="text-[10px] font-black uppercase tracking-widest text-primary hover:underline">Edit</button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {section.content && (
                            <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20">
                                <p className="text-sm font-bold text-primary mb-1">{section.content}</p>
                                <p className="text-xs text-muted-foreground">{section.info}</p>
                            </div>
                        )}
                    </motion.div>
                ))}
            </div>

            <div className="flex justify-end pt-8">
                <button className="flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground rounded-2xl font-black text-sm uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl shadow-primary/20">
                    <Save size={18} />
                    Sync Configuration
                </button>
            </div>
        </div>
    );
};

export default Settings;
