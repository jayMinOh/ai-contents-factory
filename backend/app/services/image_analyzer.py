"""
Image Analysis Service using Google Gemini Vision.

Analyzes product images to generate detailed descriptions for AI image generation.
"""

import asyncio
import base64
import logging
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductImageAnalyzer:
    """Analyze product images using Gemini Vision to generate descriptions."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def analyze(self, image_data: bytes, mime_type: str = "image/png") -> str:
        """
        Analyze a product image and generate a detailed description.

        Args:
            image_data: Raw image bytes
            mime_type: Image MIME type (image/png, image/jpeg, etc.)

        Returns:
            Detailed description of the product's appearance
        """
        system_instruction = """You are a product packaging analyst for cosmetic and beauty products.
Your task is to describe the physical appearance of products in detail for AI image generation.

Focus on:
1. Container type (bottle, tube, jar, pump, dropper, etc.)
2. Container material (glass, plastic, metal, etc.)
3. Container color and finish (matte, glossy, transparent, frosted, etc.)
4. Cap/closure type and color
5. Label design (if visible)
6. Size/proportions
7. Any distinctive design elements

Output format: A single paragraph in English, 50-100 words, describing the product's physical appearance.
Be specific about colors, shapes, and materials. This description will be used to generate consistent images of this product.

Example output: "A sleek 30ml glass dropper bottle with frosted white finish, featuring a rose gold metallic cap and dropper. The minimalist label is white with subtle gray text. The bottle has an elegant tapered shape with a flat base, giving it a premium, luxurious appearance typical of high-end serums."
"""

        def _analyze():
            # Encode image to base64
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            return self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime_type,
                                    data=image_b64,
                                )
                            ),
                            types.Part(text="Describe this product's physical appearance for image generation:"),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                    max_output_tokens=200,
                ),
            )

        try:
            response = await asyncio.to_thread(_analyze)
            description = response.text.strip()
            logger.info(f"Image analyzed: {description[:50]}...")
            return description
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise Exception(f"Image analysis failed: {str(e)}")


class MarketingImageAnalyzer:
    """Analyze marketing images to detect type and content for image generation."""

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def analyze(self, image_path: str, language: str = "en") -> dict:
        """
        Analyze an image and return its type, description, and detected elements.

        Args:
            image_path: Path to the image file
            language: Language code for descriptions (e.g., 'ko', 'en', 'ja')

        Returns:
            Dictionary with:
            - description: Detailed description of the image
            - detected_type: One of 'background', 'product', 'reference', 'person', 'unknown'
            - elements: List of detected elements/objects in the image
        """
        import os

        # Read image file
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        with open(image_path, "rb") as f:
            image_data = f.read()

        # Determine MIME type from extension
        ext = image_path.lower().split(".")[-1]
        mime_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
        }
        mime_type = mime_type_map.get(ext, "image/jpeg")

        # Map language code to full name
        language_names = {
            "ko": "Korean", "en": "English", "ja": "Japanese",
            "zh": "Chinese", "es": "Spanish", "fr": "French", "de": "German"
        }
        lang_name = language_names.get(language[:2].lower(), "English")

        system_instruction = f"""You are an expert image analyst for marketing content creation.
Analyze the uploaded image and classify it for AI image generation purposes.

IMPORTANT: Write ALL text responses (description, elements, visual_prompt) in {lang_name}.

Your task:
1. Determine the image type:
   - "background": Landscape, texture, abstract, scenic backgrounds suitable for product placement
   - "product": Physical products, packages, bottles, cosmetics, items being marketed
   - "reference": Style reference images showing desired aesthetic, mood, or composition
   - "person": Images featuring people or human subjects
   - "unknown": Cannot be classified into above categories

2. Determine if the image is REALISTIC or not:
   - is_realistic = true: Real photographs, photorealistic renders, actual product photos
   - is_realistic = false: Illustrations, cartoons, anime, digital art, paintings, stylized graphics

3. Provide description based on image type:

FOR PRODUCT IMAGES (detected_type = "product"):
Provide an EXTREMELY DETAILED visual description that can recreate the product in AI image generation:
- Exact container type (bottle, tube, jar, pump dispenser, dropper, compact, etc.)
- Material and finish (glass, plastic, metal, matte, glossy, frosted, transparent, etc.)
- Precise colors (use specific color names: rose gold, pearl white, deep burgundy, etc.)
- Shape and proportions (tall/short, slim/wide, curved/angular, etc.)
- Cap/closure details (color, material, shape)
- Label/branding (position, colors, text if readable, logo description)
- Any decorative elements (gold accents, embossing, patterns, etc.)
- Size estimation (small travel-size, standard, large, etc.)

FOR BACKGROUND IMAGES:
Describe the scene, lighting, mood, colors, and texture suitable for product placement.

FOR REFERENCE IMAGES:
Describe the style, composition, color palette, mood, and aesthetic elements.

4. List key visual elements detected in the image

Output your analysis in this exact JSON format:
{{
    "detected_type": "background|product|reference|person|unknown",
    "is_realistic": true or false,
    "description": "Detailed description...",
    "elements": ["element1", "element2", "element3"],
    "visual_prompt": "For product: A highly detailed prompt that can recreate this exact product appearance in AI image generation. For others: key visual characteristics."
}}

IMPORTANT: For product images, the visual_prompt should be detailed enough that an AI image generator can recreate the product's exact appearance without seeing the original image.
"""

        def _analyze():
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            return self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        parts=[
                            types.Part(
                                inline_data=types.Blob(
                                    mime_type=mime_type,
                                    data=image_b64,
                                )
                            ),
                            types.Part(text="Analyze this image for marketing content creation:"),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_output_tokens=1000,  # Increased for detailed product descriptions
                ),
            )

        try:
            response = await asyncio.to_thread(_analyze)
            response_text = response.text.strip()

            # Parse JSON response
            import json

            # Clean up the response if it contains markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            result = json.loads(response_text)
            # Ensure visual_prompt exists
            if "visual_prompt" not in result:
                result["visual_prompt"] = result.get("description", "")
            # Ensure is_realistic exists (default to True for safety)
            if "is_realistic" not in result:
                result["is_realistic"] = True
            logger.info(f"Marketing image analyzed: type={result.get('detected_type')}, is_realistic={result.get('is_realistic')}")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}. Response: {response_text[:200]}")
            # Return fallback response
            return {
                "detected_type": "unknown",
                "is_realistic": True,
                "description": response_text[:200] if response_text else "이미지 분석 결과를 파싱할 수 없습니다.",
                "elements": [],
                "visual_prompt": "",
            }
        except Exception as e:
            logger.error(f"Marketing image analysis failed: {e}")
            raise Exception(f"Image analysis failed: {str(e)}")


# Singleton instances
_analyzer: Optional[ProductImageAnalyzer] = None
_marketing_analyzer: Optional[MarketingImageAnalyzer] = None


def get_product_image_analyzer() -> ProductImageAnalyzer:
    """Get or create product image analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ProductImageAnalyzer()
    return _analyzer


def get_marketing_image_analyzer() -> MarketingImageAnalyzer:
    """Get or create marketing image analyzer instance."""
    global _marketing_analyzer
    if _marketing_analyzer is None:
        _marketing_analyzer = MarketingImageAnalyzer()
    return _marketing_analyzer


__all__ = [
    "ProductImageAnalyzer",
    "get_product_image_analyzer",
    "MarketingImageAnalyzer",
    "get_marketing_image_analyzer",
]
