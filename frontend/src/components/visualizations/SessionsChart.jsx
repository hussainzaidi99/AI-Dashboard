import React, { useMemo, useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2, X, Terminal } from 'lucide-react';
import PlotlyChart from './PlotlyChart';
import { useTheme } from '../../context/ThemeContext';

const SessionsChart = ({ title, value, trend, chartData: inputChartData, loading }) => {
    const [isFullScreen, setIsFullScreen] = useState(false);
    const { theme } = useTheme();

    // Body scroll lock
    useEffect(() => {
        if (isFullScreen) {
            document.body.style.overflow = 'hidden';
            console.log('[SessionsChart] Fullscreen active');
        } else {
            document.body.style.overflow = '';
        }
        return () => {
            document.body.style.overflow = '';
        };
    }, [isFullScreen]);

    const toggleFullScreen = () => {
        setIsFullScreen(prev => !prev);
    };

    const processedData = useMemo(() => {
        if (!inputChartData || !inputChartData.data || inputChartData.data.length === 0) return null;

        const featureColors = theme === 'dark' ? [
            { color: '#ffffff', fill: 'rgba(255, 255, 255, 0.05)' },
            { color: '#3b82f6', fill: 'rgba(59, 130, 246, 0.1)' },
            { color: '#2563eb', fill: 'rgba(37, 99, 235, 0.2)' }
        ] : [
            { color: '#0f172a', fill: 'rgba(15, 23, 42, 0.05)' },
            { color: '#2563eb', fill: 'rgba(37, 99, 235, 0.1)' },
            { color: '#3b82f6', fill: 'rgba(59, 130, 246, 0.2)' }
        ];

        const validTraces = inputChartData.data.filter(d => (d.y || d.values) && d.name);
        if (validTraces.length === 0) return null;

        const labels = validTraces[0].x || validTraces[0].labels || [];

        const datasets = validTraces.slice(0, 3).map((trace, idx) => {
            const rawY = trace.y || trace.values || [];
            const cleanY = rawY.map(v => {
                const num = parseFloat(v);
                return isNaN(num) ? 0 : num;
            });
            return {
                name: trace.name,
                data: cleanY,
                color: featureColors[idx]?.color || (theme === 'dark' ? '#fff' : '#000'),
                fillColor: featureColors[idx]?.fill || (theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)')
            };
        });

        const xLabel = inputChartData.layout?.xaxis?.title?.text || 'Time';
        return { labels, datasets, xLabel };
    }, [inputChartData]);

    const plotlyConfig = useMemo(() => {
        if (!processedData) return null;
        const data = processedData.datasets.map(ds => ({
            x: processedData.labels,
            y: ds.data,
            type: 'scatter',
            mode: 'lines',
            name: ds.name,
            fill: 'tonexty',
            fillcolor: ds.fillColor,
            line: { color: ds.color, width: 2, shape: 'spline' },
            hoverinfo: 'name+y'
        }));

        const layout = {
            autosize: true,
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            margin: { l: 50, r: 20, t: 30, b: 40 },
            xaxis: {
                title: { text: processedData.xLabel, font: { color: theme === 'dark' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', size: 10 } },
                showgrid: false,
                tickfont: { color: theme === 'dark' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', size: 9 },
                automargin: true
            },
            yaxis: {
                showgrid: true,
                gridcolor: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
                tickfont: { color: theme === 'dark' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', size: 9 },
                automargin: true
            },
            showlegend: true,
            legend: { x: 0, y: 1.1, orientation: 'h', font: { color: theme === 'dark' ? 'rgba(255,255,255,0.4)' : 'rgba(0,0,0,0.4)', size: 9 }, bgcolor: 'transparent' },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor: theme === 'dark' ? '#0f172a' : '#ffffff',
                font: { color: theme === 'dark' ? '#fff' : '#000', size: 11 }
            }
        };

        return { data, layout };
    }, [processedData]);

    if (loading || !processedData) {
        return (
            <div className="glass-card rounded-[2rem] p-8 h-[400px] flex items-center justify-center border-dashed border-border transition-colors">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-2 border-primary/10 border-t-primary rounded-full animate-spin" />
                    <p className="text-muted-foreground font-black tracking-widest text-[9px] uppercase">Synthesizing Representation...</p>
                </div>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card rounded-[2rem] p-8 bg-card border border-border hover:border-primary/20 transition-all group"
        >
            <div className="flex items-start justify-between mb-8">
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Terminal size={12} className="text-blue-500" />
                        <span className="text-muted-foreground text-[9px] font-black uppercase tracking-[0.2em]">{title || 'Neural Metric Stream'}</span>
                    </div>
                    <div className="flex items-baseline gap-4">
                        <span className="text-5xl font-black text-foreground tracking-tighter tabular-nums">{value || '---'}</span>
                        {trend && (
                            <div className={`px-2 py-0.5 rounded text-[10px] font-black ${trend.startsWith('+') ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                {trend}
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={toggleFullScreen}
                    className="p-3 rounded-xl bg-foreground/5 hover:bg-foreground/10 text-muted-foreground hover:text-foreground transition-all opacity-0 group-hover:opacity-100"
                >
                    <Maximize2 size={18} />
                </button>
            </div>

            <div className="h-[280px] w-full mb-4">
                <PlotlyChart key={`normal-${title}`} data={plotlyConfig.data} layout={plotlyConfig.layout} isFullScreen={false} />
            </div>

            {/* Portaled Overlay */}
            {typeof document !== 'undefined' && createPortal(
                <AnimatePresence>
                    {isFullScreen && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-background backdrop-blur-3xl overflow-hidden flex flex-col p-8 md:p-12 transition-colors duration-500"
                            style={{ zIndex: 999999, position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }}
                        >
                            <div className="flex items-center justify-between mb-12">
                                <div>
                                    <div className="flex items-center gap-3 mb-3">
                                        <Terminal size={20} className="text-blue-500" />
                                        <span className="text-blue-500/60 font-black tracking-[0.3em] uppercase text-xs">High Frequency Metric Bridge</span>
                                    </div>
                                    <h2 className="text-4xl font-black text-foreground tracking-tighter mb-4">{title}</h2>
                                    <div className="flex items-baseline gap-8">
                                        <span className="text-8xl font-black text-foreground tracking-tighter tabular-nums">{value}</span>
                                        {trend && <span className={`text-2xl font-black ${trend.startsWith('+') ? 'text-green-500' : 'text-red-500'}`}>{trend} Comparison</span>}
                                    </div>
                                </div>
                                <button
                                    onClick={toggleFullScreen}
                                    className="p-6 rounded-3xl bg-foreground/5 hover:bg-foreground/10 text-muted-foreground hover:text-foreground border border-border transition-all"
                                >
                                    <X size={32} />
                                </button>
                            </div>
                            <div className="flex-1 rounded-[3rem] bg-foreground/[0.02] border border-border p-12 shadow-inner">
                                <PlotlyChart key={`full-${title}`} data={plotlyConfig.data} layout={plotlyConfig.layout} isFullScreen={true} />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>,
                document.body
            )}
        </motion.div>
    );
};

export default SessionsChart;
