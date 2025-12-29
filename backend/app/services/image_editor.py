"""
Image Editing Service using Google Gemini API.

Uses Gemini 2.5 Flash's multimodal capabilities to edit images
while preserving the original product appearance.
"""

import asyncio
import base64
import io
import logging
import time
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiImageEditor:
    """
    Edit images using Gemini 2.5 Flash multimodal capabilities.

    This allows editing an existing image (e.g., a product image) while
    preserving its visual identity and placing it in new contexts.
    """

    # Supported aspect ratios
    SUPPORTED_ASPECT_RATIOS = ["1:1", "3:4", "4:3", "9:16", "16:9"]

    def __init__(self):
        logger.info("Initializing GeminiImageEditor...")
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not configured")
            raise ValueError("GOOGLE_API_KEY is not configured")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        # Use Gemini 3 Pro Image Preview - high-quality 4K image generation
        self.model_name = "gemini-3-pro-image-preview"
        logger.info(f"GeminiImageEditor initialized with model: {self.model_name}")

    async def edit_with_product(
        self,
        product_image_data: bytes = None,
        product_mime_type: str = None,
        edit_prompt: str = "",
        aspect_ratio: str = "16:9",
        product_description: Optional[str] = None,
        images_data: Optional[list] = None,  # List of (bytes, mime_type) tuples
    ) -> dict:
        """
        Edit/generate an image while preserving the product appearance.

        Args:
            product_image_data: Raw bytes of the product image (legacy, single image)
            product_mime_type: MIME type of the product image (legacy)
            edit_prompt: Description of the desired scene/context
            aspect_ratio: Output image aspect ratio
            product_description: Optional text description of the product
            images_data: List of (bytes, mime_type) tuples for multiple images

        Returns:
            dict with keys:
                - image_data: Base64 encoded image data
                - mime_type: MIME type of the generated image
                - generation_time_ms: Time taken in milliseconds
        """
        start_time = time.time()
        logger.info(f"Starting image edit - prompt: {edit_prompt[:100]}..., aspect_ratio: {aspect_ratio}")

        # Validate aspect ratio
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Build contents list: prompt first, then all images
        contents = [edit_prompt]

        # Handle multiple images (new approach)
        if images_data:
            logger.info(f"Processing {len(images_data)} images")
            for img_bytes, img_mime in images_data:
                pil_image = Image.open(io.BytesIO(img_bytes))
                contents.append(pil_image)
        # Fallback to single image (legacy)
        elif product_image_data:
            pil_image = Image.open(io.BytesIO(product_image_data))
            contents.append(pil_image)

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
            logger.info("Calling Gemini API for image generation...")
            response = await asyncio.to_thread(_generate)

            # Extract the generated image from response
            image_data = None
            mime_type = "image/png"

            for part in response.parts:
                if part.inline_data is not None:
                    # Get raw image data from inline_data
                    raw_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"

                    # raw_data is already bytes, encode to base64
                    if isinstance(raw_data, bytes):
                        image_data = base64.b64encode(raw_data).decode("utf-8")
                    else:
                        # If it's already a string (base64), use as-is
                        image_data = raw_data
                    break

            if not image_data:
                logger.error("No image in response")
                raise Exception("No image generated in response")

            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Image edit completed in {generation_time_ms}ms")

            return {
                "image_data": image_data,
                "mime_type": mime_type,
                "generation_time_ms": generation_time_ms,
            }

        except Exception as e:
            logger.error(f"Image edit failed: {str(e)}")
            raise Exception(f"Image edit failed: {str(e)}")

    async def compose_scene(
        self,
        product_image_data: bytes,
        product_mime_type: str,
        background_image_data: Optional[bytes] = None,
        background_mime_type: Optional[str] = None,
        scene_prompt: str = "",
        aspect_ratio: str = "16:9",
        product_description: Optional[str] = None,
    ) -> dict:
        """
        Compose a scene with product on a background.

        Args:
            product_image_data: Raw bytes of the product image
            product_mime_type: MIME type of the product image
            background_image_data: Optional raw bytes of background image
            background_mime_type: MIME type of background image
            scene_prompt: Description of how to compose the scene
            aspect_ratio: Output image aspect ratio
            product_description: Optional text description of the product

        Returns:
            dict with image_data, mime_type, generation_time_ms
        """
        start_time = time.time()
        logger.info(f"Starting scene composition - prompt: {scene_prompt[:100]}...")

        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            aspect_ratio = "16:9"

        # Convert bytes to PIL Image (official pattern for image preservation)
        product_pil = Image.open(io.BytesIO(product_image_data))

        # Build contents list - prompt first, then images (official pattern)
        contents = [scene_prompt, product_pil]

        # Add background image if provided
        if background_image_data and background_mime_type:
            background_pil = Image.open(io.BytesIO(background_image_data))
            contents.append(background_pil)

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

            # Extract the generated image from response
            image_data = None
            mime_type = "image/png"

            for part in response.parts:
                if part.inline_data is not None:
                    # Get raw image data from inline_data
                    raw_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/png"

                    # raw_data is already bytes, encode to base64
                    if isinstance(raw_data, bytes):
                        image_data = base64.b64encode(raw_data).decode("utf-8")
                    else:
                        # If it's already a string (base64), use as-is
                        image_data = raw_data
                    break

            if not image_data:
                raise Exception("No image generated in response")

            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Scene composition completed in {generation_time_ms}ms")

            return {
                "image_data": image_data,
                "mime_type": mime_type,
                "generation_time_ms": generation_time_ms,
            }

        except Exception as e:
            logger.error(f"Scene composition failed: {str(e)}")
            raise Exception(f"Scene composition failed: {str(e)}")


# Singleton instance
_editor: Optional[GeminiImageEditor] = None


def get_image_editor() -> GeminiImageEditor:
    """Get or create the image editor instance."""
    global _editor
    if _editor is None:
        _editor = GeminiImageEditor()
    return _editor


__all__ = [
    "GeminiImageEditor",
    "get_image_editor",
]
