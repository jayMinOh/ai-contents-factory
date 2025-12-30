"""
Image Composite Generator using Google Gemini API.

This module provides functionality to generate composite images by combining
product images with backgrounds using Google Imagen 3 through Gemini API.
It handles product-background composition and natural integration.
"""

import asyncio
import base64
import io
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict

from google import genai
from google.genai import types
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CompositeConfig:
    """Configuration for composite image generation."""

    output_aspect_ratio: str = "16:9"
    """Output image aspect ratio: 1:1, 3:4, 4:3, 9:16, 16:9."""

    quality_level: str = "professional"
    """Quality level: standard, professional, premium."""

    preserve_product_quality: bool = True
    """Whether to preserve product image quality in composite."""

    use_realistic_shadows: bool = True
    """Whether to use realistic shadow and lighting integration."""


@dataclass
class CompositeRequest:
    """Request structure for composite generation."""

    product_prompt: Optional[str] = None
    """Prompt for product image generation."""

    background_prompt: Optional[str] = None
    """Prompt for background image generation."""

    product_image: Optional[bytes] = None
    """Pre-generated product image data (if available)."""

    background_image: Optional[bytes] = None
    """Pre-generated background image data (if available)."""

    composition_prompt: Optional[str] = None
    """Specific composition instructions."""

    output_aspect_ratio: Optional[str] = None
    """Override output aspect ratio for this request."""


