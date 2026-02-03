import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Eye, FileText, Globe, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

import Footer from '../components/shared/Footer';

const Privacy = () => {
    const { theme } = useTheme();

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col p-6 transition-colors duration-500 overflow-x-hidden relative">
            <div className="flex-1 max-w-4xl mx-auto w-full pb-20 space-y-12">
                {/* Back to Home Link */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="pt-4"
                >
                    <Link
                        to="/"
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl glass-card border border-border hover:border-primary/50 text-sm font-bold text-muted-foreground hover:text-foreground transition-all group active:scale-95"
                    >
                        <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" />
                        Back to Home
                    </Link>
                </motion.div>

                <header className={`relative py-16 px-8 rounded-[3rem] overflow-hidden transition-all duration-500 shadow-2xl ${theme === 'dark' ? 'bg-[#0a0a0a] border border-white/5' : 'bg-primary text-primary-foreground'
                    }`}>
                    <div className="relative z-10">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-[10px] font-black uppercase tracking-widest mb-6"
                        >
                            <Shield size={12} />
                            Privacy Policy
                        </motion.div>
                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="text-5xl md:text-7xl font-black tracking-tighter mb-6"
                        >
                            Your Data. <br />
                            <span className="text-blue-300">Your Privacy.</span>
                        </motion.h1>
                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className={`text-xl max-w-2xl font-medium ${theme === 'dark' ? 'text-muted-foreground' : 'text-primary-foreground/70'}`}
                        >
                            We are committed to protecting your personal information and your right to privacy.
                        </motion.p>
                    </div>
                </header>

                <div className="space-y-8">
                    <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                <Eye size={24} />
                            </div>
                            <h2 className="text-2xl font-black text-foreground">Information We Collect</h2>
                        </div>
                        <p className="text-muted-foreground leading-relaxed font-medium mb-4">
                            We collect personal information that you provide to us such as name, address, contact information, passwords and security data, and payment information.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="p-4 rounded-2xl bg-foreground/5 border border-border text-sm font-semibold text-foreground/80">
                                Account Credentials
                            </div>
                            <div className="p-4 rounded-2xl bg-foreground/5 border border-border text-sm font-semibold text-foreground/80">
                                Usage Data & Analytics
                            </div>
                        </div>
                    </section>

                    <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                <Lock size={24} />
                            </div>
                            <h2 className="text-2xl font-black text-foreground">How We Use Your Information</h2>
                        </div>
                        <p className="text-muted-foreground leading-relaxed font-medium">
                            We use personal information collected via our Services for a variety of business purposes described below. We process your personal information for these purposes in reliance on our legitimate business interests, in order to enter into or perform a contract with you, with your consent, and/or for compliance with our legal obligations.
                        </p>
                    </section>

                    <section className="glass-card rounded-[2.5rem] p-10 border border-border">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
                                <Globe size={24} />
                            </div>
                            <h2 className="text-2xl font-black text-foreground">Data Security</h2>
                        </div>
                        <p className="text-muted-foreground leading-relaxed font-medium">
                            We have implemented appropriate technical and organizational security measures designed to protect the security of any personal information we process. However, please also remember that we cannot guarantee that the internet itself is 100% secure.
                        </p>
                    </section>
                </div>
            </div>
            <Footer />
        </div>
    );
};

export default Privacy;
