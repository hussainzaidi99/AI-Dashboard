import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Shield, Zap, Info, Loader2 } from 'lucide-react';
import { paymentsApi } from '../api/payments';

const Pricing = () => {
    const [loading, setLoading] = useState(null);

    const handleSubscribe = async (planId) => {
        setLoading(planId);
        try {
            const data = await paymentsApi.createCheckoutSession(planId);
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (error) {
            console.error('Subscription error:', error);
            alert('Failed to initiate checkout. Please try again.');
        } finally {
            setLoading(null);
        }
    };

    const plans = [
        {
            id: 'basic',
            name: 'Basic Plan',
            price: '9.99',
            credits: '142.86',
            tokens: '10,000,000',
            description: 'Perfect for getting started. Valid for 1 month.',
            features: [
                '142.86 Credits',
                'Advanced Data Visualization',
                'Basic AI Analysis',
                'Email Support',
                'Priority Processing'
            ],
            color: 'from-blue-500/20 to-cyan-500/20',
            borderColor: 'border-blue-500/30'
        },
        {
            id: 'premium',
            name: 'Premium Plan',
            price: '19.99',
            credits: '285.71',
            tokens: '20,000,000',
            description: 'Best value for researchers. Valid for 3 months.',
            features: [
                '285.71 Credits',
                'Full AI Intelligence Suite',
                'Unlimited Visualization',
                '24/7 Priority Support',
                'Early Access to New Features',
                'Custom Templates'
            ],
            popular: true,
            color: 'from-purple-500/20 to-pink-500/20',
            borderColor: 'border-purple-500/30'
        }
    ];

    return (
        <div className="p-8 md:p-16 max-w-7xl mx-auto min-h-screen">
            <div className="text-center mb-16">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="inline-block px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-primary text-sm font-medium mb-4"
                >
                    Simple, Transparent Pricing
                </motion.div>
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="text-4xl md:text-6xl font-black font-heading mb-6 tracking-tight leading-tight"
                >
                    Choose the right plan <br />
                    <span className="text-muted-foreground">for your intelligence needs</span>
                </motion.h1>
                <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="text-lg text-muted-foreground max-w-2xl mx-auto"
                >
                    Boost your analytical capabilities with more tokens. One-time payment, lifetime account access.
                </motion.p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
                {plans.map((plan, index) => (
                    <motion.div
                        key={plan.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.1 * (index + 3) }}
                        className={`relative rounded-3xl p-8 glass-card flex flex-col h-full border ${plan.borderColor} ${plan.popular ? 'ring-2 ring-primary/20 bg-primary/[0.02]' : ''}`}
                    >
                        {plan.popular && (
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-bold px-4 py-1 rounded-full uppercase tracking-wider">
                                Most Popular
                            </div>
                        )}

                        <div className="mb-8">
                            <h3 className="text-2xl font-black font-heading mb-2">{plan.name}</h3>
                            <p className="text-muted-foreground text-sm min-h-[2.5rem]">{plan.description}</p>
                        </div>

                        <div className="mb-8">
                            <div className="flex items-baseline gap-1">
                                <span className="text-5xl font-black font-heading tracking-tighter">${plan.price}</span>
                                <span className="text-muted-foreground font-medium uppercase text-xs">one-time</span>
                            </div>
                            <div className="mt-4 flex items-center gap-2 text-primary font-bold bg-primary/10 w-fit px-3 py-1 rounded-lg">
                                <Zap className="w-4 h-4 fill-primary" />
                                <span>{plan.credits} Credits</span>
                            </div>
                        </div>

                        <div className="space-y-4 mb-10 flex-grow">
                            {plan.features.map((feature, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <div className="mt-1 bg-primary/10 rounded-full p-0.5">
                                        <Check className="w-3.5 h-3.5 text-primary" />
                                    </div>
                                    <span className="text-sm text-foreground/80">{feature}</span>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => handleSubscribe(plan.id)}
                            disabled={loading !== null}
                            className={`w-full py-4 rounded-2xl font-black font-heading text-lg transition-all duration-300 flex items-center justify-center gap-3
                                ${plan.popular
                                    ? 'bg-primary text-primary-foreground hover:scale-[1.02] hover:shadow-xl shadow-primary/20'
                                    : 'bg-secondary text-secondary-foreground hover:bg-accent border border-white/5 active:scale-95'
                                } cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {loading === plan.id ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Processing...</span>
                                </>
                            ) : (
                                <>
                                    <span>Get Started</span>
                                    {!plan.popular && <Zap className="w-4 h-4 fill-current" />}
                                </>
                            )}
                        </button>
                    </motion.div>
                ))}
            </div>

            <div className="mt-24 max-w-4xl mx-auto rounded-3xl p-10 glass-card border-white/5 bg-white/[0.01]">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                    <div className="flex flex-col items-center text-center">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-5 text-primary shadow-sm bg-gradient-to-br from-primary/20 to-transparent">
                            <Shield className="w-6 h-6" />
                        </div>
                        <h4 className="font-bold mb-2">Secure Payments</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Payments are securely processed by Stripe. We never store your card details.</p>
                    </div>
                    <div className="flex flex-col items-center text-center">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-5 text-primary shadow-sm bg-gradient-to-br from-primary/20 to-transparent">
                            <Zap className="w-6 h-6" />
                        </div>
                        <h4 className="font-bold mb-2">Instant Delivery</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Tokens are added to your account instantly after successful payment confirmation.</p>
                    </div>
                    <div className="flex flex-col items-center text-center">
                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center mb-5 text-primary shadow-sm bg-gradient-to-br from-primary/20 to-transparent">
                            <Info className="w-6 h-6" />
                        </div>
                        <h4 className="font-bold mb-2">Expiry</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Paid credits will expire after the given time. For extended use, you can purchase premium plan which last upto 3 Months.</p>
                    </div>
                </div>
            </div>

            <div className="mt-16 text-center text-sm text-muted-foreground flex flex-col gap-2">
                <p>Have questions? Reach out to our support team</p>
                <a href="mailto:contact@sabasoftgames.com" className="text-primary hover:underline font-bold">contact@sabasoftgames.com</a>
            </div>
        </div>
    );
};

export default Pricing;
