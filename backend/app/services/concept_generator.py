"""
Concept Generator Service.

This service generates "Light Storyboard" / AI concept suggestions for single image
content types (single, story). It provides visual concept, copy suggestion, and
style recommendations based on reference analysis.

Uses Google Gemini for AI-powered concept generation.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

import google.generativeai as genai

from app.core.config import settings


logger = logging.getLogger(__name__)


class ConceptGenerator:
    """
    AI-powered concept generator for single image content.

    Generates visual concepts, copy suggestions, and style recommendations
    based on reference analysis data.
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
        reference_analysis: Optional[Dict[str, Any]] = None,
        uploaded_images: Optional[Dict[str, Any]] = None,
        brand_info: Optional[Dict[str, Any]] = None,
        product_info: Optional[Dict[str, Any]] = None,
        selected_items: Optional[Dict[str, Any]] = None,
        language: str = "ko",
    ) -> Dict[str, Any]:
        """
        Generate a concept suggestion for single image content.

        Args:
            content_type: Type of content (single, story)
            purpose: Purpose of the content (ad, info, lifestyle)
            reference_analysis: Reference analysis data (for reference mode)
            uploaded_images: Uploaded image URLs/data (for upload mode)
            brand_info: Brand information dict
            product_info: Product information dict
            selected_items: Selected items from reference analysis
            language: Output language code

        Returns:
            Dict containing concept_id, visual_concept, copy_suggestion,
            style_recommendation, visual_prompt, etc.
        """
        # Build the generation prompt
        gemini_prompt = self._build_prompt(
            content_type=content_type,
            purpose=purpose,
            reference_analysis=reference_analysis,
            uploaded_images=uploaded_images,
            brand_info=brand_info,
            product_info=product_info,
            selected_items=selected_items,
            language=language,
        )

        logger.info(f"Generating concept: type={content_type}, purpose={purpose}")

        # Call Gemini API with retry logic
        result = await self._call_gemini_with_retry(gemini_prompt)

        if not result:
            raise ValueError("Failed to generate valid concept from Gemini")

        # Add metadata
        concept_id = str(uuid.uuid4())
        result["concept_id"] = concept_id
        result["content_type"] = content_type
        result["purpose"] = purpose
        result["created_at"] = datetime.utcnow().isoformat()

        return result

    def _build_prompt(
        self,
        content_type: str,
        purpose: str,
        reference_analysis: Optional[Dict[str, Any]],
        uploaded_images: Optional[Dict[str, Any]],
        brand_info: Optional[Dict[str, Any]],
        product_info: Optional[Dict[str, Any]],
        selected_items: Optional[Dict[str, Any]],
        language: str,
    ) -> str:
        """Build the Gemini prompt for concept generation."""

        # Content type guidance
        content_guidance = self._get_content_type_guidance(content_type)

        # Purpose-specific guidance
        purpose_guidance = self._get_purpose_guidance(purpose)

        # Language instruction
        lang_instruction = self._get_language_instruction(language)

        # Build context sections
        brand_context = self._format_brand_context(brand_info) if brand_info else ""
        product_context = self._format_product_context(product_info) if product_info else ""

        # Reference or Upload context
        if reference_analysis:
            reference_context = self._format_reference_context(reference_analysis)
            selected_context = self._format_selected_items(selected_items) if selected_items else ""
        elif uploaded_images:
            reference_context = self._format_uploaded_images_context(uploaded_images)
            selected_context = ""
        else:
            reference_context = ""
            selected_context = ""

        # Aspect ratio based on content type
        aspect_ratio = "9:16" if content_type == "story" else "1:1"

        prompt = f"""You are an expert marketing content strategist and creative director.

{lang_instruction}

## Task
Create a concept suggestion for a {content_type} format marketing image with {purpose} purpose.
This is a "Light Storyboard" - a pre-generation concept that guides the final image creation.

## Content Format
{content_guidance}

## Purpose Guidelines
{purpose_guidance}

## Visual Requirements
- Aspect ratio: {aspect_ratio}
- Single image that captures the complete message
- Optimized for social media engagement

{brand_context}

{product_context}

{reference_context}

{selected_context}

## Output Format
Return ONLY valid JSON with no markdown formatting, no code blocks, no explanations.
The JSON must have this structure:
{{
  "visual_concept": "Detailed visual concept description in {language}. Describe the layout, composition, focal point, and how elements are arranged. Example: '세로형의 긴 공간을 활용해 상품을 상단에, 하단엔 후킹 문구를 배치합니다.'",
  "copy_suggestion": "Hooking text/copy suggestion based on reference analysis in {language}. Example: '레퍼런스에서 분석된 \"3초 후킹\" 카피: [이걸로 피부 고민 끝]'",
  "style_recommendation": "Style and tone recommendations in {language} based on purpose. Example: '일상/감성 모드에 맞춰 자연광 느낌의 텍스처 적용'",
  "visual_prompt": "Detailed English prompt for AI image generation. CRITICAL: First determine the appropriate MEDIUM based on the style/reference: (1) If anime/illustration style requested → use '2D digital illustration, artwork, NOT a photograph' (2) If realistic/product style → use 'professional product photography, studio shot' (3) If lifestyle/casual → use 'natural candid photo style'. Always START the prompt by explicitly stating the medium (e.g., '2D anime illustration of...' or 'Professional product photo of...'). Then include: subject, composition, lighting, style, mood, colors, background. Be specific about the visual medium to prevent style confusion.",
  "visual_prompt_display": "Same visual prompt content but written in {language} for user display",
  "text_overlay_suggestion": "Suggested text to overlay on the image in {language}. Should be short, impactful, and readable."
}}

IMPORTANT:
- visual_concept should explain HOW the image will be composed (layout, arrangement)
- copy_suggestion should extract and adapt the most effective hooks from the reference
- style_recommendation should match the purpose (ad=professional/polished, info=clean/informative, lifestyle=warm/authentic)
- visual_prompt MUST be in English and optimized for AI image generators
- visual_prompt_display should convey the same content in {language}
- text_overlay_suggestion should be concise (max 15 characters for impact)
- All Korean content should use natural, engaging marketing language"""

        return prompt

    def _get_content_type_guidance(self, content_type: str) -> str:
        """Get content type specific guidance."""
        guidance = {
            "single": """
- Create ONE impactful square (1:1) image that tells the complete story
- The single image must capture attention immediately
- All key information in one visual
- Strong focal point and clear message
- Balanced composition suitable for feed posts""",
            "story": """
- Create ONE impactful vertical (9:16) image for mobile viewing
- Optimized for full-screen mobile experience
- Large, readable text elements
- Vertical composition that guides the eye from top to bottom
- Strong visual hierarchy for small screens""",
        }
        return guidance.get(content_type, guidance["single"])

    def _get_purpose_guidance(self, purpose: str) -> str:
        """Get purpose-specific guidance."""
        guidance = {
            "ad": """
- Focus on product benefits and unique selling points
- Include clear call-to-action potential
- Highlight brand identity and values
- Create desire and urgency
- Professional, polished aesthetic
- Product should be prominently featured""",
            "info": """
- Focus on educating the audience
- Present information clearly and concisely
- Use data, facts, and expert insights
- Build trust and authority
- Clean, informative visual style
- Text should have clear hierarchy""",
            "lifestyle": """
- Focus on emotional connection
- Show real-life scenarios and moments
- Authentic, relatable aesthetic
- Subtle product integration if applicable
- Warm, inviting mood
- Natural lighting and textures
- Storytelling through visuals""",
        }
        return guidance.get(purpose, guidance["ad"])

    def _get_language_instruction(self, language: str) -> str:
        """Get language-specific instruction."""
        instructions = {
            "ko": "IMPORTANT: Generate all text content (visual_concept, copy_suggestion, style_recommendation, visual_prompt_display, text_overlay_suggestion) in Korean (한국어). Only visual_prompt should be in English.",
            "en": "Generate all text content in English.",
            "ja": "IMPORTANT: Generate all text content in Japanese (日本語). Only visual_prompt should be in English.",
            "zh": "IMPORTANT: Generate all text content in Chinese (中文). Only visual_prompt should be in English.",
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

        return "\n".join(parts)

    def _format_reference_context(self, reference: Dict[str, Any]) -> str:
        """Format reference analysis for the prompt."""
        if not reference:
            return ""

        parts = ["## Reference Analysis (Source for Concept)"]

        if reference.get("hook_points"):
            hooks = reference["hook_points"][:3]
            parts.append("### Hook Techniques to Apply:")
            for hook in hooks:
                if isinstance(hook, dict):
                    hook_type = hook.get("hook_type", "hook")
                    desc = hook.get("description", "")[:150]
                    template = hook.get("adaptable_template", "")
                    parts.append(f"  - {hook_type}: {desc}")
                    if template:
                        parts.append(f"    Template: {template}")

        if reference.get("emotional_triggers"):
            triggers = reference["emotional_triggers"][:2]
            parts.append("### Emotional Triggers to Use:")
            for trigger in triggers:
                if isinstance(trigger, dict):
                    trig_type = trigger.get("trigger_type", "")
                    desc = trigger.get("description", "")[:100]
                    parts.append(f"  - {trig_type}: {desc}")

        if reference.get("selling_points"):
            selling = reference["selling_points"][:3]
            parts.append("### Selling Techniques:")
            for sp in selling:
                if isinstance(sp, dict):
                    technique = sp.get("persuasion_technique", sp.get("technique", ""))
                    claim = sp.get("claim", "")[:100]
                    parts.append(f"  - {technique}: {claim}")

        if reference.get("cta_analysis"):
            cta = reference["cta_analysis"]
            if isinstance(cta, dict):
                cta_type = cta.get("cta_type", "")
                urgency = cta.get("urgency_elements", [])
                parts.append("### CTA Style:")
                parts.append(f"  - Type: {cta_type}")
                if urgency:
                    parts.append(f"  - Urgency Elements: {', '.join(urgency[:3])}")

        if reference.get("recommendations"):
            recs = reference["recommendations"][:2]
            parts.append("### Key Recommendations:")
            for rec in recs:
                if isinstance(rec, dict):
                    action = rec.get("action", rec.get("recommendation", ""))[:150]
                    parts.append(f"  - {action}")

        return "\n".join(parts)

    def _format_selected_items(self, selected: Dict[str, Any]) -> str:
        """Format user-selected items from reference analysis."""
        if not selected:
            return ""

        parts = ["## User-Selected Elements (Prioritize These)"]

        if selected.get("hook_points"):
            parts.append("### Selected Hooks (MUST use for copy):")
            for hook in selected["hook_points"][:2]:
                if isinstance(hook, dict):
                    parts.append(f"  - {hook.get('hook_type', '')}: {hook.get('description', '')[:100]}")

        if selected.get("triggers"):
            parts.append("### Selected Emotional Triggers (MUST incorporate):")
            for trigger in selected["triggers"][:2]:
                if isinstance(trigger, dict):
                    parts.append(f"  - {trigger.get('trigger_type', '')}: {trigger.get('description', '')[:100]}")

        if selected.get("selling_points"):
            parts.append("### Selected Selling Points (feature in visual):")
            for sp in selected["selling_points"][:2]:
                if isinstance(sp, dict):
                    parts.append(f"  - {sp.get('technique', sp.get('claim', ''))[:100]}")

        return "\n".join(parts)

    def _format_uploaded_images_context(self, uploaded_images: Dict[str, Any]) -> str:
        """Format uploaded images context for the prompt."""
        if not uploaded_images:
            return ""

        parts = ["## Image Context (User Uploaded)"]

        reference_urls = uploaded_images.get("reference_image_urls", [])
        if reference_urls:
            num_images = len(reference_urls)
            parts.append(f"### Reference Images ({num_images} image(s))")
            parts.append(f"  - {num_images} reference image(s) have been uploaded for style guidance")
            parts.append("  - Analyze the common visual elements, colors, and composition style")
            parts.append("  - Use similar aesthetics, lighting, and mood in the concept")
            if num_images > 1:
                parts.append("  - Find the common thread among all reference images")

        if uploaded_images.get("user_prompt"):
            user_prompt = uploaded_images["user_prompt"]
            parts.append("### User's Instructions")
            parts.append(f"  {user_prompt}")

        if reference_urls:
            parts.append("")
            parts.append("IMPORTANT: Since user uploaded reference images:")
            parts.append("- Analyze the visual style, colors, and composition from the references")
            parts.append("- The visual_prompt should describe a new image inspired by the references")
            parts.append("- Suggest backgrounds, lighting, and effects that match the reference style")
        else:
            parts.append("")
            parts.append("IMPORTANT: No reference images provided, using prompt only:")
            parts.append("- Create a concept based entirely on the user's text description")
            parts.append("- Be creative but stay within the described style parameters")

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
                if result and "visual_concept" in result:
                    logger.info(f"Gemini concept generation successful on attempt {attempt}")
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

        raise Exception(f"Gemini concept generation failed after {max_retries} attempts: {last_error}")

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
                # Remove trailing commas
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
        except:
            pass

        logger.error(f"Failed to extract JSON from response: {text[:500]}")
        return None


# Singleton instance
_generator_instance: Optional[ConceptGenerator] = None


def get_concept_generator() -> ConceptGenerator:
    """Get or create the concept generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = ConceptGenerator()
    return _generator_instance


__all__ = [
    "ConceptGenerator",
    "get_concept_generator",
]
