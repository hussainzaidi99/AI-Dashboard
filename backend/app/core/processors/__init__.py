"""
Data Processors Module
Handles parsing and extraction from various file formats
"""
#backend/app/core/processors/__init__.py

from .base import BaseProcessor, ProcessingResult
from .pdf_processor import PDFProcessor
from .excel_processor import ExcelProcessor
from .csv_processor import CSVProcessor
from .docx_processor import DOCXProcessor
from .image_processor import ImageProcessor
from .text_processor import TextProcessor

__all__ = [
    "BaseProcessor",
    "ProcessingResult",
    "PDFProcessor",
    "ExcelProcessor",
    "CSVProcessor",
    "DOCXProcessor",
    "ImageProcessor",
    "TextProcessor",
]


# Factory function to get appropriate processor
def get_processor(file_extension: str) -> BaseProcessor:
    """
    Factory function to get the appropriate processor for a file type
    
    Args:
        file_extension: File extension (without dot) e.g., 'pdf', 'xlsx'
    
    Returns:
        Appropriate processor instance
    
    Raises:
        ValueError: If file extension is not supported
    """
    extension = file_extension.lower().strip().lstrip('.')
    
    processor_map = {
        'pdf': PDFProcessor,
        'xlsx': ExcelProcessor,
        'xlsm': ExcelProcessor,
        'xls': ExcelProcessor,
        'csv': CSVProcessor,
        'txt': TextProcessor,
        'tsv': CSVProcessor,
        'docx': DOCXProcessor,
        'doc': DOCXProcessor,
        'png': ImageProcessor,
        'jpg': ImageProcessor,
        'jpeg': ImageProcessor,
        'webp': ImageProcessor,
    }
    
    processor_class = processor_map.get(extension)
    
    if processor_class is None:
        raise ValueError(
            f"Unsupported file extension: {extension}. "
            f"Supported formats: {', '.join(processor_map.keys())}"
        )
    
    return processor_class()