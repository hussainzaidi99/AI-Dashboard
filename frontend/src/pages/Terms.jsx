import React from 'react';
import { motion } from 'framer-motion';
import { FileText, CheckCircle, Scale, AlertCircle, Info } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

const Terms = () => {
    const { theme } = useTheme();

    return (
        <div className="max-w-4xl mx-auto pb-20 space-y-12">
            <header className={`relative py-16 px-8 rounded-[3rem] overflow-hidden transition-all duration-500 shadow-2xl ${theme === 'dark' ? 'bg-[#0a0a0a] border border-white/5' : 'bg-primary text-primary-foreground'
                }`}>
                <div className="relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-[10px] font-black uppercase tracking-widest mb-6"
                    >
                        <Scale size={12} />
                        Terms of Service
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-7xl font-black tracking-tighter mb-6"
                    >
                        Rules of the <br />
                        <span className="text-blue-300">Intelligence Core.</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className={`text-xl max-w-2xl font-medium ${theme === 'dark' ? 'text-muted-foreground' : 'text-primary-foreground/70'}`}
                    >
                        Please read these terms and conditions carefully before using our service.
                    </motion.p>
                </div>
            </header>

            <div className="space-y-8">
                <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                            <Info size={24} />
                        </div>
                        <h2 className="text-2xl font-black text-foreground">Agreement to Terms</h2>
                    </div>
                    <p className="text-muted-foreground leading-relaxed font-medium">
                        By accessing or using our platform, you agree to be bound by these Terms. If you disagree with any part of the terms then you may not access the service.
                    </p>
                </section>

                <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                            <CheckCircle size={24} />
                        </div>
                        <h2 className="text-2xl font-black text-foreground">User Content</h2>
                    </div>
                    <p className="text-muted-foreground leading-relaxed font-medium mb-4">
                        Our service allows you to post, link, store, share and otherwise make available certain information, text, graphics, videos, or other material. You are responsible for the content that you post to the service.
                    </p>
                    <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/20 text-xs font-medium text-blue-500/80 italic">
                        Note: AI processing results are for analytical purposes and should be verified for critical decisions.
                    </div>
                </section>

                <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                            <AlertCircle size={24} />
                        </div>
                        <h2 className="text-2xl font-black text-foreground">Termination</h2>
                    </div>
                    <p className="text-muted-foreground leading-relaxed font-medium">
                        We may terminate or suspend access to our service immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.
                    </p>
                </section>

                <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                            <FileText size={24} />
                        </div>
                        <h2 className="text-2xl font-black text-foreground">Changes</h2>
                    </div>
                    <p className="text-muted-foreground leading-relaxed font-medium">
                        We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material we will try to provide at least 30 days notice prior to any new terms taking effect.
                    </p>
                </section>
            </div>
        </div>
    );
};

export default Terms;
