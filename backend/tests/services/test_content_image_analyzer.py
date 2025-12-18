"""
RED PHASE: Content Image Analyzer Tests

Tests for AI-powered image analysis using Gemini Vision API for SNS content.
Analyzes composition, color scheme, style, and elements.
"""

import pytest
import io
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image

from app.services.content_image_analyzer import ContentImageAnalyzer, ImageAnalysisError


class TestContentImageAnalyzer:
    """Tests for content image analysis."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ContentImageAnalyzer()

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes."""
        img = Image.new("RGB", (1080, 1350), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.getvalue()

    # RED PHASE: Test basic image analysis
    @pytest.mark.asyncio
    async def test_analyze_image_basic(self, analyzer, sample_image_bytes):
        """Test analyzing image returns all required fields."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "central",
                "colorScheme": ["red", "white"],
                "style": "modern",
                "elements": ["product", "background"],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert result is not None
            assert "composition" in result
            assert "colorScheme" in result
            assert "style" in result
            assert "elements" in result

    # RED PHASE: Test composition analysis
    @pytest.mark.asyncio
    async def test_analyze_composition(self, analyzer, sample_image_bytes):
        """Test composition is analyzed correctly."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "rule_of_thirds",
                "colorScheme": [],
                "style": "",
                "elements": [],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert result["composition"] == "rule_of_thirds"

    # RED PHASE: Test color scheme detection
    @pytest.mark.asyncio
    async def test_analyze_color_scheme(self, analyzer, sample_image_bytes):
        """Test color scheme is detected."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "",
                "colorScheme": ["warm", "red", "gold"],
                "style": "",
                "elements": [],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert result["colorScheme"] is not None
            assert len(result["colorScheme"]) > 0
            assert "warm" in result["colorScheme"]

    # RED PHASE: Test style detection
    @pytest.mark.asyncio
    async def test_analyze_style(self, analyzer, sample_image_bytes):
        """Test style is analyzed."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "",
                "colorScheme": [],
                "style": "minimalist",
                "elements": [],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert result["style"] == "minimalist"

    # RED PHASE: Test element detection
    @pytest.mark.asyncio
    async def test_analyze_elements(self, analyzer, sample_image_bytes):
        """Test elements are detected."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "",
                "colorScheme": [],
                "style": "",
                "elements": ["product", "text", "people"],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert result["elements"] is not None
            assert len(result["elements"]) > 0
            assert "product" in result["elements"]

    # RED PHASE: Test invalid image
    @pytest.mark.asyncio
    async def test_analyze_invalid_image(self, analyzer):
        """Test analyzing invalid image raises error."""
        invalid_bytes = b"not an image"

        with pytest.raises(ImageAnalysisError):
            await analyzer.analyze(invalid_bytes)

    @pytest.mark.asyncio
    async def test_analyze_empty_bytes(self, analyzer):
        """Test analyzing empty bytes raises error."""
        with pytest.raises(ImageAnalysisError):
            await analyzer.analyze(b"")

    @pytest.mark.asyncio
    async def test_analyze_none_bytes(self, analyzer):
        """Test analyzing None raises error."""
        with pytest.raises(ImageAnalysisError):
            await analyzer.analyze(None)

    # RED PHASE: Test Gemini API error handling
    @pytest.mark.asyncio
    async def test_analyze_gemini_api_error(self, analyzer, sample_image_bytes):
        """Test handling Gemini API errors."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API error")

            with pytest.raises(ImageAnalysisError):
                await analyzer.analyze(sample_image_bytes)

    # RED PHASE: Test JSON parsing errors
    @pytest.mark.asyncio
    async def test_analyze_invalid_json_response(self, analyzer, sample_image_bytes):
        """Test handling invalid JSON from Gemini."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = None

            with pytest.raises(ImageAnalysisError):
                await analyzer.analyze(sample_image_bytes)

    # RED PHASE: Test retry logic
    @pytest.mark.asyncio
    async def test_analyze_with_retry(self, analyzer, sample_image_bytes):
        """Test retry logic on temporary failures."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            # First call fails with retryable error, second succeeds
            mock_call.side_effect = [
                Exception("Service unavailable 503"),  # Retryable error
                {
                    "composition": "central",
                    "colorScheme": [],
                    "style": "",
                    "elements": [],
                }
            ]

            result = await analyzer.analyze(sample_image_bytes, max_retries=2)

            assert result is not None
            assert mock_call.call_count == 2

    # RED PHASE: Test analysis completeness
    @pytest.mark.asyncio
    async def test_analyze_complete_output(self, analyzer, sample_image_bytes):
        """Test analysis output contains all required fields."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "centered",
                "colorScheme": ["warm", "red"],
                "style": "modern",
                "elements": ["product"],
            }

            result = await analyzer.analyze(sample_image_bytes)

            required_fields = ["composition", "colorScheme", "style", "elements"]
            for field in required_fields:
                assert field in result, f"Missing field: {field}"

    # RED PHASE: Test metadata inclusion
    @pytest.mark.asyncio
    async def test_analyze_includes_metadata(self, analyzer, sample_image_bytes):
        """Test analysis includes image metadata."""
        with patch.object(analyzer, '_call_gemini', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = {
                "composition": "",
                "colorScheme": [],
                "style": "",
                "elements": [],
            }

            result = await analyzer.analyze(sample_image_bytes)

            assert "width" in result
            assert "height" in result
            assert "format" in result
