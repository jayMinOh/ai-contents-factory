"""
AI Image Generation Service using Google Gemini Imagen API.

Supports multiple providers:
- gemini_imagen: Google Imagen 3 via Gemini API
- mock: Mock provider for testing (returns picsum images)
"""

import base64
import logging
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Optimize prompts for image generation using Gemini."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    def _is_well_formed_english_prompt(self, prompt: str) -> bool:
        """Check if prompt is already a well-formed English image generation prompt."""
        import re

        # Check for Korean characters
        korean_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f]')
        if korean_pattern.search(prompt):
            return False

        # Check for photography/image generation keywords
        photo_keywords = [
            'shot', 'photography', 'lighting', 'cinematic', 'aesthetic',
            'resolution', 'photo', 'image', 'background', 'composition',
            'portrait', 'product shot', 'commercial', 'studio', 'bokeh',
            'depth of field', 'high quality', 'professional', 'mood'
        ]
        prompt_lower = prompt.lower()
        keyword_count = sum(1 for kw in photo_keywords if kw in prompt_lower)

        # If prompt is in English and has 2+ photography keywords, it's well-formed
        return keyword_count >= 2

    async def optimize(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Optimize a prompt for image generation.
        Translates to English and converts to visual-friendly description.
        Skips optimization if prompt is already well-formed English.
        """
        import asyncio

        # Skip optimization if prompt is already well-formed English
        if self._is_well_formed_english_prompt(prompt):
            logger.info(f"Prompt already well-formed, skipping optimization: '{prompt[:50]}...'")
            return prompt

        system_instruction = """You are an expert at creating prompts for AI image generation for marketing videos.
Your task is to convert the given description into an optimal English prompt for image generation.

Rules:
1. ALWAYS output in English only
2. PRESERVE visual effects and techniques mentioned in the prompt:
   - Keep effects like "heat map", "gradient overlay", "blur effect", "glow", "neon", "particle effects"
   - Keep color effects like "red heat visualization", "blue mist", "golden highlights"
   - Keep visual techniques like "double exposure", "split screen", "before/after"
3. CRITICAL: Convert narrative/descriptive text into VISUAL elements:
   - Phrases like "문구가 등장", "텍스트 표시", "자막" describe overlays added in post-production, NOT rendered in the image
   - Abstract marketing concepts like "궁금증 유발", "기대감" should become facial expressions or body language
   - "시청자의 궁금증을 유발합니다" → describe the PERSON's intrigued expression, NOT text
4. Focus on visual elements: lighting, composition, colors, mood, style, poses, expressions
5. Convert abstract concepts to concrete visual representations:
   - "curiosity/궁금증" → "intrigued expression, raised eyebrows, leaning forward"
   - "anticipation/기대" → "excited smile, bright eyes, engaged posture"
   - "trust/신뢰" → "warm, confident smile, relaxed posture"
   - "강력한 찬사" → "person showing genuine enthusiasm, animated expression"
5. Keep the prompt concise but descriptive (50-100 words)
6. Add photography/cinematography terms for better quality
7. Do NOT include any Korean text in the output
8. IMPORTANT: If brand/product context is provided, ALWAYS include the actual product in the image
   - Use the exact product name and type (e.g., "Kerastase hair treatment bottle", "skincare serum tube")
   - Show the person holding or using the ACTUAL product, not a generic item or phone
9. Intentional text requests (logos, brand names on products) are OK - keep them
10. DO NOT describe what text should appear - instead describe the visual scene without text overlays

Example input: "Brand: Kerastase. Product: Hair Treatment.
Scene: 강력한 개인적인 찬사를 통해 시청자의 즉각적인 궁금증과 기대를 유발합니다"
Example output: "Asian woman with an excited, intrigued expression looking at a Kerastase hair treatment bottle in her hands, animated gestures showing enthusiasm, bright eyes, genuine smile, professional studio lighting, clean background, warm inviting atmosphere, beauty commercial aesthetic"

Example input: "Brand: Kerastase. Product: Hair Treatment.
Scene: 여전히 제품을 든 채 고개를 살짝 끄덕이며 '나는 재구매 의사'라는 문구가 등장"
Example output: "Asian woman holding a Kerastase hair treatment bottle, nodding approvingly with a satisfied expression, soft studio lighting, clean minimal background, product clearly visible in her hands, warm color tones, beauty commercial style, high-end cosmetic advertising aesthetic"
"""

        def _generate():
            return self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=f"Convert this to an image generation prompt:\n\n{prompt}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                    max_output_tokens=200,
                ),
            )

        try:
            response = await asyncio.to_thread(_generate)
            optimized = response.text.strip()
            logger.info(f"Prompt optimized: '{prompt[:50]}...' -> '{optimized[:50]}...'")
            return optimized
        except Exception as e:
            logger.warning(f"Prompt optimization failed: {e}, using original")
            return prompt


# Singleton instance
_prompt_optimizer: Optional[PromptOptimizer] = None


def get_prompt_optimizer() -> PromptOptimizer:
    """Get or create prompt optimizer instance."""
    global _prompt_optimizer
    if _prompt_optimizer is None:
        _prompt_optimizer = PromptOptimizer()
    return _prompt_optimizer


class ImageGeneratorBase(ABC):
    """Base class for image generators."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
    ) -> dict:
        """
        Generate an image from a prompt.

        Args:
            prompt: Text description of the image to generate
            aspect_ratio: Image aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4)
            style: Optional style modifier

        Returns:
            dict with keys:
                - image_data: Base64 encoded image data (or None if URL provided)
                - image_url: URL to the generated image (or None if data provided)
                - mime_type: MIME type of the image
                - generation_time_ms: Time taken to generate in milliseconds
        """
        pass


