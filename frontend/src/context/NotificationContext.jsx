import React, { createContext, useContext, useState, useCallback } from 'react';
import { toast as sonnerToast } from 'sonner';

const NotificationContext = createContext(null);

export const NotificationProvider = ({ children }) => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);

    const addNotification = useCallback((notification) => {
        const newNotification = {
            id: Date.now(),
            timestamp: new Date(),
            ...notification,
        };

        setNotifications(prev => {
            const updated = [newNotification, ...prev].slice(0, 5);
            return updated;
        });
        setUnreadCount(prev => prev + 1);
    }, []);

    const markAllAsRead = useCallback(() => {
        setUnreadCount(0);
    }, []);

    // Wrapper for sonner toast that also adds to history
    const toast = {
        success: (message, options) => {
            sonnerToast.success(message, options);
            addNotification({ type: 'success', title: message, description: options?.description });
        },
        error: (message, options) => {
            sonnerToast.error(message, options);
            addNotification({ type: 'error', title: message, description: options?.description });
        },
        info: (message, options) => {
            sonnerToast.info(message, options);
            addNotification({ type: 'info', title: message, description: options?.description });
        },
        warning: (message, options) => {
            sonnerToast.warning(message, options);
            addNotification({ type: 'warning', title: message, description: options?.description });
        }
    };

    return (
        <NotificationContext.Provider value={{
            notifications,
            setNotifications,
            unreadCount,
            addNotification,
            markAllAsRead,
            toast
        }}>
            {children}
        </NotificationContext.Provider>
    );
};

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};
