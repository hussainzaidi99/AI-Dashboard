import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useNotifications } from './NotificationContext';
import { creditsApi } from '../api/credits';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const { toast } = useNotifications();
    const [user, setUser] = useState(null);
    const [token, setToken] = useState(sessionStorage.getItem('token'));
    const [loading, setLoading] = useState(true);
    const [activeBalance, setActiveBalance] = useState(0);

    const refreshCredits = async () => {
        if (!token) return 0;
        try {
            const data = await creditsApi.getCredits();
            // The backend returns 'active_tokens'
            const balance = data.active_tokens || 0;
            setActiveBalance(balance);
            return balance;
        } catch (err) {
            console.error('Failed to refresh credits:', err);
            return activeBalance;
        }
    };

    useEffect(() => {
        const initAuth = async () => {
            if (token) {
                try {
                    const savedUser = sessionStorage.getItem('user');
                    if (savedUser) {
                        setUser(JSON.parse(savedUser));
                        // Fetch initial credits
                        refreshCredits();
                    } else {
                        setUser({ email: 'user@example.com', role: 'user' });
                    }
                } catch (err) {
                    console.error('Auth init failed:', err);
                    logout();
                }
            }
            setLoading(false);
        };
        initAuth();
    }, [token]);

    const login = async (email, password) => {
        try {
            const data = await authApi.login(email, password);
            const newToken = data.access_token;
            setToken(newToken);
            sessionStorage.setItem('token', newToken);
            setUser(data.user);
            sessionStorage.setItem('user', JSON.stringify(data.user));

            toast.success('Welcome back!', {
                description: `Successfully signed in as ${data.user.full_name || email}`
            });
            return true;
        } catch (err) {
            toast.error('Login Failed', {
                description: err.friendlyMessage || 'Invalid email or password'
            });
            throw err;
        }
    };

    const googleLogin = async (googleToken) => {
        try {
            const data = await authApi.googleLogin(googleToken);
            const newToken = data.access_token;
            setToken(newToken);
            sessionStorage.setItem('token', newToken);

            setUser(data.user);
            sessionStorage.setItem('user', JSON.stringify(data.user));

            toast.success('Welcome back!', {
                description: 'Successfully signed in with Google'
            });
            return true;
        } catch (err) {
            toast.error('Google Sign-In Failed', {
                description: err.friendlyMessage || 'Could not authenticate with Google'
            });
            throw err;
        }
    };

    const register = async (email, password, fullName) => {
        try {
            await authApi.register(email, password, fullName);
            toast.success('Account Created', {
                description: 'Please check your email to verify your account.'
            });
            return true;
        } catch (err) {
            toast.error('Registration Failed', {
                description: err.friendlyMessage || 'Could not create account'
            });
            throw err;
        }
    };

    const verifyEmail = async (email, code) => {
        try {
            const data = await authApi.verifyEmail(email, code);
            const newToken = data.access_token;
            setToken(newToken);
            sessionStorage.setItem('token', newToken);
            setUser(data.user);
            sessionStorage.setItem('user', JSON.stringify(data.user));

            toast.success('Email Verified', {
                description: 'Your account is now ready to use.'
            });
            return true;
        } catch (err) {
            toast.error('Verification Failed', {
                description: err.friendlyMessage || 'Invalid or expired code'
            });
            throw err;
        }
    };

    const resendVerification = async (email) => {
        try {
            await authApi.resendVerification(email);
            toast.success('Verification Sent', {
                description: 'A new code has been sent to your email.'
            });
            return true;
        } catch (err) {
            toast.error('Email Failed', {
                description: err.friendlyMessage || 'Could not resend code'
            });
            throw err;
        }
    };

    const requestPasswordReset = async (email) => {
        try {
            await authApi.requestPasswordReset(email);
            toast.success('Reset Code Sent', {
                description: 'Check your email for instructions.'
            });
            return true;
        } catch (err) {
            toast.error('Reset Failed', {
                description: err.friendlyMessage || 'Could not send reset code'
            });
            throw err;
        }
    };

    const verifyResetCode = async (email, code) => {
        try {
            await authApi.verifyResetCode(email, code);
            toast.success('Code Verified', {
                description: 'You can now set a new password.'
            });
            return true;
        } catch (err) {
            toast.error('Invalid Code', {
                description: err.friendlyMessage || 'The reset code is incorrect'
            });
            throw err;
        }
    };

    const confirmPasswordReset = async (email, code, newPassword) => {
        try {
            await authApi.confirmPasswordReset(email, code, newPassword);
            toast.success('Password Updated', {
                description: 'Your password has been reset successfully.'
            });
            return true;
        } catch (err) {
            toast.error('Update Failed', {
                description: err.friendlyMessage || 'Could not update password'
            });
            throw err;
        }
    };

    const logout = () => {
        setToken(null);
        setUser(null);
        setActiveBalance(0);
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
        toast.info('Signed out', {
            description: 'You have been successfully logged out.'
        });
    };

    return (
        <AuthContext.Provider value={{
            user,
            token,
            loading,
            activeBalance,
            refreshCredits,
            login,
            googleLogin,
            logout,
            register,
            verifyEmail,
            resendVerification,
            requestPasswordReset,
            verifyResetCode,
            confirmPasswordReset,
            isAuthenticated: !!token
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
