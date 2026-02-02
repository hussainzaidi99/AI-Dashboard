import React from 'react';
import { motion } from 'framer-motion';
import {
    Info,
    Globe,
    Heart,
    Cpu,
    ShieldCheck,
    Code2,
    Github,
    Twitter
} from 'lucide-react';

const About = () => {
    return (
        <div className="max-w-4xl mx-auto pb-20 space-y-12 text-center">
            {/* Hero */}
            <header className="space-y-6 pt-12">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="w-20 h-20 bg-primary/10 rounded-[2rem] flex items-center justify-center text-primary mx-auto mb-8 shadow-inner"
                >
                    <Cpu size={40} strokeWidth={1.5} />
                </motion.div>
                <motion.h1
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    className="text-6xl font-black text-foreground tracking-tighter"
                >
                    AI Analytics <span className="text-primary"></span>
                </motion.h1>
                <motion.p
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-xl text-muted-foreground font-medium max-w-2xl mx-auto leading-relaxed"
                >
                    Empowering data-driven decisions through advanced neural synthesis and high-performance visualization.
                </motion.p>
            </header>

            {/* Mission Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { icon: ShieldCheck, title: "Precision", text: "Verified analytical accuracy" },
                    { icon: Code2, title: "Core", text: "Best Engineering practices for seamless user experience." },
                    { icon: Globe, title: "Scalable", text: "Designed for scalability and performance." }
                ].map((item, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + idx * 0.1 }}
                        className="glass-card rounded-3xl p-6 border border-border"
                    >
                        <item.icon className="mx-auto mb-4 text-primary/60" size={24} />
                        <h3 className="font-bold text-foreground mb-1">{item.title}</h3>
                        <p className="text-xs text-muted-foreground font-medium">{item.text}</p>
                    </motion.div>
                ))}
            </div>

            {/* Content Section */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="glass-card rounded-[3rem] p-12 text-left border border-border relative overflow-hidden"
            >
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Cpu size={200} />
                </div>

                <h2 className="text-2xl font-black text-foreground mb-6 flex items-center gap-3">
                    <Heart size={24} className="text-red-500 fill-red-500" />
                    Built for the Future
                </h2>
                <div className="space-y-4 text-muted-foreground font-medium">
                    <p>
                        Developed by SabasoftGames, our mission is to simplify the bridge between raw datasets and actionable business intelligence. We leverage state-of-the-art LLMs and visualization libraries to provide a premium monitoring experience.
                    </p>
                    <p>
                        This dashboard is part of our commitment to open-source excellence and high-dimensional analytics tooling.
                    </p>
                </div>
            </motion.div>

        </div>
    );
};

export default About;
