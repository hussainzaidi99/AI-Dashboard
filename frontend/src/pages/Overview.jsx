import React, { useMemo } from 'react';
import { Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useDataset } from '../context/DatasetContext';
import { dataApi } from '../api/data';
import { chartsApi } from '../api/charts';
import VizWidget from '../components/visualizations/VizWidget';
import SessionsChart from '../components/visualizations/SessionsChart';

const Overview = () => {
    const { activeFileId, activeSheetIndex, hasActiveDataset } = useDataset();

    // Fetch Statistics
    const { data: stats, isLoading: statsLoading } = useQuery({
        queryKey: ['stats', activeFileId, activeSheetIndex],
        queryFn: () => dataApi.getStatistics(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,
        cacheTime: 10 * 60 * 1000,
    });

    // Fetch Dashboard with caching
    const { data: dashboard, isLoading: dashboardLoading } = useQuery({
        queryKey: ['dashboard', activeFileId, activeSheetIndex],
        queryFn: () => chartsApi.getDashboard(activeFileId, activeSheetIndex),
        enabled: hasActiveDataset,
        staleTime: 5 * 60 * 1000,
        cacheTime: 10 * 60 * 1000,
    });

    return (
        <div className="space-y-8 pb-20">
            {/* Minimal Dashboard Header */}
            <header className="pb-4 border-b border-foreground/5">
                <h1 className="text-4xl font-bold tracking-tight text-foreground">
                    {hasActiveDataset ? 'Intelligence Snapshot' : 'Global Operations Hub'}
                </h1>
            </header>

            {/* Production Dashboard Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {hasActiveDataset ? (
                    dashboard?.widgets?.map((widget, idx) => {
                        const isTripleArea = widget.chart_type === 'triple_area';

                        // Extract KPI info for the specialized chart
                        let kpiValue = '---';
                        let kpiTrend = null;

                        if (isTripleArea && widget.chart?.data) {
                            // Find all traces that have y values (the features)
                            const validTraces = widget.chart.data.filter(d => (d.y || d.values) && d.name);
                            const mainTrace = validTraces[0];
                            const values = mainTrace?.y || mainTrace?.values || [];
                            const cleanValues = values.map(v => parseFloat(v)).filter(v => !isNaN(v));

                            if (cleanValues.length > 0) {
                                const current = cleanValues[cleanValues.length - 1];
                                const previous = cleanValues.length > 1 ? cleanValues[cleanValues.length - 2] : current;
                                const change = previous !== 0 ? ((current - previous) / previous * 100) : 0;

                                kpiValue = current >= 1000000 ? `${(current / 1000000).toFixed(1)}M` :
                                    current >= 1000 ? `${(current / 1000).toFixed(1)}k` :
                                        Number.isInteger(current) ? current.toLocaleString() : current.toFixed(2);

                                kpiTrend = `${change >= 0 ? '+' : ''}${change.toFixed(0)}%`;
                            }
                        }

                        const widgetsCount = dashboard?.widgets?.length || 0;
                        const isLastTwo = idx >= widgetsCount - 2 && widgetsCount > 1;

                        return (
                            <div
                                key={idx}
                                className={
                                    isTripleArea
                                        ? "md:col-span-2 lg:col-span-2"
                                        : (isLastTwo
                                            ? "md:col-span-2 lg:col-span-2 xl:col-span-2"
                                            : (idx === 0 ? "md:col-span-2 lg:col-span-1" : ""))
                                }
                            >
                                {isTripleArea ? (
                                    <SessionsChart
                                        title={widget.title}
                                        value={kpiValue}
                                        trend={kpiTrend}
                                        chartData={widget.chart}
                                        loading={dashboardLoading}
                                    />
                                ) : (
                                    <VizWidget
                                        title={widget.title}
                                        description={widget.description}
                                        config={widget.chart}
                                        loading={dashboardLoading}
                                    />
                                )}
                            </div>
                        );
                    })
                ) : (
                    <div className="col-span-full h-[500px] glass-card rounded-[2.5rem] p-8 flex flex-col items-center justify-center border-2 border-dashed border-foreground/10 group cursor-pointer hover:border-primary/20 transition-all">
                        <div className="text-center group-hover:scale-105 transition-transform duration-500">
                            <div className="w-20 h-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-6 text-primary shadow-[0_0_30px_rgba(59,130,246,0.15)]">
                                <Activity size={36} />
                            </div>
                            <h3 className="text-xl font-bold mb-2 text-foreground">Neural Link Pending</h3>
                            <p className="text-muted-foreground max-w-sm mx-auto">
                                Feed the system a dataset to activate the intelligence core and synthesize your dashboard.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Overview;
