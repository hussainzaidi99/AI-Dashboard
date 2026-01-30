import React, { useState, useEffect } from 'react';
import { Lock, Mail, ArrowRight, ArrowLeft, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import LightRays from '../components/backgrounds/LightRays';

const ForgotPassword = () => {
    const { requestPasswordReset, verifyResetCode, confirmPasswordReset } = useAuth();
    const { theme } = useTheme();
    const navigate = useNavigate();

    const [step, setStep] = useState(1); // 1: Email, 2: Code, 3: New Password
    const [email, setEmail] = useState('');
    const [code, setCode] = useState(['', '', '', '', '', '']);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const [resendLoading, setResendLoading] = useState(false);
    const [resendCountdown, setResendCountdown] = useState(0);

    useEffect(() => {
        if (resendCountdown > 0) {
            const timer = setTimeout(() => setResendCountdown(resendCountdown - 1), 1000);
            return () => clearTimeout(timer);
        }
    }, [resendCountdown]);

    const handleSendCode = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            await requestPasswordReset(email);
            setSuccess('Reset code sent to your email!');
            setResendCountdown(60);
            setTimeout(() => {
                setStep(2);
                setSuccess('');
            }, 1500);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to send reset code. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleCodeChange = (index, value) => {
        if (value.length > 1) {
            value = value.slice(-1);
        }

        if (!/^\d*$/.test(value)) return;

        const newCode = [...code];
        newCode[index] = value;
        setCode(newCode);

        if (value && index < 5) {
            document.getElementById(`reset-code-${index + 1}`)?.focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === 'Backspace' && !code[index] && index > 0) {
            document.getElementById(`reset-code-${index - 1}`)?.focus();
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

        const nextEmptyIndex = newCode.findIndex(c => !c);
        if (nextEmptyIndex !== -1) {
            document.getElementById(`reset-code-${nextEmptyIndex}`)?.focus();
        } else {
            document.getElementById(`reset-code-5`)?.focus();
        }
    };

    const handleVerifyCode = async (e) => {
        e.preventDefault();
        setError('');

        const resetCode = code.join('');
        if (resetCode.length !== 6) {
            setError('Please enter all 6 digits');
            return;
        }

        setLoading(true);
        try {
            await verifyResetCode(email, resetCode);
            setSuccess('Code verified!');
            setTimeout(() => {
                setStep(3);
                setSuccess('');
            }, 1000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Invalid code. Please try again.');
            setCode(['', '', '', '', '', '']);
            document.getElementById('reset-code-0')?.focus();
        } finally {
            setLoading(false);
        }
    };

    const handleResetPassword = async (e) => {
        e.preventDefault();
        setError('');

        if (newPassword.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);
        try {
            await confirmPasswordReset(email, code.join(''), newPassword);
            setSuccess('Password reset successfully!');
            setTimeout(() => {
                navigate('/login');
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to reset password. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResend = async () => {
        setResendLoading(true);
        setError('');
        try {
            await requestPasswordReset(email);
            setResendCountdown(60);
            setSuccess('New code sent!');
            setTimeout(() => setSuccess(''), 2000);
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
                        <Lock size={32} />
                    </div>
                    <h1 className="text-4xl font-black font-heading tracking-tight text-foreground mb-2">
                        {step === 1 && 'Reset Password'}
                        {step === 2 && 'Enter Code'}
                        {step === 3 && 'New Password'}
                    </h1>
                    <p className="text-muted-foreground font-medium">
                        {step === 1 && 'Enter your email to receive a reset code'}
                        {step === 2 && `Code sent to ${email}`}
                        {step === 3 && 'Create a new password for your account'}
                    </p>
                </div>

                {/* Progress Indicator */}
                <div className="flex gap-2 justify-center">
                    {[1, 2, 3].map((s) => (
                        <div
                            key={s}
                            className={`h-1 flex-1 rounded-full transition-all ${s <= step ? 'bg-primary' : 'bg-border'
                                }`}
                        />
                    ))}
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
                        {success}
                    </motion.div>
                )}

                <AnimatePresence mode="wait">
                    {/* Step 1: Email Input */}
                    {step === 1 && (
                        <motion.form
                            key="step1"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            onSubmit={handleSendCode}
                            className="space-y-6"
                        >
                            <div className="space-y-2">
                                <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">
                                    Email Address
                                </label>
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

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full h-16 bg-primary text-primary-foreground font-black rounded-2xl shadow-lg shadow-primary/10 hover:shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group disabled:opacity-50"
                            >
                                {loading ? 'Sending...' : 'Send Reset Code'}
                                {!loading && <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                            </button>
                        </motion.form>
                    )}

                    {/* Step 2: Code Verification */}
                    {step === 2 && (
                        <motion.form
                            key="step2"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            onSubmit={handleVerifyCode}
                            className="space-y-6"
                        >
                            <div className="space-y-4">
                                <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">
                                    Reset Code
                                </label>
                                <div className="flex gap-2 justify-center">
                                    {code.map((digit, index) => (
                                        <input
                                            key={index}
                                            id={`reset-code-${index}`}
                                            type="text"
                                            inputMode="numeric"
                                            maxLength={1}
                                            value={digit}
                                            onChange={(e) => handleCodeChange(index, e.target.value)}
                                            onKeyDown={(e) => handleKeyDown(index, e)}
                                            onPaste={index === 0 ? handlePaste : undefined}
                                            className="w-12 h-14 bg-foreground/5 border-2 border-border rounded-xl text-center text-2xl font-bold focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all text-foreground"
                                            disabled={loading}
                                        />
                                    ))}
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading || code.join('').length !== 6}
                                className="w-full h-16 bg-primary text-primary-foreground font-black rounded-2xl shadow-lg shadow-primary/10 hover:shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group disabled:opacity-50"
                            >
                                {loading ? 'Verifying...' : 'Verify Code'}
                                {!loading && <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                            </button>

                            <div className="text-center">
                                <button
                                    type="button"
                                    onClick={handleResend}
                                    disabled={resendLoading || resendCountdown > 0}
                                    className="text-primary font-black hover:underline underline-offset-4 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 mx-auto text-sm"
                                >
                                    <RefreshCw size={14} className={resendLoading ? 'animate-spin' : ''} />
                                    {resendCountdown > 0
                                        ? `Resend in ${resendCountdown}s`
                                        : resendLoading
                                            ? 'Sending...'
                                            : 'Resend Code'
                                    }
                                </button>
                            </div>
                        </motion.form>
                    )}

                    {/* Step 3: New Password */}
                    {step === 3 && (
                        <motion.form
                            key="step3"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            onSubmit={handleResetPassword}
                            className="space-y-6"
                        >
                            <div className="space-y-2">
                                <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">
                                    New Password
                                </label>
                                <div className="relative group">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                                    <input
                                        type="password"
                                        required
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full h-14 bg-foreground/5 border border-border rounded-2xl pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground placeholder-muted-foreground/50"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground ml-1">
                                    Confirm Password
                                </label>
                                <div className="relative group">
                                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground group-focus-within:text-primary transition-colors" size={18} />
                                    <input
                                        type="password"
                                        required
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full h-14 bg-foreground/5 border border-border rounded-2xl pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all text-foreground placeholder-muted-foreground/50"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full h-16 bg-primary text-primary-foreground font-black rounded-2xl shadow-lg shadow-primary/10 hover:shadow-primary/20 hover:opacity-90 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group disabled:opacity-50"
                            >
                                {loading ? 'Resetting...' : 'Reset Password'}
                                {!loading && <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />}
                            </button>
                        </motion.form>
                    )}
                </AnimatePresence>

                {step > 1 && (
                    <div className="text-center pt-4 border-t border-border">
                        <button
                            onClick={() => setStep(step - 1)}
                            className="text-muted-foreground hover:text-foreground font-bold flex items-center gap-2 mx-auto transition-colors"
                        >
                            <ArrowLeft size={16} />
                            Back
                        </button>
                    </div>
                )}

                <div className="text-center pt-4 border-t border-border">
                    <p className="text-sm text-muted-foreground font-medium">
                        Remember your password? {' '}
                        <button
                            onClick={() => navigate('/login')}
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

export default ForgotPassword;
