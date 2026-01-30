import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2, ArrowRight, Zap } from 'lucide-react';
import { paymentsApi } from '../api/payments';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import LightRays from '../components/backgrounds/LightRays';

const PaymentStatus = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { refreshCredits, activeBalance } = useAuth();
    const { theme } = useTheme();
    const sessionId = searchParams.get('session_id');
    const [status, setStatus] = useState('loading'); // loading, success, error
    const [details, setDetails] = useState(null);
    const hasCalledConfirm = React.useRef(false);

    useEffect(() => {
        const confirmPayment = async () => {
            if (!sessionId) {
                setStatus('error');
                return;
            }

            // Prevent double calls in StrictMode or during re-renders
            if (hasCalledConfirm.current) return;
            hasCalledConfirm.current = true;

            try {
                const data = await paymentsApi.confirmPayment(sessionId);
                if (data.success) {
                    // Refresh the global credits state AND wait for it to complete
                    await refreshCredits();
                    setDetails(data);
                    setStatus('success');
                } else {
                    setStatus('error');
                }
            } catch (error) {
                console.error('Payment confirmation error:', error);
                setStatus('error');
            }
        };

        confirmPayment();
    }, [sessionId, refreshCredits]);

    if (status === 'loading') {
        return (
            <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-8 transition-colors duration-500 relative overflow-hidden">
                <div className="fixed inset-0 z-0 opacity-30">
                    <LightRays raysOrigin="center" raysColor={theme === 'dark' ? "#f8fafc" : "#64748b"} raysSpeed={0.3} />
                </div>
                <div className="relative z-10 flex flex-col items-center">
                    <Loader2 className="w-16 h-16 text-primary animate-spin mb-6" />
                    <h2 className="text-3xl font-black font-heading tracking-tight">Verifying your payment...</h2>
                    <p className="text-muted-foreground mt-2 font-medium">Please don't close this window.</p>
                </div>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-8 text-center transition-colors duration-500 relative overflow-hidden">
                <div className="fixed inset-0 z-0 opacity-40">
                    <LightRays raysOrigin="top-center" raysColor="#10b981" raysSpeed={0.2} rayLength={3} />
                </div>

                <div className="relative z-10 max-w-2xl w-full">
                    <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="w-24 h-24 bg-emerald-500/10 text-emerald-500 rounded-3xl flex items-center justify-center mb-10 mx-auto shadow-2xl shadow-emerald-500/10 border border-emerald-500/20"
                    >
                        <CheckCircle2 className="w-14 h-14" />
                    </motion.div>

                    <motion.h1
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-6xl font-black font-heading tracking-tight mb-6"
                    >
                        Payment Successful!
                    </motion.h1>

                    <motion.p
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.2 }}
                        className="text-xl text-muted-foreground max-w-lg mx-auto mb-12 font-medium"
                    >
                        Thank you for your purchase. <span className="text-foreground font-bold">{((details?.added_tokens || 0) / 70000).toFixed(2)} credits</span> have been added to your account.
                    </motion.p>

                    <motion.div
                        initial={{ y: 20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="glass-card border-emerald-500/20 bg-emerald-500/[0.03] p-8 rounded-[2.5rem] mb-14 flex items-center gap-6 text-left max-w-md mx-auto shadow-xl backdrop-blur-md"
                    >
                        <div className="bg-emerald-500/20 p-4 rounded-2xl shadow-inner">
                            <Zap className="w-8 h-8 text-emerald-500 fill-emerald-500" />
                        </div>
                        <div>
                            <div className="text-xs text-muted-foreground font-bold uppercase tracking-widest mb-1">New Credits Balance</div>
                            <div className="text-3xl font-black font-heading text-emerald-500">{((activeBalance || 0) / 70000).toFixed(2)} Credits</div>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.5 }}
                    >
                        <Link
                            to="/dashboard"
                            className="inline-flex items-center gap-3 bg-primary text-primary-foreground px-10 py-5 rounded-[2rem] font-black font-heading text-xl shadow-xl shadow-primary/20 hover:shadow-primary/30 hover:scale-[1.02] active:scale-95 transition-all"
                        >
                            <span>Go to Dashboard</span>
                            <ArrowRight className="w-6 h-6 stroke-[3]" />
                        </Link>
                    </motion.div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-8 text-center transition-colors duration-500 relative overflow-hidden">
            <div className="fixed inset-0 z-0 opacity-40">
                <LightRays raysOrigin="top-center" raysColor="#ef4444" raysSpeed={0.2} rayLength={2} />
            </div>

            <div className="relative z-10 max-w-2xl w-full">
                <div className="w-24 h-24 bg-destructive/10 text-destructive rounded-3xl flex items-center justify-center mb-10 mx-auto border border-destructive/20 shadow-2xl shadow-destructive/10">
                    <XCircle className="w-14 h-14" />
                </div>

                <h1 className="text-5xl md:text-6xl font-black font-heading tracking-tight mb-6 text-destructive">Verification Failed</h1>
                <p className="text-xl text-muted-foreground max-w-lg mx-auto mb-12 font-medium leading-relaxed">
                    We couldn't verify your payment. If your card was charged, please contact support with your session ID: <br />
                    <code className="bg-foreground/5 border border-border px-3 py-1.5 rounded-xl text-sm font-mono mt-4 inline-block text-foreground">{sessionId || 'N/A'}</code>
                </p>

                <Link
                    to="/pricing"
                    className="inline-flex items-center gap-3 bg-foreground/5 border border-border text-foreground px-10 py-5 rounded-[2rem] font-black font-heading text-xl hover:bg-foreground/10 active:scale-95 transition-all"
                >
                    Back to Pricing
                </Link>
            </div>
        </div>
    );
};

export default PaymentStatus;
