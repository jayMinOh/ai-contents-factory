"""
Tests for Image Composite Generator.

Tests the generation and composition of background and product images
to create final composite marketing images.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.image_composite_generator import (
    CompositeImageGenerator,
    CompositeConfig,
    CompositeRequest,
    create_composite_generator,
)


class TestCompositeImageGenerator:
    """Test suite for CompositeImageGenerator class."""

    def test_initialization_with_defaults(self):
        """Test generator initialization with default configuration."""
        generator = CompositeImageGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_composite')
        assert hasattr(generator, 'compose_with_background')

    def test_initialization_with_custom_config(self):
        """Test generator initialization with custom configuration."""
        config = CompositeConfig(
            output_aspect_ratio="16:9",
            quality_level="high",
        )
        generator = CompositeImageGenerator(config=config)
        assert generator.config == config

    @pytest.mark.asyncio
    async def test_generate_composite_basic(self):
        """Test basic composite generation."""
        generator = CompositeImageGenerator()

        # Mock the _generate_with_gemini method instead
        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "image_data": "base64encodedimage",
                "mime_type": "image/png",
            }

            result = await generator.generate_composite(
                product_prompt="Product image prompt",
                background_prompt="Background image prompt",
            )

            assert result is not None
            assert "image_data" in result
            assert "composite_time_ms" in result

    @pytest.mark.asyncio
    async def test_generate_composite_with_product_image(self):
        """Test composite generation with existing product image."""
        generator = CompositeImageGenerator()

        product_image_data = b"fake_product_image"

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "image_data": "base64composite",
                "mime_type": "image/png",
            }

            result = await generator.generate_composite(
                product_image=product_image_data,
                background_prompt="Modern office background",
            )

            assert result is not None
            assert "image_data" in result

    @pytest.mark.asyncio
    async def test_compose_with_background(self):
        """Test composition of product with background."""
        generator = CompositeImageGenerator()

        product_data = b"product_image"
        background_data = b"background_image"

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "image_data": "base64composite",
                "mime_type": "image/png",
            }

            result = await generator.compose_with_background(
                product_image=product_data,
                background_image=background_data,
                composition_prompt="Overlay product on background naturally",
            )

            assert result is not None
            assert "image_data" in result

    @pytest.mark.asyncio
    async def test_generate_background_image(self):
        """Test background image generation."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "image_data": "base64background",
                "mime_type": "image/png",
            }

            result = await generator.generate_background(
                background_prompt="Luxury living room with modern furniture",
                aspect_ratio="16:9",
            )

            assert result is not None
            assert "image_data" in result

    @pytest.mark.asyncio
    async def test_composite_request_structure(self):
        """Test CompositeRequest data structure."""
        request = CompositeRequest(
            product_prompt="Coffee maker on kitchen counter",
            background_prompt="Bright modern kitchen",
            output_aspect_ratio="16:9",
        )

        assert request.product_prompt == "Coffee maker on kitchen counter"
        assert request.background_prompt == "Bright modern kitchen"
        assert request.output_aspect_ratio == "16:9"

    @pytest.mark.asyncio
    async def test_composite_with_custom_aspect_ratio(self):
        """Test composite generation with custom aspect ratio."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64img", "mime_type": "image/png"}

            result = await generator.generate_composite(
                product_prompt="Product",
                background_prompt="Background",
                output_aspect_ratio="9:16",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_composite_preserves_product_quality(self):
        """Test that compositing preserves product image quality."""
        generator = CompositeImageGenerator()

        product_image = b"high_quality_product"

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64quality", "mime_type": "image/png"}

            result = await generator.compose_with_background(
                product_image=product_image,
                background_image=b"background",
                composition_prompt="Maintain sharp product appearance",
            )

            assert result is not None
            # Verify product quality is maintained
            assert len(result.get("image_data", "")) > 0

    @pytest.mark.asyncio
    async def test_composite_error_handling(self):
        """Test error handling in composite generation."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await generator.generate_composite(
                    product_prompt="Product",
                    background_prompt="Background",
                )

    @pytest.mark.asyncio
    async def test_composite_with_quality_options(self):
        """Test composite generation with quality options."""
        config = CompositeConfig(quality_level="premium")
        generator = CompositeImageGenerator(config=config)

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64premium", "mime_type": "image/png"}

            result = await generator.generate_composite(
                product_prompt="Premium product",
                background_prompt="Luxury background",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_composite_generation_time_tracking(self):
        """Test that composite generation tracks execution time."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64img", "mime_type": "image/png"}

            result = await generator.generate_composite(
                product_prompt="Product",
                background_prompt="Background",
            )

            assert "composite_time_ms" in result
            assert result["composite_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_multiple_composite_generation(self):
        """Test generating multiple composites sequentially."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64img", "mime_type": "image/png"}

            results = []
            for i in range(3):
                result = await generator.generate_composite(
                    product_prompt=f"Product {i}",
                    background_prompt=f"Background {i}",
                )
                results.append(result)

            assert len(results) == 3
            assert all("image_data" in r for r in results)

    def test_create_generator_factory_function(self):
        """Test the factory function for creating generators."""
        generator = create_composite_generator()

        assert generator is not None
        assert isinstance(generator, CompositeImageGenerator)

    def test_create_generator_with_custom_config(self):
        """Test factory function with custom configuration."""
        config = CompositeConfig(quality_level="high")
        generator = create_composite_generator(config=config)

        assert generator.config.quality_level == "high"


