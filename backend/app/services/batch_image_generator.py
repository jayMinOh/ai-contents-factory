"""
Batch Image Generator with Progress Tracking.

This module provides functionality to generate multiple images in batch
with concurrent processing, progress tracking, and error handling.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.services.image_composite_generator import get_composite_generator
from app.services.image_prompt_builder import create_image_prompt_builder

logger = logging.getLogger(__name__)


class BatchJobStatus(str, Enum):
    """Status of a batch job or individual item."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchConfig:
    """Configuration for batch image generation."""

    max_concurrent_jobs: int = 5
    """Maximum number of concurrent image generation jobs."""

    enable_progress_tracking: bool = True
    """Whether to track and report progress."""

    enable_retry: bool = True
    """Whether to retry failed jobs."""

    max_retries: int = 2
    """Maximum number of retries for failed jobs."""

    timeout_seconds: int = 300
    """Timeout for individual image generation (5 minutes)."""


@dataclass
class BatchRequest:
    """Request for batch image generation."""

    images: List[Dict[str, Any]]
    """List of image generation requests."""

    batch_id: Optional[str] = None
    """Optional batch identifier."""

    shared_context: Optional[Dict[str, Any]] = None
    """Optional shared context for all images."""

    def __post_init__(self):
        """Initialize batch ID if not provided."""
        if not self.batch_id:
            self.batch_id = f"batch-{uuid.uuid4().hex[:8]}"


@dataclass
class BatchItemResult:
    """Result of a single image generation in batch."""

    image_id: str
    """Unique identifier for the image."""

    status: BatchJobStatus
    """Status of the generation."""

    image_data: Optional[str] = None
    """Generated image data (base64)."""

    error: Optional[str] = None
    """Error message if generation failed."""

    generation_time_ms: int = 0
    """Time taken to generate (milliseconds)."""

    retry_count: int = 0
    """Number of retries performed."""

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    """Timestamp of result creation."""


