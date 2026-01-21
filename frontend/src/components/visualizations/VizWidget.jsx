import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Maximize2, Download, MoreHorizontal, Info } from 'lucide-react';

const VizWidget = ({ config, title, description, loading, error }) => {
    // Memoize Plotly layout to maintain performance
    const plotlyLayout = useMemo(() => {
        if (!config || !config.layout) return {};

        return {
            ...config.layout,
            autosize: true,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                family: 'Inter, system-ui, sans-serif',
                color: '#94a3b8',
            },
            margin: { l: 40, r: 20, t: 40, b: 40 },
            showlegend: config.layout.showlegend ?? true,
            legend: {
                orientation: 'h',
                y: -0.2,
                x: 0.5,
                xanchor: 'center',
            },
        };
    }, [config]);

    // Memoize data to prevent unnecessary re-renders
    const plotlyData = useMemo(() => {
        if (!config || !config.data || !Array.isArray(config.data)) {
            console.warn('VizWidget: Invalid or missing config.data', config);
            return [];
        }

        // Filter out any undefined or null data items
        const validData = config.data.filter(item => item != null && typeof item === 'object');

        if (validData.length === 0) {
            console.warn('VizWidget: No valid data items found in config.data');
        }

        return validData;
    }, [config]);

    // Don't render Plotly if there's no valid data
    const hasValidData = plotlyData.length > 0;

    return (
        <div className="glass-card rounded-[2.5rem] p-8 flex flex-col h-full group hover:shadow-[0_0_30px_rgba(255,255,255,0.05)] transition-all duration-500">
            {/* Widget Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold tracking-tight text-white/90">{title || 'Data Visualization'}</h3>
                    {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
                </div>

                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white transition-all">
                        <Info size={18} />
                    </button>
                    <button className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white transition-all">
                        <Download size={18} />
                    </button>
                    <button className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-muted-foreground hover:text-white transition-all">
                        <Maximize2 size={18} />
                    </button>
                </div>
            </div>

            {/* Internal Content Section */}
            <div className="flex-1 relative min-h-[300px] w-full overflow-hidden">
                {loading ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                        <div className="w-12 h-12 border-4 border-white/5 border-t-white rounded-full animate-spin" />
                        <p className="text-white/40 animate-pulse font-black uppercase text-[10px] tracking-widest">Hydrating dataset...</p>
                    </div>
                ) : error ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center space-y-4">
                        <div className="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center text-rose-500">
                            <Info size={32} />
                        </div>
                        <p className="text-rose-200/60 font-medium">Failed to render visualization.</p>
                        <button className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 rounded-lg text-sm transition-all">
                            Retry Sync
                        </button>
                    </div>
                ) : config && hasValidData ? (
                    <div className="w-full h-full animate-in fade-in zoom-in-95 duration-700">
                        <Plot
                            data={plotlyData}
                            layout={plotlyLayout}
                            useResizeHandler={true}
                            className="w-full h-full"
                            config={{
                                displayModeBar: false,
                                responsive: true,
                            }}
                        />
                    </div>
                ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center p-10 text-center border-2 border-dashed border-white/5 rounded-[2rem]">
                        <p className="text-muted-foreground/40 font-medium">
                            {config ? 'No valid chart data available.' : 'No configuration data available.'}
                        </p>
                    </div>
                )}
            </div>

            {/* Footer Info */}
            <div className="mt-6 pt-6 border-t border-white/5 flex items-center justify-between text-[10px] font-bold uppercase tracking-widest text-muted-foreground/50">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-white/40" />
                    <span>Real-time Sync</span>
                </div>
                <span>Powered by Plotly engine</span>
            </div>
        </div>
    );
};

export default VizWidget;