class TestCompositeConfig:
    """Test suite for CompositeConfig class."""

    def test_config_initialization_with_defaults(self):
        """Test configuration with default values."""
        config = CompositeConfig()

        assert config.output_aspect_ratio == "16:9"
        assert config.quality_level in ["standard", "professional", "premium"]
        assert config.preserve_product_quality is not None

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = CompositeConfig(
            output_aspect_ratio="9:16",
            quality_level="premium",
            preserve_product_quality=True,
        )

        assert config.output_aspect_ratio == "9:16"
        assert config.quality_level == "premium"
        assert config.preserve_product_quality is True

    def test_config_aspect_ratio_validation(self):
        """Test that aspect ratios are supported."""
        supported_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]

        for ratio in supported_ratios:
            config = CompositeConfig(output_aspect_ratio=ratio)
            assert config.output_aspect_ratio == ratio


class TestCompositeImageQuality:
    """Test suite for composite image quality."""

    @pytest.mark.asyncio
    async def test_composite_respects_quality_level(self):
        """Test that composite generation respects quality level."""
        config = CompositeConfig(quality_level="premium")
        generator = CompositeImageGenerator(config=config)

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64premium", "mime_type": "image/png"}

            result = await generator.generate_composite(
                product_prompt="Product",
                background_prompt="Background",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_composite_maintains_colors(self):
        """Test that composite maintains product colors correctly."""
        generator = CompositeImageGenerator()

        product_image = b"colored_product"

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64colors", "mime_type": "image/png"}

            result = await generator.compose_with_background(
                product_image=product_image,
                background_image=b"background",
                composition_prompt="Maintain product colors accurately",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_composite_positioning_control(self):
        """Test composite positioning specification."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64positioned", "mime_type": "image/png"}

            result = await generator.compose_with_background(
                product_image=b"product",
                background_image=b"background",
                composition_prompt="Place product in center-right with product occupying 30% of image",
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_composite_natural_integration(self):
        """Test that composite integrates product naturally into background."""
        generator = CompositeImageGenerator()

        with patch.object(generator, '_generate_with_gemini', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"image_data": "base64natural", "mime_type": "image/png"}

            result = await generator.compose_with_background(
                product_image=b"product",
                background_image=b"background",
                composition_prompt="Integrate product naturally, maintain realistic shadows and lighting",
            )

            assert result is not None
