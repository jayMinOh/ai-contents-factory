"""
Tests for Image Generation Prompt Builder.

Tests the creation of optimized prompts for image generation from
product and scene information.
"""

import pytest
from app.services.image_prompt_builder import (
    ImagePromptBuilder,
    ImageGenerationConfig,
    create_image_prompt_builder,
)


class TestImagePromptBuilder:
    """Test suite for ImagePromptBuilder class."""

    def test_initialization_with_defaults(self):
        """Test builder initialization with default configuration."""
        builder = ImagePromptBuilder()
        assert builder is not None
        assert hasattr(builder, 'build_prompt')
        assert hasattr(builder, 'build_batch_prompts')

    def test_initialization_with_custom_config(self):
        """Test builder initialization with custom configuration."""
        config = ImageGenerationConfig(
            max_words=100,
            include_lighting=True,
            include_style=True,
        )
        builder = ImagePromptBuilder(config=config)
        assert builder.config == config

    def test_build_simple_product_prompt(self):
        """Test building prompt for simple product."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Coffee Maker",
            product_type="Kitchen Appliance",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Coffee Maker" in prompt or "coffee" in prompt.lower()

    def test_build_prompt_with_brand_context(self):
        """Test building prompt with brand information."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Hair Treatment",
            product_type="Cosmetic",
            brand_name="Kerastase",
            brand_context="Premium hair care for damaged hair",
        )

        assert isinstance(prompt, str)
        assert "Kerastase" in prompt or "Hair Treatment" in prompt
        assert len(prompt) > 0

    def test_build_prompt_with_scene_description(self):
        """Test building prompt with scene description."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Smartphone",
            product_type="Electronics",
            scene_description="Person holding phone in modern office, natural light",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should incorporate scene description
        assert "phone" in prompt.lower() or "office" in prompt.lower()

    def test_build_prompt_with_mood_and_style(self):
        """Test building prompt with mood and style specifications."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Luxury Watch",
            product_type="Accessory",
            mood="premium",
            style="minimalist",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should reflect the mood/style
        assert "watch" in prompt.lower() or "premium" in prompt.lower()

    def test_build_prompt_with_aspect_ratio(self):
        """Test building prompt with aspect ratio specification."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Beverage",
            product_type="Drink",
            aspect_ratio="16:9",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_prompt_with_color_emphasis(self):
        """Test building prompt with specific color emphasis."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Lipstick",
            product_type="Cosmetic",
            primary_color="Red",
            color_emphasis=True,
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should mention the color or product
        assert "red" in prompt.lower() or "lipstick" in prompt.lower()

    def test_build_prompt_respects_max_words(self):
        """Test that built prompt respects word limit."""
        config = ImageGenerationConfig(max_words=30)
        builder = ImagePromptBuilder(config=config)

        prompt = builder.build_prompt(
            product_name="Product Name",
            product_type="Type",
            scene_description="This is a very long scene description that contains many words and should be truncated",
        )

        word_count = len(prompt.split())
        assert word_count <= config.max_words

    def test_build_batch_prompts(self):
        """Test building prompts for multiple products."""
        builder = ImagePromptBuilder()

        products = [
            {"product_name": "Product 1", "product_type": "Type A"},
            {"product_name": "Product 2", "product_type": "Type B"},
            {"product_name": "Product 3", "product_type": "Type C"},
        ]

        prompts = builder.build_batch_prompts(products)

        assert isinstance(prompts, list)
        assert len(prompts) == 3
        assert all(isinstance(p, str) for p in prompts)
        assert all(len(p) > 0 for p in prompts)

    def test_build_batch_prompts_with_context(self):
        """Test batch prompt building with shared context."""
        builder = ImagePromptBuilder()

        products = [
            {"product_name": "Product 1"},
            {"product_name": "Product 2"},
        ]

        prompts = builder.build_batch_prompts(
            products,
            brand_context="Premium Brand",
        )

        assert len(prompts) == 2
        # Batch prompts should share the brand context
        assert all(isinstance(p, str) for p in prompts)

    def test_build_prompt_korean_text_handling(self):
        """Test handling of Korean text in prompts."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="헤어 트리트먼트",
            product_type="화장품",
            scene_description="모던한 배경에서 제품을 들고 있는 여성",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should handle Korean text appropriately

    def test_build_prompt_with_empty_optional_fields(self):
        """Test prompt building with minimal required fields."""
        builder = ImagePromptBuilder()

        # Only required fields
        prompt = builder.build_prompt(
            product_name="Product",
            product_type="Type",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Product" in prompt or "Type" in prompt

    def test_build_prompt_consistency(self):
        """Test that same inputs produce consistent outputs."""
        builder = ImagePromptBuilder()

        inputs = {
            "product_name": "Camera",
            "product_type": "Electronics",
            "scene_description": "Professional photography studio",
        }

        prompt1 = builder.build_prompt(**inputs)
        prompt2 = builder.build_prompt(**inputs)

        # Should produce identical results for same inputs
        assert prompt1 == prompt2

    def test_create_builder_factory_function(self):
        """Test the factory function for creating builders."""
        builder = create_image_prompt_builder()

        assert builder is not None
        assert isinstance(builder, ImagePromptBuilder)

    def test_create_builder_with_custom_config(self):
        """Test factory function with custom configuration."""
        config = ImageGenerationConfig(max_words=50)
        builder = create_image_prompt_builder(config=config)

        assert builder.config.max_words == 50


class TestImageGenerationConfig:
    """Test suite for ImageGenerationConfig class."""

    def test_config_initialization_with_defaults(self):
        """Test configuration with default values."""
        config = ImageGenerationConfig()

        assert config.max_words > 0
        assert config.include_lighting is not None
        assert config.include_style is not None

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = ImageGenerationConfig(
            max_words=100,
            include_lighting=False,
            include_style=True,
            quality_level="high",
        )

        assert config.max_words == 100
        assert config.include_lighting is False
        assert config.include_style is True
        assert config.quality_level == "high"

    def test_config_has_required_attributes(self):
        """Test that config has all required attributes."""
        config = ImageGenerationConfig()

        required_attrs = ["max_words", "include_lighting", "include_style"]
        for attr in required_attrs:
            assert hasattr(config, attr)


class TestPromptQuality:
    """Test suite for prompt quality and generation."""

    def test_prompt_includes_product_information(self):
        """Test that prompts include product information."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Skincare Serum",
            product_type="Cosmetic",
        )

        # Should contain product or type information
        assert "serum" in prompt.lower() or "skincare" in prompt.lower() or "cosmetic" in prompt.lower()

    def test_prompt_quality_increases_with_context(self):
        """Test that prompts improve with more context."""
        builder = ImagePromptBuilder()

        basic_prompt = builder.build_prompt(
            product_name="Product",
            product_type="Type",
        )

        detailed_prompt = builder.build_prompt(
            product_name="Luxury Handbag",
            product_type="Fashion",
            brand_name="Premium Brand",
            scene_description="High fashion photoshoot with professional lighting",
            mood="elegant",
            style="luxury",
        )

        # Both should be valid
        assert len(basic_prompt) > 0
        assert len(detailed_prompt) > 0
        # Detailed should generally be more informative
        assert len(detailed_prompt) >= len(basic_prompt)

    def test_prompt_is_image_generation_optimized(self):
        """Test that prompts are optimized for image generation."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Camera Lens",
            product_type="Photography Equipment",
            scene_description="Professional studio setup",
        )

        # Should be a string suitable for AI image generation
        assert isinstance(prompt, str)
        assert len(prompt) > 20  # Should have meaningful length
        assert "\n\n" not in prompt  # Should not have excessive newlines

    def test_prompt_handles_special_characters(self):
        """Test that prompts handle special characters properly."""
        builder = ImagePromptBuilder()

        prompt = builder.build_prompt(
            product_name="Product & Brand",
            product_type="Type/Category",
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
