import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Maximize2, Download, Info } from 'lucide-react';

const VizWidget = ({ config, title, description, loading, error }) => {
    const [plotlyInstance, setPlotlyInstance] = useState(null);
    const plotRef = useRef(null);
    const plotInitialized = useRef(false);

    // Dynamic loading of Plotly
    useEffect(() => {
        if (!plotlyInstance && typeof window !== 'undefined') {
            import('plotly.js-dist-min').then(module => {
                setPlotlyInstance(module.default);
            });
        }
    }, [plotlyInstance]);

    // Memoize Plotly layout to maintain performance with dark theme
    const plotlyLayout = useMemo(() => {
        if (!config || !config.layout) return {};

        const isIndicator = config.data?.[0]?.type === 'indicator';

        return {
            ...config.layout,
            title: '', // Remove internal title
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)', // Transparent background
            plot_bgcolor: 'rgba(25,30,45,0.4)', // Subtler plot area
            font: {
                family: "'Segoe UI', 'Roboto', 'Inter', system-ui, sans-serif",
                color: 'rgba(220,220,230,0.8)',
                size: isIndicator ? 12 : 10
            },
            margin: isIndicator
                ? { l: 20, r: 20, t: 30, b: 20 }
                : { l: 40, r: 10, t: 10, b: 30 }, // Tightened margins for dense grid
            showlegend: config.layout.showlegend ?? (!isIndicator),
            legend: {
                orientation: 'h',
                y: -0.2,
                x: 0.5,
                xanchor: 'center',
                bgcolor: 'rgba(25,30,45,0.8)',
                bordercolor: 'rgba(100,120,160,0.3)',
                borderwidth: 1,
                font: { size: 9, color: 'rgba(200,200,220,0.9)' }
            },
            hovermode: 'x unified',
            transition: {
                duration: 500,
                easing: 'cubic-in-out'
            }
        };
    }, [config]);

    // Memoize data to prevent unnecessary re-renders
    const plotlyData = useMemo(() => {
        if (!config || !config.data || !Array.isArray(config.data)) {
            return [];
        }

        // Filter out any undefined or null data items
        const validData = config.data.filter(item => item != null && typeof item === 'object');
        return validData;
    }, [config]);

    // Don't render Plotly if there's no valid data
    const hasValidData = plotlyData.length > 0;

    // Use native Plotly.js API instead of react-plotly.js
    useEffect(() => {
        if (!plotRef.current || !plotlyInstance || !hasValidData || loading || error) {
            return;
        }

        const renderPlot = async () => {
            try {
                if (!plotInitialized.current) {
                    // Initial plot creation with smooth animation
                    await plotlyInstance.newPlot(
                        plotRef.current,
                        plotlyData,
                        plotlyLayout,
                        {
                            displayModeBar: true,
                            displaylogo: false,
                            responsive: true,
                            toImageButtonOptions: {
                                format: 'png',
                                width: 1200,
                                height: 800
                            }
                        }
                    );
                    plotInitialized.current = true;
                } else {
                    // Update existing plot with animation
                    await plotlyInstance.react(
                        plotRef.current,
                        plotlyData,
                        plotlyLayout,
                        {
                            displayModeBar: true,
                            displaylogo: false,
                            responsive: true
                        }
                    );
                }
            } catch (err) {
                console.error('Plotly rendering error:', err);
            }
        };

        renderPlot();

        // Cleanup on unmount
        return () => {
            if (plotRef.current && plotlyInstance) {
                plotlyInstance.purge(plotRef.current);
                plotInitialized.current = false;
            }
        };
    }, [plotlyInstance, plotlyData, plotlyLayout, hasValidData, loading, error]);

    // Handle window resize
    useEffect(() => {
        if (!plotRef.current || !plotlyInstance || !plotInitialized.current) {
            return;
        }

        const handleResize = () => {
            if (plotRef.current && plotlyInstance) {
                plotlyInstance.Plots.resize(plotRef.current);
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [plotlyInstance]);

    return (
        <div className="glass-card rounded-2xl p-4 flex flex-col h-full group hover:shadow-[0_8px_40px_rgba(59,130,246,0.15)] transition-all duration-500 bg-gradient-to-br from-slate-900/80 to-slate-950/90 backdrop-blur-xl border border-slate-700/30">
            {/* Widget Header with Dark Theme */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex-1">
                    <h3 className="text-base font-bold tracking-tight text-white/90">
                        {title || 'Data Visualization'}
                    </h3>
                    {description && <p className="text-[10px] text-slate-400 mt-0.5 font-medium">{description}</p>}
                </div>

                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300">
                    <button className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all duration-300 border border-white/10">
                        <Info size={18} />
                    </button>
                    <button className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all duration-300 border border-white/10">
                        <Download size={18} />
                    </button>
                    <button className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all duration-300 border border-white/10">
                        <Maximize2 size={18} />
                    </button>
                </div>
            </div>

            {/* Premium Dark Content Section */}
            <div className="flex-1 relative h-[200px] w-full overflow-hidden rounded-lg bg-gradient-to-br from-slate-800/30 to-slate-900/30 border border-slate-700/20">
                {loading ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-6 bg-gradient-to-br from-slate-900 via-blue-900/20 to-slate-900">
                        <div className="relative w-16 h-16">
                            <div className="absolute inset-0 rounded-full border-4 border-slate-600/30" />
                            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-400 border-r-cyan-400 animate-spin" style={{ animationDuration: '1.5s' }} />
                            <div className="absolute inset-2 rounded-full border-2 border-transparent border-b-purple-400 animate-spin" style={{ animationDuration: '2.5s', animationDirection: 'reverse' }} />
                        </div>
                        <div className="text-center">
                            <p className="text-slate-200 font-semibold text-sm">Loading Visualization</p>
                            <p className="text-slate-400 text-xs mt-1 animate-pulse">Rendering your chart...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center space-y-4 bg-gradient-to-br from-slate-900 via-red-900/20 to-slate-900">
                        <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 shadow-lg border border-red-400/30">
                            <Info size={32} />
                        </div>
                        <div>
                            <p className="text-red-300 font-semibold">Failed to render visualization</p>
                            <p className="text-red-400/70 text-sm mt-1">Please check your data and try again</p>
                        </div>
                        <button className="px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white rounded-lg text-sm font-medium transition-all shadow-lg hover:shadow-xl border border-red-400/30">
                            Retry Sync
                        </button>
                    </div>
                ) : config && hasValidData ? (
                    <div
                        ref={plotRef}
                        className="w-full h-full animate-in fade-in duration-700"
                    />
                ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-10 text-center">
                        <div className="w-20 h-20 rounded-full bg-slate-700/30 flex items-center justify-center mb-4 border border-slate-600/30">
                            <Info size={40} className="text-slate-500" />
                        </div>
                        <p className="text-slate-400 font-medium text-sm">
                            {config ? 'No valid chart data available.' : 'No configuration data available.'}
                        </p>
                    </div>
                )}
            </div>

            {/* Dark Theme Footer */}
            <div className="mt-6 pt-6 border-t border-slate-700/30 flex items-center justify-between text-[10px] font-bold tracking-[0.2em] text-white/30">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_white]" />
                    <span>SYSTEM ANALYTICS HUB</span>
                </div>
                <span className="text-right">HDA-CORE 1.0</span>
            </div>
        </div>
    );
};

export default VizWidget;