class BatchImageGenerator:
    """
    Generates multiple images in batch with progress tracking.

    Supports concurrent processing, error handling, retry logic,
    and detailed progress reporting.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Initialize the BatchImageGenerator.

        Args:
            config: Optional BatchConfig for customizing generation.
        """
        self.config = config or BatchConfig()
        self.composite_generator = get_composite_generator()
        self.prompt_builder = create_image_prompt_builder()
        self._active_batches: Dict[str, List[BatchItemResult]] = {}
        logger.info("BatchImageGenerator initialized")

    async def generate_batch(
        self,
        images: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate images in batch with concurrent processing.

        Args:
            images: List of image generation requests.
            batch_id: Optional batch identifier.
            shared_context: Optional shared context for all images.

        Returns:
            List of generation results with image data and metadata.
        """
        if not images:
            return []

        batch_id = batch_id or f"batch-{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        logger.info(
            f"Starting batch generation - batch_id: {batch_id}, "
            f"image_count: {len(images)}, concurrent_jobs: {self.config.max_concurrent_jobs}"
        )

        # Initialize batch tracking
        self._active_batches[batch_id] = []

        try:
            # Create semaphore to limit concurrent jobs
            semaphore = asyncio.Semaphore(self.config.max_concurrent_jobs)

            # Create tasks for all images
            tasks = [
                self._generate_with_semaphore(
                    semaphore,
                    image_data,
                    batch_id,
                    shared_context,
                )
                for image_data in images
            ]

            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {str(result)}")
                    processed_results.append({
                        "status": "failed",
                        "error": str(result),
                    })
                else:
                    processed_results.append(result)

            batch_time_ms = int((time.time() - start_time) * 1000)
            successful = sum(1 for r in processed_results if r.get("status") == "completed")

            logger.info(
                f"Batch generation completed - batch_id: {batch_id}, "
                f"total_time_ms: {batch_time_ms}, successful: {successful}/{len(images)}"
            )

            return processed_results

        finally:
            # Clean up batch tracking
            if batch_id in self._active_batches:
                del self._active_batches[batch_id]

    async def _generate_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        image_data: Dict[str, Any],
        batch_id: str,
        shared_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate image with semaphore-controlled concurrency.

        Args:
            semaphore: Asyncio semaphore for concurrency control.
            image_data: Image generation request data.
            batch_id: Batch identifier.
            shared_context: Shared context for all images.

        Returns:
            Generation result dictionary.
        """
        async with semaphore:
            return await self._generate_single_image(
                image_data,
                batch_id=batch_id,
                shared_context=shared_context,
            )

    async def _generate_single_image(
        self,
        image_data: Dict[str, Any],
        batch_id: Optional[str] = None,
        shared_context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a single image with retry logic.

        Args:
            image_data: Image generation request data.
            batch_id: Optional batch identifier.
            shared_context: Optional shared context.
            retry_count: Current retry attempt number.

        Returns:
            Generation result dictionary.
        """
        image_id = image_data.get("image_id", f"img-{uuid.uuid4().hex[:8]}")
        start_time = time.time()

        try:
            logger.debug(
                f"Generating image - id: {image_id}, retry: {retry_count}, "
                f"product: {image_data.get('product_name')}"
            )

            # Build prompt from image data
            prompt = self.prompt_builder.build_prompt(
                product_name=image_data.get("product_name", "Product"),
                product_type=image_data.get("product_type", ""),
                brand_name=image_data.get("brand_name"),
                scene_description=image_data.get("scene_description"),
                mood=image_data.get("mood"),
                style=image_data.get("style"),
            )

            # Generate image using composite generator
            result = await self.composite_generator.generate_background(
                background_prompt=prompt,
                aspect_ratio=image_data.get("aspect_ratio", "16:9"),
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            return {
                "image_id": image_id,
                "status": "completed",
                "image_data": result["image_data"],
                "mime_type": result.get("mime_type", "image/png"),
                "generation_time_ms": generation_time_ms,
                "retry_count": retry_count,
            }

        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            logger.warning(
                f"Image generation failed - id: {image_id}, "
                f"retry: {retry_count}, error: {error_msg}"
            )

            # Retry logic
            if self.config.enable_retry and retry_count < self.config.max_retries:
                logger.info(f"Retrying image generation - id: {image_id}, retry: {retry_count + 1}")
                await asyncio.sleep(1)  # Wait before retry
                return await self._generate_single_image(
                    image_data,
                    batch_id=batch_id,
                    shared_context=shared_context,
                    retry_count=retry_count + 1,
                )

            # Final failure
            return {
                "image_id": image_id,
                "status": "failed",
                "error": error_msg,
                "generation_time_ms": generation_time_ms,
                "retry_count": retry_count,
            }

    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """
        Get progress information for a batch.

        Args:
            batch_id: Batch identifier.

        Returns:
            Progress information dictionary with status counts and percentages.
        """
        if batch_id not in self._active_batches:
            return {
                "batch_id": batch_id,
                "status": "not_found",
                "total": 0,
            }

        results = self._active_batches[batch_id]

        status_counts = {
            "pending": sum(1 for r in results if r.status == BatchJobStatus.PENDING),
            "processing": sum(1 for r in results if r.status == BatchJobStatus.PROCESSING),
            "completed": sum(1 for r in results if r.status == BatchJobStatus.COMPLETED),
            "failed": sum(1 for r in results if r.status == BatchJobStatus.FAILED),
        }

        total = len(results)
        progress_percentage = (
            (status_counts["completed"] / total * 100) if total > 0 else 0
        )

        return {
            "batch_id": batch_id,
            "total": total,
            "status_counts": status_counts,
            "progress_percentage": progress_percentage,
        }

    async def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a batch generation.

        Args:
            batch_id: Batch identifier.

        Returns:
            True if batch was cancelled, False if batch not found.
        """
        if batch_id not in self._active_batches:
            return False

        logger.info(f"Cancelling batch - batch_id: {batch_id}")
        del self._active_batches[batch_id]
        return True


def create_batch_generator(
    config: Optional[BatchConfig] = None,
) -> BatchImageGenerator:
    """
    Factory function to create a BatchImageGenerator.

    Args:
        config: Optional custom configuration.

    Returns:
        Configured BatchImageGenerator instance.
    """
    return BatchImageGenerator(config=config)


__all__ = [
    "BatchImageGenerator",
    "BatchConfig",
    "BatchRequest",
    "BatchJobStatus",
    "BatchItemResult",
    "create_batch_generator",
]
