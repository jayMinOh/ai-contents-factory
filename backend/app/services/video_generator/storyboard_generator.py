"""
AI-powered storyboard generation service.

Supports multiple providers:
- mock: Mock provider for testing
- gemini: Google Gemini API for production
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

import google.generativeai as genai

from app.core.config import settings


class StoryboardGeneratorBase(ABC):
    """Base class for storyboard generators."""

    @abstractmethod
    async def generate(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        mode: str = "reference_structure",
        target_duration: Optional[int] = None,
        language: str = "ko",
    ) -> Dict[str, Any]:
        """
        Generate storyboard from reference analysis and product info.

        Args:
            reference_analysis: Reference video analysis result with segments, hooks, etc.
            brand_info: Brand information (name, description, tone_and_manner, etc.)
            product_info: Product information (name, description, features, benefits, etc.)
            mode: Generation mode ("reference_structure" or "ai_optimized")
            target_duration: Target video duration in seconds (optional)

        Returns:
            dict with keys:
                - scenes: List of Scene objects
                - total_duration_seconds: Total video duration
                - generation_mode: The mode used for generation
        """
        pass


class MockStoryboardGenerator(StoryboardGeneratorBase):
    """Mock storyboard generator for testing (returns deterministic results)."""

    async def generate(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        mode: str = "reference_structure",
        target_duration: Optional[int] = None,
        language: str = "ko",
    ) -> Dict[str, Any]:
        """
        Generate mock storyboard.

        Uses reference analysis structure to create scenes with product/brand content.
        """
        # Simulate processing delay
        await asyncio.sleep(0.1)

        if mode == "reference_structure":
            scenes = self._generate_from_reference_structure(
                reference_analysis=reference_analysis,
                brand_info=brand_info,
                product_info=product_info,
                target_duration=target_duration,
            )
        elif mode == "ai_optimized":
            scenes = self._generate_ai_optimized(
                reference_analysis=reference_analysis,
                brand_info=brand_info,
                product_info=product_info,
                target_duration=target_duration,
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Calculate total duration
        total_duration = sum(scene["duration_seconds"] for scene in scenes)

        return {
            "scenes": scenes,
            "total_duration_seconds": total_duration,
            "generation_mode": mode,
        }

    def _generate_from_reference_structure(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        target_duration: Optional[int] = None,
    ) -> list:
        """Generate scenes maintaining reference structure."""
        segments = reference_analysis.get("segments", [])
        scenes = []

        # Calculate scale factor for duration normalization
        scale_factor = self._calculate_duration_scale_factor(
            reference_analysis.get("duration", 30),
            target_duration,
        )

        for idx, segment in enumerate(segments, 1):
            scene = self._create_scene_from_segment(
                segment=segment,
                scene_number=idx,
                scale_factor=scale_factor,
                brand_info=brand_info,
                product_info=product_info,
            )
            scenes.append(scene)

        return scenes

    def _calculate_duration_scale_factor(
        self,
        reference_duration: float,
        target_duration: Optional[int],
    ) -> float:
        """Calculate scale factor for duration normalization."""
        if not target_duration or reference_duration <= 0:
            return 1
        return target_duration / reference_duration

    def _create_scene_from_segment(
        self,
        segment: Dict[str, Any],
        scene_number: int,
        scale_factor: float,
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a scene object from a segment."""
        scene_type = segment.get("segment_type", "transition")
        duration = segment.get("end_time", 0) - segment.get("start_time", 0)
        scaled_duration = duration * scale_factor

        return {
            "scene_number": scene_number,
            "scene_type": scene_type,
            "title": self._generate_title(scene_type, scene_number),
            "description": self._generate_description(
                scene_type=scene_type,
                segment=segment,
                brand_info=brand_info,
                product_info=product_info,
            ),
            "narration_script": self._generate_narration(
                scene_type=scene_type,
                brand_info=brand_info,
                product_info=product_info,
                segment=segment,
            ),
            "visual_direction": self._generate_visual_direction(
                scene_type=scene_type,
                segment=segment,
            ),
            "background_music_suggestion": self._generate_music_suggestion(
                scene_type=scene_type,
            ),
            "transition_effect": self._generate_transition(scene_type),
            "subtitle_text": self._generate_subtitle(
                scene_type=scene_type,
                product_info=product_info,
            ),
            "duration_seconds": max(1.0, scaled_duration),
            "generated_image_id": None,
        }

    def _generate_ai_optimized(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        target_duration: Optional[int] = None,
    ) -> list:
        """Generate AI-optimized scenes based on analysis insights."""
        # For mock, we'll generate a simplified structure based on key insights
        hook_points = reference_analysis.get("hook_points", [])
        pain_points = reference_analysis.get("pain_points", [])
        selling_points = reference_analysis.get("selling_points", [])

        scenes = []
        scene_number = 1

        # Generate hook scenes from hook points
        if hook_points:
            for hook_point in hook_points[:2]:  # Limit to 2 hooks
                scene = {
                    "scene_number": scene_number,
                    "scene_type": "hook",
                    "title": "Compelling Hook",
                    "description": f"Create an eye-catching hook featuring {product_info.get('name', 'the product')} that captures attention immediately. Use {hook_point.get('hook_type', 'curiosity_gap')} technique.",
                    "narration_script": f"{hook_point.get('adaptable_template', 'Engaging opening statement')} - {product_info.get('name')}",
                    "visual_direction": "Fast-paced, high-energy opening with dynamic transitions",
                    "background_music_suggestion": "Upbeat, modern electronic",
                    "transition_effect": "fade_in",
                    "subtitle_text": product_info.get("name", "Product"),
                    "duration_seconds": 3.0,
                    "generated_image_id": None,
                }
                scenes.append(scene)
                scene_number += 1

        # Generate problem scenes from pain points
        if pain_points:
            scene = {
                "scene_number": scene_number,
                "scene_type": "problem",
                "title": "Problem Identification",
                "description": f"Visualize the pain point: {pain_points[0].get('description', 'Customer challenges')} that {product_info.get('name')} solves",
                "narration_script": f"Many people struggle with {pain_points[0].get('description', 'this challenge')}...",
                "visual_direction": "Show relatable problem scenarios",
                "background_music_suggestion": "Subtle tension building",
                "transition_effect": "fade_in",
                "subtitle_text": "The Challenge",
                "duration_seconds": 4.0,
                "generated_image_id": None,
            }
            scenes.append(scene)
            scene_number += 1

        # Generate solution/benefit scenes
        benefits = product_info.get("benefits", [])
        for benefit in benefits[:2]:  # Limit to 2 benefits
            scene = {
                "scene_number": scene_number,
                "scene_type": "benefit",
                "title": "Solution & Benefits",
                "description": f"{product_info.get('name')} delivers: {benefit}. Show the transformation and positive impact.",
                "narration_script": f"With {product_info.get('name')}, you can {benefit.lower()}.",
                "visual_direction": "Showcase product in action with positive emotions",
                "background_music_suggestion": "Uplifting, inspirational",
                "transition_effect": "fade_in",
                "subtitle_text": benefit,
                "duration_seconds": 4.0,
                "generated_image_id": None,
            }
            scenes.append(scene)
            scene_number += 1

        # Add CTA scene
        scene = {
            "scene_number": scene_number,
            "scene_type": "cta",
            "title": "Call to Action",
            "description": "Create a strong call to action with clear next steps for the viewer.",
            "narration_script": f"Ready to transform with {product_info.get('name')}? Take action today!",
            "visual_direction": "Clear, branded CTA with strong visual hierarchy",
            "background_music_suggestion": "Energetic conclusion",
            "transition_effect": "zoom_in",
            "subtitle_text": "Get Started Now",
            "duration_seconds": 3.0,
            "generated_image_id": None,
        }
        scenes.append(scene)

        return scenes

    def _generate_title(self, scene_type: str, scene_number: int) -> str:
        """Generate scene title based on type."""
        titles = {
            "hook": "Opening Hook",
            "problem": "Problem Statement",
            "agitation": "Agitation",
            "solution": "Solution Introduction",
            "feature": "Feature Showcase",
            "benefit": "Key Benefit",
            "social_proof": "Social Proof",
            "urgency": "Urgency/Scarcity",
            "cta": "Call to Action",
        }
        return titles.get(scene_type, f"Scene {scene_number}")

    def _generate_description(
        self,
        scene_type: str,
        segment: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ) -> str:
        """Generate image description for the scene."""
        product_name = product_info.get("name", "Product")
        brand_name = brand_info.get("name", "Brand")
        features = product_info.get("features", [])
        features_text = ", ".join(features[:2]) if features else "innovative solution"

        descriptions = {
            "hook": f"Eye-catching opening scene featuring {product_name} from {brand_name}. Use dynamic visuals, bold colors, and motion to capture attention immediately.",
            "problem": f"Realistic scenario showing a customer struggling with a challenge that {product_name} solves. Relatable and emotionally resonant imagery.",
            "agitation": f"Emphasize the pain point and consequences of not solving it. Build tension and urgency around the problem that {product_name} addresses.",
            "solution": f"Showcase {product_name} solving the problem elegantly. Display key features: {features_text}",
            "feature": f"Detailed demonstration of {product_name} features. Clean, professional presentation highlighting {features_text}",
            "benefit": f"Visualize the positive outcomes and benefits of using {product_name}. Show transformation, relief, and success achieved by customers.",
            "social_proof": f"Display testimonials, reviews, or user stories of {product_name} success. Include logos, faces, or quotes from satisfied customers.",
            "urgency": f"Create sense of time-sensitivity around {product_name} offer. Show limited availability, special pricing, or exclusive benefits.",
            "cta": f"Clear call-to-action screen for {product_name}. Include website, app download link, or contact information with {brand_name} branding.",
        }

        base_description = descriptions.get(
            scene_type,
            f"Professional scene featuring {product_name} from {brand_name}",
        )

        # Add tone and manner
        tone = brand_info.get("tone_and_manner", "")
        if tone:
            base_description += f" Tone: {tone}."

        return base_description

    def _generate_narration(
        self,
        scene_type: str,
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        segment: Dict[str, Any],
    ) -> str:
        """Generate narration script for the scene."""
        product_name = product_info.get("name", "Product")
        brand_name = brand_info.get("name", "Brand")
        description = product_info.get("description", "")

        scripts = {
            "hook": f"Imagine if you could solve this in seconds... Introducing {product_name} from {brand_name}.",
            "problem": f"You're not alone. Many people struggle with this challenge every day. But what if there was a better way?",
            "agitation": f"The cost of inaction is high. Without the right solution, you're losing time and opportunity every single day.",
            "solution": f"That's where {product_name} comes in. {description[:100] if description else 'Revolutionary solution'} that changes everything.",
            "feature": f"{product_name} includes powerful features designed to solve your biggest challenges. With intelligent automation and intuitive design.",
            "benefit": f"Users of {product_name} report significant improvements. Save time, increase productivity, and achieve better results.",
            "social_proof": f"Thousands of users trust {product_name}. Join the community of successful users who've transformed their workflow.",
            "urgency": f"Don't miss out. Limited spots available for the special launch offer. Get started with {product_name} today.",
            "cta": f"Ready to transform your workflow with {product_name}? Click the link in the description to get started now.",
        }

        return scripts.get(
            scene_type,
            f"Discover the power of {product_name} from {brand_name}.",
        )

    def _generate_visual_direction(
        self,
        scene_type: str,
        segment: Dict[str, Any],
    ) -> str:
        """Generate visual direction/cinematography guidance."""
        directions = {
            "hook": "Fast cuts, dynamic camera movements, bold transitions. High energy, immediate visual impact.",
            "problem": "Realistic, relatable visuals. Steady camera. Show emotions of struggle or difficulty.",
            "agitation": "Darker tones, tension-building shots. Maybe time-lapse or quick cuts to show urgency.",
            "solution": "Bright, clean visuals. Product-focused. Smooth transitions. Professional presentation.",
            "feature": "Detailed close-ups of product. Screen recordings or detailed demonstrations. Clear labeling.",
            "benefit": "Happy customers, success moments. Before/after sequences. Aspirational imagery.",
            "social_proof": "Testimonial videos, profile photos, quote cards. Authentic and credible presentation.",
            "urgency": "Countdown timers, limited availability badges. Bold typography. Energetic pacing.",
            "cta": "Clear, centered design. Easy-to-read text. Click arrows or hand pointers. Bright, contrasting colors.",
        }

        return directions.get(
            scene_type,
            "Professional, clear presentation. Align with brand guidelines.",
        )

    def _generate_music_suggestion(self, scene_type: str) -> str:
        """Generate background music suggestion."""
        suggestions = {
            "hook": "Modern, energetic electronic. Upbeat tempo. Grabs attention immediately.",
            "problem": "Subtle, slightly tense. Builds concern without being alarming.",
            "agitation": "Tension building. Dramatic strings or synth. Creates urgency.",
            "solution": "Uplifting, inspiring. Suggests relief and confidence.",
            "feature": "Professional, modern background. Neutral, doesn't distract.",
            "benefit": "Positive, celebratory. Feel-good music. Uplifting vibe.",
            "social_proof": "Trustworthy, professional. Classic uplifting background.",
            "urgency": "Fast-paced, energetic. Emphasizes time-sensitivity.",
            "cta": "Energetic, memorable. Final hook to encourage action.",
        }

        return suggestions.get(
            scene_type,
            "Modern, professional background music that complements the brand.",
        )

    def _generate_transition(self, scene_type: str) -> str:
        """Generate transition effect suggestion."""
        transitions = {
            "hook": "fade_in",
            "problem": "fade_in",
            "agitation": "quick_cut",
            "solution": "fade_in",
            "feature": "fade_in",
            "benefit": "fade_in",
            "social_proof": "fade_in",
            "urgency": "zoom_in",
            "cta": "zoom_in",
        }

        return transitions.get(scene_type, "fade_in")

    def _generate_subtitle(
        self,
        scene_type: str,
        product_info: Dict[str, Any],
    ) -> str:
        """Generate subtitle/on-screen text."""
        product_name = product_info.get("name", "Product")

        subtitles = {
            "hook": "Introducing " + product_name,
            "problem": "The Challenge",
            "agitation": "The Cost of Inaction",
            "solution": "The Solution",
            "feature": "Powerful Features",
            "benefit": "Real Results",
            "social_proof": "Trusted by Thousands",
            "urgency": "Limited Time Offer",
            "cta": "Get Started Now",
        }

        return subtitles.get(scene_type, product_name)


