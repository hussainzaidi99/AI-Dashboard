import React, { useEffect, useRef, useState } from 'react';

const PlotlyChart = ({ data, layout, loading, error, isFullScreen }) => {
    const chartRef = useRef(null);
    const [plotlyInstance, setPlotlyInstance] = useState(null);
    const isInitialized = useRef(false);

    // Dynamic loading of Plotly
    useEffect(() => {
        if (!plotlyInstance && typeof window !== 'undefined') {
            import('plotly.js-dist-min').then(module => {
                setPlotlyInstance(module.default);
            });
        }
    }, [plotlyInstance]);

    useEffect(() => {
        if (!chartRef.current || !plotlyInstance || !data || loading || error) return;

        const render = async () => {
            try {
                // Ensure container has calculated dimensions by waiting for browser layout
                await new Promise(resolve => setTimeout(resolve, 100));

                if (!chartRef.current || !plotlyInstance) return;

                if (!isInitialized.current) {
                    await plotlyInstance.newPlot(chartRef.current, data, layout, {
                        displayModeBar: isFullScreen,
                        displaylogo: false,
                        responsive: true,
                        toImageButtonOptions: {
                            format: 'png',
                            width: 1200,
                            height: 800
                        }
                    });
                    isInitialized.current = true;
                } else {
                    await plotlyInstance.react(chartRef.current, data, layout, {
                        displayModeBar: isFullScreen,
                        displaylogo: false,
                        responsive: true
                    });
                }
            } catch (err) {
                console.warn('Plotly rendering warning:', err);
            }
        };

        render();

        // Use ResizeObserver for more robust resizing than just window resize
        const resizeObserver = new ResizeObserver(() => {
            if (chartRef.current && plotlyInstance) {
                plotlyInstance.Plots.resize(chartRef.current);
            }
        });

        if (chartRef.current) resizeObserver.observe(chartRef.current);

        // Force a global resize event to help Plotly find its container
        window.dispatchEvent(new Event('resize'));

        return () => {
            if (resizeObserver) resizeObserver.disconnect();
            if (chartRef.current && plotlyInstance) {
                plotlyInstance.purge(chartRef.current);
                isInitialized.current = false;
            }
        };
    }, [data, layout, plotlyInstance, loading, error, isFullScreen]);

    return <div ref={chartRef} className="w-full h-full animate-in fade-in duration-500" />;
};

export default PlotlyChart;
