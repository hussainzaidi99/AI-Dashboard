"""
Text Processor - Extract content from plain text files
Handles basic text extraction and table detection from text
"""
#backend/app/core/processors/text_processor.py

import time
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

from .base import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)


class TextProcessor(BaseProcessor):
    """Process plain text files and detect embedded tables"""
    
    def __init__(self):
        super().__init__()
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process text file and extract content
        
        Args:
            file_path: Path to text file
            **kwargs:
                - encoding: str (default: auto-detect)
                - extract_tables: bool (default: True)
        
        Returns:
            ProcessingResult with extracted data
        """
        start_time = time.time()
        
        try:
            # Validate file
            self.validate_file(file_path)
            
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            
            # Detect encoding (using a helper or standard utf-8)
            encoding = kwargs.get('encoding')
            if not encoding:
                # Try to import from csv_processor helper if available or use chardet
                try:
                    import chardet
                    with open(file_path, 'rb') as f:
                        raw_data = f.read(100000)
                        result = chardet.detect(raw_data)
                        encoding = result['encoding'] or 'utf-8'
                except:
                    encoding = 'utf-8'
            
            metadata['encoding'] = encoding
            
            # Read text content
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                text_content = f.read()
            
            dataframes = []
            warnings = []
            
            # Try to extract tables if requested
            extract_tables = kwargs.get('extract_tables', True)
            if extract_tables:
                dataframes = self.extract_tables_from_text(text_content)
                if not dataframes:
                    warnings.append("No table structures detected in text file")
            
            # Add text statistics to metadata
            metadata['char_count'] = len(text_content)
            metadata['line_count'] = len(text_content.splitlines())
            metadata['word_count'] = len(text_content.split())
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                file_type='text',
                dataframes=dataframes,
                text_content=text_content,
                metadata=metadata,
                processing_time=time.time() - start_time,
                warnings=warnings,
                sheet_names=[f"Table_{i+1}" for i in range(len(dataframes))]
            )
            
            self.log_processing_info(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing text file {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                file_path=file_path,
                file_type='text',
                error_message=str(e),
                processing_time=time.time() - start_time
            )
