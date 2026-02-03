import React from 'react';
import { Link } from 'react-router-dom';
import { BarChart3 } from 'lucide-react';

const Footer = () => {
    return (
        <footer className="relative z-10 py-8 border-t border-border bg-background transition-colors duration-500">
            <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-10">
                <div className="flex items-center gap-3 opacity-40">
                    <BarChart3 size={20} className="text-foreground" />
                    <span className="font-heading font-bold text-base tracking-tight text-foreground">AI Analytics</span>
                </div>
                <p className="text-sm text-muted-foreground font-medium">© 2026 SabasSoft Games. All rights reserved.</p>
                <div className="flex gap-10 text-sm font-semibold text-muted-foreground">
                    <Link to="/privacy" className="hover:text-foreground transition-colors">Privacy</Link>
                    <Link to="/terms" className="hover:text-foreground transition-colors">Terms</Link>
                    <Link to="/docs" className="hover:text-foreground transition-colors">Docs</Link>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
