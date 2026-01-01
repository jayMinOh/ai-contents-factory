"""
Prompt Enhancer Service.

Enhances simple user prompts into detailed, optimized prompts
for AI image generation (Gemini/Nano Banana Pro).
"""

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from app.core.config import settings


logger = logging.getLogger(__name__)


class PromptEnhancer:
    """
    AI-powered prompt enhancement for image generation.

    Takes a simple user prompt and image context, then generates
    a detailed, optimized prompt that Gemini/Nano Banana Pro
    can better understand and execute.
    """

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def enhance(
        self,
        user_prompt: str,
        images: Optional[List[Dict[str, Any]]] = None,
        aspect_ratio: str = "1:1",
        language: str = "ko",
    ) -> Dict[str, Any]:
        """
        Enhance a user prompt for optimal image generation.

        Args:
            user_prompt: User's simple prompt
            images: List of image contexts with detected_type, is_realistic, description
            aspect_ratio: Target aspect ratio (1:1, 4:5, 9:16, 16:9)
            language: Output language code

        Returns:
            Dict containing enhanced_prompt, enhanced_prompt_display,
            composition_suggestion, detected_intent
        """
        images = images or []

        # Analyze image contexts
        has_product = any(img.get("detected_type") == "product" for img in images)
        has_background = any(img.get("detected_type") == "background" for img in images)
        has_reference = any(img.get("detected_type") == "reference" for img in images)
        is_realistic = all(img.get("is_realistic", True) for img in images)

        # Determine intent
        if has_product and has_background:
            detected_intent = "composite"
        elif has_product and not has_background:
            detected_intent = "edit"
        elif has_reference:
            detected_intent = "style_transfer"
        else:
            detected_intent = "generate"

        # Build the enhancement prompt
        gemini_prompt = self._build_prompt(
            user_prompt=user_prompt,
            images=images,
            aspect_ratio=aspect_ratio,
            language=language,
            detected_intent=detected_intent,
            is_realistic=is_realistic,
        )

        logger.info(f"Enhancing prompt: intent={detected_intent}, images={len(images)}")

        # Call Gemini API
        result = await self._call_gemini(gemini_prompt)

        if not result:
            # Fallback: return minimally enhanced prompt
            return {
                "original_prompt": user_prompt,
                "enhanced_prompt": user_prompt,
                "enhanced_prompt_display": user_prompt,
                "composition_suggestion": None,
                "detected_intent": detected_intent,
            }

        result["original_prompt"] = user_prompt
        result["detected_intent"] = detected_intent

        return result

    def _build_prompt(
        self,
        user_prompt: str,
        images: List[Dict[str, Any]],
        aspect_ratio: str,
        language: str,
        detected_intent: str,
        is_realistic: bool,
    ) -> str:
        """Build the Gemini prompt for enhancement."""

        # Language instruction
        lang_instruction = self._get_language_instruction(language)

        # Image context description
        image_context = self._format_image_context(images)

        # Intent-specific guidance
        intent_guidance = self._get_intent_guidance(detected_intent, is_realistic)

        prompt = f"""You are an expert prompt engineer for AI image generation.
Your task is to enhance a simple user prompt into a detailed, optimized prompt
that will produce high-quality results with Gemini Image Generation.

{lang_instruction}

## User's Original Prompt
"{user_prompt}"

## Target Specifications
- Aspect Ratio: {aspect_ratio}
- Visual Style: {"Photorealistic" if is_realistic else "Illustration/Artistic"}

{image_context}

## Enhancement Guidelines
{intent_guidance}

## Key Enhancement Rules
1. Add specific details about lighting, composition, and atmosphere
2. Include technical photography/art terms when appropriate
3. Specify camera angle and perspective if relevant
4. Describe textures, materials, and surface qualities
5. Add mood and emotional tone descriptors
6. For product images: ensure product is prominently featured and recognizable
7. Keep the enhanced prompt concise but detailed (50-150 words)
8. CRITICAL: The enhanced prompt must be actionable for AI image generation

## Output Format
Return ONLY valid JSON with no markdown formatting:
{{
    "enhanced_prompt": "Detailed English prompt optimized for AI image generation. Start with the main subject, then add composition, lighting, style, and mood details.",
    "enhanced_prompt_display": "Same content but in {language} for user display",
    "composition_suggestion": "Brief suggestion about image composition in {language}"
}}

IMPORTANT:
- enhanced_prompt MUST be in English for optimal AI generation
- enhanced_prompt_display MUST be in {language}
- Both should convey the same meaning
- Be specific but avoid overly complex descriptions"""

        return prompt

    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction."""
        instructions = {
            "ko": "Generate enhanced_prompt_display and composition_suggestion in Korean (한국어).",
            "en": "Generate all text content in English.",
            "ja": "Generate enhanced_prompt_display and composition_suggestion in Japanese (日本語).",
            "zh": "Generate enhanced_prompt_display and composition_suggestion in Chinese (中文).",
        }
        return instructions.get(language, instructions["en"])

    def _format_image_context(self, images: List[Dict[str, Any]]) -> str:
        """Format image context for the prompt."""
        if not images:
            return "## Image Context\nNo reference images provided. Generate based on text prompt only."

        parts = ["## Image Context"]

        for i, img in enumerate(images, 1):
            img_type = img.get("detected_type", "unknown")
            is_realistic = img.get("is_realistic", True)
            description = img.get("description", "")
            visual_prompt = img.get("visual_prompt", "")

            parts.append(f"\n### Image {i}: {img_type.upper()}")
            parts.append(f"- Style: {'Photorealistic' if is_realistic else 'Illustration/Artistic'}")
            if description:
                parts.append(f"- Description: {description[:200]}")
            if visual_prompt:
                parts.append(f"- Visual Details: {visual_prompt[:200]}")

        return "\n".join(parts)

    def _get_intent_guidance(self, intent: str, is_realistic: bool) -> str:
        """Get intent-specific enhancement guidance."""
        guidance = {
            "composite": """
