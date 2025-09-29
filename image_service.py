import os
import logging
import asyncio
import fal_client
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.api_key = os.environ.get('FAL_KEY')
        if self.api_key:
            os.environ["FAL_KEY"] = self.api_key
        
        # Cover art styles by genre
        self.genre_styles = {
            'ebook': {
                'professional': 'Clean, modern, professional design with elegant typography',
                'minimalist': 'Simple, clean design with minimal elements and plenty of white space',
                'technical': 'Technical diagrams, charts, or industry-specific imagery'
            },
            'novel': {
                'dramatic': 'Dramatic scenes with rich colors and emotional depth',
                'mysterious': 'Dark, atmospheric imagery with intriguing elements',
                'romantic': 'Soft, warm colors with romantic elements and elegant design',
                'adventure': 'Dynamic, action-packed imagery with bold compositions'
            },
            'kids_story': {
                'cartoon': 'Bright, colorful cartoon-style illustrations with friendly characters',
                'watercolor': 'Soft watercolor style with gentle, dreamy aesthetics',
                'digital_art': 'Modern digital art with vibrant colors and playful elements',
                'storybook': 'Classic storybook illustration style with warm, inviting imagery'
            },
            'coloring_book': {
                'line_art': 'Clean black and white line art suitable for coloring',
                'mandala': 'Intricate mandala patterns with geometric designs',
                'nature': 'Natural elements like flowers, animals, and landscapes in line art',
                'geometric': 'Geometric patterns and shapes in clean line art style'
            }
        }
    
    def _build_cover_prompt(self, title: str, genre: str, description: str, style: str) -> str:
        """Build optimized prompt for cover art generation"""
        
        # Get style description
        style_desc = self.genre_styles.get(genre, {}).get(style, 'professional and eye-catching')
        
        # Genre-specific prompt additions
        genre_additions = {
            'ebook': 'book cover design, professional layout, readable title placement',
            'novel': 'book cover design, compelling imagery that hints at the story',
            'kids_story': 'children\'s book cover, bright and engaging, child-friendly',
            'coloring_book': 'coloring book cover design, indicates the content inside'
        }
        
        genre_context = genre_additions.get(genre, 'book cover design')
        
        prompt = f"""Create a {genre_context} for a book titled "{title}".

Description: {description}

Style requirements: {style_desc}

Additional requirements:
- High quality, professional appearance
- Suitable for both print and digital formats
- Eye-catching and genre-appropriate
- Leave space for title text overlay
- 6:9 aspect ratio (typical book cover proportions)
"""
        
        return prompt
    
    def _build_kids_story_illustration_prompt(self, scene_description: str, style: str = 'cartoon') -> str:
        """Build prompt for kids story illustrations"""
        style_descriptions = {
            'cartoon': 'Disney/Pixar style cartoon illustration, bright colors, friendly characters',
            'watercolor': 'Soft watercolor illustration style, gentle and dreamy',
            'digital_art': 'Modern digital art style, vibrant and playful',
            'storybook': 'Classic children\'s storybook illustration style'
        }
        
        style_desc = style_descriptions.get(style, style_descriptions['cartoon'])
        
        prompt = f"""{style_desc}

Scene: {scene_description}

Requirements:
- Child-friendly and appropriate
- Bright, engaging colors
- Clear, simple composition
- High quality illustration
- Suitable for children's book
"""
        
        return prompt
    
    def _build_coloring_page_prompt(self, subject: str, style: str = 'line_art') -> str:
        """Build prompt for coloring book pages"""
        style_descriptions = {
            'line_art': 'Clean black and white line art, perfect for coloring',
            'mandala': 'Intricate mandala design with geometric patterns',
            'nature': 'Nature-themed line art with organic shapes',
            'geometric': 'Geometric patterns and abstract designs'
        }
        
        style_desc = style_descriptions.get(style, style_descriptions['line_art'])
        
        prompt = f"""{style_desc}

Subject: {subject}

Requirements:
- Black outlines on white background
- No filled areas or shading
- Clear, bold lines suitable for coloring
- Appropriate detail level for coloring
- Clean, printable design
"""
        
        return prompt
    
    async def generate_cover_art(self, title: str, genre: str, description: str, 
                                style: str = 'professional') -> Dict[str, Any]:
        """Generate book cover art using Flux API"""
        try:
            if not self.api_key:
                raise Exception("FAL_KEY not configured")
            
            # Build optimized prompt
            prompt = self._build_cover_prompt(title, genre, description, style)
            
            # Submit request to fal.ai
            handler = await fal_client.submit_async(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                    "image_size": "portrait_4_3",  # Good for book covers
                    "num_inference_steps": 50,
                    "guidance_scale": 7.5,
                    "num_images": 1
                }
            )
            
            # Get result
            result = await handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                image_url = result['images'][0]['url']
                
                return {
                    'success': True,
                    'image_url': image_url,
                    'prompt_used': prompt,
                    'style': style,
                    'genre': genre
                }
            else:
                raise Exception("No images generated")
                
        except Exception as e:
            logger.error(f"Cover art generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'prompt_used': prompt if 'prompt' in locals() else None
            }
    
    async def generate_kids_story_illustrations(self, scenes: list, style: str = 'cartoon') -> list:
        """Generate multiple illustrations for kids story book"""
        illustrations = []
        
        for i, scene in enumerate(scenes):
            try:
                if not self.api_key:
                    # Mock illustration for development
                    illustrations.append({
                        'scene_number': i + 1,
                        'scene_description': scene,
                        'image_url': f'/mock-illustration-{i+1}.jpg',
                        'success': True,
                        'style': style
                    })
                    continue
                
                # Build prompt for this scene
                prompt = self._build_kids_story_illustration_prompt(scene, style)
                
                # Generate illustration
                handler = await fal_client.submit_async(
                    "fal-ai/flux/dev",
                    arguments={
                        "prompt": prompt,
                        "image_size": "landscape_4_3",
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5,
                        "num_images": 1
                    }
                )
                
                result = await handler.get()
                
                if result and 'images' in result and len(result['images']) > 0:
                    illustrations.append({
                        'scene_number': i + 1,
                        'scene_description': scene,
                        'image_url': result['images'][0]['url'],
                        'success': True,
                        'style': style
                    })
                else:
                    illustrations.append({
                        'scene_number': i + 1,
                        'scene_description': scene,
                        'image_url': None,
                        'success': False,
                        'error': 'No image generated',
                        'style': style
                    })
                
                # Small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Illustration generation failed for scene {i+1}: {e}")
                illustrations.append({
                    'scene_number': i + 1,
                    'scene_description': scene,
                    'image_url': None,
                    'success': False,
                    'error': str(e),
                    'style': style
                })
        
        return illustrations
    
    async def generate_coloring_pages(self, subjects: list, style: str = 'line_art') -> list:
        """Generate coloring book pages"""
        pages = []
        
        for i, subject in enumerate(subjects):
            try:
                if not self.api_key:
                    # Mock coloring page for development
                    pages.append({
                        'page_number': i + 1,
                        'subject': subject,
                        'image_url': f'/mock-coloring-page-{i+1}.jpg',
                        'success': True,
                        'style': style
                    })
                    continue
                
                # Build prompt for coloring page
                prompt = self._build_coloring_page_prompt(subject, style)
                
                # Generate coloring page
                handler = await fal_client.submit_async(
                    "fal-ai/flux/dev",
                    arguments={
                        "prompt": prompt,
                        "image_size": "square",
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5,
                        "num_images": 1
                    }
                )
                
                result = await handler.get()
                
                if result and 'images' in result and len(result['images']) > 0:
                    pages.append({
                        'page_number': i + 1,
                        'subject': subject,
                        'image_url': result['images'][0]['url'],
                        'success': True,
                        'style': style
                    })
                else:
                    pages.append({
                        'page_number': i + 1,
                        'subject': subject,
                        'image_url': None,
                        'success': False,
                        'error': 'No image generated',
                        'style': style
                    })
                
                # Small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Coloring page generation failed for subject {i+1}: {e}")
                pages.append({
                    'page_number': i + 1,
                    'subject': subject,
                    'image_url': None,
                    'success': False,
                    'error': str(e),
                    'style': style
                })
        
        return pages
    
    async def get_genre_styles(self, genre: str = None) -> Dict[str, Any]:
        """Get available styles for a genre"""
        if genre:
            return self.genre_styles.get(genre, {})
        return self.genre_styles
    
    def is_configured(self) -> bool:
        """Check if image service is properly configured"""
        return bool(self.api_key)
