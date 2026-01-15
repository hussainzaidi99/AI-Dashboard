import React from 'react';
import {
    Search,
    Download,
    ChevronLeft,
    ChevronRight,
    Filter,
    ArrowUpDown
} from 'lucide-react';

const DataTable = ({ data, columns, loading }) => {
    if (loading) {
        return (
            <div className="w-full h-96 flex flex-col items-center justify-center space-y-4">
                <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                <p className="text-muted-foreground font-medium animate-pulse">Syncing table data...</p>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="w-full h-96 flex flex-col items-center justify-center text-center p-10 border-2 border-dashed border-white/5 rounded-[2rem]">
                <p className="text-muted-foreground italic">No data records found in this segment.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full">
            {/* Table Actions */}
            <div className="flex items-center justify-between mb-6">
                <div className="relative max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input
                        type="text"
                        placeholder="Search records..."
                        className="w-80 h-10 pl-10 pr-4 bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-1 focus:ring-primary text-sm"
                    />
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-xs font-bold uppercase tracking-widest text-muted-foreground">
                        <Filter size={14} />
                        Filter
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-xs font-bold uppercase tracking-widest text-muted-foreground">
                        <Download size={14} />
                        CSV
                    </button>
                </div>
            </div>

            {/* Table Container */}
            <div className="flex-1 overflow-auto custom-scrollbar border border-white/5 rounded-2xl bg-white/5">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/10 bg-white/5 sticky top-0 z-10">
                            {columns.map((col) => (
                                <th key={col} className="px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    <div className="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
                                        {col}
                                        <ArrowUpDown size={12} />
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {data.map((row, idx) => (
                            <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                {columns.map((col) => (
                                    <td key={col} className="px-6 py-4 text-sm text-foreground/80 font-medium whitespace-nowrap">
                                        {row[col]?.toString() || '—'}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-6">
                <p className="text-xs text-muted-foreground font-medium">
                    Showing <span className="text-foreground">1-50</span> of <span className="text-foreground">{data.length}</span> entries
                </p>
                <div className="flex items-center gap-2">
                    <button className="p-2 rounded-xl bg-white/5 border border-white/10 text-muted-foreground hover:text-white disabled:opacity-30 disabled:hover:text-muted-foreground transition-all">
                        <ChevronLeft size={18} />
                    </button>
                    <div className="flex items-center gap-1">
                        <button className="w-8 h-8 rounded-lg bg-primary text-white font-bold text-xs">1</button>
                        <button className="w-8 h-8 rounded-lg bg-white/5 text-muted-foreground font-bold text-xs hover:bg-white/10">2</button>
                        <button className="w-8 h-8 rounded-lg bg-white/5 text-muted-foreground font-bold text-xs hover:bg-white/10">3</button>
                    </div>
                    <button className="p-2 rounded-xl bg-white/5 border border-white/10 text-muted-foreground hover:text-white transition-all">
                        <ChevronRight size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DataTable;
