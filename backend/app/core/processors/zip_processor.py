"""
Zip Processor - Handles .zip file extraction and recursive processing
"""
import os
import zipfile
import tempfile
import shutil
import logging
from typing import List, Dict, Any, Optional

from .base import BaseProcessor, ProcessingResult


class ZipProcessor(BaseProcessor):
    """
    Processor for .zip files.
    Extracts the archive and processes valid files within it.
    Resulting dataframes are aggregated.
    """
    
    def process(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        Extract zip file and process compatible contained files
        """
        self.logger.info(f"Processing zip file: {file_path}")
        
        # Initialize result
        result = ProcessingResult(
            success=False,
            file_path=file_path,
            file_type="zip"
        )
        
        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 1. Extract zip file
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Security check: Don't extract if too many files (Zip bomb protection)
                    file_list = zip_ref.namelist()
                    if len(file_list) > 50:
                        raise ValueError(f"Zip contains too many files ({len(file_list)}). Max 50 allowed.")
                    
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile:
                result.error_message = "Invalid or corrupted zip file"
                return result
            except Exception as e:
                result.error_message = f"Error extracting zip: {str(e)}"
                return result
            
            # 2. Iterate through extracted files
            processed_files_count = 0
            
            # Lazy import to avoid circular dependency
            # We need to import the factory function here because __init__ imports this module
            from . import get_processor
            
            for root, dirs, files in os.walk(temp_dir):
                # Skip invisible folders and __MACOSX
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__MACOSX']
                
                for filename in files:
                    # Skip hidden files
                    if filename.startswith('.'):
                        continue
                        
                    file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
                    full_path = os.path.join(root, filename)
                    
                    # Skip the zip file itself if it somehow got in there (unlikely in temp dir)
                    if full_path == file_path:
                        continue
                        
                    try:
                        # Attempt to get a processor for this file type
                        try:
                            processor = get_processor(file_ext)
                        except ValueError:
                            # Unsupported file type
                            continue
                            
                        # Process the file
                        sub_result = processor.process(full_path)
                        
                        if sub_result.success:
                            processed_files_count += 1
                            
                            # Aggregate Dataframes
                            # Rename sheets to include filename context if multiple files
                            for i, df in enumerate(sub_result.dataframes):
                                # If sheet name is generic (Sheet_1), prefix with filename
                                # If we have multiple files, we definitely want to distinguish them
                                sheet_name = sub_result.sheet_names[i]
                                
                                # Clean filename for sheet name (remove ext)
                                clean_filename = os.path.splitext(filename)[0]
                                new_sheet_name = f"{clean_filename} - {sheet_name}"
                                
                                result.dataframes.append(df)
                                result.sheet_names.append(new_sheet_name)
                                
                            # Aggregate Text Content
                            if sub_result.text_content:
                                header = f"\n\n--- Content from {filename} ---\n\n"
                                if result.text_content:
                                    result.text_content += header + sub_result.text_content
                                else:
                                    result.text_content = header.strip() + sub_result.text_content
                            
                            # Aggregate Metadata?
                            # Maybe just keep a list of processed files in metadata
                            processed_list = result.metadata.get("processed_files", [])
                            processed_list.append(filename)
                            result.metadata["processed_files"] = processed_list
                            
                        else:
                            result.warnings.append(f"Failed to process {filename}: {sub_result.error_message}")
                            
                    except Exception as e:
                        result.warnings.append(f"Error processing {filename}: {str(e)}")
            
            if processed_files_count == 0:
                result.error_message = "No valid processing targets found in zip file"
                return result
            
            result.success = True
            self.log_processing_info(result)
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in ZipProcessor: {str(e)}")
            result.error_message = f"System error processing zip: {str(e)}"
            return result
            
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
