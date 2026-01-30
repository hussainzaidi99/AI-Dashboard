import React, { useState, useEffect } from 'react';
import { Mail, ArrowRight, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import LightRays from '../components/backgrounds/LightRays';

const EmailVerification = () => {
    const { verifyEmail, resendVerification } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();
    const location = useLocation();
    const email = location.state?.email || '';

    const [code, setCode] = useState(['', '', '', '', '', '']);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);
    const [resendLoading, setResendLoading] = useState(false);
    const [resendCountdown, setResendCountdown] = useState(0);

    useEffect(() => {
        if (!email) {
            navigate('/login');
        }
    }, [email, navigate]);

    useEffect(() => {
        if (resendCountdown > 0) {
            const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCountdown]);

    const handleCodeChange = (index, value) => {
        if (value.length > 1) {
            value = value.slice(-1);
        }

        if (!/^\d*$/.test(value)) return;

        const newCode = [...code];
        newCode[index] = value;
        setCode(newCode);

        // Auto-focus next input
        if (value && index < 5) {
            document.getElementById(`code-${index + 1}`)?.focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !code[index] && index > 0) {
            document.getElementById(`code-${index - 1}`)?.focus();
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
        const newCode = [...code];

        for (let i = 0; i < pastedData.length; i++) {
            newCode[i] = pastedData[i];
        }

        setCode(newCode);

        // Focus the next empty input or the last one
        const nextEmptyIndex = newCode.findIndex(c => !c);
        if (nextEmptyIndex !== -1) {
            document.getElementById(`code-${nextEmptyIndex}`)?.focus();
        } else {
            document.getElementById(`code-5`)?.focus();
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        const verificationCode = code.join('');
        if (verificationCode.length !== 6) {
            setError('Please enter all 6 digits');
            return;
        }

        setLoading(true);
        try {
            await verifyEmail(email, verificationCode);
            setSuccess(true);
            setTimeout(() => {
                navigate('/dashboard');
            }, 1500);
        } catch (err) {
            setError(err.response?.data?.detail || 'Invalid verification code. Please try again.');
            setCode(['', '', '', '', '', '']);
            document.getElementById('code-0')?.focus();
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        setResendLoading(true);
        setError('');
        try {
            await resendVerification(email);
            setResendCountdown(60);
        } catch (err) {
            setError('Failed to resend code. Please try again.');
        } finally {
            setResendLoading(false);
        }
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
                        <Mail size={32} />
                    </div>
                    <h1 className="text-4xl font-black font-heading tracking-tight text-foreground mb-2">Verify Your Email</h1>
                    <p className="text-muted-foreground font-medium">
                        We sent a 6-digit code to<br />
                        <span className="text-foreground font-bold">{email}</span>
                    </p>
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

                {success && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="p-4 rounded-2xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-3"
                    >
                        <CheckCircle size={18} />
                        Email verified! Redirecting to dashboard...
                    </motion.div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-4">
                        <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">
                            Verification Code
                        </label>
                        <div className="flex gap-2 justify-center">
                            {code.map((digit, index) => (
                                <input
                                    key={index}
                                    id={`code-${index}`}
                                    type="text"
                                    inputMode="numeric"
                                    maxLength={1}
                                    value={digit}
                                    onChange={(e) => handleCodeChange(index, e.target.value)}
                                    onKeyDown={(e) => handleKeyDown(index, e)}
                                    onPaste={index === 0 ? handlePaste : undefined}
                                    className="w-12 h-14 bg-foreground/5 border-2 border-border rounded-xl text-center text-2xl font-bold focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-foreground"
                                    disabled={loading || success}
                                />
                            ))}
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={loading || success || code.join('').length !== 6}
                        className="w-full h-16 bg-primary text-primary-foreground font-black rounded-2xl shadow-lg shadow-primary/10 hover:shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Verifying...' : success ? 'Verified!' : 'Verify Email'}
                        {!loading && !success && <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                    </button>
                </form>

                <div className="text-center pt-4 border-t border-border space-y-3">
                    <p className="text-sm text-muted-foreground font-medium">
                        Didn't receive the code?
                    </p>
                    <button
                        onClick={handleResend}
                        disabled={resendLoading || resendCountdown > 0}
                        className="text-primary font-black hover:underline underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto"
                    >
                        <RefreshCw size={16} className={resendLoading ? 'animate-spin' : ''} />
                        {resendCountdown > 0
                            ? `Resend in ${resendCountdown}s`
                            : resendLoading
                                ? 'Sending...'
                                : 'Resend Code'
                        }
                    </button>
                </div>
            </motion.div>
        </div>
    );
};

export default EmailVerification;
