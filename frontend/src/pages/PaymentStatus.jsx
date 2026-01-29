import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2, ArrowRight, Zap } from 'lucide-react';
import { paymentsApi } from '../api/payments';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const PaymentStatus = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { refreshCredits } = useAuth();
    const sessionId = searchParams.get('session_id');
    const [status, setStatus] = useState('loading'); // loading, success, error
    const [details, setDetails] = useState(null);

    useEffect(() => {
        const confirmPayment = async () => {
            if (!sessionId) {
                setStatus('error');
                return;
            }

            try {
                const data = await paymentsApi.confirmPayment(sessionId);
                if (data.success) {
                    setStatus('success');
                    setDetails(data);
                    // Refresh the global credits state immediately
                    refreshCredits();
                } else {
                    setStatus('error');
                }
            } catch (error) {
                console.error('Payment confirmation error:', error);
                setStatus('error');
            }
        };

        confirmPayment();
    }, [sessionId]);

    if (status === 'loading') {
        return (
            <div className="min-h-[60vh] flex flex-col items-center justify-center p-8">
                <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
                <h2 className="text-2xl font-black font-heading tracking-tight">Verifying your payment...</h2>
                <p className="text-muted-foreground mt-2">Please don't close this window.</p>
            </div>
        );
    }

    if (status === 'success') {
        return (
            <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-center">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="w-20 h-20 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mb-8"
                >
                    <CheckCircle2 className="w-12 h-12" />
                </motion.div>

                <motion.h1
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="text-4xl md:text-5xl font-black font-heading tracking-tight mb-4"
                >
                    Payment Successful!
                </motion.h1>

                <motion.p
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="text-lg text-muted-foreground max-w-md mx-auto mb-10"
                >
                    Thank you for your purchase. {((details?.added_tokens || 0) / 70000).toFixed(2)} credits have been added to your account.
                </motion.p>

                <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="glass-card border-green-500/20 bg-green-500/[0.02] p-6 rounded-2xl mb-12 flex items-center gap-4 text-left"
                >
                    <div className="bg-green-500/20 p-2 rounded-lg">
                        <Zap className="w-6 h-6 text-green-500 fill-green-500" />
                    </div>
                    <div>
                        <div className="text-xs text-muted-foreground font-bold uppercase tracking-wider">New Balance</div>
                        <div className="text-2xl font-black font-heading">{((details?.new_balance || 0) / 70000).toFixed(2)} Credits</div>
                    </div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                >
                    <Link
                        to="/dashboard"
                        className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-8 py-4 rounded-2xl font-black font-heading text-lg hover:scale-105 transition-transform"
                    >
                        <span>Go to Dashboard</span>
                        <ArrowRight className="w-5 h-5" />
                    </Link>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="min-h-[70vh] flex flex-col items-center justify-center p-8 text-center">
            <div className="w-20 h-20 bg-destructive/10 text-destructive rounded-full flex items-center justify-center mb-8">
                <XCircle className="w-12 h-12" />
            </div>

            <h1 className="text-4xl font-black font-heading tracking-tight mb-4 text-destructive">Verification Failed</h1>
            <p className="text-lg text-muted-foreground max-w-md mx-auto mb-10">
                We couldn't verify your payment. If your card was charged, please contact support with your session ID: <code className="bg-muted px-2 py-1 rounded text-sm">{sessionId || 'N/A'}</code>
            </p>

            <Link
                to="/pricing"
                className="inline-flex items-center gap-2 bg-secondary text-secondary-foreground px-8 py-4 rounded-2xl font-black font-heading text-lg hover:bg-accent transition-colors"
            >
                Back to Pricing
            </Link>
        </div>
    );
};

export default PaymentStatus;
