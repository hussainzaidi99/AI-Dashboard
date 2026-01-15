import React from 'react';
import { Database, FileText, History, Info } from 'lucide-react';
import FileUploader from '../components/data/FileUploader';
import { useDataset } from '../context/DatasetContext';
import { useQuery } from '@tanstack/react-query';
import { fileApi } from '../api/file';
import { format } from 'date-fns';

const DataUpload = () => {
    const { activeFileId, setActiveFileId, setActiveFileName } = useDataset();

    // Fetch recent uploads
    const { data: recentFiles, refetch } = useQuery({
        queryKey: ['recentUploads'],
        queryFn: async () => {
            const response = await fileApi.list();
            return response.files;
        }
    });

    const handleUploadSuccess = (fileId) => {
        setActiveFileId(fileId);
        refetch(); // Refresh the list
        console.log('File uploaded and processed:', fileId);
    };

    const selectFile = (file) => {
        setActiveFileId(file.file_id);
        setActiveFileName(file.filename);
    };

    return (
        <div className="space-y-12 pb-20">
            {/* Header Section */}
            <div className="flex flex-col gap-2 max-w-3xl">
                <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-widest mb-2">
                    <Database size={14} />
                    <span>Data Ingestion</span>
                </div>
                <h2 className="text-4xl font-bold tracking-tight">Ingest your datasets</h2>
                <p className="text-muted-foreground text-lg">
                    Upload your files to our AI engine. We'll automatically extract entities, identify patterns,
                    and prepare your data for deep visual analysis.
                </p>
            </div>

            {/* Main Uploader Zone */}
            <section className="relative">
                <div className="absolute inset-0 bg-primary/5 blur-[120px] rounded-full -z-10" />
                <FileUploader onUploadSuccess={handleUploadSuccess} />
            </section>

            {/* Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-card p-8 rounded-[2rem] space-y-4 border-white/5">
                    <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400">
                        <FileText size={24} />
                    </div>
                    <h3 className="text-lg font-bold">Smart Extraction</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        Our AI identifies column types, handles missing values, and normalizes date formats automatically.
                    </p>
                </div>

                <div className="glass-card p-8 rounded-[2rem] space-y-4 border-white/5">
                    <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400">
                        <History size={24} />
                    </div>
                    <h3 className="text-lg font-bold">Version Tracking</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        Keep track of multiple versions of your datasets. Compare changes and trends over time.
                    </p>
                </div>

                <div className="glass-card p-8 rounded-[2rem] space-y-4 border-white/5">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-400">
                        <Info size={24} />
                    </div>
                    <h3 className="text-lg font-bold">Privacy First</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        Data is encrypted at rest and in transit. Your datasets are isolated and never used for global training.
                    </p>
                </div>
            </div>

            {/* Recent Uploads Section */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold flex items-center gap-3">
                        Recently Processed
                        <span className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] font-bold border border-white/10 uppercase tracking-widest">Live</span>
                    </h3>
                    <button
                        onClick={() => refetch()}
                        className="text-xs font-bold text-primary hover:underline"
                    >
                        Refresh List
                    </button>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {!recentFiles || recentFiles.length === 0 ? (
                        <div className="glass-card overflow-hidden rounded-[2rem] border-white/5">
                            <div className="px-8 py-10 text-center text-muted-foreground">
                                <p className="font-medium">No recent uploads found.</p>
                                <p className="text-sm">Start by dropping a file above.</p>
                            </div>
                        </div>
                    ) : (
                        recentFiles.slice(0, 5).map((file) => (
                            <button
                                key={file.file_id}
                                onClick={() => selectFile(file)}
                                className={`flex items-center justify-between p-6 glass-card rounded-2xl border transition-all text-left group ${activeFileId === file.file_id
                                        ? 'border-primary bg-primary/5 shadow-[0_0_20px_rgba(59,130,246,0.1)]'
                                        : 'border-white/5 hover:border-white/10 hover:bg-white/5'
                                    }`}
                            >
                                <div className="flex items-center gap-4">
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${activeFileId === file.file_id ? 'bg-primary/20 text-primary' : 'bg-white/5 text-muted-foreground group-hover:text-white'
                                        }`}>
                                        <FileText size={24} />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-sm mb-1">{file.filename}</h4>
                                        <div className="flex items-center gap-3 text-[10px] font-medium text-muted-foreground uppercase tracking-widest">
                                            <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                            <span className="w-1 h-1 rounded-full bg-white/20" />
                                            <span>{file.metadata?.content_type || 'Document'}</span>
                                            <span className="w-1 h-1 rounded-full bg-white/20" />
                                            <span>{format(new Date(file.created_at || Date.now()), 'MMM d, yyyy')}</span>
                                        </div>
                                    </div>
                                </div>

                                {activeFileId === file.file_id ? (
                                    <div className="flex items-center gap-2 text-primary">
                                        <span className="text-[10px] font-bold uppercase tracking-widest">Active</span>
                                        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                                    </div>
                                ) : (
                                    <span className="text-[10px] font-bold text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest">
                                        Switch to Dataset
                                    </span>
                                )}
                            </button>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default DataUpload;
