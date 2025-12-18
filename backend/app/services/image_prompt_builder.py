"""
Image Generation Prompt Builder for Product Marketing.

This module provides the ImagePromptBuilder class that constructs optimized prompts
for AI image generation (Google Imagen 3) for product marketing and advertising.

The builder creates visual, detailed prompts from product information, brand context,
and scene specifications, optimized for high-quality image generation.
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationConfig:
    """Configuration for image prompt generation."""

    max_words: int = 80
    """Maximum words in generated prompt (optimal for Imagen: 50-100)."""

    include_lighting: bool = True
    """Include lighting descriptions in prompt."""

    include_style: bool = True
    """Include style information in prompt."""

    quality_level: str = "professional"
    """Quality level: 'standard', 'professional', 'premium'."""

    aspect_ratio: str = "16:9"
    """Default aspect ratio for images."""


class ImagePromptBuilder:
    """
    Builds optimized prompts for AI image generation (Imagen 3).

    Transforms product information, brand context, and scene specifications
    into detailed visual prompts suitable for high-quality image generation.
    """

    # Lighting descriptions by quality level
    LIGHTING_STYLES: Dict[str, List[str]] = {
        "standard": [
            "clear lighting",
            "bright daylight",
            "neutral lighting",
        ],
        "professional": [
            "professional studio lighting",
            "soft key lighting",
            "balanced three-point lighting",
            "studio-quality illumination",
        ],
        "premium": [
            "cinematic lighting",
            "luxury product photography lighting",
            "artfully diffused studio lighting",
            "professional commercial photography lighting",
        ],
    }

    # Style descriptors by mood
    MOOD_STYLES: Dict[str, str] = {
        "premium": "luxury, high-end, sophisticated",
        "elegant": "refined, graceful, elegant",
        "casual": "relaxed, casual, approachable",
        "professional": "professional, corporate, business",
        "dynamic": "energetic, vibrant, dynamic",
        "minimalist": "minimal, clean, simple",
        "artistic": "artistic, creative, aesthetic",
        "commercial": "commercial, advertising, marketing",
    }

    # Photography style descriptors
    PHOTOGRAPHY_STYLES: Dict[str, str] = {
        "product": "product photography, clean background, centered focus",
        "lifestyle": "lifestyle photography, natural setting, authentic moment",
        "beauty": "beauty photography, cosmetics advertising, glamour",
        "fashion": "fashion photography, editorial, high-fashion",
        "food": "food photography, appetizing, culinary",
        "tech": "technology product photography, sleek, modern",
        "home": "interior design, home decor, lifestyle",
    }

    def __init__(self, config: Optional[ImageGenerationConfig] = None):
        """
        Initialize the ImagePromptBuilder.

        Args:
            config: Optional ImageGenerationConfig for customizing prompt generation.
        """
        self.config = config or ImageGenerationConfig()

    def build_prompt(
        self,
        product_name: str,
        product_type: str,
        brand_name: Optional[str] = None,
        brand_context: Optional[str] = None,
        scene_description: Optional[str] = None,
        mood: Optional[str] = None,
        style: Optional[str] = None,
        primary_color: Optional[str] = None,
        color_emphasis: bool = False,
        aspect_ratio: Optional[str] = None,
    ) -> str:
        """
        Build an optimized prompt for image generation.

        Args:
            product_name: Name of the product.
            product_type: Type/category of the product.
            brand_name: Optional brand name.
            brand_context: Optional brand story or context.
            scene_description: Optional description of the scene.
            mood: Optional mood descriptor (premium, elegant, casual, etc.).
            style: Optional style specification (product, lifestyle, beauty, etc.).
            primary_color: Optional primary color of the product.
            color_emphasis: Whether to emphasize color in the prompt.
            aspect_ratio: Optional aspect ratio for the image.

        Returns:
            Optimized prompt string for image generation.
        """
        prompt_parts: List[str] = []

        # Build product description
        product_desc = self._build_product_description(
            product_name,
            product_type,
            brand_name,
            primary_color,
            color_emphasis,
        )
        prompt_parts.append(product_desc)

        # Add scene description if provided
        if scene_description:
            scene_part = self._normalize_text(scene_description)
            if scene_part:
                prompt_parts.append(scene_part)

        # Add brand context if provided
        if brand_context:
            context_part = self._normalize_text(brand_context)
            if context_part:
                prompt_parts.append(context_part)

        # Add mood and style
        if mood or style:
            style_part = self._build_style_description(mood, style)
            if style_part:
                prompt_parts.append(style_part)

        # Add lighting if configured
        if self.config.include_lighting:
            lighting = self._get_lighting_description()
            prompt_parts.append(lighting)

        # Add quality/finish description
        quality_desc = self._get_quality_description(self.config.quality_level)
        prompt_parts.append(quality_desc)

        # Combine all parts
        full_prompt = ", ".join(prompt_parts)

        # Truncate to max words
        final_prompt = self._truncate_to_word_limit(
            full_prompt,
            self.config.max_words,
        )

        logger.debug(f"Built prompt: {final_prompt[:100]}...")
        return final_prompt

    def build_batch_prompts(
        self,
        products: List[Dict[str, str]],
        brand_context: Optional[str] = None,
        shared_scene: Optional[str] = None,
    ) -> List[str]:
        """
        Build prompts for multiple products.

        Args:
            products: List of product dictionaries with keys: product_name, product_type, etc.
            brand_context: Optional shared brand context for all products.
            shared_scene: Optional shared scene description for all products.

        Returns:
            List of optimized prompts for each product.
        """
        prompts = []

        for product in products:
            prompt = self.build_prompt(
                product_name=product.get("product_name", ""),
                product_type=product.get("product_type", ""),
                brand_name=product.get("brand_name"),
                brand_context=brand_context or product.get("brand_context"),
                scene_description=shared_scene or product.get("scene_description"),
                mood=product.get("mood"),
                style=product.get("style"),
                primary_color=product.get("primary_color"),
                color_emphasis=product.get("color_emphasis", False),
                aspect_ratio=product.get("aspect_ratio"),
            )
            prompts.append(prompt)

        return prompts

    def _build_product_description(
        self,
        product_name: str,
        product_type: str,
        brand_name: Optional[str] = None,
        primary_color: Optional[str] = None,
        color_emphasis: bool = False,
    ) -> str:
        """Build the product description part of the prompt."""
        parts = []

        # Include brand if specified
        if brand_name:
            parts.append(brand_name)

        # Add product name
        parts.append(product_name)

        # Add color if emphasizing
        if color_emphasis and primary_color:
            parts.append(f"{primary_color}")

        # Add product type
        if product_type and product_type.lower() not in product_name.lower():
            parts.append(f"({product_type})")

        return " ".join(parts)

    def _build_style_description(
        self,
        mood: Optional[str] = None,
        style: Optional[str] = None,
    ) -> str:
        """Build the style and mood part of the prompt."""
        style_parts = []

        # Add mood-based style
        if mood and mood.lower() in self.MOOD_STYLES:
            style_parts.append(self.MOOD_STYLES[mood.lower()])

        # Add photography style
        if style and style.lower() in self.PHOTOGRAPHY_STYLES:
            style_parts.append(self.PHOTOGRAPHY_STYLES[style.lower()])

        return ", ".join(style_parts) if style_parts else ""

    def _get_lighting_description(self) -> str:
        """Get appropriate lighting description based on quality level."""
        quality = self.config.quality_level.lower()
        if quality not in self.LIGHTING_STYLES:
            quality = "professional"

        # Select first lighting option for the quality level
        lighting_options = self.LIGHTING_STYLES[quality]
        return lighting_options[0] if lighting_options else "professional lighting"

    def _get_quality_description(self, quality_level: str) -> str:
        """Get quality and finish description."""
        quality = quality_level.lower()

        if quality == "premium":
            return "premium quality, 4K resolution, high-end advertising"
        elif quality == "professional":
            return "professional quality, commercial grade, advertising photography"
        else:
            return "good quality, clear resolution"

    def _normalize_text(self, text: str) -> str:
        """Normalize and clean text input."""
        if not text:
            return ""

        # Remove extra whitespace
        normalized = " ".join(text.split())

        # Ensure it doesn't end with punctuation that would look odd in a list
        normalized = normalized.rstrip(".,;:")

        return normalized

    def _truncate_to_word_limit(self, text: str, max_words: int) -> str:
        """Truncate text to maximum word limit."""
        words = text.split()

        if len(words) <= max_words:
            return text

        # Truncate and rejoin
        truncated = " ".join(words[:max_words])

        # Clean up trailing punctuation
        truncated = truncated.rstrip(".,;:")

        return truncated


def create_image_prompt_builder(
    config: Optional[ImageGenerationConfig] = None,
) -> ImagePromptBuilder:
    """
    Factory function to create an ImagePromptBuilder.

    Args:
        config: Optional custom configuration.

    Returns:
        Configured ImagePromptBuilder instance.
    """
    return ImagePromptBuilder(config=config)


__all__ = [
    "ImagePromptBuilder",
    "ImageGenerationConfig",
    "create_image_prompt_builder",
]
