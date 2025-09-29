import os
import json
import logging
import requests
from typing import Optional, Dict, Any, List
import asyncio
from dashscope import Generation, ImageSynthesis
import dashscope

logger = logging.getLogger(__name__)

class QwenService:
    def __init__(self):
        self.api_key = os.environ.get('DASHSCOPE_API_KEY')
        self.available = bool(self.api_key)
        
        if self.available:
            # Configure region (Singapore for international users)
            dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
            
            # Set system-wide encoding environment variables to force UTF-8
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['LC_ALL'] = 'en_US.UTF-8'
            os.environ['LANG'] = 'en_US.UTF-8'
            
            logger.info("Qwen service initialized with system-wide UTF-8 encoding")
        else:
            logger.warning("DASHSCOPE_API_KEY not found - Qwen service unavailable")
    
    def _make_ascii_safe(self, text: str) -> str:
        """Convert text to ASCII-safe version to avoid DashScope Unicode errors"""
        import unicodedata
        import re
        
        try:
            # Remove Unicode characters that cause DashScope issues
            # Replace common Unicode punctuation with ASCII equivalents
            text = text.replace('\uff0c', ',')  # Full-width comma
            text = text.replace('\u201c', '"')  # Left double quotation
            text = text.replace('\u201d', '"')  # Right double quotation
            text = text.replace('\u2018', "'")  # Left single quotation
            text = text.replace('\u2019', "'")  # Right single quotation
            text = text.replace('\u2013', '-')  # En dash
            text = text.replace('\u2014', '--') # Em dash
            
            # Normalize to remove accents and convert to ASCII
            normalized = unicodedata.normalize('NFKD', text)
            ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
            
            # Clean up any weird spacing
            ascii_safe = re.sub(r'\s+', ' ', ascii_only).strip()
            
            logger.debug(f"🔤 ASCII conversion: {len(text)} chars → {len(ascii_safe)} chars")
            return ascii_safe
            
        except Exception as e:
            logger.warning(f"ASCII conversion failed: {e}, using original text")
            return text
    
    async def generate_kids_story_text(self, prompt: str, length: str = "medium", style: str = "cheerful") -> str:
        """Generate a complete kids story with proper narrative structure"""
        if not self.available or not self.api_key:
            raise ValueError("Qwen service not available - API key not configured")
            
        try:
            # Determine word count and page count based on length
            word_counts = {
                "short": {"words": 800, "pages": 12},
                "medium": {"words": 1200, "pages": 20}, 
                "long": {"words": 1800, "pages": 25}
            }
            
            target_config = word_counts.get(length, word_counts["medium"])
            
            story_prompt = f"""Create a complete children's storybook based on this prompt: "{prompt}"

REQUIREMENTS:
- Target length: {target_config['words']} words across {target_config['pages']} pages
- Style: {style}, engaging, age-appropriate for children 4-8 years old
- Format: Complete narrative with page breaks, not just an outline
- Include: Character development, plot progression, educational elements
- Structure: Beginning, middle, end with clear story arc
- Language: Simple, engaging vocabulary suitable for young readers

STORY STRUCTURE:
- Page 1: Introduction of main character and setting
- Pages 2-4: Problem or adventure begins
- Pages 5-15: Main adventure with challenges and discoveries
- Pages 16-18: Climax and resolution
- Pages 19-20: Happy ending with lesson learned

Please write the COMPLETE story with full narrative text for each page, not just summaries or outlines. Include dialogue, descriptive scenes, and emotional moments that will engage young readers. Make it similar in quality to published children's books.

Write the story now:"""

            # UNICODE FIX: Sanitize prompt for DashScope text generation too
            ascii_safe_story_prompt = self._make_ascii_safe(story_prompt)
            
            # Use the correct DashScope Generation API with ASCII-safe prompt
            response = Generation.call(
                api_key=self.api_key,
                model="qwen-plus",
                prompt=ascii_safe_story_prompt,  # Use ASCII-safe version
                result_format='text'
            )
            
            # If the above fails, log the error and return empty to trigger fallback
            if not response or hasattr(response, 'status_code') and response.status_code != 200:
                logger.error("🚫 DashScope text generation failed, using comprehensive fallback")
                return ""
            
            # Handle the response correctly for DashScope native format
            if response.status_code == 200:
                story_text = response.output.text
                logger.info(f"Qwen generated {len(story_text)} characters")
                return story_text
            else:
                logger.error(f"Qwen text generation failed: {response.message if hasattr(response, 'message') else 'Unknown error'}")
                raise Exception(f"Failed to generate story: {response.message if hasattr(response, 'message') else 'API call failed'}")
                
        except Exception as e:
            logger.error(f"Kids story generation failed: {e}")
            raise Exception(f"Failed to generate kids story: {str(e)}")
    
    async def generate_story_illustration(self, scene_description: str, page_number: int, total_pages: int, characters: str = "") -> str:
        """Generate a single illustration for a story page"""
        if not self.available or not self.api_key:
            logger.warning("Qwen service not available for image generation")
            return ""
            
        try:
            # Use original text with proper UTF-8 encoding (no ASCII cleaning needed)
            illustration_prompt = f"""Create a vibrant, professional children's book illustration for page {page_number} of {total_pages}.

SCENE: {scene_description}
CHARACTERS: {characters}

STYLE REQUIREMENTS:
- Art Style: Disney/Pixar quality animation style
- Quality: Professional children's book illustration
- Colors: Bright, warm, inviting colors
- Mood: Happy, safe, engaging for children aged 4-8
- Composition: Clear focal point, balanced layout
- Detail Level: Rich but not overwhelming for young viewers

TECHNICAL SPECS:
- Child-safe content only
- No scary or inappropriate elements
- Include story elements that match the text
- Professional publishing quality
- Warm lighting and cheerful atmosphere

Create a beautiful, engaging illustration that brings this story scene to life."""

            # UNICODE FIX: Sanitize prompt to ASCII before DashScope call
            ascii_safe_prompt = self._make_ascii_safe(illustration_prompt)
            
            # Try DashScope ImageSynthesis with ASCII-safe prompt
            try:
                response = ImageSynthesis.call(
                    api_key=self.api_key,
                    model="wan2.5-t2i-preview",  # Available in your playground!
                    prompt=ascii_safe_prompt,  # Use ASCII-safe version
                    size="1024*1024",
                    negative_prompt="scary, dark, violent, inappropriate, low quality, blurry"
                )
            except Exception as encoding_error:
                # If still fails, log specific Unicode error and skip DashScope completely
                logger.error(f"🚫 DashScope ImageSynthesis UNICODE ERROR: {encoding_error}")
                logger.info("🔄 Bypassing DashScope due to Unicode incompatibility, returning failure to trigger OpenAI fallback")
                return ""  # Return empty to trigger OpenAI fallback in AI service
            
            if hasattr(response, 'output') and hasattr(response.output, 'results') and response.output.results:
                # Extract image URL from response
                image_url = response.output.results[0].url
                logger.info(f"Generated illustration: {image_url}")
                return image_url
            else:
                logger.error(f"Qwen image generation failed: No results in response")
                return ""
                
        except Exception as e:
            logger.error(f"Story illustration generation failed: {e}")
            return ""
    
    async def generate_complete_kids_book(self, prompt: str, genre: str = "kids_story", length: str = "medium", style: str = "cheerful") -> Dict[str, Any]:
        """Generate a complete kids book with text and illustrations"""
        try:
            # Step 1: Generate the complete story text
            logger.info(f"Generating kids story text for prompt: {prompt}")
            story_text = await self.generate_kids_story_text(prompt, length, style)
            
            # Step 2: Parse story into pages (simple approach - split by paragraphs/sections)
            story_pages = self._parse_story_into_pages(story_text)
            
            # Step 3: Generate illustrations for key pages
            logger.info(f"Generating illustrations for {len(story_pages)} story pages")
            illustrations = []
            
            # Generate illustrations for every 2-3 pages to keep it manageable
            illustration_pages = list(range(0, len(story_pages), max(1, len(story_pages) // 8)))[:8]
            
            for i, page_idx in enumerate(illustration_pages):
                if page_idx < len(story_pages):
                    page_content = story_pages[page_idx]
                    scene_description = page_content[:200] + "..." if len(page_content) > 200 else page_content
                    
                    logger.info(f"Generating illustration {i+1}/{len(illustration_pages)} for page {page_idx+1}")
                    image_url = await self.generate_story_illustration(
                        scene_description=scene_description,
                        page_number=page_idx + 1,
                        total_pages=len(story_pages),
                        characters=self._extract_characters_from_prompt(prompt)
                    )
                    
                    if image_url:
                        illustrations.append({
                            "page_number": page_idx + 1,
                            "image_url": image_url,
                            "description": scene_description
                        })
                    
                    # Small delay to respect rate limits
                    await asyncio.sleep(2)
            
            # Combine everything into the final book
            complete_book = {
                "title": self._generate_title_from_prompt(prompt),
                "story_text": story_text,
                "total_pages": len(story_pages),
                "pages": story_pages,
                "illustrations": illustrations,
                "word_count": len(story_text.split()),
                "character_count": len(story_text),
                "metadata": {
                    "genre": genre,
                    "length": length,
                    "style": style,
                    "illustration_count": len(illustrations)
                }
            }
            
            return complete_book
            
        except Exception as e:
            logger.error(f"Complete kids book generation failed: {e}")
            raise Exception(f"Failed to generate complete kids book: {str(e)}")
    
    def _parse_story_into_pages(self, story_text: str) -> List[str]:
        """Parse story text into individual pages"""
        # Simple approach: split by double newlines or page indicators
        pages = []
        
        # First try to split by obvious page breaks
        if "Page " in story_text:
            raw_pages = story_text.split("Page ")[1:]  # Skip content before first page
            for page in raw_pages:
                # Clean up page content
                page_content = page.split("\n\n")[0] if "\n\n" in page else page
                page_content = page_content.strip()
                if page_content and len(page_content) > 20:  # Minimum content length
                    pages.append(page_content)
        else:
            # Split by paragraphs and group them
            paragraphs = [p.strip() for p in story_text.split("\n\n") if p.strip()]
            
            # Group paragraphs into pages (aim for 50-100 words per page)
            current_page = ""
            for paragraph in paragraphs:
                if len(current_page.split()) + len(paragraph.split()) > 100 and current_page:
                    pages.append(current_page.strip())
                    current_page = paragraph
                else:
                    current_page += ("\n\n" + paragraph) if current_page else paragraph
            
            if current_page:
                pages.append(current_page.strip())
        
        # Ensure we have at least 10 pages for a proper kids book
        if len(pages) < 10:
            # Split longer pages or add more content
            expanded_pages = []
            for page in pages:
                if len(page.split()) > 80:
                    # Split long pages
                    sentences = page.split(". ")
                    mid_point = len(sentences) // 2
                    expanded_pages.append(". ".join(sentences[:mid_point]) + ".")
                    expanded_pages.append(". ".join(sentences[mid_point:]))
                else:
                    expanded_pages.append(page)
            pages = expanded_pages
        
        return pages[:25]  # Limit to 25 pages maximum
    
    def _extract_characters_from_prompt(self, prompt: str) -> str:
        """Extract character information from the prompt for consistent illustrations"""
        # Simple keyword extraction for characters
        character_words = ["bunny", "rabbit", "girl", "boy", "child", "princess", "prince", 
                          "cat", "dog", "bear", "mouse", "elephant", "lion", "tiger"]
        
        found_characters = []
        prompt_lower = prompt.lower()
        
        for char in character_words:
            if char in prompt_lower:
                found_characters.append(char)
        
        return ", ".join(found_characters) if found_characters else "friendly characters"
    
    def _generate_title_from_prompt(self, prompt: str) -> str:
        """Generate a simple title from the prompt"""
        # Extract key words and create a title
        words = prompt.split()[:6]  # Take first 6 words
        title = " ".join(words).title()
        
        # Add "The Adventures of" or similar if it's a character story
        if any(char in prompt.lower() for char in ["bunny", "rabbit", "girl", "boy", "cat", "dog"]):
            title = f"The Adventures of {title}"
        
        return title

# Create global instance (with error handling)
try:
    qwen_service = QwenService()
except Exception as e:
    logger.warning(f"Failed to initialize Qwen service: {e}")
    qwen_service = None
