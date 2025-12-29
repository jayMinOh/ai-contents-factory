"""
Content Image Analyzer Service

AI-powered image analysis using Google Gemini Vision API for SNS content.
Analyzes composition, color schemes, styles, and visual elements.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any

from app.core.config import settings
from app.services.image_metadata import ImageMetadataExtractor, ImageMetadataError

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


class ImageAnalysisError(Exception):
    """Raised when image analysis fails."""
    pass


class ContentImageAnalyzer:
    """
    Analyze images for SNS content creation.

    Provides:
    - Composition analysis (rule of thirds, centered, etc.)
    - Color scheme detection (warm, cool, vibrant, etc.)
    - Style classification (modern, minimalist, etc.)
    - Element detection (product, people, text, background, etc.)
    """

    def __init__(self):
        """Initialize analyzer with Gemini API."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai is not installed")

        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.metadata_extractor = ImageMetadataExtractor()

    async def analyze(
        self,
        image_data: Optional[bytes],
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Analyze image using Gemini Vision API.

        Args:
            image_data: Raw image bytes
            max_retries: Maximum retry attempts on failure

        Returns:
            Dictionary with analysis results and metadata

        Raises:
            ImageAnalysisError: If analysis fails
        """
        if not image_data:
            raise ImageAnalysisError("Image data cannot be empty")

        # Extract metadata first
        try:
            metadata = self.metadata_extractor.extract_from_bytes(
                image_data,
                mime_type="image/jpeg"
            )
        except ImageMetadataError as e:
            raise ImageAnalysisError(f"Image metadata extraction failed: {str(e)}")

        # Retry logic for Gemini API calls
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                analysis = await self._call_gemini(image_data)

                if analysis is None:
                    raise ImageAnalysisError("Gemini returned empty response")

                # Merge analysis with metadata
                result = {**analysis, **metadata}
                logger.info(f"Image analysis completed: {result.get('style', 'unknown')}")
                return result

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if error is retryable
                is_retryable = any(keyword in error_msg for keyword in [
                    'timeout', 'connection', 'unavailable', '503', '504',
                    'rate limit', 'quota', 'overloaded'
                ])

                if is_retryable and attempt < max_retries:
                    wait_time = attempt * 2  # 2s, 4s exponential backoff
                    logger.warning(f"Retryable error (attempt {attempt}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ImageAnalysisError(f"Image analysis failed: {str(e)}")

        raise ImageAnalysisError(f"Analysis failed after {max_retries} attempts: {last_error}")

    async def _call_gemini(self, image_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Call Gemini Vision API to analyze image.

        Args:
            image_data: Raw image bytes

        Returns:
            Analysis results dictionary or None

        Raises:
            Exception: If API call fails
        """
        import base64

        system_instruction = """You are an expert SNS content analyst specializing in Instagram,
Facebook, and Pinterest marketing content. Analyze the provided image for content creation purposes.

Provide analysis in the following JSON format:
{
    "composition": "description of how elements are arranged (e.g., 'rule_of_thirds', 'centered', 'diagonal', 'leading_lines')",
    "colorScheme": ["list", "of", "color", "characteristics", "e.g.", "warm", "red", "gold"],
    "style": "overall visual style (e.g., 'minimalist', 'modern', 'luxury', 'playful', 'professional')",
    "elements": ["list", "of", "detected", "elements", "e.g.", "product", "text", "people", "background"]
}

Focus on:
1. COMPOSITION: How is the image structured? What compositional technique is used?
2. COLOR SCHEME: What colors dominate? Are they warm/cool? Vibrant/muted?
3. STYLE: What is the overall aesthetic? Professional? Casual? Luxury? Minimalist?
4. ELEMENTS: What objects/content are present? Product, people, text, nature, background?

Return ONLY valid JSON, no additional text."""

        def _analyze():
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            response = self.client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type="image/jpeg",
                                    data=image_b64,
                                )
                            ),
                            types.Part(text="Analyze this image for SNS content:"),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=500,
                ),
            )

            return response.text.strip()

        try:
            response_text = await asyncio.to_thread(_analyze)
            result = self._parse_analysis_response(response_text)
            return result

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    @staticmethod
    def _parse_analysis_response(response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse Gemini response as JSON.

        Args:
            response_text: Raw response from Gemini

        Returns:
            Parsed JSON dictionary or None

        Raises:
            Exception: If parsing fails
        """
        # Clean up response (remove markdown code blocks if present)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        # Parse JSON
        result = json.loads(response_text)

        # Ensure required fields exist
        result.setdefault("composition", "")
        result.setdefault("colorScheme", [])
        result.setdefault("style", "")
        result.setdefault("elements", [])

        return result


def get_content_image_analyzer() -> ContentImageAnalyzer:
    """Get or create analyzer instance."""
    return ContentImageAnalyzer()
