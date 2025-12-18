"""
RED PHASE: Image Metadata Extraction Service Tests

Tests for extracting metadata from uploaded images (size, format, dimensions).
"""

import pytest
import io
from PIL import Image
from app.services.image_metadata import ImageMetadataExtractor, ImageMetadataError


class TestImageMetadataExtractor:
    """Tests for image metadata extraction."""

    @pytest.fixture
    def extractor(self):
        """Create metadata extractor instance."""
        return ImageMetadataExtractor()

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes (JPG)."""
        img = Image.new("RGB", (1080, 1350), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.fixture
    def sample_image_png_bytes(self):
        """Create sample PNG image bytes."""
        img = Image.new("RGBA", (800, 600), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    # RED PHASE: Test basic metadata extraction
    def test_extract_metadata_from_bytes(self, extractor, sample_image_bytes):
        """Test extracting metadata from image bytes."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        assert result is not None
        assert result["width"] == 1080
        assert result["height"] == 1350
        assert result["format"] == "JPEG"
        assert result["size_mb"] > 0

    def test_extract_metadata_png(self, extractor, sample_image_png_bytes):
        """Test extracting metadata from PNG image."""
        result = extractor.extract_from_bytes(
            sample_image_png_bytes,
            mime_type="image/png"
        )

        assert result["format"] == "PNG"
        assert result["width"] == 800
        assert result["height"] == 600

    # RED PHASE: Test aspect ratio calculation
    def test_extract_metadata_aspect_ratio(self, extractor, sample_image_bytes):
        """Test aspect ratio is calculated correctly."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        # 1080x1350 = 0.8 or 4:5 ratio
        assert result["aspect_ratio"] == pytest.approx(1080/1350, rel=0.01)

    # RED PHASE: Test file size calculation
    def test_extract_metadata_file_size(self, extractor, sample_image_bytes):
        """Test file size is calculated correctly."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        expected_size_mb = len(sample_image_bytes) / (1024 * 1024)
        assert result["size_mb"] == pytest.approx(expected_size_mb, rel=0.01)

    # RED PHASE: Test invalid image data
    def test_extract_metadata_invalid_bytes(self, extractor):
        """Test extracting metadata from invalid image bytes raises error."""
        invalid_bytes = b"This is not an image"

        with pytest.raises(ImageMetadataError):
            extractor.extract_from_bytes(invalid_bytes, mime_type="image/jpeg")

    def test_extract_metadata_empty_bytes(self, extractor):
        """Test extracting metadata from empty bytes raises error."""
        with pytest.raises(ImageMetadataError):
            extractor.extract_from_bytes(b"", mime_type="image/jpeg")

    def test_extract_metadata_none_bytes(self, extractor):
        """Test extracting metadata from None raises error."""
        with pytest.raises(ImageMetadataError):
            extractor.extract_from_bytes(None, mime_type="image/jpeg")

    # RED PHASE: Test content type detection
    def test_detect_format_jpeg(self, extractor, sample_image_bytes):
        """Test detecting JPEG format."""
        detected = extractor.detect_format(sample_image_bytes)
        assert detected == "JPEG"

    def test_detect_format_png(self, extractor, sample_image_png_bytes):
        """Test detecting PNG format."""
        detected = extractor.detect_format(sample_image_png_bytes)
        assert detected == "PNG"

    def test_detect_format_invalid(self, extractor):
        """Test detecting format from invalid data."""
        result = extractor.detect_format(b"not an image")
        # Should return None or "UNKNOWN" for invalid data
        assert result in [None, "UNKNOWN"]

    # RED PHASE: Test max file size validation
    def test_validate_size_under_limit(self, extractor, sample_image_bytes):
        """Test file size validation passes for small files."""
        # Default limit is usually 50MB
        result = extractor.is_within_size_limit(
            sample_image_bytes,
            max_size_mb=50
        )
        assert result is True

    def test_validate_size_over_limit(self, extractor):
        """Test file size validation fails for large files."""
        # Create large fake data
        large_data = b"x" * (100 * 1024 * 1024)  # 100MB

        result = extractor.is_within_size_limit(
            large_data,
            max_size_mb=50
        )
        assert result is False

    # RED PHASE: Test image dimensions
    def test_extract_metadata_dimensions(self, extractor, sample_image_bytes):
        """Test extracting correct dimensions."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        assert result["width"] == 1080
        assert result["height"] == 1350
        assert result["dimensions"] == "1080x1350"

    # RED PHASE: Test color mode detection
    def test_extract_metadata_color_mode(self, extractor, sample_image_bytes):
        """Test color mode is detected correctly."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        # JPEG is typically RGB
        assert result["color_mode"] == "RGB"

    def test_extract_metadata_color_mode_rgba(self, extractor, sample_image_png_bytes):
        """Test RGBA color mode is detected."""
        result = extractor.extract_from_bytes(
            sample_image_png_bytes,
            mime_type="image/png"
        )

        assert result["color_mode"] == "RGBA"

    # RED PHASE: Test metadata completeness
    def test_extract_metadata_complete(self, extractor, sample_image_bytes):
        """Test extracted metadata contains all required fields."""
        result = extractor.extract_from_bytes(
            sample_image_bytes,
            mime_type="image/jpeg"
        )

        required_fields = [
            "width", "height", "format", "size_mb",
            "aspect_ratio", "dimensions", "color_mode"
        ]

        for field in required_fields:
            assert field in result, f"Missing field: {field}"
