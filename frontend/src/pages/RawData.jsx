import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Database, Filter, ArrowRight, FileText } from 'lucide-react';
import { useDataset } from '../context/DatasetContext';
import { dataApi } from '../api/data';
import DataTable from '../components/shared/DataTable';
import { useNavigate } from 'react-router-dom';

const RawData = () => {
    const navigate = useNavigate();
    const { activeFileId, activeSheetIndex, hasActiveDataset, isTextOnly, textContent } = useDataset();

    // Fetch Raw Data with error handling
    const { data: rawData, isLoading, isError } = useQuery({
        queryKey: ['raw-data', activeFileId, activeSheetIndex],
        queryFn: () => dataApi.getRows(activeFileId, activeSheetIndex, 50),
        enabled: hasActiveDataset && !isTextOnly,
        retry: 1,
        staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
        cacheTime: 10 * 60 * 1000, // Keep in memory for 10 minutes
    });

    const columns = rawData?.data?.[0] ? Object.keys(rawData.data[0]) : [];

    return (
        <div className="space-y-10 pb-20">
            {/* Header Section */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div className="max-w-3xl">
                    <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest mb-2">
                        <Database size={14} />
                        <span>Structured Data Explorer</span>
                    </div>
                    <h2 className="text-4xl font-bold tracking-tight">Raw Data Preview</h2>
                    <p className="text-muted-foreground text-lg mt-2">
                        Inspect all records and entities extracted by the AI engine.
                        Cross-reference validation states and schema integrity.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white/70 text-[10px] font-black uppercase tracking-[0.2em] shadow-inner">
                        Schema Validated
                    </div>
                </div>
            </div>

            {hasActiveDataset ? (
                <div className="glass-card rounded-[2.5rem] p-10 min-h-[600px]">
                    {isTextOnly ? (
                        <div className="space-y-6">
                            <div className="flex items-center gap-3 pb-6 border-b border-white/5">
                                <div className="p-2 rounded-lg bg-primary/10 text-primary">
                                    <FileText size={20} />
                                </div>
                                <h3 className="text-xl font-bold">Extracted Text Content</h3>
                            </div>
                            <div className="prose prose-invert max-w-none">
                                <p className="text-muted-foreground whitespace-pre-wrap leading-relaxed font-medium">
                                    {textContent || "No text content available."}
                                </p>
                            </div>
                        </div>
                    ) : (
                        <DataTable
                            data={rawData?.data || []}
                            columns={columns}
                            loading={isLoading}
                        />
                    )}
                </div>
            ) : (
                <div className="h-[60vh] glass-card rounded-[3rem] p-12 flex flex-col items-center justify-center text-center space-y-6">
                    <div className="w-24 h-24 rounded-[2rem] bg-white/5 border border-white/10 flex items-center justify-center text-muted-foreground/30">
                        <Database size={48} />
                    </div>
                    <div className="max-w-sm space-y-2">
                        <h3 className="text-2xl font-bold">Explorer Offline</h3>
                        <p className="text-muted-foreground">
                            We cannot render the data grid without an active ingest stream. Please navigate to the Ingestion Zone.
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/upload')}
                        className="group flex items-center gap-2 px-8 py-3 rounded-2xl bg-white text-black font-extrabold transition-all shadow-xl hover:bg-neutral-200"
                    >
                        Go to Ingestion Zone
                        <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            )}
        </div>
    );
};

export default RawData;
