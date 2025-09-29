import os
import logging
import aiofiles
from typing import Optional, Dict, Any
import tempfile
import shutil
from pathlib import Path
import mimetypes

# Document processing libraries
import PyPDF2
from docx import Document
import mammoth

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = os.environ.get('UPLOAD_DIR', '/tmp/uploads')
        self.max_file_size = int(os.environ.get('MAX_FILE_SIZE_MB', '25')) * 1024 * 1024  # Convert to bytes
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Supported file types
        self.supported_types = {
            'text/plain': ['.txt'],
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/msword': ['.doc']
        }
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Save uploaded file and return file info"""
        try:
            # Validate file size
            if len(file_content) > self.max_file_size:
                raise Exception(f"File size exceeds maximum allowed size of {self.max_file_size // (1024*1024)}MB")
            
            # Validate file type
            if not self._is_supported_type(content_type, filename):
                raise Exception(f"File type not supported. Supported types: TXT, PDF, DOCX")
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(filename)
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Extract text content
            extracted_text = await self.extract_text_from_file(file_path, content_type)
            
            return {
                'success': True,
                'filename': safe_filename,
                'original_filename': filename,
                'file_path': file_path,
                'file_size': len(file_content),
                'content_type': content_type,
                'extracted_text': extracted_text,
                'word_count': len(extracted_text.split()) if extracted_text else 0
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_supported_type(self, content_type: str, filename: str) -> bool:
        """Check if file type is supported"""
        # Check by content type
        if content_type in self.supported_types:
            return True
        
        # Check by file extension
        file_ext = Path(filename).suffix.lower()
        for supported_exts in self.supported_types.values():
            if file_ext in supported_exts:
                return True
        
        return False
    
    def _generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename"""
        import uuid
        import time
        
        # Get file extension
        file_ext = Path(filename).suffix.lower()
        
        # Generate unique filename
        timestamp = str(int(time.time()))
        unique_id = str(uuid.uuid4())[:8]
        safe_name = f"{timestamp}_{unique_id}{file_ext}"
        
        return safe_name
    
    async def extract_text_from_file(self, file_path: str, content_type: str) -> str:
        """Extract text content from uploaded file"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.txt' or content_type == 'text/plain':
                return await self._extract_from_txt(file_path)
            elif file_ext == '.pdf' or content_type == 'application/pdf':
                return await self._extract_from_pdf(file_path)
            elif file_ext == '.docx' or content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return await self._extract_from_docx(file_path)
            elif file_ext == '.doc' or content_type == 'application/msword':
                return await self._extract_from_doc(file_path)
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return f"Error extracting text: {str(e)}"
    
    async def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except UnicodeDecodeError:
            # Try different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                        content = await f.read()
                    return content
                except:
                    continue
            raise Exception("Could not decode text file")
    
    async def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return f"Error extracting PDF content: {str(e)}"
    
    async def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            # Use mammoth for better formatting preservation
            with open(file_path, "rb") as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                
            if result.messages:
                logger.warning(f"DOCX extraction warnings: {result.messages}")
            
            return result.value
            
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            # Fallback to python-docx
            try:
                doc = Document(file_path)
                text_content = []
                
                for paragraph in doc.paragraphs:
                    text_content.append(paragraph.text)
                
                return '\n\n'.join(text_content)
                
            except Exception as e2:
                logger.error(f"DOCX fallback extraction failed: {e2}")
                return f"Error extracting DOCX content: {str(e)}"
    
    async def _extract_from_doc(self, file_path: str) -> str:
        """Extract text from legacy DOC file"""
        try:
            # For legacy DOC files, we'd need additional libraries like python-docx2txt
            # For now, return an error message suggesting conversion
            return "Legacy DOC files are not supported. Please convert to DOCX format."
            
        except Exception as e:
            logger.error(f"DOC extraction failed: {e}")
            return f"Error extracting DOC content: {str(e)}"
    
    async def delete_file(self, filename: str) -> bool:
        """Delete uploaded file"""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
            
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    async def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about uploaded file"""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            content_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'filename': filename,
                'file_path': file_path,
                'file_size': stat.st_size,
                'content_type': content_type,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
            
        except Exception as e:
            logger.error(f"Getting file info failed: {e}")
            return None
    
    def get_supported_types(self) -> Dict[str, Any]:
        """Get list of supported file types"""
        return {
            'mime_types': list(self.supported_types.keys()),
            'extensions': [ext for exts in self.supported_types.values() for ext in exts],
            'max_file_size_mb': self.max_file_size // (1024 * 1024),
            'description': 'Supported formats: TXT (plain text), PDF (Portable Document Format), DOCX (Microsoft Word Document)'
        }
    
    def cleanup_old_files(self, days_old: int = 7) -> int:
        """Clean up files older than specified days"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            removed_count = 0
            
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"Removed old file: {filename}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def validate_text_content(self, content: str) -> Dict[str, Any]:
        """Validate extracted text content"""
        validation_result = {
            'valid': True,
            'issues': [],
            'stats': {
                'character_count': len(content),
                'word_count': len(content.split()),
                'paragraph_count': len(content.split('\n\n')),
                'line_count': len(content.split('\n'))
            }
        }
        
        # Check if content is too short
        if len(content.strip()) < 100:
            validation_result['issues'].append("Content appears to be very short (less than 100 characters)")
        
        # Check if content is mostly non-text characters
        alpha_chars = sum(1 for c in content if c.isalpha())
        if alpha_chars / max(len(content), 1) < 0.5:
            validation_result['issues'].append("Content appears to contain mostly non-text characters")
        
        # Check for reasonable word count
        word_count = validation_result['stats']['word_count']
        if word_count < 10:
            validation_result['issues'].append("Content has very few words, may not be suitable for book generation")
        
        # Set validity based on issues
        validation_result['valid'] = len(validation_result['issues']) == 0
        
        return validation_result
    
    def get_supported_types(self):
        """Get supported file types for API"""
        return {
            "mime_types": list(self.supported_types.keys()),
            "extensions": [ext for exts in self.supported_types.values() for ext in exts],
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "description": "Supported formats: TXT, PDF, DOCX"
        }