#backend/app/core/processors/pdf_processor.py

import time
from typing import List, Optional
import pandas as pd
import logging

from .base import BaseProcessor, ProcessingResult
from app.config import settings

logger = logging.getLogger(__name__)


class PDFProcessor(BaseProcessor):
    """Process PDF files and extract text and tables"""
    
    def __init__(self):
        super().__init__()
        self.max_pages = settings.PDF_MAX_PAGES
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process PDF file and extract content
        
        Args:
            file_path: Path to PDF file
            **kwargs:
                - extract_text: bool (default: True)
                - extract_tables: bool (default: True)
                - pages: List[int] or None (specific pages to process)
        
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
            extract_text = kwargs.get('extract_text', True)
            extract_tables = kwargs.get('extract_tables', True)
            specific_pages = kwargs.get('pages')
            
            # Extract content
            text_content = ""
            dataframes = []
            warnings = []
            
            if extract_text:
                text_content = self._extract_text_with_pdfplumber(
                    file_path, specific_pages
                )
            
            if extract_tables:
                # Try pdfplumber first
                tables = self._extract_tables_with_pdfplumber(
                    file_path, specific_pages
                )
                
                if not tables:
                    # Fallback to tabula
                    self.logger.info("No tables found with pdfplumber, trying tabula...")
                    tables = self._extract_tables_with_tabula(
                        file_path, specific_pages
                    )
                
                # Clean and add tables
                for table_data in tables:
                    try:
                        # Handle both dictionary (pdfplumber/updated tabula) and raw DataFrame (old tabula)
                        if isinstance(table_data, dict):
                            table_df = table_data.get('df')
                            page_num = table_data.get('page', 'Unknown')
                        else:
                            table_df = table_data
                            page_num = 'Unknown'

                        if table_df is not None and not table_df.empty:
                            cleaned_df = self.clean_dataframe(table_df)
                            dataframes.append(cleaned_df)
                            metadata[f'table_{len(dataframes)}_location'] = f"Page {page_num}"
                    except Exception as table_err:
                        self.logger.warning(f"Error cleaning table: {str(table_err)}")
                        continue
            
            # Check if we hit page limit
            if specific_pages is None:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
                    metadata['total_pages'] = total_pages
                    
                    if total_pages > self.max_pages:
                        warnings.append(
                            f"PDF has {total_pages} pages, but only first "
                            f"{self.max_pages} were processed (limit)"
                        )
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                file_type='pdf',
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
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                file_path=file_path,
                file_type='pdf',
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _extract_text_with_pdfplumber(
        self,
        file_path: str,
        pages: Optional[List[int]] = None
    ) -> str:
        """
        Extract text using pdfplumber
        
        Args:
            file_path: Path to PDF
            pages: Specific pages to extract (None = all pages)
        
        Returns:
            Extracted text content
        """
        try:
            import pdfplumber
            
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = pages if pages else range(min(total_pages, self.max_pages))
                
                for page_num in pages_to_process:
                    if page_num < total_pages:
                        page = pdf.pages[page_num]
                        text = page.extract_text()
                        if text:
                            text_content.append(f"--- Page {page_num + 1} ---\n{text}\n")
            
            return "\n".join(text_content)
        
        except Exception as e:
            self.logger.error(f"Error extracting text with pdfplumber: {str(e)}")
            return ""
    
    def _extract_tables_with_pdfplumber(
        self,
        file_path: str,
        pages: Optional[List[int]] = None
    ) -> List[pd.DataFrame]:
        """
        Extract tables using pdfplumber
        
        Args:
            file_path: Path to PDF
            pages: Specific pages to extract
        
        Returns:
            List of DataFrames containing tables
        """
        try:
            import pdfplumber
            
            dataframes = []
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_process = pages if pages else range(min(total_pages, self.max_pages))
                
                for page_num in pages_to_process:
                    if page_num < total_pages:
                        page = pdf.pages[page_num]
                        extracted_tables = page.extract_tables()
                        
                        for table in extracted_tables:
                            if table and len(table) > 1:
                                # Convert to DataFrame
                                df = pd.DataFrame(table[1:], columns=table[0])
                                dataframes.append({
                                    'df': df,
                                    'page': page_num + 1
                                })
            
            return dataframes
        
        except Exception as e:
            self.logger.error(f"Error extracting tables with pdfplumber: {str(e)}")
            return []
    
    def _extract_tables_with_tabula(
        self,
        file_path: str,
        pages: Optional[List[int]] = None
    ) -> List[pd.DataFrame]:
        """
        Extract tables using tabula-py (fallback method)
        
        Args:
            file_path: Path to PDF
            pages: Specific pages to extract
        
        Returns:
            List of DataFrames containing tables
        """
        try:
            import tabula
            
            # Get actual page count to avoid "Page number does not exist" error
            total_pages = 0
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    total_pages = len(pdf_reader.pages)
            except Exception as e:
                self.logger.warning(f"Could not get page count for tabula: {e}")
            
            # Convert page numbers to tabula format (1-indexed, comma-separated)
            if pages:
                pages_str = ','.join(str(p + 1) for p in pages)
            else:
                effective_max = min(total_pages, self.max_pages) if total_pages > 0 else self.max_pages
                pages_str = f'1-{effective_max}'
            
            # Extract tables
            raw_dfs = tabula.read_pdf(
                file_path,
                pages=pages_str,
                multiple_tables=True,
                silent=True
            )
            
            # Format to match pdfplumber's return (list of dicts)
            formatted_tables = []
            if raw_dfs:
                for df in raw_dfs:
                    formatted_tables.append({
                        'df': df,
                        'page': 'Multiple/Unknown' # Tabula doesn't easily map back to single pages in bulk
                    })
            
            return formatted_tables
        
        except Exception as e:
            msg = str(e)
            if "java" in msg.lower() or "jpype" in msg.lower():
                self.logger.warning(f"Tabula requires Java JRE/JDK which was not found: {msg}")
                return []
            self.logger.error(f"Error extracting tables with tabula: {msg}")
            return []
    
    def extract_specific_pages(
        self,
        file_path: str,
        page_numbers: List[int]
    ) -> ProcessingResult:
        """
        Extract content from specific pages only
        
        Args:
            file_path: Path to PDF
            page_numbers: List of page numbers (0-indexed)
        
        Returns:
            ProcessingResult
        """
        return self.process(file_path, pages=page_numbers)
    
    def get_page_count(self, file_path: str) -> int:
        """
        Get total number of pages in PDF
        
        Args:
            file_path: Path to PDF
        
        Returns:
            Number of pages
        """
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                return len(pdf_reader.pages)
        except Exception as e:
            self.logger.error(f"Error getting page count: {str(e)}")
            return 0