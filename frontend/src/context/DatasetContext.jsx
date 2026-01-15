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
            // Fetch metadata if missing
            if (!activeFileName) {
                fileApi.getStatus(activeFileId).then(data => {
                    setActiveFileName(data.filename);
                    localStorage.setItem('activeFileName', data.filename);
                }).catch(err => console.error("Failed to fetch file status:", err));
            }

            // Fetch processing result to check type
            import('../api/processing').then(({ processingApi }) => {
                processingApi.getResult(activeFileId).then(data => {
                    setIsTextOnly(data.dataframes?.length === 0);
                    setTextContent(data.text_content || '');
                }).catch(err => console.error("Failed to fetch processing result:", err));
            });
        } else {
            localStorage.removeItem('activeFileId');
            localStorage.removeItem('activeFileName');
            setActiveFileName(null);
            setActiveMetadata(null);
        }
    }, [activeFileId, activeFileName]);

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
