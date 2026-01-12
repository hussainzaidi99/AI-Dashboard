"""
Excel Processor - Extract data from Excel files (.xlsx, .xls)
Supports multiple sheets, formulas, and formatting
"""
#backend/app/core/processors/excel_processor.py


import time
from typing import List, Optional, Dict, Any
import pandas as pd
import logging

from .base import BaseProcessor, ProcessingResult
from app.config import settings

logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """Process Excel files and extract data from all sheets"""
    
    def __init__(self):
        super().__init__()
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process Excel file and extract all sheets
        
        Args:
            file_path: Path to Excel file
            **kwargs:
                - sheet_name: str or int or list (default: None = all sheets)
                - header: int or None (default: 0)
                - skiprows: int (default: 0)
                - usecols: str or list (columns to use)
        
        Returns:
            ProcessingResult with extracted data
        """
        start_time = time.time()
        
        try:
            # Validate file
            self.validate_file(file_path)
            
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            
            # Extract options
            sheet_name = kwargs.get('sheet_name')
            header = kwargs.get('header', 0)
            skiprows = kwargs.get('skiprows', 0)
            usecols = kwargs.get('usecols')
            
            # Determine Excel engine based on file extension
            engine = 'openpyxl' if file_path.endswith('.xlsx') or file_path.endswith('.xlsm') else 'xlrd'
            
            # Read Excel file
            dataframes = []
            sheet_names = []
            warnings = []
            
            if engine == 'xlrd' and not file_path.endswith('.xls'):
                warnings.append(f"Using xlrd engine for unknown extension. This may fail on modern Excel files.")
            
            try:
                # Read all sheets or specific sheet
                excel_data = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    header=header,
                    skiprows=skiprows,
                    usecols=usecols,
                    engine=engine
                )
                
                # Handle single sheet vs multiple sheets
                if isinstance(excel_data, dict):
                    # Multiple sheets
                    for sheet, df in excel_data.items():
                        if not df.empty:
                            cleaned_df = self.clean_dataframe(df)
                            dataframes.append(cleaned_df)
                            sheet_names.append(str(sheet))
                else:
                    # Single sheet
                    if not excel_data.empty:
                        cleaned_df = self.clean_dataframe(excel_data)
                        dataframes.append(cleaned_df)
                        sheet_names.append(
                            str(sheet_name) if sheet_name else "Sheet1"
                        )
                
                # Get additional metadata using openpyxl
                if file_path.endswith('.xlsx'):
                    excel_metadata = self._extract_excel_metadata(file_path)
                    metadata.update(excel_metadata)
            
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc().splitlines()[-1]
                self.logger.error(f"Error reading Excel file: {str(e)}")
                warnings.append(f"Error reading sheets: {error_detail}")
                
                if engine == 'xlrd' and "Excel 2007" in str(e):
                    warnings.append("Note: xlrd only supports old .xls files. For .xlsx, openpyxl is required.")
            
            if not dataframes:
                raise ValueError("No data could be extracted from Excel file")
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                file_type='excel',
                dataframes=dataframes,
                metadata=metadata,
                processing_time=time.time() - start_time,
                warnings=warnings,
                sheet_names=sheet_names
            )
            
            self.log_processing_info(result)
            return result
        
        except Exception as e:
            self.logger.error(f"Error processing Excel {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                file_path=file_path,
                file_type='excel',
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _extract_excel_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from Excel file using openpyxl
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        try:
            from openpyxl import load_workbook
            
            # Load workbook (read-only for performance)
            wb = load_workbook(file_path, read_only=True, data_only=True)
            
            # Get sheet information
            metadata['sheet_count'] = len(wb.sheetnames)
            metadata['sheet_names'] = wb.sheetnames
            
            # Get workbook properties
            props = wb.properties
            if props:
                metadata['created'] = str(props.created) if props.created else None
                metadata['modified'] = str(props.modified) if props.modified else None
                metadata['creator'] = props.creator
                metadata['last_modified_by'] = props.lastModifiedBy
                metadata['title'] = props.title
                metadata['subject'] = props.subject
            
            wb.close()
        
        except Exception as e:
            self.logger.warning(f"Could not extract Excel metadata: {str(e)}")
        
        return metadata
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get all sheet names from Excel file
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            List of sheet names
        """
        try:
            engine = 'openpyxl' if file_path.endswith('.xlsx') else 'xlrd'
            excel_file = pd.ExcelFile(file_path, engine=engine)
            return excel_file.sheet_names
        except Exception as e:
            self.logger.error(f"Error getting sheet names: {str(e)}")
            return []
    
    def process_specific_sheet(
        self,
        file_path: str,
        sheet_name: str
    ) -> ProcessingResult:
        """
        Process only a specific sheet from Excel file
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of the sheet to process
        
        Returns:
            ProcessingResult with single sheet data
        """
        return self.process(file_path, sheet_name=sheet_name)
    
    def process_with_formulas(self, file_path: str) -> Dict[str, Any]:
        """
        Process Excel file and extract formulas (not just values)
        
        Args:
            file_path: Path to Excel file
        
        Returns:
            Dictionary with sheet data including formulas
        """
        try:
            from openpyxl import load_workbook
            
            wb = load_workbook(file_path, data_only=False)
            
            sheets_data = {}
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                
                sheet_info = {
                    'data': [],
                    'formulas': {},
                    'dimensions': ws.dimensions
                }
                
                # Extract data and formulas
                for row_idx, row in enumerate(ws.iter_rows(values_only=False), 1):
                    row_data = []
                    for col_idx, cell in enumerate(row, 1):
                        row_data.append(cell.value)
                        
                        # Check if cell has a formula
                        if cell.data_type == 'f':
                            cell_coord = f"{chr(64 + col_idx)}{row_idx}"
                            sheet_info['formulas'][cell_coord] = cell.value
                    
                    sheet_info['data'].append(row_data)
                
                sheets_data[sheet_name] = sheet_info
            
            wb.close()
            return sheets_data
        
        except Exception as e:
            self.logger.error(f"Error extracting formulas: {str(e)}")
            return {}
    
    def detect_data_range(self, file_path: str, sheet_name: str = None) -> Dict[str, Any]:
        """
        Detect the actual data range in Excel sheet (skip empty rows/cols)
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name (optional)
        
        Returns:
            Dictionary with data range information
        """
        try:
            from openpyxl import load_workbook
            
            wb = load_workbook(file_path, read_only=True)
            sheet = wb[sheet_name] if sheet_name else wb.active
            
            # Get dimensions
            min_row = sheet.min_row
            max_row = sheet.max_row
            min_col = sheet.min_column
            max_col = sheet.max_column
            
            # Find actual data range (skip empty leading rows/cols)
            actual_min_row = min_row
            actual_min_col = min_col
            
            # Find actual min row
            for row_idx in range(min_row, max_row + 1):
                row_cells = [sheet.cell(row=row_idx, column=c).value for c in range(min_col, max_col + 1)]
                if any(v is not None for v in row_cells):
                    actual_min_row = row_idx
                    break
            
            # Find actual min column
            for col_idx in range(min_col, max_col + 1):
                col_cells = [sheet.cell(row=r, column=col_idx).value for r in range(min_row, max_row + 1)]
                if any(v is not None for v in col_cells):
                    actual_min_col = col_idx
                    break
            
            wb.close()
            
            return {
                'min_row': actual_min_row,
                'max_row': max_row,
                'min_col': actual_min_col,
                'max_col': max_col,
                'total_rows': max_row - actual_min_row + 1,
                'total_cols': max_col - actual_min_col + 1
            }
        
        except Exception as e:
            self.logger.error(f"Error detecting data range: {str(e)}")
            return {}