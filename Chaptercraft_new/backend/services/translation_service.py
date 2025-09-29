import os
import logging
import deepl
from typing import Optional, Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.api_key = os.environ.get('DEEPL_AUTH_KEY')
        self.translator = None
        
        if self.api_key:
            try:
                self.translator = deepl.Translator(self.api_key)
            except Exception as e:
                logger.warning(f"DeepL translator initialization failed: {e}")
        
        # Language mappings
        self.supported_languages = {
            'en': 'EN',
            'fr': 'FR', 
            'es': 'ES',
            'zh': 'ZH',
            'ja': 'JA'
            # Note: Hindi not supported by DeepL
        }
        
        self.language_names = {
            'en': 'English',
            'fr': 'French',
            'es': 'Spanish', 
            'zh': 'Chinese (Mandarin)',
            'hi': 'Hindi',
            'ja': 'Japanese'
        }
    
    async def translate_text(self, text: str, target_language: str, 
                           source_language: Optional[str] = None) -> Dict[str, Any]:
        """Translate text to target language"""
        try:
            if not self.translator:
                return await self._mock_translation(text, target_language, source_language)
            
            # Handle Hindi separately since DeepL doesn't support it
            if target_language == 'hi':
                return await self._handle_hindi_translation(text, source_language)
            
            # Convert language codes to DeepL format
            target_lang = self.supported_languages.get(target_language, target_language.upper())
            source_lang = self.supported_languages.get(source_language) if source_language else None
            
            # Perform translation
            result = self.translator.translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang
            )
            
            return {
                'success': True,
                'original_text': text,
                'translated_text': result.text,
                'source_language': result.detected_source_language.lower(),
                'target_language': target_language,
                'confidence': 0.95,  # DeepL typically has high confidence
                'service': 'deepl'
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return await self._mock_translation(text, target_language, source_language)
    
    async def _handle_hindi_translation(self, text: str, source_language: Optional[str]) -> Dict[str, Any]:
        """Handle Hindi translation (not supported by DeepL)"""
        logger.warning("Hindi translation requested but not supported by DeepL")
        
        # For MVP, return a mock translation
        return {
            'success': False,
            'original_text': text,
            'translated_text': text,  # Return original text
            'source_language': source_language or 'auto',
            'target_language': 'hi',
            'confidence': 0.0,
            'error': 'Hindi translation not available. DeepL does not support Hindi.',
            'service': 'mock'
        }
    
    async def _mock_translation(self, text: str, target_language: str, 
                              source_language: Optional[str]) -> Dict[str, Any]:
        """Provide mock translation for development/fallback"""
        logger.info(f"Using mock translation service for {target_language}")
        
        # Simple mock translations for common phrases
        mock_translations = {
            'fr': {
                'hello': 'bonjour',
                'world': 'monde',
                'book': 'livre',
                'story': 'histoire',
                'chapter': 'chapitre'
            },
            'es': {
                'hello': 'hola',
                'world': 'mundo', 
                'book': 'libro',
                'story': 'historia',
                'chapter': 'capítulo'
            },
            'zh': {
                'hello': '你好',
                'world': '世界',
                'book': '书',
                'story': '故事',
                'chapter': '章节'
            },
            'ja': {
                'hello': 'こんにちは',
                'world': '世界',
                'book': '本',
                'story': '物語', 
                'chapter': '章'
            },
            'hi': {
                'hello': 'नमस्ते',
                'world': 'दुनिया',
                'book': 'किताब',
                'story': 'कहानी',
                'chapter': 'अध्याय'
            }
        }
        
        # Attempt simple word replacement for demo
        translated_text = text.lower()
        if target_language in mock_translations:
            for en_word, translated_word in mock_translations[target_language].items():
                translated_text = translated_text.replace(en_word, translated_word)
        
        return {
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_language or 'en',
            'target_language': target_language,
            'confidence': 0.5,  # Low confidence for mock
            'service': 'mock',
            'note': 'This is a mock translation for development purposes'
        }
    
    async def translate_book_content(self, content: str, target_language: str,
                                   source_language: Optional[str] = None,
                                   progress_callback=None) -> Dict[str, Any]:
        """Translate entire book content with progress tracking"""
        try:
            # Chunk content for translation
            chunks = self._chunk_content(content)
            total_chunks = len(chunks)
            
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    await progress_callback(f"Translating chunk {i+1}/{total_chunks}", 
                                          int((i / total_chunks) * 100))
                
                # Translate chunk
                result = await self.translate_text(chunk, target_language, source_language)
                
                if result['success']:
                    translated_chunks.append(result['translated_text'])
                else:
                    translated_chunks.append(chunk)  # Keep original if translation fails
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            
            # Combine translated chunks
            translated_content = '\n\n'.join(translated_chunks)
            
            if progress_callback:
                await progress_callback("Translation completed", 100)
            
            return {
                'success': True,
                'original_content': content,
                'translated_content': translated_content,
                'source_language': source_language or 'auto',
                'target_language': target_language,
                'chunks_processed': total_chunks,
                'service': 'deepl' if self.translator else 'mock'
            }
            
        except Exception as e:
            logger.error(f"Book content translation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'original_content': content,
                'translated_content': content  # Return original on failure
            }
    
    def _chunk_content(self, content: str, max_chunk_size: int = 4000) -> List[str]:
        """Chunk content for translation while preserving structure"""
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ''
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += '\n\n' + paragraph
                else:
                    current_chunk = paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of text"""
        try:
            # Simple language detection using character patterns
            # In production, you might use langdetect or similar
            
            # Check for common patterns
            if any(char in text for char in '你好世界中文'):
                return {'language': 'zh', 'confidence': 0.9}
            elif any(char in text for char in 'こんにちは日本語'):
                return {'language': 'ja', 'confidence': 0.9}
            elif any(char in text for char in 'नमस्ते हिंदी'):
                return {'language': 'hi', 'confidence': 0.9}
            elif any(word in text.lower() for word in ['le', 'la', 'des', 'français']):
                return {'language': 'fr', 'confidence': 0.7}
            elif any(word in text.lower() for word in ['el', 'la', 'los', 'español']):
                return {'language': 'es', 'confidence': 0.7}
            else:
                return {'language': 'en', 'confidence': 0.8}  # Default to English
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {'language': 'en', 'confidence': 0.5}
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.language_names
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.language_names
    
    def is_configured(self) -> bool:
        """Check if translation service is properly configured"""
        return bool(self.api_key and self.translator)
    
    async def get_usage_info(self) -> Dict[str, Any]:
        """Get translation service usage information"""
        try:
            if not self.translator:
                return {'configured': False, 'usage': None}
            
            usage = self.translator.get_usage()
            return {
                'configured': True,
                'character_count': usage.character.count,
                'character_limit': usage.character.limit,
                'character_remaining': usage.character.limit - usage.character.count if usage.character.limit else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage info: {e}")
            return {'configured': False, 'error': str(e)}