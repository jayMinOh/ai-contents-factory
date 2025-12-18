"""
Video Prompt Builder for Marketing Video Generation.

This module provides the VideoPromptBuilder class that constructs optimized prompts
for video generation AI models (specifically Veo API). The builder supports two modes:

1. Image-to-Video Mode: When scene has image_data, generates simple English motion
   prompts (max 30 words) focusing on camera work and movement.

2. Text-to-Video Mode: When no scene image exists, generates descriptive prompts
   with product context (max 50 words).

All prompts are output in English for optimal Veo API compatibility.

Korean text is translated to English using Gemini LLM for natural sentence handling,
with fallback to keyword mapping if API fails.
"""

import asyncio
import logging
import re
from typing import Optional, List, Dict

import google.generativeai as genai

from app.core.config import settings
from .video_generator_service import SceneInput

logger = logging.getLogger(__name__)


# Simple in-memory cache for LLM translations to avoid repeated API calls
_translation_cache: Dict[str, str] = {}

# Maximum cache size to prevent memory issues
_MAX_CACHE_SIZE = 500


def _contains_korean(text: str) -> bool:
    """
    Check if text contains Korean characters.

    Args:
        text: Input text to check.

    Returns:
        True if text contains Korean characters, False otherwise.
    """
    if not text:
        return False
    # Korean Unicode ranges: Hangul Jamo, Hangul Compatibility Jamo,
    # Hangul Syllables, Hangul Jamo Extended-A/B
    korean_pattern = re.compile(r'[\uac00-\ud7af\u1100-\u11ff\u3130-\u318f\ua960-\ua97f\ud7b0-\ud7ff]')
    return bool(korean_pattern.search(text))


async def translate_korean_to_english_llm(text: str) -> str:
    """
    Translate Korean text to English using Gemini LLM.

    Optimized for video generation prompts - produces concise, visual descriptions.
    Uses in-memory cache to avoid repeated API calls for the same text.

    Args:
        text: Korean text to translate.

    Returns:
        English translation optimized for video prompts.
        Returns original text if translation fails or text is already English.
    """
    global _translation_cache

    if not text or not text.strip():
        return ""

    # Check if text contains Korean
    if not _contains_korean(text):
        return text

    # Check cache first
    cache_key = text.strip()
    if cache_key in _translation_cache:
        logger.debug(f"Translation cache hit: '{text[:30]}...'")
        return _translation_cache[cache_key]

    # Check if API key is configured
    if not settings.GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not configured, falling back to keyword mapping")
        return text

    try:
        # Configure Gemini
        genai.configure(api_key=settings.GOOGLE_API_KEY)

        # Use gemini-2.0-flash-lite for fast, cheap translations
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        system_prompt = """You are a translator specializing in video production directions.
Translate the Korean text to concise English optimized for video generation AI.

Rules:
1. Output ONLY the English translation, no explanations
2. Keep it concise (under 25 words)
3. Focus on visual actions, camera movements, and scene descriptions
4. Translate naturally, not word-by-word
5. Preserve technical video terms (close-up, pan, zoom, etc.)
6. Convert Korean expressions to equivalent English video directions

Example:
Korean: "엉킨 머리카락을 빗다가 좌절하는 person의 뒷모습"
English: "Back view of person brushing tangled hair with frustrated expression"

Korean: "제품을 손에 들고 카메라를 향해 자연스럽게 미소짓는 모습"
English: "Person holding product, naturally smiling at camera"
"""

        def _generate():
            return model.generate_content(
                f"{system_prompt}\n\nTranslate this Korean video direction to English:\n{text}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=100,
                )
            )

        # Run synchronously in thread pool for async compatibility
        response = await asyncio.to_thread(_generate)
        translated = response.text.strip()

        # Basic validation - ensure we got a reasonable response
        if translated and len(translated) > 0 and not _contains_korean(translated):
            # Manage cache size
            if len(_translation_cache) >= _MAX_CACHE_SIZE:
                # Remove oldest entries (first 100)
                keys_to_remove = list(_translation_cache.keys())[:100]
                for key in keys_to_remove:
                    del _translation_cache[key]

            _translation_cache[cache_key] = translated
            logger.info(f"LLM translation: '{text[:30]}...' -> '{translated[:30]}...'")
            return translated
        else:
            logger.warning(f"Invalid translation result, falling back to keyword mapping")
            return text

    except Exception as e:
        logger.warning(f"LLM translation failed: {e}, falling back to keyword mapping")
        return text


