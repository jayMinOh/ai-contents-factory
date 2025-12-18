"""
Test suite for StoryboardGenerator.

Tests both MockStoryboardGenerator and GeminiStoryboardGenerator.
"""

import pytest
from typing import Dict, Any, Optional


@pytest.fixture
def reference_analysis() -> Dict[str, Any]:
    """Sample reference analysis result from reference analyzer."""
    return {
        "duration": 30.0,
        "segments": [
            {
                "start_time": 0.0,
                "end_time": 3.0,
                "segment_type": "hook",
                "visual_description": "Strong visual with fast cuts",
                "engagement_score": 0.9,
                "techniques": ["pattern_interrupt", "curiosity_gap"],
            },
            {
                "start_time": 3.0,
                "end_time": 8.0,
                "segment_type": "problem",
                "visual_description": "Problem demonstration",
                "engagement_score": 0.7,
                "techniques": ["pain_point_visualization"],
            },
            {
                "start_time": 8.0,
                "end_time": 15.0,
                "segment_type": "solution",
                "visual_description": "Product solution showcase",
                "engagement_score": 0.8,
                "techniques": ["demonstration", "before_after"],
            },
            {
                "start_time": 15.0,
                "end_time": 25.0,
                "segment_type": "benefit",
                "visual_description": "User testimonials",
                "engagement_score": 0.75,
                "techniques": ["social_proof"],
            },
            {
                "start_time": 25.0,
                "end_time": 30.0,
                "segment_type": "cta",
                "visual_description": "Call to action",
                "engagement_score": 0.85,
                "techniques": ["urgency", "scarcity"],
            },
        ],
        "hook_points": [
            {
                "timestamp": "0:00-0:03",
                "hook_type": "curiosity_gap",
                "effectiveness_score": 0.85,
                "description": "Compelling opening question",
                "adaptable_template": "What if you could [benefit] without [pain_point]?",
            }
        ],
        "pain_points": [
            {
                "timestamp": "0:03-0:08",
                "pain_type": "explicit",
                "description": "Time waste problem",
                "empathy_technique": "problem_validation",
            }
        ],
        "selling_points": [
            {
                "timestamp": "0:08-0:15",
                "claim": "10x faster solution",
                "evidence_type": "demonstration",
                "persuasion_technique": "social_proof",
                "effectiveness": 0.85,
            }
        ],
        "structure_pattern": {
            "framework": "PAS",
            "flow": ["hook", "problem", "agitation", "solution", "cta"],
            "effectiveness_note": "This structure maximizes engagement",
        },
        "recommendations": [
            {
                "priority": 1,
                "action": "Use strong opening hook",
                "reason": "Reduces early abandonment",
                "example": "Start with curiosity gap",
            }
        ],
    }


@pytest.fixture
def brand_info() -> Dict[str, Any]:
    """Sample brand information."""
    return {
        "name": "TechFlow",
        "description": "Modern productivity software",
        "tone_and_manner": "Professional, friendly, innovative",
        "key_values": ["efficiency", "reliability", "innovation"],
        "target_audience": "Tech-savvy professionals",
    }


@pytest.fixture
def product_info() -> Dict[str, Any]:
    """Sample product information."""
    return {
        "name": "TaskFlow",
        "description": "AI-powered task management system",
        "features": [
            "Intelligent task prioritization",
            "Real-time collaboration",
            "AI-powered scheduling",
        ],
        "benefits": [
            "Save 5+ hours per week",
            "Reduce stress from task management",
            "Increase team productivity",
        ],
        "unique_selling_proposition": "Only platform with AI task understanding",
        "target_audience": "Remote teams and freelancers",
    }


class TestStoryboardGeneratorBase:
    """Test StoryboardGeneratorBase interface."""

    def test_import_base_class(self):
        """Test that StoryboardGeneratorBase can be imported."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorBase,
        )

        assert StoryboardGeneratorBase is not None

    def test_base_class_is_abstract(self):
        """Test that StoryboardGeneratorBase is abstract."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorBase,
        )

        # Should not be able to instantiate abstract class
        with pytest.raises(TypeError):
            StoryboardGeneratorBase()


