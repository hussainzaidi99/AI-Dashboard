import React, { useState, useRef } from 'react';
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

const FileUploader = ({ onUploadSuccess }) => {
    const navigate = useNavigate();
    const [isDragging, setIsDragging] = useState(false);
    const [uploadState, setUploadState] = useState('idle'); // idle, uploading, processing, success, error
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);
    const [fileInfo, setFileInfo] = useState(null);
    const [isTextOnly, setIsTextOnly] = useState(false);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) validateAndUpload(file);
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) validateAndUpload(file);
    };

    const validateAndUpload = async (file) => {
        // Basic validation
        const allowedTypes = ['.csv', '.xlsx', '.xls', '.pdf', '.docx'];
        const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

        if (!allowedTypes.includes(extension)) {
            setError('Unsupported file type. Please upload Excel, CSV, PDF or Word documents.');
            setUploadState('error');
            return;
        }

        setFileInfo({ name: file.name, size: (file.size / 1024 / 1024).toFixed(2) + ' MB' });
        setIsTextOnly(false);
        setUploadState('uploading');
        setError(null);
        setProgress(0);

        try {
            // Import API here to avoid circular dependencies if any
            const { fileApi } = await import('../../api/file');
            const { processingApi } = await import('../../api/processing');

            // 1. Upload
            const uploadResult = await fileApi.upload(file, (p) => setProgress(p));

            // 2. Start Processing
            setUploadState('processing');
            const processResult = await processingApi.start(uploadResult.file_id);

            // 3. Detect if text-only
            if (processResult.dataframes_count === 0) {
                setIsTextOnly(true);
            }

            // 4. Notify Success
            setUploadState('success');
            if (onUploadSuccess) onUploadSuccess(uploadResult.file_id);

        } catch (err) {
            console.error('Upload error:', err);
            setError(err.response?.data?.detail || 'Failed to upload file. Please try again.');
            setUploadState('error');
        }
    };

    const reset = () => {
        setUploadState('idle');
        setFileInfo(null);
        setError(null);
        setProgress(0);
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <AnimatePresence mode="wait">
                {uploadState === 'idle' && (
                    <motion.div
                        key="idle"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current.click()}
                        className={`cursor-pointer group relative overflow-hidden rounded-[2.5rem] border-2 border-dashed transition-all duration-300 p-12 text-center ${isDragging ? 'border-primary bg-primary/5' : 'border-white/10 hover:border-primary/30 hover:bg-white/5'
                            }`}
                    >
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            className="hidden"
                            accept=".csv,.xlsx,.xls,.pdf,.docx"
                        />

                        <div className="relative z-10">
                            <div className={`w-20 h-20 rounded-3xl bg-primary/10 flex items-center justify-center mx-auto mb-6 transition-transform duration-500 ${isDragging ? 'scale-110' : 'group-hover:scale-110'}`}>
                                <Upload className="text-primary" size={36} />
                            </div>
                            <h3 className="text-2xl font-bold mb-2">Drop your data here</h3>
                            <p className="text-muted-foreground mb-6">Support for CSV, Excel, PDF and Word documents</p>

                            <div className="flex items-center justify-center gap-4 text-xs font-bold uppercase tracking-widest text-muted-foreground/60">
                                <span>Max 100MB</span>
                                <span className="w-1 h-1 rounded-full bg-white/20" />
                                <span>AI-Powered Processing</span>
                            </div>
                        </div>

                        {/* Background decorative elements */}
                        <div className="absolute -top-24 -right-24 w-48 h-48 bg-primary/5 rounded-full blur-3xl" />
                        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/5 rounded-full blur-3xl" />
                    </motion.div>
                )}

                {(uploadState === 'uploading' || uploadState === 'processing') && (
                    <motion.div
                        key="active"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass-card rounded-[2.5rem] p-10 text-center"
                    >
                        <div className="relative w-24 h-24 mx-auto mb-8">
                            <svg className="w-full h-full" viewBox="0 0 100 100">
                                <circle className="text-white/5 stroke-current" strokeWidth="8" fill="transparent" r="42" cx="50" cy="50" />
                                <motion.circle
                                    className="text-primary stroke-current"
                                    strokeWidth="8"
                                    strokeLinecap="round"
                                    fill="transparent"
                                    r="42"
                                    cx="50"
                                    cy="50"
                                    style={{
                                        pathLength: uploadState === 'uploading' ? progress / 100 : 1,
                                        rotate: -90,
                                        originX: '50%',
                                        originY: '50%'
                                    }}
                                    transition={{ type: 'spring', damping: 20 }}
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                {uploadState === 'uploading' ? (
                                    <span className="text-xl font-bold">{progress}%</span>
                                ) : (
                                    <Loader2 className="animate-spin text-primary" size={32} />
                                )}
                            </div>
                        </div>

                        <h3 className="text-2xl font-bold mb-2">
                            {uploadState === 'uploading' ? 'Uploading...' : 'AI Analysis in Progress'}
                        </h3>
                        <p className="text-muted-foreground mb-6 font-medium">
                            {fileInfo?.name} • {fileInfo?.size}
                        </p>

                        <div className="space-y-3 max-w-sm mx-auto">
                            <div className="flex justify-between text-xs font-bold uppercase tracking-tighter text-muted-foreground">
                                <span>Status</span>
                                <span>{uploadState === 'uploading' ? 'Saving to server' : 'Extracting data entities'}</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-primary"
                                    animate={{
                                        width: uploadState === 'uploading' ? `${progress}%` : '100%',
                                        opacity: uploadState === 'processing' ? [0.4, 1, 0.4] : 1
                                    }}
                                    transition={{
                                        opacity: { repeat: Infinity, duration: 1.5 }
                                    }}
                                />
                            </div>
                        </div>
                    </motion.div>
                )}

                {uploadState === 'success' && (
                    <motion.div
                        key="success"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass-card border-emerald-500/20 rounded-[2.5rem] p-10 text-center"
                    >
                        <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
                            <CheckCircle2 className="text-emerald-500" size={40} />
                        </div>
                        <h3 className="text-2xl font-bold mb-2 text-emerald-400">
                            {isTextOnly ? 'Document Processed!' : 'Analysis Complete!'}
                        </h3>
                        <p className="text-muted-foreground mb-8">
                            {isTextOnly
                                ? "We've extracted the text content. Head to the Intelligence Hub to ask questions about this document."
                                : "Your tabular data has been processed and is ready for discovery."
                            }
                        </p>
                        <div className="flex gap-4 justify-center">
                            <button onClick={reset} className="px-6 py-3 rounded-2xl bg-white/5 hover:bg-white/10 transition-all font-medium">
                                Upload Another
                            </button>
                            <button
                                onClick={() => navigate(isTextOnly ? '/intelligence' : '/dashboard')}
                                className="px-6 py-3 rounded-2xl bg-primary text-white font-bold shadow-lg shadow-primary/20 hover:bg-blue-600 transition-all"
                            >
                                {isTextOnly ? 'Ask AI' : 'View Insights'}
                            </button>
                        </div>
                    </motion.div>
                )}

                {uploadState === 'error' && (
                    <motion.div
                        key="error"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass-card border-rose-500/20 rounded-[2.5rem] p-10 text-center"
                    >
                        <div className="w-20 h-20 rounded-full bg-rose-500/10 flex items-center justify-center mx-auto mb-6">
                            <AlertCircle className="text-rose-500" size={40} />
                        </div>
                        <h3 className="text-2xl font-bold mb-2 text-rose-400">Upload Failed</h3>
                        <p className="text-rose-200/60 mb-8 max-w-sm mx-auto">
                            {error}
                        </p>
                        <button onClick={reset} className="px-8 py-3 rounded-2xl bg-rose-500 text-white font-bold shadow-lg shadow-rose-500/20 hover:bg-rose-600 transition-all">
                            Try Again
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default FileUploader;