COMPOSITE MODE: Product + Background
- Describe how the product should be placed on the background
- Specify realistic shadows and lighting integration
- Ensure the product maintains its exact appearance
- Add details about the scene context and atmosphere
- Consider perspective and scale matching""",
            "edit": """
EDIT MODE: Product in New Context
- Describe the new scene/context for the product
- Keep the product as the focal point
- Add environmental details (lighting, setting, mood)
- Specify any additional elements around the product
- Maintain product visual consistency""",
            "style_transfer": """
STYLE REFERENCE MODE: Apply Reference Style
- Describe the style elements to apply
- Specify color palette, mood, and aesthetic
- Include composition and framing details
- Add texture and visual effect descriptions""",
            "generate": """
GENERATION MODE: Create New Image
- Be specific about the main subject
- Add detailed environment and setting descriptions
- Specify lighting conditions and atmosphere
- Include composition and framing instructions
- Describe the overall mood and feel""",
        }

        base = guidance.get(intent, guidance["generate"])

        if not is_realistic:
            base += "\n- Use artistic/illustration style terminology"
            base += "\n- Specify art style (anime, digital art, watercolor, etc.)"

        return base

    async def _call_gemini(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API and parse response."""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
            )

            result = self._extract_and_parse_json(response.text)
            if result and "enhanced_prompt" in result:
                logger.info("Prompt enhancement successful")
                return result

            logger.warning("Failed to parse enhancement response")
            return None

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None

    def _extract_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response text."""

        # Method 1: Try direct parsing
        try:
            return json.loads(text.strip())
        except:
            pass

        # Method 2: ```json ... ``` block
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # Method 3: ``` ... ``` block
        if "```" in text:
            try:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # Method 4: Find { } block
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass

        # Method 5: Fix common JSON errors
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
        except:
            pass

        logger.error(f"Failed to extract JSON from response: {text[:300]}")
        return None


# Singleton instance
_enhancer_instance: Optional[PromptEnhancer] = None


def get_prompt_enhancer() -> PromptEnhancer:
    """Get or create the prompt enhancer instance."""
    global _enhancer_instance
    if _enhancer_instance is None:
        _enhancer_instance = PromptEnhancer()
    return _enhancer_instance


__all__ = [
    "PromptEnhancer",
    "get_prompt_enhancer",
]
