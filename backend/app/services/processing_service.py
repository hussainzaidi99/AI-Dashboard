#backend/app/services/processing_service.py

"""
Processing Service
Business logic for file processing operations
"""

import pandas as pd
from typing import Dict, Any, List, Optional
import logging

from app.core.processors import get_processor
from app.services.file_service import FileService

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for file processing operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.file_service = FileService()
    
    async def process_file(
        self,
        file_id: str,
        file_extension: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a file and extract data with preview
        
        Args:
            file_id: File ID
            file_extension: File extension
            options: Processing options
        
        Returns:
            Processing result dictionary
        """
        try:
            options = options or {}
            preview_rows = int(options.get("preview_rows", 200))
            
            # Get file path
            file_path = self.file_service.get_file_path(file_id, file_extension)
            
            if not self.file_service.file_exists(file_id, file_extension):
                raise FileNotFoundError(f"File not found: {file_id}")
            
            # Get appropriate processor
            processor = get_processor(file_extension)
            
            # Process file
            result = processor.process(file_path, **options)
            
            if not result.success:
                raise RuntimeError(result.error_message or "Processing failed")
            
            # Serialize dataframes (with preview)
            serialized_dataframes = []
            for idx, df in enumerate(result.dataframes):
                preview_df = df.head(preview_rows)
                
                serialized_dataframes.append({
                    "sheet_name": result.sheet_names[idx] if idx < len(result.sheet_names) else f"Sheet_{idx+1}",
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "data_preview": preview_df.to_dict('records'),
                    "showing_rows": len(preview_df),
                    "dtypes": df.dtypes.astype(str).to_dict()
                })
            
            return {
                "file_id": file_id,
                "success": True,
                "dataframes": serialized_dataframes,
                "text_content": result.text_content,
                "metadata": result.metadata,
                "total_rows": result.total_rows,
                "total_columns": result.total_columns,
                "processing_time": result.processing_time,
                "warnings": result.warnings
            }
        
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")
            raise
    
    def get_dataframe(
        self,
        processed_data: Dict[str, Any],
        sheet_index: int = 0
    ) -> pd.DataFrame:
        """
        Get DataFrame from processed data
        
        Args:
            processed_data: Processed data dictionary
            sheet_index: Sheet index
        
        Returns:
            pandas DataFrame
        """
        if sheet_index >= len(processed_data['dataframes']):
            raise IndexError(f"Sheet index {sheet_index} out of range")
        
        sheet_data = processed_data['dataframes'][sheet_index]
        
        # Note: If processed_data only contains a preview, this will only return the preview.
        # In a real app we might reload from disk/cache.
        data_key = 'data' if 'data' in sheet_data else 'data_preview'
        return pd.DataFrame(sheet_data[data_key])