class CompositeImageGenerator:
    """
    Generates composite images by combining product and background images.

    Uses Google Gemini API (Imagen 3) to create natural-looking composites
    where product images are integrated into background scenes with proper
    lighting, shadows, and positioning.
    """

    # Supported aspect ratios for Imagen 3
    SUPPORTED_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]

    # Composition quality instructions
    COMPOSITION_INSTRUCTIONS: Dict[str, str] = {
        "standard": "Composite the product onto the background naturally with basic integration.",
        "professional": "Professional product composite with realistic shadows, lighting, and integration.",
        "premium": "Premium luxury composite with perfect lighting integration, realistic shadows, and cinematic quality.",
    }

    def __init__(self, config: Optional[CompositeConfig] = None):
        """
        Initialize the CompositeImageGenerator.

        Args:
            config: Optional CompositeConfig for customizing generation.

        Raises:
            ValueError: If GOOGLE_API_KEY is not configured.
        """
        self.config = config or CompositeConfig()

        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not configured")
            raise ValueError("GOOGLE_API_KEY is not configured")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        # Use Gemini 3 Pro Image Preview - high-quality 4K image generation
        self.model_name = "gemini-3-pro-image-preview"
        logger.info("CompositeImageGenerator initialized successfully")

    async def generate_composite(
        self,
        product_prompt: Optional[str] = None,
        background_prompt: Optional[str] = None,
        product_image: Optional[bytes] = None,
        background_image: Optional[bytes] = None,
        composition_prompt: Optional[str] = None,
        output_aspect_ratio: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate a composite image combining product and background.

        Args:
            product_prompt: Prompt for product image (if not providing product_image).
            background_prompt: Prompt for background image (if not providing background_image).
            product_image: Pre-generated product image data.
            background_image: Pre-generated background image data.
            composition_prompt: Custom composition instructions.
            output_aspect_ratio: Override output aspect ratio.

        Returns:
            Dictionary with keys:
                - image_data: Base64 encoded image data
                - mime_type: MIME type of image
                - composite_time_ms: Generation time in milliseconds
        """
        start_time = time.time()

        # Validate and set aspect ratio
        aspect_ratio = output_aspect_ratio or self.config.output_aspect_ratio
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, using 16:9")
            aspect_ratio = "16:9"

        # Build composition instruction
        if composition_prompt is None:
            composition_prompt = self._build_composition_prompt(
                product_prompt,
                background_prompt,
            )

        logger.info(f"Generating composite - prompt: {composition_prompt[:100]}...")

        # Call API to generate composite
        try:
            result = await self._generate_with_gemini(
                composition_prompt,
                aspect_ratio,
                [product_image, background_image] if product_image or background_image else None,
            )

            composite_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Composite generated in {composite_time_ms}ms")

            return {
                "image_data": result["image_data"],
                "mime_type": result.get("mime_type", "image/png"),
                "composite_time_ms": composite_time_ms,
            }

        except Exception as e:
            logger.error(f"Composite generation failed: {str(e)}")
            raise

    async def compose_with_background(
        self,
        product_image: bytes,
        background_image: Optional[bytes] = None,
        composition_prompt: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Compose product image onto background image.

        Args:
            product_image: Product image bytes.
            background_image: Background image bytes.
            composition_prompt: Custom composition instructions.
            aspect_ratio: Output aspect ratio.

        Returns:
            Dictionary with image_data, mime_type, composite_time_ms.
        """
        start_time = time.time()

        if not composition_prompt:
            composition_prompt = (
                "Composite the product onto the background naturally with proper lighting "
                "and shadow integration, maintaining realistic appearance."
            )

        aspect_ratio = aspect_ratio or self.config.output_aspect_ratio

        try:
            logger.info(f"Composing product with background...")

            result = await self._generate_with_gemini(
                composition_prompt,
                aspect_ratio,
                [product_image, background_image] if background_image else [product_image],
            )

            composite_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Composition completed in {composite_time_ms}ms")

            return {
                "image_data": result["image_data"],
                "mime_type": result.get("mime_type", "image/png"),
                "composite_time_ms": composite_time_ms,
            }

        except Exception as e:
            logger.error(f"Composition failed: {str(e)}")
            raise

    async def generate_background(
        self,
        background_prompt: str,
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Generate background image from prompt.

        Args:
            background_prompt: Description of desired background.
            aspect_ratio: Output aspect ratio.

        Returns:
            Dictionary with image_data, mime_type, generation_time_ms.
        """
        start_time = time.time()

        aspect_ratio = aspect_ratio or self.config.output_aspect_ratio

        logger.info(f"Generating background - prompt: {background_prompt[:100]}...")

        try:
            result = await self._generate_with_gemini(
                background_prompt,
                aspect_ratio,
                None,
            )

            gen_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Background generated in {gen_time_ms}ms")

            return {
                "image_data": result["image_data"],
                "mime_type": result.get("mime_type", "image/png"),
                "generation_time_ms": gen_time_ms,
            }

        except Exception as e:
            logger.error(f"Background generation failed: {str(e)}")
            raise

    def _build_composition_prompt(
        self,
        product_prompt: Optional[str],
        background_prompt: Optional[str],
    ) -> str:
        """Build a composition prompt from product and background prompts."""
        parts = []

        if product_prompt:
            parts.append(f"Product: {product_prompt}")

        if background_prompt:
            parts.append(f"Background: {background_prompt}")

        # Add composition instruction based on quality level
        quality = self.config.quality_level.lower()
        if quality in self.COMPOSITION_INSTRUCTIONS:
            parts.append(self.COMPOSITION_INSTRUCTIONS[quality])
        else:
            parts.append(self.COMPOSITION_INSTRUCTIONS["professional"])

        # Add quality directives
        if self.config.preserve_product_quality:
            parts.append("Preserve product image quality and details.")

        if self.config.use_realistic_shadows:
            parts.append("Use realistic shadows and lighting integration.")

        return " ".join(parts)

    async def _generate_with_gemini(
        self,
        prompt: str,
        aspect_ratio: str,
        images: Optional[list] = None,
    ) -> Dict[str, str]:
        """
        Call Gemini API to generate or edit image.

        Args:
            prompt: Generation prompt.
            aspect_ratio: Output aspect ratio.
            images: Optional list of image bytes to include.

        Returns:
            Dictionary with image_data and mime_type.
        """
        # Build contents list
        contents = [prompt]

        # Add images if provided
        if images:
            for img_data in images:
                if img_data:
                    try:
                        pil_image = Image.open(io.BytesIO(img_data))
                        contents.append(pil_image)
                    except Exception as e:
                        logger.warning(f"Could not process image data: {e}")

        def _generate():
            return self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size="2K",
                    ),
                ),
            )

        try:
            response = await asyncio.to_thread(_generate)

            # Extract image from response
            image_data = None
            mime_type = "image/png"

            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    raw_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"

                    if isinstance(raw_data, bytes):
                        # Check if raw_data is actual binary or base64-encoded bytes
                        # JPEG starts with FF D8 FF, PNG starts with 89 50 4E 47
                        if raw_data[:2] == b'\xff\xd8' or raw_data[:4] == b'\x89PNG':
                            # Actual binary image data
                            image_data = base64.b64encode(raw_data).decode("utf-8")
                        else:
                            # Likely base64 string as bytes, decode to string
                            image_data = raw_data.decode("utf-8")
                    else:
                        image_data = raw_data

                    break

            if not image_data:
                raise Exception("No image generated in response")

            logger.debug(f"Image generated successfully, mime_type: {mime_type}")

            return {
                "image_data": image_data,
                "mime_type": mime_type,
            }

        except Exception as e:
            logger.error(f"Gemini API call failed: {str(e)}")
            raise

    async def _call_gemini_api(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        images: Optional[list] = None,
    ) -> bytes:
        """
        Internal method to call Gemini API (for mocking in tests).

        Args:
            prompt: Generation prompt.
            aspect_ratio: Output aspect ratio.
            images: Optional list of image bytes.

        Returns:
            Image data as bytes.
        """
        result = await self._generate_with_gemini(prompt, aspect_ratio, images)
        return base64.b64decode(result["image_data"])


# Singleton instance
_generator: Optional[CompositeImageGenerator] = None


def get_composite_generator() -> CompositeImageGenerator:
    """Get or create composite generator instance."""
    global _generator
    if _generator is None:
        _generator = CompositeImageGenerator()
    return _generator


def create_composite_generator(
    config: Optional[CompositeConfig] = None,
) -> CompositeImageGenerator:
    """
    Factory function to create a CompositeImageGenerator.

    Args:
        config: Optional custom configuration.

    Returns:
        Configured CompositeImageGenerator instance.
    """
    return CompositeImageGenerator(config=config)


__all__ = [
    "CompositeImageGenerator",
    "CompositeConfig",
    "CompositeRequest",
    "get_composite_generator",
    "create_composite_generator",
]
