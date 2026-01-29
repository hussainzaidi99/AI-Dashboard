import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, RotateCcw, ChevronDown, User, Bot, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { useDataset } from '../../context/DatasetContext';
import { useLocation } from 'react-router-dom';
import { aiApi } from '../../api/ai';
import { useAuth } from '../../context/AuthContext';

const Chatbot = () => {
    const { activeFileId, activeFileName, activeSheetIndex, hasActiveDataset } = useDataset();
    const { refreshCredits } = useAuth();
    const location = useLocation();
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState([]);

    // Initialize greeting based on context
    useEffect(() => {
        if (messages.length === 0) {
            let greeting = "Hello! I am your AI Intelligence Assistant. How can I help you navigate your data today?";

            if (!hasActiveDataset) {
                greeting = "Welcome! I'm your AI data assistant. Upload a dataset in the ingestion zone to get started.";
            } else if (location.pathname.includes('upload')) {
                greeting = `I'm following "${activeFileName}". Would you like to head to analysis or upload more data?`;
            } else if (location.pathname.includes('analysis')) {
                greeting = `Ready to analyze "${activeFileName}". What insights can I discover for you?`;
            } else if (activeFileName) {
                greeting = `Assisting with "${activeFileName}". How can I help with your analysis?`;
            }

            setMessages([
                {
                    id: 1,
                    type: 'bot',
                    text: greeting,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            ]);
        }
    }, [hasActiveDataset, activeFileName, location.pathname, messages.length]);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!message.trim() || loading) return;

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

        // Add a placeholder bot message for streaming
        const botMsgId = Date.now() + 1;
        const botMsgPlaceholder = {
            id: botMsgId,
            type: 'bot',
            text: '',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isStreaming: true
        };
        setMessages(prev => [...prev, botMsgPlaceholder]);

        try {
            if (!hasActiveDataset) {
                updateBotMessage(botMsgId, "I'm ready to analyze your data, but you haven't uploaded a file yet! Please visit the Ingestion Zone and I'll walk you through the process.");
                setLoading(false);
                return;
            }

            const token = sessionStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/ai/ask/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': token ? `Bearer ${token}` : ''
                },
                body: JSON.stringify({
                    file_id: activeFileId,
                    question: userText,
                    sheet_index: activeSheetIndex
                })
            });

            if (!response.ok) throw new Error('Failed to start stream');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (dataStr === '[DONE]') continue;

                        try {
                            const data = JSON.parse(dataStr);
                            if (data.token) {
                                accumulatedText += data.token;
                                updateBotMessage(botMsgId, accumulatedText);
                                if (loading) setLoading(false); // Stop bounce as soon as tokens arrive
                            } else if (data.error) {
                                updateBotMessage(botMsgId, `Error: ${data.error}`);
                            }
                        } catch (e) {
                            console.error("Error parsing stream chunk", e);
                        }
                    }
                }
            }

            // Mark stream as complete
            setMessages(prev => prev.map(m => m.id === botMsgId ? { ...m, isStreaming: false } : m));

            // Refresh global credits state after interaction
            refreshCredits();

        } catch (err) {
            console.error('Chat error:', err);
            updateBotMessage(botMsgId, "I'm having trouble connecting to my brain right now. Please check if the backend is running!");
        } finally {
            setLoading(false);
        }
    };

    const updateBotMessage = (id, text) => {
        setMessages(prev => prev.map(msg =>
            msg.id === id ? { ...msg, text } : msg
        ));
    };

    return (
        <div className="fixed bottom-8 right-8 z-[100]">
            {/* Chat Toggle Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(!isOpen)}
                className={`w-14 h-14 rounded-full flex items-center justify-center shadow-2xl transition-all duration-500 ${isOpen ? 'bg-white/10 rotate-90 scale-90' : 'bg-white text-black hover:scale-110 shadow-white/10'
                    }`}
            >
                {isOpen ? <X size={24} /> : (
                    <div className="relative">
                        <MessageSquare size={28} />
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
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
                                        <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center ${msg.type === 'user' ? 'bg-white text-black' : 'bg-white/10 text-white/70'
                                            }`}>
                                            {msg.type === 'user' ? <User size={16} /> : <Bot size={16} />}
                                        </div>
                                        <div className="space-y-1">
                                            <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.type === 'user'
                                                ? 'bg-white/10 border border-white/20 text-white rounded-tr-none'
                                                : 'bg-white/5 border border-white/10 text-white/90 rounded-tl-none font-medium'
                                                } ${msg.isStreaming ? 'animate-pulse border-white/20' : ''}`}>
                                                {msg.type === 'user' ? (
                                                    msg.text
                                                ) : (
                                                    <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-headings:mb-2 prose-headings:mt-4 first:prose-headings:mt-0">
                                                        <ReactMarkdown>{msg.text || (msg.isStreaming ? '...' : '')}</ReactMarkdown>
                                                    </div>
                                                )}
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
                                            <div className="flex gap-1.5 py-1">
                                                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" />
                                                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce delay-75" />
                                                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce delay-150" />
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
                                    className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-14 py-4 text-sm focus:outline-none focus:border-white/40 focus:bg-white/10 transition-all placeholder:text-muted-foreground"
                                />
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/50">
                                    <Sparkles size={18} />
                                </div>
                                <button
                                    type="submit"
                                    disabled={!message.trim() || loading}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 bg-white text-black rounded-xl flex items-center justify-center hover:bg-neutral-200 disabled:opacity-20 disabled:hover:bg-white transition-all shadow-xl"
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
