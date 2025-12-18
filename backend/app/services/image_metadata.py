"""
Image Metadata Extraction Service

Handles extraction of metadata from uploaded images including
dimensions, format, file size, and color information.
"""

import io
import logging
from typing import Optional, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)


class ImageMetadataError(Exception):
    """Raised when image metadata extraction fails."""
    pass


class ImageMetadataExtractor:
    """
    Extract metadata from image files.

    Provides:
    - Image dimensions (width, height)
    - File format (JPEG, PNG, WebP, etc.)
    - File size in MB
    - Aspect ratio
    - Color mode (RGB, RGBA, etc.)
    """

    # Supported image formats
    SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

    def extract_from_bytes(
        self,
        image_data: Optional[bytes],
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from image bytes.

        Args:
            image_data: Raw image bytes
            mime_type: MIME type (e.g., "image/jpeg")

        Returns:
            Dictionary with metadata

        Raises:
            ImageMetadataError: If image data is invalid
        """
        if not image_data:
            raise ImageMetadataError("Image data cannot be empty")

        if not isinstance(image_data, bytes):
            raise ImageMetadataError("Image data must be bytes")

        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(image_data))

            # Extract basic information
            width, height = img.size
            file_format = img.format
            color_mode = img.mode
            size_mb = len(image_data) / (1024 * 1024)
            aspect_ratio = width / height if height > 0 else 0

            metadata = {
                "width": width,
                "height": height,
                "format": file_format or "UNKNOWN",
                "size_mb": size_mb,
                "aspect_ratio": aspect_ratio,
                "dimensions": f"{width}x{height}",
                "color_mode": color_mode,
            }

            logger.info(f"Extracted metadata: {width}x{height}, {file_format}, {size_mb:.2f}MB")
            return metadata

        except Exception as e:
            logger.error(f"Image metadata extraction failed: {e}")
            raise ImageMetadataError(f"Invalid image data: {str(e)}")

    def detect_format(self, image_data: bytes) -> Optional[str]:
        """
        Detect image format from bytes.

        Args:
            image_data: Raw image bytes

        Returns:
            Image format (JPEG, PNG, etc.) or None
        """
        if not image_data:
            return None

        try:
            img = Image.open(io.BytesIO(image_data))
            return img.format or "UNKNOWN"
        except Exception:
            return None

    def is_within_size_limit(
        self,
        image_data: bytes,
        max_size_mb: float = 50.0
    ) -> bool:
        """
        Check if image size is within limit.

        Args:
            image_data: Raw image bytes
            max_size_mb: Maximum allowed size in MB

        Returns:
            True if within limit, False otherwise
        """
        if not image_data:
            return False

        size_mb = len(image_data) / (1024 * 1024)
        return size_mb <= max_size_mb

    @staticmethod
    def validate_format(file_format: str) -> bool:
        """
        Validate if image format is supported.

        Args:
            file_format: Image format (JPEG, PNG, etc.)

        Returns:
            True if format is supported
        """
        return file_format.upper() in ImageMetadataExtractor.SUPPORTED_FORMATS