class TestMockStoryboardGenerator:
    """Test MockStoryboardGenerator implementation."""

    @pytest.mark.asyncio
    async def test_mock_generator_import(self):
        """Test that MockStoryboardGenerator can be imported."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        assert MockStoryboardGenerator is not None

    @pytest.mark.asyncio
    async def test_mock_generator_instantiation(self):
        """Test that MockStoryboardGenerator can be instantiated."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        assert generator is not None

    @pytest.mark.asyncio
    async def test_mock_generate_reference_structure_mode(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test mock generator with reference_structure mode."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="reference_structure",
        )

        # Verify output structure
        assert isinstance(result, dict)
        assert "scenes" in result
        assert "total_duration_seconds" in result
        assert "generation_mode" in result

        # Verify scenes
        assert isinstance(result["scenes"], list)
        assert len(result["scenes"]) > 0

        # Verify scene structure
        for scene in result["scenes"]:
            assert isinstance(scene, dict)
            assert "scene_number" in scene
            assert "scene_type" in scene
            assert "title" in scene
            assert "description" in scene
            assert "narration_script" in scene
            assert "visual_direction" in scene
            assert "background_music_suggestion" in scene
            assert "transition_effect" in scene
            assert "subtitle_text" in scene
            assert "duration_seconds" in scene
            assert "generated_image_id" in scene

    @pytest.mark.asyncio
    async def test_mock_generate_ai_optimized_mode(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test mock generator with ai_optimized mode."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="ai_optimized",
        )

        # Verify basic structure
        assert "scenes" in result
        assert "total_duration_seconds" in result
        assert "generation_mode" in result
        assert result["generation_mode"] == "ai_optimized"

    @pytest.mark.asyncio
    async def test_mock_generate_with_target_duration(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test mock generator with target duration."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        target_duration = 15  # seconds

        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="reference_structure",
            target_duration=target_duration,
        )

        # Total duration should be close to target
        total_duration = result["total_duration_seconds"]
        assert total_duration <= target_duration + 2  # Allow small margin

    @pytest.mark.asyncio
    async def test_mock_generate_scene_content_quality(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that generated scenes have meaningful content."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="reference_structure",
        )

        # Check scene content
        for scene in result["scenes"]:
            # Descriptions should mention product or brand
            description_lower = scene["description"].lower()
            assert (
                product_info["name"].lower() in description_lower
                or brand_info["name"].lower() in description_lower
                or len(scene["description"]) > 20
            )

            # Scripts should have content
            assert len(scene["narration_script"]) > 0
            assert len(scene["narration_script"]) > 10

            # Duration should be positive
            assert scene["duration_seconds"] > 0


class TestStoryboardGeneratorFactory:
    """Test StoryboardGeneratorFactory."""

    def test_factory_import(self):
        """Test that factory can be imported."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorFactory,
        )

        assert StoryboardGeneratorFactory is not None

    def test_factory_create_mock(self):
        """Test factory creates mock generator."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorFactory,
            MockStoryboardGenerator,
        )

        generator = StoryboardGeneratorFactory.create("mock")
        assert isinstance(generator, MockStoryboardGenerator)

    def test_factory_available_providers(self):
        """Test factory returns available providers."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorFactory,
        )

        providers = StoryboardGeneratorFactory.available_providers()
        assert isinstance(providers, list)
        assert "mock" in providers
        assert "gemini" in providers

    def test_factory_invalid_provider(self):
        """Test factory raises error for invalid provider."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorFactory,
        )

        with pytest.raises(ValueError):
            StoryboardGeneratorFactory.create("invalid_provider")


class TestGetStoryboardGenerator:
    """Test get_storyboard_generator helper function."""

    def test_get_mock_generator(self):
        """Test get_storyboard_generator returns mock generator."""
        from app.services.video_generator.storyboard_generator import (
            get_storyboard_generator,
            MockStoryboardGenerator,
        )

        generator = get_storyboard_generator("mock")
        assert isinstance(generator, MockStoryboardGenerator)

    def test_get_storyboard_generator_default_mock(self):
        """Test get_storyboard_generator defaults to mock."""
        from app.services.video_generator.storyboard_generator import (
            get_storyboard_generator,
            MockStoryboardGenerator,
        )

        generator = get_storyboard_generator()
        assert isinstance(generator, MockStoryboardGenerator)


class TestGeminiStoryboardGenerator:
    """Test GeminiStoryboardGenerator implementation."""

    @pytest.mark.asyncio
    async def test_gemini_generator_import(self):
        """Test that GeminiStoryboardGenerator can be imported."""
        from app.services.video_generator.storyboard_generator import (
            GeminiStoryboardGenerator,
        )

        assert GeminiStoryboardGenerator is not None

    @pytest.mark.asyncio
    async def test_gemini_generator_instantiation(self):
        """Test that GeminiStoryboardGenerator can be instantiated."""
        from app.services.video_generator.storyboard_generator import (
            GeminiStoryboardGenerator,
        )

        # This test just checks instantiation - actual API calls are separate
        try:
            generator = GeminiStoryboardGenerator()
            assert generator is not None
        except ValueError:
            # OK if API key not configured
            pass


