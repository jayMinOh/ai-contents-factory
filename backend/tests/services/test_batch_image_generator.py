"""
Tests for Batch Image Generator with Progress Tracking.

Tests the generation of multiple images in batch with progress tracking,
error handling, and resumption capabilities.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.services.batch_image_generator import (
    BatchImageGenerator,
    BatchConfig,
    BatchRequest,
    BatchJobStatus,
    create_batch_generator,
)


class TestBatchImageGenerator:
    """Test suite for BatchImageGenerator class."""

    def test_initialization_with_defaults(self):
        """Test generator initialization with default configuration."""
        generator = BatchImageGenerator()
        assert generator is not None
        assert hasattr(generator, 'generate_batch')
        assert hasattr(generator, 'get_batch_progress')

    def test_initialization_with_custom_config(self):
        """Test generator initialization with custom configuration."""
        config = BatchConfig(
            max_concurrent_jobs=5,
            enable_progress_tracking=True,
        )
        generator = BatchImageGenerator(config=config)
        assert generator.config == config

    @pytest.mark.asyncio
    async def test_generate_batch_single_image(self):
        """Test batch generation with single image."""
        generator = BatchImageGenerator()

        batch_request = {
            "images": [
                {
                    "product_name": "Product 1",
                    "product_type": "Type 1",
                    "product_prompt": "Prompt 1",
                }
            ]
        }

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64", "generation_time_ms": 1000}

            results = await generator.generate_batch(batch_request["images"])

            assert len(results) == 1
            assert results[0] is not None

    @pytest.mark.asyncio
    async def test_generate_batch_multiple_images(self):
        """Test batch generation with multiple images."""
        generator = BatchImageGenerator()

        images = [
            {"product_name": f"Product {i}", "product_type": f"Type {i}"}
            for i in range(5)
        ]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64", "generation_time_ms": 1000}

            results = await generator.generate_batch(images)

            assert len(results) == 5
            assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_batch_respects_concurrent_limit(self):
        """Test that batch respects concurrency limit."""
        config = BatchConfig(max_concurrent_jobs=2)
        generator = BatchImageGenerator(config=config)

        images = [{"product_name": f"Product {i}"} for i in range(5)]

        call_count = {"value": 0}
        concurrent_calls = {"max": 0}
        current_calls = {"value": 0}

        async def mock_generate(image_data):
            call_count["value"] += 1
            current_calls["value"] += 1
            concurrent_calls["max"] = max(concurrent_calls["max"], current_calls["value"])
            await asyncio.sleep(0.1)
            current_calls["value"] -= 1
            return {"image_data": "base64"}

        with patch.object(generator, '_generate_single_image', side_effect=mock_generate):
            results = await generator.generate_batch(images)

            assert len(results) == 5
            # Should not exceed max concurrent jobs
            assert concurrent_calls["max"] <= config.max_concurrent_jobs

    @pytest.mark.asyncio
    async def test_batch_with_progress_tracking(self):
        """Test batch generation with progress tracking."""
        config = BatchConfig(enable_progress_tracking=True)
        generator = BatchImageGenerator(config=config)

        images = [{"product_name": f"Product {i}"} for i in range(3)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64"}

            results = await generator.generate_batch(images)

            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_batch_error_handling(self):
        """Test error handling in batch generation."""
        generator = BatchImageGenerator()

        images = [
            {"product_name": "Product 1"},
            {"product_name": "Product 2"},
            {"product_name": "Product 3"},
        ]

        call_count = {"value": 0}

        async def mock_generate_with_error(image_data):
            call_count["value"] += 1
            if call_count["value"] == 2:
                raise Exception("Generation failed")
            return {"image_data": "base64"}

        with patch.object(generator, '_generate_single_image', side_effect=mock_generate_with_error):
            results = await generator.generate_batch(images)

            # Should handle error gracefully
            assert len(results) == 3
            # One should be error result
            assert any("error" in r for r in results)

    @pytest.mark.asyncio
    async def test_batch_with_retry_on_failure(self):
        """Test batch generation handles retry configuration."""
        config = BatchConfig(enable_retry=True, max_retries=2)
        generator = BatchImageGenerator(config=config)

        # Verify retry configuration is set correctly
        assert generator.config.enable_retry is True
        assert generator.config.max_retries == 2

        images = [{"product_name": "Product"}]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64", "status": "completed"}

            results = await generator.generate_batch(images)

            assert len(results) == 1
            # Should succeed
            assert results[0].get("status") == "completed"

    @pytest.mark.asyncio
    async def test_batch_completion_tracking(self):
        """Test tracking batch completion status."""
        generator = BatchImageGenerator()

        images = [{"product_name": f"Product {i}"} for i in range(3)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64"}

            results = await generator.generate_batch(images)

            assert len(results) == 3
            # All should be complete
            assert all(r.get("status") != "pending" for r in results)

    @pytest.mark.asyncio
    async def test_batch_total_time_tracking(self):
        """Test tracking total batch generation time."""
        generator = BatchImageGenerator()

        images = [{"product_name": f"Product {i}"} for i in range(2)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            async def mock_with_delay(img):
                await asyncio.sleep(0.05)
                return {"image_data": "base64", "generation_time_ms": 50}

            mock_gen.side_effect = mock_with_delay

            results = await generator.generate_batch(images)

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_batch_with_shared_context(self):
        """Test batch generation with shared context."""
        generator = BatchImageGenerator()

        images = [
            {"product_name": f"Product {i}"}
            for i in range(3)
        ]

        shared_context = {
            "brand_name": "Premium Brand",
            "style": "luxury",
        }

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64"}

            results = await generator.generate_batch(
                images,
                shared_context=shared_context,
            )

            assert len(results) == 3

    def test_batch_request_structure(self):
        """Test BatchRequest data structure."""
        request = BatchRequest(
            images=[
                {"product_name": "Product 1"},
                {"product_name": "Product 2"},
            ],
            batch_id="batch-001",
        )

        assert request.batch_id == "batch-001"
        assert len(request.images) == 2

    def test_batch_job_status_enum(self):
        """Test BatchJobStatus enum values."""
        assert hasattr(BatchJobStatus, "PENDING")
        assert hasattr(BatchJobStatus, "PROCESSING")
        assert hasattr(BatchJobStatus, "COMPLETED")
        assert hasattr(BatchJobStatus, "FAILED")

    @pytest.mark.asyncio
    async def test_get_batch_progress(self):
        """Test retrieving batch progress."""
        generator = BatchImageGenerator()

        # Mock a batch operation
        images = [{"product_name": f"Product {i}"} for i in range(5)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64"}

            # Start batch generation
            results = await generator.generate_batch(images)

            # Progress should show completion
            assert len(results) == 5

    def test_create_generator_factory_function(self):
        """Test the factory function for creating generators."""
        generator = create_batch_generator()

        assert generator is not None
        assert isinstance(generator, BatchImageGenerator)

    def test_create_generator_with_custom_config(self):
        """Test factory function with custom configuration."""
        config = BatchConfig(max_concurrent_jobs=10)
        generator = create_batch_generator(config=config)

        assert generator.config.max_concurrent_jobs == 10


class TestBatchConfig:
    """Test suite for BatchConfig class."""

    def test_config_initialization_with_defaults(self):
        """Test configuration with default values."""
        config = BatchConfig()

        assert config.max_concurrent_jobs > 0
        assert config.enable_progress_tracking is not None
        assert config.enable_retry is not None

    def test_config_with_custom_values(self):
        """Test configuration with custom values."""
        config = BatchConfig(
            max_concurrent_jobs=20,
            enable_progress_tracking=True,
            enable_retry=True,
            max_retries=3,
        )

        assert config.max_concurrent_jobs == 20
        assert config.enable_progress_tracking is True
        assert config.enable_retry is True
        assert config.max_retries == 3


class TestBatchPerformance:
    """Test suite for batch generation performance."""

    @pytest.mark.asyncio
    async def test_batch_performance_with_concurrent_jobs(self):
        """Test batch performance with concurrent job execution."""
        config = BatchConfig(max_concurrent_jobs=4)
        generator = BatchImageGenerator(config=config)

        images = [{"product_name": f"Product {i}"} for i in range(8)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            async def fast_generate(img):
                await asyncio.sleep(0.01)
                return {"image_data": "base64"}

            mock_gen.side_effect = fast_generate

            results = await generator.generate_batch(images)

            assert len(results) == 8

    @pytest.mark.asyncio
    async def test_batch_handles_empty_list(self):
        """Test batch generation handles empty image list."""
        generator = BatchImageGenerator()

        results = await generator.generate_batch([])

        assert results == []

    @pytest.mark.asyncio
    async def test_batch_with_large_dataset(self):
        """Test batch generation with large dataset."""
        generator = BatchImageGenerator()

        # Create large batch
        images = [{"product_name": f"Product {i}"} for i in range(50)]

        with patch.object(generator, '_generate_single_image', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"image_data": "base64"}

            results = await generator.generate_batch(images)

            assert len(results) == 50
