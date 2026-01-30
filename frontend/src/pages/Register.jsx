import React, { useState } from 'react';
import { UserPlus, Mail, Lock, User, AlertCircle, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { GoogleLogin } from '@react-oauth/google';
import LightRays from '../components/backgrounds/LightRays';

const Register = ({ onToggle }) => {
    const { register, googleLogin } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await register(email, password, fullName);
            // Navigate to email verification page with email in state
            navigate('/verify-email', { state: { email } });
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse) => {
        setLoading(true);
        setError('');
        try {
            await googleLogin(credentialResponse.credential);
            navigate('/dashboard');
        } catch (err) {
            setError('Google authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleError = () => {
        setError('Google signup failed. Please try again.');
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-6 transition-colors duration-500 overflow-hidden relative">
            {/* Background Effect */}
            <div className="fixed inset-0 z-0 opacity-40">
                <LightRays
                    raysOrigin="top-center"
                    raysColor={theme === 'dark' ? "#f8fafc" : "#64748b"}
                    raysSpeed={0.2}
                    rayLength={3}
                />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-md glass-card rounded-[3rem] p-10 space-y-8 relative z-10 border border-border shadow-2xl"
            >
                <div className="text-center space-y-3">
                    <div className="w-16 h-16 bg-primary/10 border border-primary/20 rounded-2xl flex items-center justify-center text-primary mx-auto mb-6 shadow-xl shadow-primary/5">
                        <UserPlus size={32} />
                    </div>
                    <h1 className="text-4xl font-black font-heading tracking-tight text-foreground mb-2">Create Account</h1>
                    <p className="text-muted-foreground font-medium">Start your journey with AI-driven analytics</p>
                </div>

                {error && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm flex items-center gap-3"
                    >
                        <AlertCircle size={18} />
                        {error}
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                        <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">Full Name</label>
                        <div className="relative group">
                            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="text"
                                required
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full h-14 bg-foreground/5 border border-border rounded-2xl pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground placeholder-muted-foreground/50"
                                placeholder="John Doe"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">Email Address</label>
                        <div className="relative group">
                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full h-14 bg-foreground/5 border border-border rounded-2xl pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground placeholder-muted-foreground/50"
                                placeholder="name@company.com"
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">Password</label>
                        <div className="relative group">
                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full h-14 bg-foreground/5 border border-border rounded-2xl pl-12 pr-12 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground placeholder-muted-foreground/50"
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                            >
                                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full h-16 bg-primary text-primary-foreground font-black rounded-2xl shadow-lg shadow-primary/10 hover:shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group disabled:opacity-50"
                    >
                        {loading ? 'Creating Account...' : 'Get Started'}
                        {!loading && <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                    </button>
                </form>

                <div className="relative flex items-center gap-4 py-2">
                    <div className="flex-1 h-px bg-border" />
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Or continue with</span>
                    <div className="flex-1 h-px bg-border" />
                </div>

                <div className="flex justify-center">
                    <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={handleGoogleError}
                        theme={theme === 'dark' ? 'filled_black' : 'outline'}
                        shape="pill"
                        size="large"
                        width="100%"
                        text="signup_with"
                    />
                </div>

                <div className="text-center pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground font-medium">
                        Already have an account? {' '}
                        <button
                            onClick={onToggle}
                            className="text-primary font-black hover:underline underline-offset-4"
                        >
                            Sign In
                        </button>
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Register;
