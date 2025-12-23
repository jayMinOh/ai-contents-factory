"""
Storyboard Generation Service V2.

This service uses Google Gemini to generate storyboards based on content type,
purpose, and either a free-form prompt or reference analysis data.

Supports:
- Content types: single (1 slide), carousel (5-10 slides), story (vertical format)
- Purposes: ad (advertising), info (informational), lifestyle (casual/emotional)
- Methods: reference (based on analysis), prompt (free-form)
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from app.core.config import settings


logger = logging.getLogger(__name__)


class StoryboardGeneratorV2:
    """
    AI-powered storyboard generator using Google Gemini.

    Generates structured storyboards with visual prompts optimized for
    AI image generation.
    """

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate(
        self,
        content_type: str,
        purpose: str,
        method: str,
        prompt: Optional[str] = None,
        brand_info: Optional[Dict[str, Any]] = None,
        product_info: Optional[Dict[str, Any]] = None,
        reference_analysis: Optional[Dict[str, Any]] = None,
        selected_items: Optional[Dict[str, Any]] = None,
        language: str = "ko",
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a storyboard based on the provided parameters.

        Args:
            content_type: Type of content (single, carousel, story)
            purpose: Purpose of the content (ad, info, lifestyle)
            method: Generation method (reference, prompt)
            prompt: Free-form prompt for method='prompt'
            brand_info: Brand information dict
            product_info: Product information dict
            reference_analysis: Reference analysis data for method='reference'
            selected_items: Selected items from reference analysis
            language: Output language code
            aspect_ratio: Aspect ratio for visual prompts

        Returns:
            Dict containing storyboard_id, slides, total_slides, storyline, etc.
        """
        # Determine aspect ratio based on content type if not provided
        if not aspect_ratio:
            aspect_ratio = self._get_default_aspect_ratio(content_type)

        # Build the generation prompt
        gemini_prompt = self._build_prompt(
            content_type=content_type,
            purpose=purpose,
            method=method,
            user_prompt=prompt,
            brand_info=brand_info,
            product_info=product_info,
            reference_analysis=reference_analysis,
            selected_items=selected_items,
            language=language,
            aspect_ratio=aspect_ratio,
        )

        logger.info(f"Generating storyboard: type={content_type}, purpose={purpose}, method={method}")

        # Call Gemini API with retry logic
        result = await self._call_gemini_with_retry(gemini_prompt)

        if not result or "slides" not in result:
            raise ValueError("Failed to generate valid storyboard from Gemini")

        # Add metadata
        storyboard_id = str(uuid.uuid4())
        result["storyboard_id"] = storyboard_id
        result["total_slides"] = len(result.get("slides", []))
        result["content_type"] = content_type
        result["purpose"] = purpose
        result["generation_method"] = method
        result["created_at"] = datetime.utcnow().isoformat()

        return result

    def _get_default_aspect_ratio(self, content_type: str) -> str:
        """Get default aspect ratio based on content type."""
        ratios = {
            "single": "1:1",
            "carousel": "1:1",
            "story": "9:16",
        }
        return ratios.get(content_type, "1:1")

    def _build_prompt(
        self,
        content_type: str,
        purpose: str,
        method: str,
        user_prompt: Optional[str],
        brand_info: Optional[Dict[str, Any]],
        product_info: Optional[Dict[str, Any]],
        reference_analysis: Optional[Dict[str, Any]],
        selected_items: Optional[Dict[str, Any]],
        language: str,
        aspect_ratio: str,
    ) -> str:
        """Build the Gemini prompt for storyboard generation."""

        # Determine slide count based on content type
        slide_counts = {
            "single": "exactly 1",
            "carousel": "5 to 10",
            "story": "3 to 7",
        }
        slide_count = slide_counts.get(content_type, "5")

        # Purpose-specific guidance
        purpose_guidance = self._get_purpose_guidance(purpose)

        # Content type guidance
        content_guidance = self._get_content_type_guidance(content_type)

        # Language instruction
        lang_instruction = self._get_language_instruction(language)

        # Build context sections
        brand_context = self._format_brand_context(brand_info) if brand_info else ""
        product_context = self._format_product_context(product_info) if product_info else ""
        reference_context = ""
        selected_context = ""

        if method == "reference" and reference_analysis:
            reference_context = self._format_reference_context(reference_analysis)
            if selected_items:
                selected_context = self._format_selected_items(selected_items)

        # Build the main prompt
        prompt = f"""You are an expert marketing content strategist and storyboard creator.

{lang_instruction}

## Task
Create a storyboard for a {content_type} format marketing content with {purpose} purpose.
Generate {slide_count} slides that tell a compelling story.

## Content Format
{content_guidance}

## Purpose Guidelines
{purpose_guidance}

## Visual Requirements
- Aspect ratio: {aspect_ratio}
- Each slide needs a detailed visual_prompt in ENGLISH that can be used for AI image generation
- Visual prompts should be specific, descriptive, and optimized for image generation
- Include composition, lighting, style, mood, and specific visual elements
- For product-focused content, ensure the product is prominently featured

{brand_context}

{product_context}

{reference_context}

{selected_context}

## User Request
{user_prompt or "Create an engaging marketing storyboard based on the provided context."}

## Output Format
Return ONLY valid JSON with no markdown formatting, no code blocks, no explanations.
The JSON must have this structure:
{{
  "slides": [
    {{
      "slide_number": 1,
      "section_type": "hook",
      "title": "Slide title in {language}",
      "description": "Detailed description of this slide's content and message in {language}",
      "visual_prompt": "Detailed English prompt for AI image generation. Include: subject, composition, lighting, style, mood, colors, background. Be specific and descriptive.",
      "visual_prompt_display": "Same visual prompt content but written in {language} for user display",
      "text_overlay": "Text to display on the slide in {language}",
      "narration_script": "Optional narration script in {language}",
      "duration_seconds": 3.0
    }}
  ],
  "storyline": "Brief summary of the overall narrative in {language}"
}}

Valid section_type values: hook, problem, solution, benefit, cta, intro, outro, transition, feature

IMPORTANT:
- visual_prompt MUST be in English and optimized for AI image generators
- visual_prompt_display MUST be in {language} and describe the same visual content for user understanding
- All other text fields (title, description, text_overlay, narration_script, storyline) should be in {language}
- Ensure each visual_prompt is detailed enough to generate a high-quality image
- For carousel content, each slide should contribute to a coherent narrative
- For story format, optimize for vertical viewing with impactful visuals"""

        return prompt

    def _get_purpose_guidance(self, purpose: str) -> str:
        """Get purpose-specific guidance."""
        guidance = {
            "ad": """
- Focus on product benefits and unique selling points
- Include clear call-to-action
- Highlight brand identity and values
- Create desire and urgency
- Professional, polished aesthetic
- Include product prominently in visuals""",
            "info": """
- Focus on educating the audience
- Present information clearly and concisely
- Use data, facts, and expert insights
- Build trust and authority
- Clean, informative visual style
- Text-heavy slides with clear hierarchy""",
            "lifestyle": """
- Focus on emotional connection
- Show real-life scenarios and moments
- Authentic, relatable aesthetic
- Subtle product integration
- Warm, inviting mood
- Storytelling through visuals""",
        }
        return guidance.get(purpose, guidance["ad"])

    def _get_content_type_guidance(self, content_type: str) -> str:
        """Get content type specific guidance."""
        guidance = {
            "single": """
- Create ONE impactful image that tells the complete story
- The single image must capture attention immediately
- All key information in one visual
- Strong focal point and clear message""",
            "carousel": """
- Create a swipeable sequence of 5-10 slides
- First slide must be the strongest hook
- Each slide should make viewers want to swipe
- Build narrative momentum across slides
- Final slide should have clear CTA
- Maintain visual consistency across all slides""",
            "story": """
- Optimized for vertical (9:16) mobile viewing
- 3-7 quick, impactful slides
- Large text for mobile readability
- Fast-paced, engaging content
- Each slide should work independently
- Strong visual hierarchy for small screens""",
        }
        return guidance.get(content_type, guidance["carousel"])

    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction."""
        instructions = {
            "ko": "IMPORTANT: Generate all text content (title, description, text_overlay, narration_script, storyline) in Korean (한국어). Only visual_prompt should be in English.",
            "en": "Generate all text content in English.",
            "ja": "IMPORTANT: Generate all text content (title, description, text_overlay, narration_script, storyline) in Japanese (日本語). Only visual_prompt should be in English.",
            "zh": "IMPORTANT: Generate all text content (title, description, text_overlay, narration_script, storyline) in Chinese (中文). Only visual_prompt should be in English.",
        }
        return instructions.get(language, instructions["en"])

    def _format_brand_context(self, brand_info: Dict[str, Any]) -> str:
        """Format brand information for the prompt."""
        if not brand_info:
            return ""

        parts = ["## Brand Information"]
        if brand_info.get("name"):
            parts.append(f"- Brand Name: {brand_info['name']}")
        if brand_info.get("description"):
            parts.append(f"- Description: {brand_info['description']}")
        if brand_info.get("tone_and_manner"):
            parts.append(f"- Tone & Manner: {brand_info['tone_and_manner']}")
        if brand_info.get("target_audience"):
            parts.append(f"- Target Audience: {brand_info['target_audience']}")
        if brand_info.get("usp"):
            parts.append(f"- USP: {brand_info['usp']}")
        if brand_info.get("keywords"):
            keywords = brand_info["keywords"]
            if isinstance(keywords, list):
                parts.append(f"- Keywords: {', '.join(keywords)}")

        return "\n".join(parts)

    def _format_product_context(self, product_info: Dict[str, Any]) -> str:
        """Format product information for the prompt."""
        if not product_info:
            return ""

        parts = ["## Product Information"]
        if product_info.get("name"):
            parts.append(f"- Product Name: {product_info['name']}")
        if product_info.get("description"):
            parts.append(f"- Description: {product_info['description']}")
        if product_info.get("image_description"):
            parts.append(f"- Product Appearance: {product_info['image_description']}")
        if product_info.get("product_category"):
            parts.append(f"- Category: {product_info['product_category']}")
        if product_info.get("features"):
            features = product_info["features"]
            if isinstance(features, list) and features:
                parts.append(f"- Features: {', '.join(features[:5])}")
        if product_info.get("benefits"):
            benefits = product_info["benefits"]
            if isinstance(benefits, list) and benefits:
                parts.append(f"- Benefits: {', '.join(benefits[:5])}")
        if product_info.get("key_ingredients"):
            ingredients = product_info["key_ingredients"]
            if isinstance(ingredients, list) and ingredients:
                ing_names = [ing.get("name", "") for ing in ingredients[:3] if isinstance(ing, dict)]
                if ing_names:
                    parts.append(f"- Key Ingredients: {', '.join(ing_names)}")
        if product_info.get("suitable_skin_types"):
            skin_types = product_info["suitable_skin_types"]
            if isinstance(skin_types, list) and skin_types:
                parts.append(f"- Suitable For: {', '.join(skin_types)}")

        return "\n".join(parts)

    def _format_reference_context(self, reference: Dict[str, Any]) -> str:
        """Format reference analysis for the prompt."""
        if not reference:
            return ""

        parts = ["## Reference Analysis"]

        if reference.get("segments"):
            segments = reference["segments"][:3]
            parts.append("### Content Structure:")
            for seg in segments:
                if isinstance(seg, dict):
                    seg_type = seg.get("segment_type", "segment")
                    desc = seg.get("description", "")[:100]
                    parts.append(f"  - {seg_type}: {desc}")

        if reference.get("hook_points"):
            hooks = reference["hook_points"][:2]
            parts.append("### Hook Techniques Used:")
            for hook in hooks:
                if isinstance(hook, dict):
                    hook_type = hook.get("hook_type", "hook")
                    desc = hook.get("description", "")[:100]
                    parts.append(f"  - {hook_type}: {desc}")

        if reference.get("selling_points"):
            selling = reference["selling_points"][:2]
            parts.append("### Selling Points:")
            for sp in selling:
                if isinstance(sp, dict):
                    technique = sp.get("technique", "")
                    desc = sp.get("description", "")[:100]
                    parts.append(f"  - {technique}: {desc}")

        return "\n".join(parts)

    def _format_selected_items(self, selected: Dict[str, Any]) -> str:
        """Format user-selected items from reference analysis."""
        if not selected:
            return ""

        parts = ["## User-Selected Elements to Incorporate"]

        if selected.get("hook_points"):
            parts.append("### Selected Hooks (use for opening slides):")
            for hook in selected["hook_points"][:2]:
                if isinstance(hook, dict):
                    parts.append(f"  - {hook.get('hook_type', '')}: {hook.get('description', '')[:100]}")

        if selected.get("triggers"):
            parts.append("### Selected Emotional Triggers (use for emotional appeal):")
            for trigger in selected["triggers"][:2]:
                if isinstance(trigger, dict):
                    parts.append(f"  - {trigger.get('trigger_type', '')}: {trigger.get('description', '')[:100]}")

        if selected.get("selling_points"):
            parts.append("### Selected Selling Points (use for benefit slides):")
            for sp in selected["selling_points"][:3]:
                if isinstance(sp, dict):
                    parts.append(f"  - {sp.get('technique', '')}: {sp.get('description', '')[:100]}")

        if selected.get("recommendations"):
            parts.append("### Selected Recommendations (apply to structure):")
            for rec in selected["recommendations"][:2]:
                if isinstance(rec, dict):
                    parts.append(f"  - {rec.get('recommendation', '')[:150]}")

        if selected.get("edge_points"):
            parts.append("### Selected Differentiation Elements:")
            for edge in selected["edge_points"][:2]:
                if isinstance(edge, dict):
                    parts.append(f"  - {edge.get('description', '')[:100]}")

        return "\n".join(parts)

    async def _call_gemini_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """Call Gemini API with retry logic."""
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                )

                result = self._extract_and_parse_json(response.text)
                if result and "slides" in result:
                    logger.info(f"Gemini storyboard generation successful on attempt {attempt}")
                    return result

                # JSON parsing failed, retry
                logger.warning(f"Failed to parse JSON on attempt {attempt}")
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                logger.error(f"Gemini API error on attempt {attempt}: {e}")

                is_retryable = any(
                    keyword in error_msg
                    for keyword in ["timeout", "connection", "network", "503", "504", "quota", "rate"]
                )

                if is_retryable and attempt < max_retries:
                    wait_time = attempt * 5
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise

        raise Exception(f"Gemini storyboard generation failed after {max_retries} attempts: {last_error}")

    def _extract_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response text."""

        # Method 1: Try direct parsing (in case response is clean JSON)
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
                # Remove trailing commas
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
        except:
            pass

        logger.error(f"Failed to extract JSON from response: {text[:500]}")
        return None


# Singleton instance
_generator_instance: Optional[StoryboardGeneratorV2] = None


def get_storyboard_generator_v2() -> StoryboardGeneratorV2:
    """Get or create the storyboard generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = StoryboardGeneratorV2()
    return _generator_instance


__all__ = [
    "StoryboardGeneratorV2",
    "get_storyboard_generator_v2",
]
