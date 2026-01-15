import React, { createContext, useContext, useState, useEffect } from 'react';

const DatasetContext = createContext();

export const DatasetProvider = ({ children }) => {
    const [activeFileId, setActiveFileId] = useState(() => {
        return localStorage.getItem('activeFileId') || null;
    });
    const [activeSheetIndex, setActiveSheetIndex] = useState(0);

    useEffect(() => {
        if (activeFileId) {
            localStorage.setItem('activeFileId', activeFileId);
        } else {
            localStorage.removeItem('activeFileId');
        }
    }, [activeFileId]);

    return (
        <DatasetContext.Provider
            value={{
                activeFileId,
                setActiveFileId,
                activeSheetIndex,
                setActiveSheetIndex,
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
