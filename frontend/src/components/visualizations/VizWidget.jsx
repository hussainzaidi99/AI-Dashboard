import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2, Download, Info, X, ExternalLink } from 'lucide-react';
import PlotlyChart from './PlotlyChart';

const VizWidget = ({ config, title, description, loading, error }) => {
    const [isFullScreen, setIsFullScreen] = useState(false);

    // Body scroll lock and status logging
    useEffect(() => {
        if (isFullScreen) {
            document.body.style.overflow = 'hidden';
            console.log(`[VizWidget] Fullscreen active for: ${title}`);
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isFullScreen, title]);

    const toggleFullScreen = () => {
        setIsFullScreen(prev => !prev);
    };

    const plotlyLayout = useMemo(() => {
        if (!config || !config.layout) return {};
        const isIndicator = config.data?.[0]?.type === 'indicator';
        const hasAnnotations = config.layout?.annotations?.length > 0;

        return {
            ...config.layout,
            title: '',
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                family: "'Inter', system-ui, sans-serif",
                color: 'rgba(226, 232, 240, 0.8)',
                size: config.layout?.font?.size || (isIndicator ? 12 : 10)
            },
            margin: config.layout?.margin || (isIndicator || hasAnnotations
                ? { l: 20, r: 20, t: 80, b: 20 }
                : { l: 40, r: 20, t: 30, b: 40 }),
            showlegend: config.layout?.showlegend ?? (!isIndicator && !hasAnnotations),
            legend: {
                orientation: 'h',
                y: -0.15,
                x: 0.5,
                xanchor: 'center',
                bgcolor: 'transparent',
                font: { size: 9, color: 'rgba(148, 163, 184, 0.8)' }
            },
            hovermode: 'closest',
            hoverlabel: {
                bgcolor: '#0f172a',
                bordercolor: 'rgba(56, 189, 248, 0.2)',
                font: { color: '#f8fafc', size: 11 },
                namelength: -1
            }
        };
    }, [config]);

    const plotlyData = useMemo(() => {
        if (!config || !config.data) return [];
        return config.data.filter(Boolean).map(item => {
            if (item.type === 'bar' || item.type === 'histogram') {
                return { ...item, marker: { ...item.marker, cornerradius: 8 } };
            }
            return item;
        });
    }, [config]);

    const hasValidData = plotlyData.length > 0;

    // Custom Legend Component
    const CustomPieLegend = ({ data, isFull }) => {
        if (!data?.[0] || data[0].type !== 'pie') return null;
        const labels = data[0].labels || [];
        const values = data[0].values || [];
        const colors = data[0].marker?.colors || [];
        const total = values.reduce((a, b) => a + b, 0);

        return (
            <div className={`grid ${isFull ? 'grid-cols-2 md:grid-cols-4 gap-6 px-10 pb-10' : 'gap-3 px-6 pb-6'}`}>
                {labels.map((label, idx) => {
                    const percentage = total > 0 ? Math.round((values[idx] / total) * 100) : 0;
                    return (
                        <div key={idx} className="space-y-1 group/item">
                            <div className="flex items-center justify-between text-[10px] uppercase font-bold tracking-wider">
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[idx] || '#fff' }} />
                                    <span className="text-slate-400 group-hover/item:text-slate-200 transition-colors">{label}</span>
                                </div>
                                <span className="text-slate-500">{percentage}%</span>
                            </div>
                            <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${percentage}%` }}
                                    transition={{ duration: 0.8, delay: idx * 0.1 }}
                                    className="h-full rounded-full opacity-60"
                                    style={{ backgroundColor: colors[idx] || '#fff' }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="glass-card rounded-2xl flex flex-col h-full bg-[#0a0a0b]/80 border border-white/5 overflow-hidden group">
            {/* Header */}
            <div className="p-4 flex items-center justify-between border-b border-white/5 bg-white/[0.02]">
                <div>
                    <h3 className="text-sm font-bold text-white/90">{title}</h3>
                    {description && <p className="text-[10px] text-slate-500">{description}</p>}
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={toggleFullScreen} className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                        <Maximize2 size={16} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                        <Download size={16} />
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col relative min-h-[300px]">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                        <div className="w-6 h-6 border-2 border-slate-700 border-t-white rounded-full animate-spin" />
                    </div>
                ) : error ? (
                    <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-red-400/80 text-xs">
                        Failed to load visualization data
                    </div>
                ) : hasValidData ? (
                    <div className="flex-1 flex flex-col">
                        <div className="flex-1 min-h-[220px]">
                            <PlotlyChart key={`normal-${title}`} data={plotlyData} layout={plotlyLayout} isFullScreen={false} />
                        </div>
                        <CustomPieLegend data={plotlyData} isFull={false} />
                    </div>
                ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-[10px] uppercase font-bold tracking-widest">
                        Ready for Sync
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-white/5 bg-white/[0.01] flex items-center justify-between text-[9px] font-black tracking-widest text-slate-600 uppercase">
                <div className="flex items-center gap-2">
                    <div className="w-1 h-1 rounded-full bg-slate-500 shadow-[0_0_5px_rgba(255,255,255,0.2)]" />
                    <span>HDA CORE UNIT 4</span>
                </div>
                <span>v1.0.8</span>
            </div>

            {/* Portaled Fullscreen Overlay */}
            {typeof document !== 'undefined' && createPortal(
                <AnimatePresence>
                    {isFullScreen && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.98 }}
                            className="fixed inset-0 bg-[#020617] backdrop-blur-3xl overflow-hidden flex flex-col"
                            style={{ zIndex: 999999, position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }}
                        >
                            <div className="p-8 md:p-12 flex items-center justify-between">
                                <div>
                                    <h2 className="text-3xl font-black text-white tracking-tight underline decoration-blue-500/50 underline-offset-8">{title}</h2>
                                    <p className="text-slate-400 mt-3 text-sm font-medium">{description}</p>
                                </div>
                                <button
                                    onClick={toggleFullScreen}
                                    className="p-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all border border-white/10 group"
                                >
                                    <X size={24} className="group-hover:rotate-90 transition-transform duration-300" />
                                </button>
                            </div>

                            <div className="flex-1 mx-8 mb-8 md:mx-12 md:mb-12 rounded-[2.5rem] bg-slate-900/40 border border-white/5 shadow-2xl overflow-hidden flex flex-col">
                                <div className="flex-1">
                                    <PlotlyChart key={`full-${title}`} data={plotlyData} layout={plotlyLayout} isFullScreen={true} />
                                </div>
                                <CustomPieLegend data={plotlyData} isFull={true} />
                            </div>

                            <div className="px-8 pb-8 md:px-12 md:pb-12 flex items-center justify-between text-[11px] font-black tracking-[0.4em] text-white/10 uppercase">
                                <div className="flex items-center gap-4">
                                    <div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)] animate-pulse" />
                                    <span>High Dimensional Analytics Environment</span>
                                </div>
                                <span>Deployment Stable</span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>,
                document.body
            )}
        </div>
    );
};

export default VizWidget;
