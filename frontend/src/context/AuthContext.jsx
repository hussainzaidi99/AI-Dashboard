import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { creditsApi } from '../api/credits';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
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
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);

        try {
            const response = await axios.post(`${import.meta.env.VITE_API_URL}/auth/login`, formData);
            const newToken = response.data.access_token;
            setToken(newToken);
            sessionStorage.setItem('token', newToken);
            setUser(response.data.user);
            sessionStorage.setItem('user', JSON.stringify(response.data.user));
            // Credits will be fetched by the useEffect
            return true;
        } catch (err) {
            console.error('Login error:', err);
            throw err;
        }
    };

    const googleLogin = async (googleToken) => {
        try {
            const response = await axios.post(`${import.meta.env.VITE_API_URL}/auth/google`, {
                token: googleToken
            });
            const newToken = response.data.access_token;
            setToken(newToken);
            sessionStorage.setItem('token', newToken);

            setUser(response.data.user);
            sessionStorage.setItem('user', JSON.stringify(response.data.user));
            // Credits will be fetched by the useEffect
            return true;
        } catch (err) {
            console.error('Google login error:', err);
            throw err;
        }
    };

    const register = async (email, password, fullName) => {
        try {
            await axios.post(`${import.meta.env.VITE_API_URL}/auth/register`, {
                email,
                password,
                full_name: fullName,
                role: 'user'
            });
            return await login(email, password);
        } catch (err) {
            console.error('Registration error:', err);
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
            isAuthenticated: !!token
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
