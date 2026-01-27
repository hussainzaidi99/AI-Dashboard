"""
Base Processor - Abstract base class for all file processors
"""
#backend/app/core/processors/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """
    Standard result structure for all processors
    """
    success: bool
    file_path: str
    file_type: str
    
    # Extracted data
    dataframes: List[pd.DataFrame] = field(default_factory=list)
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing info
    processing_time: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    # Statistics
    total_rows: int = 0
    total_columns: int = 0  # Legacy: sum of all columns
    max_columns: int = 0    # Maximum columns in any single dataframe
    total_columns_sum: int = 0 # Explicit sum for clarity
    sheet_names: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate statistics after initialization"""
        if self.dataframes:
            self.total_rows = sum(len(df) for df in self.dataframes)
            self.total_columns = sum(len(df.columns) for df in self.dataframes)
            self.total_columns_sum = self.total_columns
            self.max_columns = max(len(df.columns) for df in self.dataframes) if self.dataframes else 0
            
            if not self.sheet_names:
                self.sheet_names = [f"Sheet_{i+1}" for i in range(len(self.dataframes))]


class BaseProcessor(ABC):
    """
    Abstract base class for all file processors
    All processors must implement the process() method
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process a file and extract data
        
        Args:
            file_path: Path to the file to process
            **kwargs: Additional processor-specific arguments
        
        Returns:
            ProcessingResult with extracted data
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that file exists and is readable
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if file is valid
        
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
        """
        import os
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")
        
        return True
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic file metadata
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary with file metadata
        """
        import os
        from pathlib import Path
        
        file_stat = os.stat(file_path)
        path_obj = Path(file_path)
        
        return {
            "file_name": path_obj.name,
            "file_size": file_stat.st_size,
            "file_size_mb": round(file_stat.st_size / (1024 * 1024), 2),
            "file_extension": path_obj.suffix.lower(),
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
        }
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize a DataFrame
        
        Args:
            df: Input DataFrame
        
        Returns:
            Cleaned DataFrame
        """
        # Remove completely empty rows and columns
        df = df.dropna(how='all', axis=0)  # Empty rows
        df = df.dropna(how='all', axis=1)  # Empty columns
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Handle "Unnamed" columns from pandas
        new_columns = []
        for i, col in enumerate(df.columns):
            if "Unnamed:" in col or col.lower() == "nan" or not col:
                new_columns.append(f"Column_{i+1}")
            else:
                new_columns.append(col)
        df.columns = new_columns
        
        # Remove duplicate column names
        df.columns = self._make_unique_columns(df.columns.tolist())
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Infer better data types
        df = self._infer_data_types(df)
        
        return df
    
    def _make_unique_columns(self, columns: List[str]) -> List[str]:
        """
        Make column names unique by appending numbers to duplicates
        
        Args:
            columns: List of column names
        
        Returns:
            List of unique column names
        """
        seen = {}
        unique_columns = []
        
        for col in columns:
            if col not in seen:
                seen[col] = 0
                unique_columns.append(col)
            else:
                seen[col] += 1
                unique_columns.append(f"{col}_{seen[col]}")
        
        return unique_columns
    
    def _infer_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Infer and convert data types for better analysis.
        Note: Timestamps are detected but remain as pd.Timestamp objects for analysis.
        They will be serialized to ISO 8601 strings by the custom JSON encoder.
        
        Args:
            df: Input DataFrame
        
        Returns:
            DataFrame with inferred types
        """
        import re
        import warnings
        
        # Date pattern heuristic (e.g., YYYY-MM-DD, DD/MM/YYYY, etc.)
        date_pattern = re.compile(r'(\d{1,4})[/-]\d{1,2}[/-]\d{1,4}')
        
        for col in df.columns:
            # Skip if already numeric or complex type
            if not df[col].dtype == 'object':
                continue
                
            # Try to convert to numeric
            try:
                # errors='coerce' then check if we should keep it
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                # If we didn't lose too much data (e.g. at least 50% successful conversion)
                if numeric_col.notna().sum() >= df[col].notna().sum() * 0.5:
                    df[col] = numeric_col
            except:
                pass
            
            # Try to convert to datetime
            if df[col].dtype == 'object':
                try:
                    # Quick heuristic: check if strings look like dates
                    sample = df[col].dropna().head(20)
                    if len(sample) > 0:
                        # Only attempt if at least one sample matches date pattern
                        if any(date_pattern.search(str(s)) for s in sample):
                            # Suppress the dateutil parsing warning as we're intentionally
                            # allowing flexible date parsing
                            with warnings.catch_warnings():
                                warnings.filterwarnings('ignore', 
                                                      message='Could not infer format')
                                df[col] = pd.to_datetime(df[col], errors='coerce')
                except:
                    pass
        
        return df
    
    def extract_tables_from_text(self, text: str) -> List[pd.DataFrame]:
        """
        Try to extract table-like structures from plain text with strict heuristics
        to avoid false positives from natural sentences.
        """
        dataframes = []
        
        # Split by double newlines (potential table boundaries)
        blocks = text.split('\n\n')
        
        for block in blocks:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            # HEURISTIC 1: Minimum rows (at least 3: header + 2 data rows)
            if len(lines) < 3:
                continue
            
            # Check if lines have consistent delimiters
            for delimiter in ['\t', '|', ',', ';']:
                # Count occurances in each line
                counts = [line.count(delimiter) for line in lines]
                
                # HEURISTIC 2: Minimum columns (at least 1 delimiter for 2 columns)
                if all(count >= 1 for count in counts):
                    # HEURISTIC 3: Structural Consistency
                    # Most lines should have the exact same number of delimiters
                    most_common_count = max(set(counts), key=counts.count)
                    consistency = counts.count(most_common_count) / len(counts)
                    
                    if consistency >= 0.7: # 70% of rows must match the common structure
                        try:
                            from io import StringIO
                            df = pd.read_csv(
                                StringIO('\n'.join(lines)),
                                sep=delimiter,
                                engine='python',
                                on_bad_lines='skip'
                            )
                            
                            # HEURISTIC 4: Density check
                            # Tables usually have short cells. If average cell length is too high, it might be text.
                            avg_cell_len = df.astype(str).map(len).values.mean()
                            
                            # HEURISTIC 5: Delimiter vs Text Ratio
                            # In a table, delimiters should be fairly frequent compared to non-space text.
                            total_chars = sum(len(line.replace(' ', '')) for line in lines)
                            total_delimiters = sum(counts)
                            chars_per_delimiter = total_chars / total_delimiters if total_delimiters > 0 else 999
                            
                            # HEURISTIC 6: Row Length Consistency (CV)
                            line_lens = [len(line) for line in lines]
                            std_dev = pd.Series(line_lens).std()
                            mean_len = pd.Series(line_lens).mean()
                            cv = std_dev / mean_len if mean_len > 0 else 1.0

                            # HEURISTIC 7: Trailing Punctuation (Sentences usually end with periods)
                            ends_with_period = sum(1 for line in lines if line.strip().endswith('.'))
                            period_ratio = ends_with_period / len(lines)

                            # Strict check: 
                            # - Avg Cell < 40 (Tables have short cells)
                            # - Chars/Delim < 15 (Tables have high delimiter density)
                            # - Consistency CV < 0.3 (Tables are very uniform)
                            # - Period Ratio < 0.5 (Tables don't usually end with periods on every row)
                            if (len(df.columns) > 1 and len(df) >= 2 and 
                                avg_cell_len < 40 and chars_per_delimiter < 20 and 
                                cv < 0.3 and period_ratio < 0.5):
                                dataframes.append(self.clean_dataframe(df))
                                break
                        except:
                            continue
        
        return dataframes
    
    def log_processing_info(self, result: ProcessingResult):
        """
        Log processing information
        
        Args:
            result: ProcessingResult to log
        """
        if result.success:
            self.logger.info(
                f"Successfully processed {result.file_path}: "
                f"{len(result.dataframes)} tables, "
                f"{result.total_rows} rows, "
                f"{result.total_columns} columns, "
                f"Time: {result.processing_time:.2f}s"
            )
        else:
            self.logger.error(
                f"Failed to process {result.file_path}: {result.error_message}"
            )
        
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(f"Warning: {warning}")