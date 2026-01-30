import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2, Download, Info, X, ExternalLink } from 'lucide-react';
import PlotlyChart from './PlotlyChart';
import { useTheme } from '../../context/ThemeContext';

const VizWidget = ({ config, title, description, loading, error }) => {
    const { theme } = useTheme();
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
                color: theme === 'dark' ? 'rgba(226, 232, 240, 0.8)' : 'rgba(15, 23, 42, 0.8)',
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
                font: { size: 9, color: theme === 'dark' ? 'rgba(148, 163, 184, 0.8)' : 'rgba(71, 85, 105, 0.8)' }
            },
            hovermode: 'closest',
            hoverlabel: {
                bgcolor: theme === 'dark' ? '#0f172a' : '#ffffff',
                bordercolor: theme === 'dark' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(37, 99, 235, 0.2)',
                font: { color: theme === 'dark' ? '#f8fafc' : '#0f172a', size: 11 },
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
                                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: colors[idx] || (theme === 'dark' ? '#fff' : '#000') }} />
                                    <span className="text-muted-foreground group-hover/item:text-foreground transition-colors">{label}</span>
                                </div>
                                <span className="text-muted-foreground/60">{percentage}%</span>
                            </div>
                            <div className="h-1 w-full bg-foreground/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${percentage}%` }}
                                    transition={{ duration: 0.8, delay: idx * 0.1 }}
                                    className="h-full rounded-full opacity-60"
                                    style={{ backgroundColor: colors[idx] || (theme === 'dark' ? '#fff' : '#000') }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="glass-card rounded-2xl flex flex-col h-full bg-card border border-border overflow-hidden group transition-all duration-500">
            {/* Header */}
            <div className="p-4 flex items-center justify-between border-b border-border bg-foreground/[0.02]">
                <div>
                    <h3 className="text-sm font-bold text-foreground">{title}</h3>
                    {description && <p className="text-[10px] text-muted-foreground">{description}</p>}
                </div>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={toggleFullScreen} className="p-2 rounded-lg hover:bg-foreground/5 text-muted-foreground hover:text-foreground transition-colors">
                        <Maximize2 size={16} />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-foreground/5 text-muted-foreground hover:text-foreground transition-colors">
                        <Download size={16} />
                    </button>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col relative min-h-[300px]">
                {loading ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/20 backdrop-blur-sm">
                        <div className="w-6 h-6 border-2 border-border border-t-primary rounded-full animate-spin" />
                    </div>
                ) : error ? (
                    <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-destructive text-xs">
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
                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground/40 text-[10px] uppercase font-black tracking-widest">
                        Ready for Sync
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-border bg-foreground/[0.01] flex items-center justify-between text-[9px] font-black tracking-widest text-muted-foreground uppercase">
                <div className="flex items-center gap-2">
                    <div className="w-1 h-1 rounded-full bg-primary shadow-sm" />
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
                            className="fixed inset-0 bg-background backdrop-blur-3xl overflow-hidden flex flex-col transition-colors duration-500"
                            style={{ zIndex: 999999, position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }}
                        >
                            <div className="p-8 md:p-12 flex items-center justify-between">
                                <div>
                                    <h2 className="text-3xl font-black text-foreground tracking-tight underline decoration-primary underline-offset-8">{title}</h2>
                                    <p className="text-muted-foreground mt-3 text-sm font-medium">{description}</p>
                                </div>
                                <button
                                    onClick={toggleFullScreen}
                                    className="p-4 rounded-2xl bg-foreground/5 hover:bg-foreground/10 text-muted-foreground hover:text-foreground transition-all border border-border group"
                                >
                                    <X size={24} className="group-hover:rotate-90 transition-transform duration-300" />
                                </button>
                            </div>

                            <div className="flex-1 mx-8 mb-8 md:mx-12 md:mb-12 rounded-[2.5rem] bg-card border border-border shadow-2xl overflow-hidden flex flex-col">
                                <div className="flex-1">
                                    <PlotlyChart key={`full-${title}`} data={plotlyData} layout={plotlyLayout} isFullScreen={true} />
                                </div>
                                <CustomPieLegend data={plotlyData} isFull={true} />
                            </div>

                            <div className="px-8 pb-8 md:px-12 md:pb-12 flex items-center justify-between text-[11px] font-black tracking-[0.4em] text-foreground/20 uppercase">
                                <div className="flex items-center gap-4">
                                    <div className="w-2 h-2 rounded-full bg-primary shadow-lg shadow-primary/20 animate-pulse" />
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