class TestStoryboardGeneratorIntegration:
    """Integration tests for storyboard generation."""

    @pytest.mark.asyncio
    async def test_mock_generator_returns_valid_storyboard(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that mock generator returns a valid storyboard."""
        from app.services.video_generator.storyboard_generator import (
            get_storyboard_generator,
        )

        generator = get_storyboard_generator("mock")
        storyboard = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
        )

        # Validate storyboard structure
        assert isinstance(storyboard, dict)
        assert len(storyboard["scenes"]) > 0
        assert storyboard["total_duration_seconds"] > 0

        # Validate all scenes have required fields
        required_fields = {
            "scene_number",
            "scene_type",
            "title",
            "description",
            "narration_script",
            "visual_direction",
            "background_music_suggestion",
            "transition_effect",
            "subtitle_text",
            "duration_seconds",
            "generated_image_id",
        }

        for scene in storyboard["scenes"]:
            assert all(field in scene for field in required_fields)

    @pytest.mark.asyncio
    async def test_reference_structure_mode_maintains_segment_types(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that reference_structure mode maintains segment types from reference."""
        from app.services.video_generator.storyboard_generator import (
            get_storyboard_generator,
        )

        generator = get_storyboard_generator("mock")
        storyboard = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="reference_structure",
        )

        # Extract scene types
        scene_types = [scene["scene_type"] for scene in storyboard["scenes"]]

        # Should contain original segment types
        original_types = set(s["segment_type"] for s in reference_analysis["segments"])
        generated_types = set(scene_types)

        # At least some original types should be present
        assert len(original_types & generated_types) > 0

    @pytest.mark.asyncio
    async def test_storyboard_duration_calculation(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that total duration is calculated correctly."""
        from app.services.video_generator.storyboard_generator import (
            get_storyboard_generator,
        )

        generator = get_storyboard_generator("mock")
        storyboard = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
        )

        # Calculate duration from scenes
        calculated_duration = sum(
            scene["duration_seconds"] for scene in storyboard["scenes"]
        )

        # Should match total_duration_seconds
        assert abs(
            calculated_duration - storyboard["total_duration_seconds"]
        ) < 0.1


class TestStoryboardGeneratorEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_generate_with_empty_segments(self):
        """Test handling of empty segments in reference analysis."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis={
                "duration": 0,
                "segments": [],
            },
            brand_info={"name": "TestBrand"},
            product_info={"name": "TestProduct"},
            mode="reference_structure",
        )

        # Should handle gracefully with empty scenes
        assert isinstance(result, dict)
        assert "scenes" in result
        assert isinstance(result["scenes"], list)
        assert result["total_duration_seconds"] == 0

    @pytest.mark.asyncio
    async def test_generate_with_missing_optional_fields(self):
        """Test handling when optional fields are missing."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        minimal_ref_analysis = {
            "duration": 10,
            "segments": [
                {
                    "start_time": 0,
                    "end_time": 5,
                    # Missing optional fields like engagement_score, techniques
                }
            ],
        }

        result = await generator.generate(
            reference_analysis=minimal_ref_analysis,
            brand_info={},
            product_info={},
        )

        assert len(result["scenes"]) > 0

    @pytest.mark.asyncio
    async def test_ai_optimized_with_minimal_insights(self):
        """Test AI optimized mode with minimal hook/pain/selling points."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis={
                "duration": 20,
                "segments": [],
                "hook_points": [],
                "pain_points": [],
                "selling_points": [],
            },
            brand_info={"name": "Brand"},
            product_info={"name": "Product"},
            mode="ai_optimized",
        )

        # Should still generate valid scenes despite minimal insights
        assert len(result["scenes"]) > 0
        assert all(
            "scene_type" in scene and "description" in scene
            for scene in result["scenes"]
        )

    def test_invalid_generation_mode_raises_error(self):
        """Test that invalid generation mode raises ValueError."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()

        with pytest.raises(ValueError, match="Unknown mode"):
            import asyncio

            asyncio.run(
                generator.generate(
                    reference_analysis={},
                    brand_info={},
                    product_info={},
                    mode="invalid_mode",
                )
            )

    def test_factory_with_invalid_provider(self):
        """Test factory raises error for invalid provider."""
        from app.services.video_generator.storyboard_generator import (
            StoryboardGeneratorFactory,
        )

        with pytest.raises(ValueError, match="Unknown provider"):
            StoryboardGeneratorFactory.create("nonexistent_provider")

    @pytest.mark.asyncio
    async def test_scene_numbers_are_sequential(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that scene numbers are sequential and unique."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode="reference_structure",
        )

        scene_numbers = [scene["scene_number"] for scene in result["scenes"]]

        # Should be sequential starting from 1
        assert scene_numbers == list(range(1, len(scene_numbers) + 1))

    @pytest.mark.asyncio
    async def test_all_scene_durations_are_positive(
        self,
        reference_analysis: Dict[str, Any],
        brand_info: Dict[str, Any],
        product_info: Dict[str, Any],
    ):
        """Test that all scene durations are positive numbers."""
        from app.services.video_generator.storyboard_generator import (
            MockStoryboardGenerator,
        )

        generator = MockStoryboardGenerator()
        result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
        )

        for scene in result["scenes"]:
            assert isinstance(scene["duration_seconds"], (int, float))
            assert scene["duration_seconds"] > 0
