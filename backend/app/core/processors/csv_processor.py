"""
CSV Processor - Extract data from CSV and text files
Handles various delimiters, encodings, and malformed data
"""
#backend/app/core/processors/csv_processor.py

import time
from typing import Optional, List
import pandas as pd
import chardet
import logging

from .base import BaseProcessor, ProcessingResult
from app.config import settings

logger = logging.getLogger(__name__)


class CSVProcessor(BaseProcessor):
    """Process CSV, TSV, and text files with intelligent parsing"""
    
    def __init__(self):
        super().__init__()
        
        # Common delimiters to try (removed space as it over-splits text)
        self.delimiters = [',', '\t', ';', '|']
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process CSV/text file with auto-detection
        
        Args:
            file_path: Path to CSV file
            **kwargs:
                - delimiter: str (default: auto-detect)
                - encoding: str (default: auto-detect)
                - header: int or None (default: 0)
                - skiprows: int (default: 0)
                - na_values: list (additional NA values)
        
        Returns:
            ProcessingResult with extracted data
        """
        start_time = time.time()
        
        try:
            # Validate file
            self.validate_file(file_path)
            
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            
            # Detect encoding
            encoding = kwargs.get('encoding') or self._detect_encoding(file_path)
            metadata['detected_encoding'] = encoding
            
            # Detect delimiter
            delimiter = kwargs.get('delimiter') or self._detect_delimiter(
                file_path, encoding
            )
            metadata['detected_delimiter'] = repr(delimiter)
            
            # Extract other options
            header = kwargs.get('header', 0)
            skiprows = kwargs.get('skiprows', 0)
            na_values = kwargs.get('na_values', [])
            
            warnings = []
            
            # Read CSV
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    header=header,
                    skiprows=skiprows,
                    na_values=na_values,
                    low_memory=False,
                    on_bad_lines='warn'
                )
                
                # Clean the dataframe
                df = self.clean_dataframe(df)
                
                # Validate data
                if df.empty:
                    raise ValueError("CSV file is empty or could not be parsed")
                
                if len(df.columns) == 1:
                    warnings.append(
                        "Only one column detected. The delimiter might be incorrect."
                    )
                
                # Additional metadata
                metadata['rows'] = len(df)
                metadata['columns'] = len(df.columns)
                metadata['column_names'] = df.columns.tolist()
                metadata['data_types'] = df.dtypes.astype(str).to_dict()
            
            except Exception as e:
                self.logger.error(f"Error reading CSV with pandas: {str(e)}")
                # Try fallback encodings if it might be an encoding issue
                fallback_encodings = ['utf-8', 'latin-1', 'cp1252']
                df = None
                
                for enc in fallback_encodings:
                    if enc == encoding: continue
                    try:
                        self.logger.info(f"Trying fallback encoding: {enc}")
                        df = pd.read_csv(
                            file_path,
                            delimiter=delimiter,
                            encoding=enc,
                            header=header,
                            skiprows=skiprows,
                            na_values=na_values,
                            low_memory=False,
                            on_bad_lines='skip'
                        )
                        if not df.empty:
                            encoding = enc
                            metadata['detected_encoding'] = enc
                            warnings.append(f"Used fallback encoding: {enc}")
                            break
                    except:
                        continue
                
                if df is None:
                    # Try alternative parsing methods (delimiters)
                    df = self._parse_with_fallback(file_path, encoding)
                
                if df is None or df.empty:
                    raise ValueError(f"Could not parse CSV file: {str(e)}")
                
                df = self.clean_dataframe(df)
                warnings.append(f"Used fallback parser due to initial error: {str(e)}")
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                file_type='csv',
                dataframes=[df],
                metadata=metadata,
                processing_time=time.time() - start_time,
                warnings=warnings,
                sheet_names=['Data']
            )
            
            self.log_processing_info(result)
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing CSV {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                file_path=file_path,
                file_type='csv',
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding using chardet
        
        Args:
            file_path: Path to file
        
        Returns:
            Detected encoding string
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 100KB for detection
                raw_data = f.read(100000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                confidence = result['confidence']
                
                self.logger.info(
                    f"Detected encoding: {encoding} (confidence: {confidence:.2f})"
                )
                
                # Fallback chain for low confidence
                if confidence < 0.7:
                    self.logger.warning(
                        f"Low confidence ({confidence:.2f}) in {encoding}, using fallback chain"
                    )
                    # We'll return the detected one, but the process() loop will try others
                    return encoding
                
                return encoding
        
        except Exception as e:
            self.logger.warning(f"Error detecting encoding: {str(e)}, using UTF-8")
            return 'utf-8'
    
    def _detect_delimiter(self, file_path: str, encoding: str) -> str:
        """
        Detect CSV delimiter by analyzing file content
        
        Args:
            file_path: Path to file
            encoding: File encoding
        
        Returns:
            Detected delimiter
        """
        try:
            import csv
            
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first few lines
                sample = f.read(8192)
                
                # Use Python's csv.Sniffer
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                self.logger.info(f"Detected delimiter: {repr(delimiter)}")
                return delimiter
        
        except Exception as e:
            self.logger.warning(
                f"Could not auto-detect delimiter: {str(e)}, trying manual detection"
            )
            return self._manual_delimiter_detection(file_path, encoding)
    
    def _manual_delimiter_detection(self, file_path: str, encoding: str) -> str:
        """
        Manually detect delimiter by counting occurrences
        
        Args:
            file_path: Path to file
            encoding: File encoding
        
        Returns:
            Most likely delimiter
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                # Read first 10 lines
                lines = [f.readline() for _ in range(10)]
            
            # Count delimiter occurrences
            delimiter_counts = {delim: [] for delim in self.delimiters}
            
            for line in lines:
                if line.strip():
                    for delim in self.delimiters:
                        count = line.count(delim)
                        delimiter_counts[delim].append(count)
            
            # Find delimiter with most consistent count (and count > 0)
            best_delimiter = ','
            best_score = 0
            
            for delim, counts in delimiter_counts.items():
                if not counts or all(c == 0 for c in counts):
                    continue
                
                # Calculate consistency (lower std dev = more consistent)
                avg_count = sum(counts) / len(counts)
                if avg_count > 0:
                    variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
                    std_dev = variance ** 0.5
                    
                    # Score: higher average, lower variance
                    score = avg_count / (std_dev + 1)
                    
                    if score > best_score:
                        best_score = score
                        best_delimiter = delim
            
            self.logger.info(f"Manual detection found delimiter: {repr(best_delimiter)}")
            return best_delimiter
        
        except Exception as e:
            self.logger.error(f"Manual delimiter detection failed: {str(e)}")
            return ','  # Default to comma
    
    def _parse_with_fallback(self, file_path: str, encoding: str) -> Optional[pd.DataFrame]:
        """
        Try alternative parsing methods when standard parsing fails
        
        Args:
            file_path: Path to file
            encoding: File encoding
        
        Returns:
            DataFrame or None
        """
        # Try each delimiter
        for delimiter in self.delimiters:
            try:
                df = pd.read_csv(
                    file_path,
                    delimiter=delimiter,
                    encoding=encoding,
                    engine='python',
                    on_bad_lines='skip'
                )
                
                if not df.empty and len(df.columns) > 1:
                    self.logger.info(f"Fallback successful with delimiter: {repr(delimiter)}")
                    return df
            except:
                continue
        
        # Try reading as fixed-width
        try:
            df = pd.read_fwf(file_path, encoding=encoding)
            if not df.empty:
                self.logger.info("Fallback successful with fixed-width format")
                return df
        except:
            pass
        
        return None
    
    def validate_csv_structure(self, file_path: str) -> dict:
        """
        Validate CSV structure and provide diagnostics
        
        Args:
            file_path: Path to CSV file
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': False,
            'issues': [],
            'suggestions': []
        }
        
        try:
            encoding = self._detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            if not lines:
                results['issues'].append("File is empty")
                return results
            
            # Check for consistent column count
            delimiter = self._detect_delimiter(file_path, encoding)
            col_counts = [line.count(delimiter) for line in lines[:100]]
            
            if len(set(col_counts)) > 3:
                results['issues'].append("Inconsistent number of columns")
                results['suggestions'].append("Check for unescaped delimiters in data")
            
            # Check for header using Sniffer
            results['has_header'] = False
            try:
                import csv
                sniffer = csv.Sniffer()
                results['has_header'] = sniffer.has_header(sample)
                results['detected_delimiter'] = delimiter
            except:
                # Basic fallback
                first_line = lines[0].strip()
                if delimiter in first_line:
                    results['has_header'] = True
            
            results['valid'] = len(results['issues']) == 0
            
        except Exception as e:
            results['issues'].append(f"Validation error: {str(e)}")
        
        return results