import React, { createContext, useContext, useState, useEffect } from 'react';
import { fileApi } from '../api/file';

const DatasetContext = createContext();

export const DatasetProvider = ({ children }) => {
    const [activeFileId, setActiveFileId] = useState(() => {
        return localStorage.getItem('activeFileId') || null;
    });
    const [activeFileName, setActiveFileName] = useState(() => {
        return localStorage.getItem('activeFileName') || null;
    });
    const [activeMetadata, setActiveMetadata] = useState(null);
    const [activeSheetIndex, setActiveSheetIndex] = useState(0);
    const [isTextOnly, setIsTextOnly] = useState(false);
    const [textContent, setTextContent] = useState('');

    useEffect(() => {
        if (activeFileId) {
            localStorage.setItem('activeFileId', activeFileId);

            // Check if file actually exists on server
            fileApi.getStatus(activeFileId).then(data => {
                if (data.filename) {
                    setActiveFileName(data.filename);
                    localStorage.setItem('activeFileName', data.filename);
                }
            }).catch(err => {
                console.warn("File no longer exists on server, clearing session:", activeFileId);
                // Clear state if file not found (404)
                setActiveFileId(null);
                setActiveFileName(null);
                localStorage.removeItem('activeFileId');
                localStorage.removeItem('activeFileName');
            });

            // Fetch processing result to check type
            import('../api/processing').then(({ processingApi }) => {
                processingApi.getResult(activeFileId).then(data => {
                    setIsTextOnly(data.dataframes?.length === 0);
                    setTextContent(data.text_content || '');
                }).catch(err => {
                    // Non-critical, might still be processing
                    console.log("Processing result not yet available");
                });
            });
        } else {
            localStorage.removeItem('activeFileId');
            localStorage.removeItem('activeFileName');
            setActiveFileName(null);
            setActiveMetadata(null);
        }
    }, [activeFileId]);

    return (
        <DatasetContext.Provider
            value={{
                activeFileId,
                setActiveFileId,
                activeFileName,
                setActiveFileName,
                activeMetadata,
                setActiveMetadata,
                activeSheetIndex,
                setActiveSheetIndex,
                isTextOnly,
                textContent,
                hasActiveDataset: !!activeFileId
            }}
        >
            {children}
        </DatasetContext.Provider>
    );
};

export const useDataset = () => {
    const context = useContext(DatasetContext);
    if (!context) {
        throw new Error('useDataset must be used within a DatasetProvider');
    }
    return context;
};
