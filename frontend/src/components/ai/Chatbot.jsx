import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, RotateCcw, ChevronDown, User, Bot, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDataset } from '../../context/DatasetContext';
import { aiApi } from '../../api/ai';

const Chatbot = () => {
    const { activeFileId, activeSheetIndex, hasActiveDataset } = useDataset();
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([
        { id: 1, type: 'bot', text: 'Hello! I am AI Assistant from AI Analytics. How can I help you today?', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    ]);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!message.trim()) return;

        const userText = message;
        const newUserMsg = {
            id: Date.now(),
            type: 'user',
            text: userText,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, newUserMsg]);
        setMessage('');
        setLoading(true);

        try {
            let responseText = "";

            if (hasActiveDataset) {
                const response = await aiApi.askQuestion(activeFileId, userText, activeSheetIndex);
                responseText = response.answer;
            } else {
                responseText = "I'm ready to analyze your data, but you haven't uploaded a file yet! Go to 'Data Upload' and I'll help you break it down.";
            }

            const botMsg = {
                id: Date.now() + 1,
                type: 'bot',
                text: responseText,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            const botMsg = {
                id: Date.now() + 1,
                type: 'bot',
                text: "I'm having trouble connecting to my brain right now. Please check if the backend is running!",
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, botMsg]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-8 right-8 z-[100]">
            {/* Chat Toggle Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className={`w-14 h-14 rounded-full flex items-center justify-center shadow-[0_0_25px_rgba(59,130,246,0.5)] transition-all duration-300 ${isOpen ? 'bg-zinc-800 rotate-90' : 'bg-primary'
                    }`}
            >
                {isOpen ? <X className="text-white" size={28} /> : (
                    <div className="relative">
                        <MessageSquare className="text-white" size={28} />
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-primary" />
                    </div>
                )}
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="absolute bottom-20 right-0 w-[400px] h-[600px] glass-card rounded-[2rem] flex flex-col overflow-hidden shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-5 bg-white/5 border-b border-white/10 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-800 to-black flex items-center justify-center text-white shadow-lg overflow-hidden border border-white/10">
                                    <Sparkles size={20} />
                                </div>
                                <div>
                                    <h3 className="font-bold text-sm">Intelligence Assistant</h3>
                                    <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-medium uppercase tracking-widest">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                        Online
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <button className="p-2 hover:bg-white/10 rounded-lg text-muted-foreground transition-colors">
                                    <RotateCcw size={16} />
                                </button>
                                <button className="p-2 hover:bg-white/10 rounded-lg text-muted-foreground transition-colors" onClick={() => setIsOpen(false)}>
                                    <ChevronDown size={20} />
                                </button>
                            </div>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
                            {messages.map((msg) => (
                                <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`flex gap-3 max-w-[85%] ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                                        <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center ${msg.type === 'user' ? 'bg-primary text-white' : 'bg-white/10 text-primary'
                                            }`}>
                                            {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                                        </div>
                                        <div className="space-y-1">
                                            <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.type === 'user'
                                                ? 'bg-primary text-white rounded-tr-none'
                                                : 'bg-white/5 border border-white/10 rounded-tl-none'
                                                }`}>
                                                {msg.text}
                                            </div>
                                            <p className={`text-[10px] text-muted-foreground ${msg.type === 'user' ? 'text-right' : 'text-left'}`}>
                                                {msg.time}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="flex justify-start">
                                    <div className="flex gap-3 max-w-[85%]">
                                        <div className="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center bg-white/10 text-primary">
                                            <Bot size={16} />
                                        </div>
                                        <div className="bg-white/5 border border-white/10 px-4 py-3 rounded-2xl rounded-tl-none">
                                            <div className="flex gap-1">
                                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce" />
                                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce delay-75" />
                                                <span className="w-1.5 h-1.5 bg-primary/40 rounded-full animate-bounce delay-150" />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Footer / Input */}
                        <div className="p-5 bg-white/5 border-t border-white/10">
                            <form onSubmit={handleSend} className="relative group">
                                <input
                                    type="text"
                                    value={message}
                                    onChange={(e) => setMessage(e.target.value)}
                                    placeholder="Ask me anything..."
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-14 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all placeholder:text-muted-foreground"
                                />
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-primary">
                                    <Sparkles size={18} />
                                </div>
                                <button
                                    type="submit"
                                    disabled={!message.trim() || loading}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-primary text-white rounded-xl flex items-center justify-center hover:bg-blue-600 disabled:opacity-50 disabled:hover:bg-primary transition-all shadow-lg"
                                >
                                    <Send size={18} />
                                </button>
                            </form>
                            <div className="mt-4 text-center">
                                <p className="text-[10px] text-muted-foreground">
                                    Powered by <span className="font-bold text-foreground">AI Analytics Engine</span>
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Chatbot;
