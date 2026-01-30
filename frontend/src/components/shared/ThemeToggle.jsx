import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../context/ThemeContext';

const ThemeToggle = ({ className = "" }) => {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className={`relative p-2 rounded-xl transition-all duration-300 group ${theme === 'dark'
                ? 'bg-white/5 hover:bg-white/10 text-yellow-400'
                : 'bg-foreground/5 hover:bg-foreground/10 text-foreground shadow-sm'
                } ${className}`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
            <AnimatePresence mode="wait" initial={false}>
                <motion.div
                    key={theme}
                    initial={{ y: 20, opacity: 0, rotate: -90 }}
                    animate={{ y: 0, opacity: 1, rotate: 0 }}
                    exit={{ y: -20, opacity: 0, rotate: 90 }}
                    transition={{ duration: 0.2, ease: "easeInOut" }}
                >
                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </motion.div>
            </AnimatePresence>

            {/* Subtle glow effect */}
            <div className={`absolute inset-0 rounded-xl blur-md transition-opacity duration-300 -z-10 ${theme === 'dark'
                ? 'bg-yellow-400/20 opacity-0 group-hover:opacity-100'
                : 'bg-foreground/10 opacity-0 group-hover:opacity-100'
                }`} />
        </button>
    );
};

export default ThemeToggle;
