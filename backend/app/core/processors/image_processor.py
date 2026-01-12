"""
Image Processor - Extract text from images using OCR (Tesseract)
Supports PNG, JPG, JPEG formats
"""
#backend/app/core/processors/image_processor.py

import time
from typing import List, Dict, Any, Optional
import pandas as pd
from PIL import Image
import logging

from .base import BaseProcessor, ProcessingResult
from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessor(BaseProcessor):
    """Process images and extract text using OCR"""
    
    def __init__(self):
        super().__init__()
        self.max_size = settings.IMAGE_MAX_SIZE
        
        # Set tesseract path if configured
        self.tesseract_available = False
        if settings.TESSERACT_PATH:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
                # Quick check if tesseract is actually responsive
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except Exception as e:
                self.logger.warning(f"Tesseract not found at {settings.TESSERACT_PATH}: {str(e)}")
        else:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except:
                self.logger.warning("Tesseract not found in PATH. OCR will be disabled.")
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Process image file and extract text using OCR
        
        Args:
            file_path: Path to image file
            **kwargs:
                - language: str (default: 'eng') - Tesseract language
                - preprocess: bool (default: True) - Apply preprocessing
                - extract_tables: bool (default: True) - Try to extract tables
                - psm: int (default: 3) - Page segmentation mode
        
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
            language = kwargs.get('language', 'eng')
            preprocess = kwargs.get('preprocess', True)
            extract_tables = kwargs.get('extract_tables', True)
            psm = kwargs.get('psm', 3)
            
            # Load and preprocess image
            image = Image.open(file_path)
            
            # Get image info
            image_info = self._get_image_info(image)
            metadata.update(image_info)
            
            # Resize if too large
            if preprocess:
                image = self._preprocess_image(image)
            
            # Extract text using OCR
            text_content = self._extract_text_ocr(image, language, psm)
            
            warnings = []
            dataframes = []
            
            # Try to extract tables if requested
            if extract_tables and text_content:
                tables = self._extract_tables_from_text(text_content)
                if tables:
                    dataframes.extend(tables)
                else:
                    warnings.append("No tables could be extracted from OCR text")
            
            # Check OCR confidence
            confidence = self._get_ocr_confidence(image, language)
            metadata['ocr_confidence'] = confidence
            
            if confidence < 60:
                warnings.append(
                    f"Low OCR confidence ({confidence}%). "
                    "Consider using a higher quality image."
                )
            
            # Create result
            result = ProcessingResult(
                success=True,
                file_path=file_path,
                file_type='image',
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
            self.logger.error(f"Error processing image {file_path}: {str(e)}")
            return ProcessingResult(
                success=False,
                file_path=file_path,
                file_type='image',
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract image information
        
        Args:
            image: PIL Image object
        
        Returns:
            Dictionary with image metadata
        """
        return {
            'width': image.width,
            'height': image.height,
            'format': image.format,
            'mode': image.mode,
            'dpi': image.info.get('dpi', (72, 72))
        }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        
        Args:
            image: PIL Image object
        
        Returns:
            Preprocessed image
        """
        # Resize if too large
        if image.width > self.max_size[0] or image.height > self.max_size[1]:
            self.logger.info(f"Resizing image from {image.size}")
            image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Convert to grayscale for better OCR
        image = image.convert('L')
        
        # Apply threshold to make text more clear
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        return image
    
    def _extract_text_ocr(
        self,
        image: Image.Image,
        language: str,
        psm: int
    ) -> str:
        """
        Extract text using Tesseract OCR
        
        Args:
            image: PIL Image object
            language: Tesseract language code
            psm: Page segmentation mode
        
        Returns:
            Extracted text
        """
        if not self.tesseract_available:
            raise RuntimeError("Tesseract OCR is not installed or not in PATH.")
            
        import pytesseract
        
        # Configure Tesseract
        config = f'--psm {psm}'
        
        # Extract text
        text = pytesseract.image_to_string(
            image,
            lang=language,
            config=config
        )
        
        return text.strip()
    
    def _get_ocr_confidence(self, image: Image.Image, language: str) -> float:
        """
        Get OCR confidence score
        
        Args:
            image: PIL Image object
            language: Tesseract language code
        
        Returns:
            Average confidence score (0-100)
        """
        try:
            import pytesseract
            
            # Get detailed data with confidence scores
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence (excluding -1 values)
            confidences = [
                float(conf) for conf in data['conf'] 
                if conf != -1 and conf != '-1' and conf is not None
            ]
            
            if confidences:
                return sum(confidences) / len(confidences)
            return 0.0
        
        except Exception as e:
            self.logger.warning(f"Could not get OCR confidence: {str(e)}")
            return 0.0
    
    def _extract_tables_from_text(self, text: str) -> List[pd.DataFrame]:
        """
        Try to extract tables from OCR text
        
        Args:
            text: Extracted text
        
        Returns:
            List of DataFrames
        """
        # Use the base class method
        return self.extract_tables_from_text(text)
    
    def extract_with_layout(
        self,
        file_path: str,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Extract text while preserving layout information
        
        Args:
            file_path: Path to image file
            language: Tesseract language code
        
        Returns:
            Dictionary with text and layout data
        """
        try:
            import pytesseract
            
            image = Image.open(file_path)
            
            # Preprocess
            image = self._preprocess_image(image)
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT
            )
            
            # Organize by blocks
            blocks = {}
            for i in range(len(data['text'])):
                if data['text'][i].strip():
                    block_num = data['block_num'][i]
                    
                    if block_num not in blocks:
                        blocks[block_num] = {
                            'text': [],
                            'positions': [],
                            'confidence': []
                        }
                    
                    blocks[block_num]['text'].append(data['text'][i])
                    blocks[block_num]['positions'].append({
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    })
                    blocks[block_num]['confidence'].append(data['conf'][i])
            
            return {
                'blocks': blocks,
                'full_text': '\n'.join(data['text']),
                'total_blocks': len(blocks)
            }
        
        except Exception as e:
            self.logger.error(f"Layout extraction failed: {str(e)}")
            return {}
    
    def detect_orientation(self, file_path: str) -> Dict[str, Any]:
        """
        Detect image orientation and rotation angle
        
        Args:
            file_path: Path to image file
        
        Returns:
            Dictionary with orientation info
        """
        try:
            import pytesseract
            
            image = Image.open(file_path)
            
            # Get orientation and script detection
            osd = pytesseract.image_to_osd(image)
            
            # Parse OSD output
            orientation_info = {}
            for line in osd.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    orientation_info[key.strip()] = value.strip()
            
            return orientation_info
        
        except Exception as e:
            self.logger.error(f"Orientation detection failed: {str(e)}")
            return {}
    
    def auto_rotate(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Auto-rotate image based on detected orientation
        
        Args:
            file_path: Path to image file
            output_path: Path to save rotated image (optional)
        
        Returns:
            Path to rotated image
        """
        try:
            orientation_info = self.detect_orientation(file_path)
            angle = float(orientation_info.get('Rotate', 0))
            
            if angle != 0:
                image = Image.open(file_path)
                rotated = image.rotate(-angle, expand=True)
                
                save_path = output_path or file_path
                rotated.save(save_path)
                
                self.logger.info(f"Rotated image by {angle} degrees")
                return save_path
            
            return file_path
        
        except Exception as e:
            self.logger.error(f"Auto-rotation failed: {str(e)}")
            return file_path