class GeminiImagenGenerator(ImageGeneratorBase):
    """
    Image generator using Google Gemini Imagen 3 API.

    Pricing: ~$0.03 per image
    Uses the new google-genai SDK.
    """

    # Supported aspect ratios for Imagen 3
    SUPPORTED_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]

    def __init__(self):
        logger.info("Initializing GeminiImagenGenerator...")
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not configured")
            raise ValueError("GOOGLE_API_KEY is not configured")

        logger.info(f"GOOGLE_API_KEY configured (length: {len(settings.GOOGLE_API_KEY)})")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        # Use Gemini 3 Pro Image Preview - high-quality 4K image generation
        self.model_name = "gemini-3-pro-image-preview"
        logger.info(f"GeminiImagenGenerator initialized successfully with model: {self.model_name}")

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> dict:
        import asyncio

        start_time = time.time()
        logger.info(f"Starting image generation - prompt: {prompt[:100]}..., aspect_ratio: {aspect_ratio}, style: {style}, purpose: {purpose}")

        # Validate aspect ratio
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Build enhanced prompt with photographic details for better quality
        enhanced_prompt = prompt
        if style:
            enhanced_prompt = f"{style} style: {prompt}"

        # Add quality indicators based on purpose
        if purpose == "ad":
            # For advertising: use professional photography style
            enhanced_prompt = f"{enhanced_prompt}. High-quality, professional photography, studio-grade lighting, commercial product shot."
        else:
            # For info/lifestyle: avoid photography terms to allow illustrations
            enhanced_prompt = f"{enhanced_prompt}. High-quality, high resolution, detailed, masterpiece."

        def _generate():
            return self.client.models.generate_content(
                model=self.model_name,
                contents=enhanced_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    temperature=0.8,
                ),
            )

        try:
            logger.info(f"Calling Nano Banana Pro API with enhanced_prompt: {enhanced_prompt[:100]}...")

            response = await asyncio.to_thread(_generate)
            logger.info(f"Nano Banana Pro API response received: {type(response)}")

            # Extract image from response
            image_data = None
            mime_type = "image/png"

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = base64.b64encode(part.inline_data.data).decode("utf-8")
                    mime_type = part.inline_data.mime_type or "image/png"
                    break

            if not image_data:
                logger.error("No images in response")
                raise Exception("No images generated")

            logger.info(f"Image data length: {len(image_data)}")

            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Image generation completed in {generation_time_ms}ms")

            return {
                "image_data": image_data,
                "image_url": None,
                "mime_type": mime_type,
                "generation_time_ms": generation_time_ms,
            }

        except Exception as e:
            logger.error(f"Nano Banana Pro generation failed: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Image generation failed: {str(e)}")


class MockImageGenerator(ImageGeneratorBase):
    """Mock image generator for testing (returns picsum placeholder images)."""

    async def generate(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
    ) -> dict:
        import asyncio

        start_time = time.time()

        # Simulate generation delay
        await asyncio.sleep(1)

        # Calculate dimensions based on aspect ratio
        width, height = 800, 450  # Default 16:9
        if aspect_ratio == "9:16":
            width, height = 450, 800
        elif aspect_ratio == "1:1":
            width, height = 600, 600
        elif aspect_ratio == "4:3":
            width, height = 800, 600
        elif aspect_ratio == "3:4":
            width, height = 600, 800

        # Generate unique seed for variety
        seed = uuid.uuid4().hex[:8]
        image_url = f"https://picsum.photos/seed/{seed}/{width}/{height}"

        generation_time_ms = int((time.time() - start_time) * 1000)

        return {
            "image_data": None,
            "image_url": image_url,
            "mime_type": "image/jpeg",
            "generation_time_ms": generation_time_ms,
        }


class ImageGeneratorFactory:
    """Factory for creating image generators."""

    _generators: dict[str, type[ImageGeneratorBase]] = {
        "gemini_imagen": GeminiImagenGenerator,
        "mock": MockImageGenerator,
    }

    @classmethod
    def create(cls, provider: str) -> ImageGeneratorBase:
        """Create an image generator for the specified provider."""
        if provider not in cls._generators:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._generators.keys())}")

        return cls._generators[provider]()

    @classmethod
    def available_providers(cls) -> list[str]:
        """Get list of available providers."""
        return list(cls._generators.keys())


# Singleton instances for reuse
_generator_instances: dict[str, ImageGeneratorBase] = {}


def get_image_generator(provider: str = "mock") -> ImageGeneratorBase:
    """Get or create an image generator instance."""
    if provider not in _generator_instances:
        _generator_instances[provider] = ImageGeneratorFactory.create(provider)
    return _generator_instances[provider]


__all__ = [
    "ImageGeneratorBase",
    "GeminiImagenGenerator",
    "MockImageGenerator",
    "ImageGeneratorFactory",
    "get_image_generator",
    "PromptOptimizer",
    "get_prompt_optimizer",
]