class GeminiStoryboardGenerator(StoryboardGeneratorBase):
    """
    Storyboard generator using Google Gemini API.

    Uses advanced AI to generate contextually relevant scenes based on analysis.
    """

    def __init__(self):
        if not settings.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is not configured")

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        mode: str = "reference_structure",
        target_duration: Optional[int] = None,
        language: str = "ko",
    ) -> Dict[str, Any]:
        """
        Generate storyboard using Gemini API.

        Supports two modes:
        1. reference_structure: Maintains reference video structure
        2. ai_optimized: Uses AI to create optimal structure
        """

        if mode == "reference_structure":
            prompt = self._build_reference_structure_prompt(
                reference_analysis=reference_analysis,
                brand_info=brand_info,
                product_info=product_info,
                target_duration=target_duration,
                language=language,
            )
        elif mode == "ai_optimized":
            prompt = self._build_ai_optimized_prompt(
                reference_analysis=reference_analysis,
                brand_info=brand_info,
                product_info=product_info,
                target_duration=target_duration,
                language=language,
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Call Gemini API with retry logic
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                )

                result = self._extract_and_parse_json(response.text)
                if result and "scenes" in result:
                    result["generation_mode"] = mode

                    # Calculate total duration
                    total_duration = sum(
                        scene.get("duration_seconds", 0) for scene in result.get("scenes", [])
                    )
                    result["total_duration_seconds"] = total_duration

                    return result

                # JSON parsing failed, retry
                if attempt < max_retries:
                    await asyncio.sleep(attempt * 2)
                    continue

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Check if network error
                is_network_error = any(
                    keyword in error_msg
                    for keyword in [
                        "timeout",
                        "connection",
                        "network",
                        "503",
                        "504",
                        "quota",
                    ]
                )

                if is_network_error and attempt < max_retries:
                    wait_time = attempt * 5
                    print(f"Network error (attempt {attempt}/{max_retries}): {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

        # All retries failed
        raise Exception(f"Gemini storyboard generation failed: {last_error}")

    def _build_reference_structure_prompt(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        target_duration: Optional[int] = None,
        language: str = "ko",
    ) -> str:
        """Build prompt for reference structure mode."""

        segments_info = json.dumps(reference_analysis.get("segments", [])[:3], indent=2)

        # Language instruction
        lang_instruction = ""
        if language.startswith("ko"):
            lang_instruction = "IMPORTANT: Generate ALL content (title, description, narration_script, visual_direction, subtitle_text) in Korean (한국어)."
        elif language.startswith("ja"):
            lang_instruction = "IMPORTANT: Generate ALL content in Japanese (日本語)."
        elif language.startswith("zh"):
            lang_instruction = "IMPORTANT: Generate ALL content in Chinese (中文)."
        else:
            lang_instruction = "Generate all content in English."

        prompt = f"""You are an expert video marketing storyboard creator.

{lang_instruction}

Create a detailed storyboard for a marketing video based on a reference video structure and product information.

## Reference Video Structure
{segments_info}

## Brand Information
- Name: {brand_info.get('name', 'Brand')}
- Tone & Manner: {brand_info.get('tone_and_manner', 'Professional')}

## Product Information
- Name: {product_info.get('name', 'Product')}
- Description: {product_info.get('description', '')}
- Features: {', '.join(product_info.get('features', [])[:3])}
- Benefits: {', '.join(product_info.get('benefits', [])[:3])}

{f"Target Duration: {target_duration} seconds" if target_duration else ""}

For each segment in the reference structure, create a detailed scene with:
1. title: Scene title
2. description: Detailed image generation description (include product, colors, mood, setting)
3. narration_script: Script for voiceover/narration
4. visual_direction: Cinematography and styling guidance
5. background_music_suggestion: Music mood and style
6. transition_effect: Type of transition (fade_in, zoom_in, quick_cut, etc.)
7. subtitle_text: On-screen text/captions
8. duration_seconds: Scene duration in seconds
9. scene_type: Type of scene matching the reference segment
10. scene_number: Sequential number

Return ONLY valid JSON with a "scenes" array. No markdown, no explanations, just the JSON object.

Example format:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "scene_type": "hook",
      "title": "...",
      "description": "...",
      "narration_script": "...",
      "visual_direction": "...",
      "background_music_suggestion": "...",
      "transition_effect": "fade_in",
      "subtitle_text": "...",
      "duration_seconds": 3.0,
      "generated_image_id": null
    }}
  ]
}}"""

        return prompt

    def _build_ai_optimized_prompt(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
        target_duration: Optional[int] = None,
        language: str = "ko",
    ) -> str:
        """Build prompt for AI-optimized mode."""

        hook_points = reference_analysis.get("hook_points", [])[:2]
        pain_points = reference_analysis.get("pain_points", [])[:2]
        selling_points = reference_analysis.get("selling_points", [])[:2]

        hook_info = json.dumps(hook_points, indent=2) if hook_points else "[]"
        pain_info = json.dumps(pain_points, indent=2) if pain_points else "[]"
        selling_info = json.dumps(selling_points, indent=2) if selling_points else "[]"

        # Language instruction
        lang_instruction = ""
        if language.startswith("ko"):
            lang_instruction = "IMPORTANT: Generate ALL content (title, description, narration_script, visual_direction, subtitle_text) in Korean (한국어). Write compelling Korean marketing copy."
        elif language.startswith("ja"):
            lang_instruction = "IMPORTANT: Generate ALL content in Japanese (日本語)."
        elif language.startswith("zh"):
            lang_instruction = "IMPORTANT: Generate ALL content in Chinese (中文)."
        else:
            lang_instruction = "Generate all content in English."

        prompt = f"""You are an expert video marketing strategist and storyboard creator.

{lang_instruction}

Create an optimized marketing video storyboard using AI-powered insights from a reference video analysis.

## Key Marketing Insights
**Hook Points (attention-grabbing techniques):**
{hook_info}

**Pain Points (customer challenges):**
{pain_info}

**Selling Points (persuasion elements):**
{selling_info}

## Brand Information
- Name: {brand_info.get('name', 'Brand')}
- Tone & Manner: {brand_info.get('tone_and_manner', 'Professional')}
- Values: {', '.join(brand_info.get('key_values', [])[:3])}

## Product Information
- Name: {product_info.get('name', 'Product')}
- Description: {product_info.get('description', '')}
- Features: {', '.join(product_info.get('features', [])[:3])}
- Benefits: {', '.join(product_info.get('benefits', [])[:3])}
- USP: {product_info.get('unique_selling_proposition', '')}

{f"Target Duration: {target_duration} seconds" if target_duration else ""}

Design an optimized storyboard that:
1. Opens with a compelling hook from the analysis
2. Addresses identified pain points with empathy
3. Presents the product as the solution
4. Highlights key benefits and unique selling points
5. Includes social proof or credibility
6. Ends with a clear call to action

Create 6-8 scenes total. For each scene provide:
- scene_number, scene_type, title, description, narration_script
- visual_direction, background_music_suggestion, transition_effect
- subtitle_text, duration_seconds, generated_image_id (null for now)

Return ONLY valid JSON with a "scenes" array. No markdown, no explanations.

Example format:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "scene_type": "hook",
      "title": "Compelling Opening",
      "description": "...",
      "narration_script": "...",
      "visual_direction": "...",
      "background_music_suggestion": "...",
      "transition_effect": "fade_in",
      "subtitle_text": "...",
      "duration_seconds": 3.0,
      "generated_image_id": null
    }}
  ]
}}"""

        return prompt

    def _extract_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from response text."""

        # Method 1: ```json ... ``` block
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # Method 2: ``` ... ``` block
        if "```" in text:
            try:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # Method 3: Find { } block
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass

        # Method 4: Fix common JSON errors
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                # Remove trailing commas
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # Replace single quotes with double quotes
                json_str = json_str.replace("'", '"')
                return json.loads(json_str)
        except:
            pass

        return None


class StoryboardGeneratorFactory:
    """Factory for creating storyboard generators."""

    _generators: Dict[str, type[StoryboardGeneratorBase]] = {
        "mock": MockStoryboardGenerator,
        "gemini": GeminiStoryboardGenerator,
    }

    @classmethod
    def create(cls, provider: str) -> StoryboardGeneratorBase:
        """Create a storyboard generator for the specified provider."""
        if provider not in cls._generators:
            raise ValueError(
                f"Unknown provider: {provider}. Available: {list(cls._generators.keys())}"
            )

        return cls._generators[provider]()

    @classmethod
    def available_providers(cls) -> list[str]:
        """Get list of available providers."""
        return list(cls._generators.keys())


# Singleton instances for reuse
_generator_instances: Dict[str, StoryboardGeneratorBase] = {}


def get_storyboard_generator(provider: str = "mock") -> StoryboardGeneratorBase:
    """Get or create a storyboard generator instance."""
    if provider not in _generator_instances:
        _generator_instances[provider] = StoryboardGeneratorFactory.create(provider)
    return _generator_instances[provider]


__all__ = [
    "StoryboardGeneratorBase",
    "MockStoryboardGenerator",
    "GeminiStoryboardGenerator",
    "StoryboardGeneratorFactory",
    "get_storyboard_generator",
]
