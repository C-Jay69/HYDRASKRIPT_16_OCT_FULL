import os
import logging
import aiofiles
import asyncio
from typing import Optional, Dict, Any
import tempfile
import hashlib

logger = logging.getLogger(__name__)

class AudioService:
    def __init__(self):
        # Note: Fish Audio API integration would go here
        # For now, we'll create a mock implementation that shows the structure
        self.api_key = os.environ.get('FISH_AUDIO_API_KEY')
        self.output_dir = os.environ.get('AUDIO_OUTPUT_DIR', '/app/audio_output')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Supported voices by language
        self.voice_models = {
            'en': ['english_narrator_1', 'english_narrator_2', 'english_female_1', 'english_male_1'],
            'fr': ['french_narrator_1', 'french_female_1', 'french_male_1'],
            'es': ['spanish_narrator_1', 'spanish_female_1', 'spanish_male_1'],
            'zh': ['mandarin_narrator_1', 'mandarin_female_1', 'mandarin_male_1'],
            'hi': ['hindi_narrator_1', 'hindi_female_1', 'hindi_male_1'],
            'ja': ['japanese_narrator_1', 'japanese_female_1', 'japanese_male_1']
        }
    
    def _get_voice_model(self, language: str, voice_style: str) -> str:
        """Get appropriate voice model based on language and style"""
        available_voices = self.voice_models.get(language, self.voice_models['en'])
        
        # Map voice styles to specific models
        style_mapping = {
            'neutral': 0,
            'female': 1,
            'male': 2,
            'narrator': 0
        }
        
        voice_index = style_mapping.get(voice_style, 0)
        if voice_index < len(available_voices):
            return available_voices[voice_index]
        return available_voices[0]
    
    def _chunk_text(self, text: str, max_chunk_size: int = 5000) -> list:
        """Chunk text into smaller pieces for audio generation"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def generate_audio(self, text: str, language: str = 'en', voice_style: str = 'neutral', 
                           speed: float = 1.0, project_id: str = None) -> Dict[str, Any]:
        """Generate audio from text using Fish Audio API"""
        try:
            # Get appropriate voice model
            voice_model = self._get_voice_model(language, voice_style)
            
            # Create output filename
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            filename = f"{project_id}_{text_hash}_{language}_{voice_style}.mp3"
            output_path = os.path.join(self.output_dir, filename)
            
            # For MVP - create a mock audio file
            # In production, this would use the actual Fish Audio API
            await self._create_mock_audio(text, output_path, language, voice_style, speed)
            
            # Get file stats
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            duration = len(text) * 0.06 / speed  # Rough estimate: ~60ms per character
            
            return {
                'audio_url': f'/audio/{filename}',
                'file_path': output_path,
                'duration': duration,
                'file_size': file_size,
                'language': language,
                'voice_style': voice_style,
                'speed': speed
            }
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    async def _create_mock_audio(self, text: str, output_path: str, language: str, 
                               voice_style: str, speed: float):
        """Create a mock audio file for development/testing"""
        # Create a simple text file indicating audio would be generated
        audio_info = {
            'text': text[:100] + '...' if len(text) > 100 else text,
            'language': language,
            'voice_style': voice_style,
            'speed': speed,
            'note': 'This is a mock audio file for development. In production, this would be actual audio.'
        }
        
        # Create mock audio metadata file
        mock_path = output_path.replace('.mp3', '_mock.txt')
        async with aiofiles.open(mock_path, 'w') as f:
            await f.write(str(audio_info))
        
        # Create empty audio file placeholder
        async with aiofiles.open(output_path, 'wb') as f:
            # Write minimal MP3 header (empty file)
            await f.write(b'')
    
    async def generate_audiobook(self, project_id: str, content: str, language: str = 'en',
                                voice_style: str = 'narrator', speed: float = 1.0,
                                progress_callback=None) -> Dict[str, Any]:
        """Generate complete audiobook from content"""
        try:
            # Chunk the content for processing
            chunks = self._chunk_text(content)
            total_chunks = len(chunks)
            
            audio_files = []
            total_duration = 0
            total_size = 0
            
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    await progress_callback(f"Generating audio chunk {i+1}/{total_chunks}", 
                                          int((i / total_chunks) * 100))
                
                # Generate audio for this chunk
                audio_result = await self.generate_audio(
                    text=chunk,
                    language=language,
                    voice_style=voice_style,
                    speed=speed,
                    project_id=f"{project_id}_chunk_{i}"
                )
                
                audio_files.append(audio_result)
                total_duration += audio_result['duration']
                total_size += audio_result['file_size']
                
                # Small delay to prevent overwhelming the API
                await asyncio.sleep(0.1)
            
            # In production, you might want to combine all chunks into a single file
            combined_filename = f"{project_id}_audiobook.mp3"
            combined_path = os.path.join(self.output_dir, combined_filename)
            
            # For now, just create a manifest file
            manifest = {
                'project_id': project_id,
                'total_chunks': total_chunks,
                'total_duration': total_duration,
                'total_size': total_size,
                'language': language,
                'voice_style': voice_style,
                'speed': speed,
                'audio_files': audio_files
            }
            
            async with aiofiles.open(combined_path.replace('.mp3', '_manifest.json'), 'w') as f:
                import json
                await f.write(json.dumps(manifest, indent=2))
            
            if progress_callback:
                await progress_callback("Audiobook generation completed", 100)
            
            return {
                'audiobook_url': f'/audio/{combined_filename}',
                'manifest_path': combined_path.replace('.mp3', '_manifest.json'),
                'total_duration': total_duration,
                'total_size': total_size,
                'chunks_count': total_chunks,
                'language': language,
                'voice_style': voice_style
            }
            
        except Exception as e:
            logger.error(f"Audiobook generation failed: {e}")
            raise Exception(f"Failed to generate audiobook: {str(e)}")
    
    async def get_available_voices(self, language: str = None) -> Dict[str, list]:
        """Get list of available voices"""
        if language:
            return {language: self.voice_models.get(language, [])}
        return self.voice_models
    
    async def get_voice_preview(self, voice_model: str, sample_text: str = None) -> str:
        """Generate a preview of a voice model"""
        if not sample_text:
            sample_text = "Hello, this is a preview of the selected voice model."
        
        # For MVP, return a mock preview
        return f"Preview for {voice_model}: {sample_text}"
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages for audio generation"""
        return list(self.voice_models.keys())
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ['mp3', 'wav', 'opus']
    
    async def validate_text_for_audio(self, text: str, language: str) -> Dict[str, Any]:
        """Validate text before audio generation"""
        issues = []
        
        # Check text length
        if len(text) > 100000:  # 100k characters
            issues.append("Text is very long and may take significant time to process")
        
        # Check for special characters that might cause issues
        problematic_chars = ['<', '>', '{', '}', '[', ']']
        if any(char in text for char in problematic_chars):
            issues.append("Text contains special characters that may affect audio quality")
        
        # Check language compatibility
        if language not in self.voice_models:
            issues.append(f"Language '{language}' is not supported")
        
        # Estimate processing time
        estimated_minutes = len(text) * 0.001  # Rough estimate
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'estimated_processing_time': estimated_minutes,
            'character_count': len(text),
            'word_count': len(text.split())
        }