def translate_korean_to_english_llm_sync(text: str) -> str:
    """
    Synchronous wrapper for translate_korean_to_english_llm.

    For use in synchronous code paths. Uses ThreadPoolExecutor to handle
    both sync and async contexts safely.

    Args:
        text: Korean text to translate.

    Returns:
        English translation optimized for video prompts.
    """
    import concurrent.futures

    if not text or not _contains_korean(text):
        return text if text else ""

    def _run_translation():
        """Run translation in a new event loop (for thread)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(translate_korean_to_english_llm(text))
        finally:
            loop.close()

    try:
        # Use ThreadPoolExecutor to run translation in separate thread
        # This works regardless of whether we're in an async context
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_translation)
            # Wait with timeout to avoid hanging
            result = future.result(timeout=10.0)
            return result
    except concurrent.futures.TimeoutError:
        logger.warning("Translation timed out, falling back to original text")
        return text
    except Exception as e:
        logger.warning(f"Sync translation wrapper failed: {e}")
        return text


def clear_translation_cache() -> None:
    """Clear the translation cache. Useful for testing."""
    global _translation_cache
    _translation_cache.clear()
    logger.info("Translation cache cleared")


# Korean to English concept mapping for video directions
# Used to translate Korean scene concepts to English motion directions
# Ordered by specificity (longer phrases first) to avoid partial replacements
KOREAN_TO_ENGLISH_CONCEPTS: Dict[str, str] = {
    # Camera movements - longer phrases first
    "클로즈업 샷": "close-up shot",
    "클로즈 업 샷": "close-up shot",
    "클로즈업": "close-up",
    "클로즈 업": "close-up",
    "줌인하면서": "while zooming in",
    "줌아웃하면서": "while zooming out",
    "확대하면서": "while zooming in",
    "확대": "zoom in",
    "줌인": "zoom in",
    "줌 인": "zoom in",
    "줌아웃": "zoom out",
    "줌 아웃": "zoom out",
    "축소": "zoom out",
    "팬샷": "pan shot",
    "팬": "pan",
    "패닝": "panning",
    "틸트업": "tilt up",
    "틸트다운": "tilt down",
    "틸트": "tilt",
    "돌리샷": "dolly shot",
    "돌리": "dolly",
    "트래킹샷": "tracking shot",
    "트래킹": "tracking",
    "슬라이드": "slide",
    "360도 회전": "360 degree rotation",
    "회전": "rotation",
    "360도": "360 degree",
    "오버헤드 샷": "overhead shot",
    "오버헤드": "overhead",
    "버드아이 뷰": "bird's eye view",
    "버드아이": "bird's eye view",
    "로우앵글 샷": "low angle shot",
    "로우앵글": "low angle",
    "하이앵글 샷": "high angle shot",
    "하이앵글": "high angle",
    "와이드샷": "wide shot",
    "와이드 샷": "wide shot",
    "미디엄샷": "medium shot",
    "미디엄 샷": "medium shot",
    # Transitions and effects
    "페이드인": "fade in",
    "페이드아웃": "fade out",
    "페이드": "fade",
    "디졸브": "dissolve",
    "컷": "cut",
    "와이프": "wipe",
    "크로스페이드": "crossfade",
    # Objects and subjects
    "제품 강조": "product emphasis",
    "제품 소개": "product introduction",
    "제품": "product",
    "상품": "product",
    "로고": "logo",
    "브랜드": "brand",
    "배경": "background",
    "전경": "foreground",
    "인물": "person",
    "모델": "model",
    "손": "hand",
    "얼굴": "face",
    "텍스트": "text",
    "자막": "subtitle",
    # Lighting and mood
    "자연광": "natural light",
    "스튜디오 조명": "studio lighting",
    "조명": "lighting",
    "스튜디오": "studio",
    "부드러운 조명": "soft lighting",
    "부드러운": "soft",
    "강렬한": "intense",
    "따뜻한 톤": "warm tone",
    "따뜻한": "warm",
    "차가운 톤": "cool tone",
    "차가운": "cool",
    "밝은": "bright",
    "어두운": "dark",
    "드라마틱한": "dramatic",
    "드라마틱": "dramatic",
    # Motion descriptors
    "천천히": "slowly",
    "빠르게": "quickly",
    "부드럽게": "smoothly",
    "역동적으로": "dynamically",
    "역동적": "dynamic",
    "정적인": "static",
    "정적": "static",
    "우아하게": "elegantly",
    "자연스럽게": "naturally",
    # Scene types
    "인트로": "intro",
    "아웃트로": "outro",
    "엔딩": "ending",
    "오프닝": "opening",
    # Common phrases - add spaces for proper joining
    "하면서": " while ",
    "으로": " ",
    "에서": " from ",
    "으로부터": " from ",
    # Marketing terms
    "광고": "advertisement",
    "마케팅": "marketing",
    "프로모션": "promotion",
    "캠페인": "campaign",
    # Additional common terms
    "프리미엄": "premium",
    "고급": "premium",
    "럭셔리": "luxury",
    "최신": "latest",
    "신제품": "new product",
    "베스트셀러": "bestseller",
    "할인": "discount",
    "특가": "special price",
    "한정판": "limited edition",
    "커피": "coffee",
    "메이커": "maker",
    "기계": "machine",
    "가전": "appliance",
    "전자": "electronic",
    "디지털": "digital",
    "스마트": "smart",
    "자동": "automatic",
    "고화질": "high quality",
    "깨끗한": "clean",
    "현대적인": "modern",
    "세련된": "elegant",
    "심플한": "simple",
    "미니멀": "minimal",
}

# Scene type to motion style mapping
# Maps marketing scene types to appropriate motion styles for image-to-video
SCENE_TYPE_MOTION: Dict[str, str] = {
    "hook": "dynamic",        # Attention grabbing, energetic
    "problem": "subtle",      # Empathetic, slow movements
    "solution": "cinematic",  # Hero moment, professional
    "benefit": "cinematic",   # Aspirational, smooth
    "cta": "product_focus",   # Clear product view, rotating showcase
    "intro": "cinematic",     # Professional entry
    "outro": "subtle",        # Memorable, calm ending
}

# Motion style definitions for image-to-video generation
# Each style contains a list of possible prompt templates
MOTION_STYLE_PROMPTS: Dict[str, List[str]] = {
    "cinematic": [
        "Cinematic slow zoom into center of frame, professional lighting, smooth motion",
        "Elegant camera movement with soft focus transitions, cinematic quality",
        "Smooth dolly shot with professional studio lighting, film-like motion",
        "Gradual push in with shallow depth of field, cinematic atmosphere",
    ],
    "dynamic": [
        "Dynamic camera movement with energetic pacing, attention-grabbing motion",
        "Quick zoom with vibrant energy, fast-paced marketing style",
        "Energetic pan across scene with dynamic lighting shifts",
        "Bold camera sweep with high contrast, eye-catching movement",
    ],
    "subtle": [
        "Subtle ambient motion with soft lighting, gentle atmosphere",
        "Minimal camera movement, calm and steady visual flow",
        "Soft breathing motion with atmospheric lighting, serene mood",
        "Gentle parallax effect with warm ambient glow",
    ],
    "product_focus": [
        "Slow 360 degree product rotation, clean professional lighting",
        "Smooth orbit around product, studio showcase lighting",
        "Gradual zoom on product details, commercial quality presentation",
        "Product spotlight with subtle rotation, premium showcase style",
    ],
}

# Default motion prompts when style is not specified
DEFAULT_MOTION_PROMPTS: List[str] = [
    "Smooth professional camera motion, clean visual presentation",
    "Subtle movement with balanced lighting, marketing video quality",
]

# Maximum word limits for prompts
MAX_WORDS_IMAGE_TO_VIDEO = 30
MAX_WORDS_TEXT_TO_VIDEO = 50


class VideoPromptBuilder:
    """
    Builds optimized English prompts for video generation AI models (Veo API).

    This builder supports two generation modes:
    1. Image-to-Video: Simple English motion prompts when scene has image_data
    2. Text-to-Video: Descriptive prompts with product context when no image exists

    All output prompts are in English for optimal Veo API compatibility.
    Korean input is automatically translated to English concepts.
    """

    def __init__(
        self,
        korean_to_english: Optional[Dict[str, str]] = None,
        scene_type_motion: Optional[Dict[str, str]] = None,
        motion_style_prompts: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize the VideoPromptBuilder with optional custom mappings.

        Args:
            korean_to_english: Optional dictionary to override or extend the
                default Korean to English concept mappings.
            scene_type_motion: Optional dictionary to override scene type to
                motion style mappings.
            motion_style_prompts: Optional dictionary to override motion style
                prompt templates.
        """
        # Merge custom mappings with defaults
        self.korean_to_english = KOREAN_TO_ENGLISH_CONCEPTS.copy()
        if korean_to_english:
            self.korean_to_english.update(korean_to_english)

        self.scene_type_motion = SCENE_TYPE_MOTION.copy()
        if scene_type_motion:
            self.scene_type_motion.update(scene_type_motion)

        self.motion_style_prompts = MOTION_STYLE_PROMPTS.copy()
        if motion_style_prompts:
            self.motion_style_prompts.update(motion_style_prompts)

    def translate_korean_to_english(self, text: str) -> str:
        """
        Translate Korean video direction concepts to English.

        This method first attempts LLM-based translation for natural Korean sentences.
        If LLM translation fails or returns Korean, falls back to keyword mapping.

        Args:
            text: Input text that may contain Korean terms.

        Returns:
            Text with Korean terms translated to English equivalents.
        """
        if not text:
            return ""

        # Check if text contains Korean characters
        if not _contains_korean(text):
            return text

        # Try LLM translation first for natural Korean sentences
        llm_result = translate_korean_to_english_llm_sync(text)

        # If LLM succeeded and result is different from input and doesn't contain Korean
        if llm_result and llm_result != text and not _contains_korean(llm_result):
            return llm_result

        # Fall back to keyword mapping if LLM failed or returned Korean
        logger.debug("Falling back to keyword mapping for translation")
        result = text

        # Sort by length (descending) to process longer phrases first
        # This prevents partial matches (e.g., "제품 강조" before "제품")
        sorted_mappings = sorted(
            self.korean_to_english.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for korean, english in sorted_mappings:
            result = result.replace(korean, english)

        # Clean up any resulting double spaces
        while "  " in result:
            result = result.replace("  ", " ")

        return result.strip()

    def get_motion_style(self, scene_type: Optional[str]) -> str:
        """
        Get the appropriate motion style for a scene type.

        Args:
            scene_type: The type of scene (hook, problem, solution, etc.).

        Returns:
            The motion style name (cinematic, dynamic, subtle, product_focus).
        """
        if not scene_type:
            return "cinematic"

        normalized_type = scene_type.lower().strip()
        return self.scene_type_motion.get(normalized_type, "cinematic")

    def _get_motion_prompt(self, motion_style: str, scene_number: int = 1) -> str:
        """
        Get a motion prompt template for the given style.

        Uses scene_number to vary the prompt selection for visual variety
        across multiple scenes.

        Args:
            motion_style: The motion style (cinematic, dynamic, subtle, product_focus).
            scene_number: Scene number for prompt variation.

        Returns:
            A motion prompt string.
        """
        prompts = self.motion_style_prompts.get(motion_style, DEFAULT_MOTION_PROMPTS)
        # Use modulo to cycle through available prompts
        index = (scene_number - 1) % len(prompts)
        return prompts[index]

    def _truncate_to_word_limit(self, text: str, max_words: int) -> str:
        """
        Truncate text to a maximum number of words.

        Args:
            text: The input text to truncate.
            max_words: Maximum number of words allowed.

        Returns:
            Truncated text within the word limit.
        """
        words = text.split()
        if len(words) <= max_words:
            return text

        return " ".join(words[:max_words])

    def build_image_to_video_prompt(
        self,
        scene: SceneInput,
        motion_style: Optional[str] = None,
    ) -> str:
        """
        Build a simple English prompt for image-to-video generation.

        When a scene has image_data, the image already shows the content,
        so the prompt should focus on motion and camera work rather than
        content description. Output is limited to 30 words.

        If visual_direction is available from the storyboard, it is translated
        to English and prepended to provide specific guidance before the
        generic motion style template.

        Args:
            scene: The SceneInput containing scene metadata.
            motion_style: Optional motion style override. If not provided,
                will be inferred from scene_type. Valid values:
                - "cinematic": Smooth, professional camera movements
                - "dynamic": Quick cuts, energetic motion
                - "subtle": Minimal motion, atmospheric
                - "product_focus": Rotating product showcase

        Returns:
            A simple English motion-focused prompt (max 30 words).
        """
        # Determine motion style
        if not motion_style:
            motion_style = self.get_motion_style(scene.scene_type)

        # Build prompt parts list
        prompt_parts: List[str] = []

        # Add visual direction from storyboard if available (translated to English)
        if scene.visual_direction:
            translated_direction = self.translate_korean_to_english(
                scene.visual_direction
            )
            if translated_direction:
                prompt_parts.append(translated_direction)

        # Get base motion prompt template
        base_motion = self._get_motion_prompt(motion_style, scene.scene_number)
        prompt_parts.append(base_motion)

        # Add duration hint if relevant
        if scene.duration_seconds:
            if scene.duration_seconds <= 3:
                prompt_parts.append("brief sequence")
            elif scene.duration_seconds >= 6:
                prompt_parts.append("extended smooth take")

        # Add transition hint if specified
        if scene.transition_effect:
            effect = scene.transition_effect.lower()
            if effect == "fade":
                prompt_parts.append("ending with fade")
            elif effect == "zoom":
                prompt_parts.append("forward momentum")

        # Combine and truncate
        full_prompt = ", ".join(prompt_parts)
        return self._truncate_to_word_limit(full_prompt, MAX_WORDS_IMAGE_TO_VIDEO)

    def build_text_to_video_prompt(
        self,
        scene: SceneInput,
        brand_context: Optional[str] = None,
    ) -> str:
        """
        Build a descriptive prompt for text-to-video generation.

        When no scene image exists, the prompt should describe the visual
        content including product context. Output is limited to 50 words.

        Args:
            scene: The SceneInput containing scene metadata.
            brand_context: Optional brand/product context to include.

        Returns:
            A descriptive English prompt (max 50 words).
        """
        prompt_parts: List[str] = []

        # Add visual direction (translated to English)
        if scene.visual_direction:
            translated = self.translate_korean_to_english(scene.visual_direction)
            prompt_parts.append(translated.strip())

        # Add scene description (translated)
        if scene.description:
            translated = self.translate_korean_to_english(scene.description)
            # Avoid duplicate content
            if not prompt_parts or translated.strip() not in prompt_parts[0]:
                prompt_parts.append(translated.strip())

        # Add brand context for text-to-video
        if brand_context:
            translated = self.translate_korean_to_english(brand_context)
            prompt_parts.append(translated.strip())

        # Add motion style hint based on scene type
        motion_style = self.get_motion_style(scene.scene_type)
        style_hint = {
            "cinematic": "cinematic professional style",
            "dynamic": "energetic marketing style",
            "subtle": "calm atmospheric style",
            "product_focus": "product showcase style",
        }.get(motion_style, "professional video style")
        prompt_parts.append(style_hint)

        # Combine and truncate
        full_prompt = ", ".join(prompt_parts)
        return self._truncate_to_word_limit(full_prompt, MAX_WORDS_TEXT_TO_VIDEO)

    def build_scene_prompt(
        self,
        scene: SceneInput,
        brand_context: Optional[str] = None,
        has_scene_image: Optional[bool] = None,
    ) -> str:
        """
        Build an optimized English prompt for video generation.

        Automatically selects the appropriate mode based on whether the scene
        has image data:
        - Image-to-Video: Simple motion-focused prompt (max 30 words)
        - Text-to-Video: Descriptive prompt with context (max 50 words)

        Args:
            scene: The SceneInput containing all scene metadata.
            brand_context: Optional brand/product context. Only used in
                text-to-video mode (when no scene image exists).
            has_scene_image: Optional override to explicitly specify mode.
                If None, will auto-detect based on scene.image_data.

        Returns:
            An optimized English prompt for Veo API video generation.
        """
        # Determine if this is image-to-video or text-to-video
        if has_scene_image is None:
            has_scene_image = bool(scene.image_data)

        if has_scene_image:
            # Image-to-video: simple motion prompt, no brand context
            return self.build_image_to_video_prompt(scene)
        else:
            # Text-to-video: descriptive prompt with brand context
            return self.build_text_to_video_prompt(scene, brand_context)

    def build_multi_scene_prompt(
        self,
        scenes: List[SceneInput],
        brand_context: Optional[str] = None,
    ) -> str:
        """
        Build a combined prompt for generating video from multiple scenes.

        Each scene is processed according to whether it has image data.
        The combined prompt maintains visual consistency guidance.

        Args:
            scenes: List of SceneInput objects representing the video sequence.
            brand_context: Optional brand/product context to integrate.

        Returns:
            A combined English prompt for multi-scene video generation.
        """
        if not scenes:
            return "Generate an engaging marketing video, professional quality."

        prompt_parts: List[str] = []

        # Add overall video context
        total_duration = sum(s.duration_seconds for s in scenes)
        prompt_parts.append(
            f"Marketing video {total_duration:.0f} seconds, "
            f"{len(scenes)} scenes, professional quality."
        )

        # Build individual scene prompts
        for scene in scenes:
            scene_prompt = self.build_scene_prompt(scene, brand_context=brand_context)
            scene_marker = f"Scene {scene.scene_number}:"
            prompt_parts.append(f"{scene_marker} {scene_prompt}")

        # Add consistency guidance
        prompt_parts.append("Smooth transitions, consistent visual style.")

        # Combine all parts
        full_prompt = " ".join(prompt_parts)

        return full_prompt.strip()


# Factory function for convenience
def create_prompt_builder(
    storyboard_priority: bool = True,
    custom_strategies: Optional[Dict[str, str]] = None,
    custom_korean_mappings: Optional[Dict[str, str]] = None,
    custom_motion_styles: Optional[Dict[str, str]] = None,
) -> VideoPromptBuilder:
    """
    Create a VideoPromptBuilder with optional custom configurations.

    Args:
        storyboard_priority: Legacy parameter for backward compatibility.
            This parameter is accepted but no longer affects behavior as the
            new builder uses different logic (image-to-video vs text-to-video).
        custom_strategies: Legacy parameter for backward compatibility.
            Use custom_motion_styles instead for scene type to motion mapping.
        custom_korean_mappings: Optional dictionary of additional Korean to
            English concept mappings.
        custom_motion_styles: Optional dictionary of scene type to motion
            style mappings.

    Returns:
        A configured VideoPromptBuilder instance.
    """
    # Merge legacy custom_strategies into motion styles if provided
    merged_motion_styles = custom_motion_styles
    if custom_strategies and not custom_motion_styles:
        # Legacy: custom_strategies were scene type descriptions
        # New behavior ignores them but accepts the parameter for compatibility
        merged_motion_styles = None

    return VideoPromptBuilder(
        korean_to_english=custom_korean_mappings,
        scene_type_motion=merged_motion_styles,
    )


__all__ = [
    "VideoPromptBuilder",
    "create_prompt_builder",
    "translate_korean_to_english_llm",
    "translate_korean_to_english_llm_sync",
    "clear_translation_cache",
    "KOREAN_TO_ENGLISH_CONCEPTS",
    "SCENE_TYPE_MOTION",
    "MOTION_STYLE_PROMPTS",
    "MAX_WORDS_IMAGE_TO_VIDEO",
    "MAX_WORDS_TEXT_TO_VIDEO",
]
