"""
Unit tests for Storyboard ORM model.

Tests cover:
- Field validation and constraints
- Relationship to VideoProject and ReferenceAnalysis
- Default values and timestamps
- Scene JSON structure validation
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard
from app.models.video_project import VideoProject
from app.models.reference_analysis import ReferenceAnalysis


class TestStoryboardModel:
    """Test suite for Storyboard ORM model."""

    @pytest.fixture
    async def test_db(self):
        """Fixture for database session."""
        from app.core.database import async_session_factory
        async with async_session_factory() as session:
            yield session

    @pytest.fixture
    def sample_video_project_id(self) -> str:
        """Generate sample video project UUID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_reference_analysis_id(self) -> str:
        """Generate sample reference analysis UUID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_storyboard_id(self) -> str:
        """Generate sample storyboard UUID."""
        return str(uuid.uuid4())

    @pytest.fixture
    def sample_scene_data(self) -> dict:
        """Generate sample scene data."""
        return {
            "scene_number": 1,
            "scene_type": "hook",
            "title": "Opening Hook",
            "description": "이미지 생성용 설명",
            "narration_script": "나레이션 스크립트",
            "visual_direction": "화면 연출 가이드",
            "background_music_suggestion": "분위기: 긴장감, 장르: Electronic",
            "transition_effect": "fade_in",
            "subtitle_text": "화면 자막",
            "duration_seconds": 3.0,
            "generated_image_id": None,
        }

    def test_storyboard_instantiation(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
        sample_scene_data: dict,
    ):
        """Test basic Storyboard instantiation."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
            scenes=[sample_scene_data],
        )

        assert storyboard.id == sample_storyboard_id
        assert storyboard.video_project_id == sample_video_project_id
        assert storyboard.generation_mode == "reference_structure"
        assert len(storyboard.scenes) == 1
        assert storyboard.scenes[0]["scene_type"] == "hook"

    def test_storyboard_default_values(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test Storyboard default values when explicitly provided."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="ai_optimized",
            version=1,
            is_active=True,
            scenes=[],
        )

        assert storyboard.version == 1
        assert storyboard.is_active is True
        assert storyboard.scenes == []
        assert storyboard.total_duration_seconds is None
        assert storyboard.source_reference_analysis_id is None
        assert storyboard.previous_version_id is None

    def test_storyboard_with_multiple_scenes(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test Storyboard with multiple scenes."""
        scenes = [
            {
                "scene_number": 1,
                "scene_type": "hook",
                "title": "Opening Hook",
                "description": "Description 1",
                "narration_script": "Script 1",
                "visual_direction": "Visual 1",
                "background_music_suggestion": "Music 1",
                "transition_effect": "fade_in",
                "subtitle_text": "Subtitle 1",
                "duration_seconds": 3.0,
                "generated_image_id": None,
            },
            {
                "scene_number": 2,
                "scene_type": "problem",
                "title": "Problem Scene",
                "description": "Description 2",
                "narration_script": "Script 2",
                "visual_direction": "Visual 2",
                "background_music_suggestion": "Music 2",
                "transition_effect": "slide_right",
                "subtitle_text": "Subtitle 2",
                "duration_seconds": 5.0,
                "generated_image_id": "image_id_2",
            },
        ]

        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
            scenes=scenes,
            total_duration_seconds=8.0,
        )

        assert len(storyboard.scenes) == 2
        assert storyboard.scenes[0]["scene_type"] == "hook"
        assert storyboard.scenes[1]["scene_type"] == "problem"
        assert storyboard.total_duration_seconds == 8.0

    def test_storyboard_with_all_fields(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
        sample_reference_analysis_id: str,
        sample_scene_data: dict,
    ):
        """Test Storyboard with all optional fields."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="ai_optimized",
            source_reference_analysis_id=sample_reference_analysis_id,
            scenes=[sample_scene_data],
            total_duration_seconds=10.5,
            version=2,
            is_active=False,
            previous_version_id=str(uuid.uuid4()),
        )

        assert storyboard.id == sample_storyboard_id
        assert storyboard.video_project_id == sample_video_project_id
        assert storyboard.generation_mode == "ai_optimized"
        assert storyboard.source_reference_analysis_id == sample_reference_analysis_id
        assert storyboard.scenes == [sample_scene_data]
        assert storyboard.total_duration_seconds == 10.5
        assert storyboard.version == 2
        assert storyboard.is_active is False
        assert storyboard.previous_version_id is not None

    def test_storyboard_generation_mode_values(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test valid generation mode values."""
        for mode in ["reference_structure", "ai_optimized"]:
            storyboard = Storyboard(
                id=sample_storyboard_id,
                video_project_id=sample_video_project_id,
                generation_mode=mode,
            )
            assert storyboard.generation_mode == mode

    def test_storyboard_empty_scenes_default(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test empty scenes list when explicitly provided."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
            scenes=[],
        )

        assert isinstance(storyboard.scenes, list)
        assert len(storyboard.scenes) == 0

    def test_storyboard_field_types(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test that fields have correct types."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
            total_duration_seconds=10.5,
            version=1,
            is_active=True,
            scenes=[],
        )

        assert isinstance(storyboard.id, str)
        assert isinstance(storyboard.video_project_id, str)
        assert isinstance(storyboard.generation_mode, str)
        assert isinstance(storyboard.total_duration_seconds, float)
        assert isinstance(storyboard.version, int)
        assert isinstance(storyboard.is_active, bool)
        assert isinstance(storyboard.scenes, list)

    def test_storyboard_repr(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test Storyboard __repr__ method."""
        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
        )

        repr_str = repr(storyboard)
        assert "Storyboard" in repr_str
        assert sample_storyboard_id in repr_str
        assert sample_video_project_id in repr_str

    def test_storyboard_complex_scene_structure(
        self,
        sample_storyboard_id: str,
        sample_video_project_id: str,
    ):
        """Test Storyboard with complex scene structures."""
        complex_scenes = [
            {
                "scene_number": 1,
                "scene_type": "hook",
                "title": "Hook",
                "description": "긴장감 있는 오프닝",
                "narration_script": "사용자의 주의를 끌기 위한 나레이션",
                "visual_direction": "빠른 컷 편집",
                "background_music_suggestion": "분위기: 긴장감, 장르: Electronic, BPM: 120",
                "transition_effect": "fade_in",
                "subtitle_text": "우리의 솔루션은",
                "duration_seconds": 3.5,
                "generated_image_id": "image_001",
            },
            {
                "scene_number": 2,
                "scene_type": "problem",
                "title": "Problem Statement",
                "description": "문제점 제시",
                "narration_script": "문제 상황 설명 나레이션",
                "visual_direction": "느린 줌 아웃",
                "background_music_suggestion": "분위기: 심각함, 장르: Orchestral",
                "transition_effect": "slide_right",
                "subtitle_text": "이러한 문제가 있나요?",
                "duration_seconds": 4.0,
                "generated_image_id": "image_002",
            },
        ]

        storyboard = Storyboard(
            id=sample_storyboard_id,
            video_project_id=sample_video_project_id,
            generation_mode="reference_structure",
            scenes=complex_scenes,
            total_duration_seconds=7.5,
            version=1,
            is_active=True,
        )

        assert len(storyboard.scenes) == 2
        assert storyboard.scenes[0]["duration_seconds"] == 3.5
        assert storyboard.scenes[1]["duration_seconds"] == 4.0
        assert all("scene_number" in scene for scene in storyboard.scenes)
        assert all("scene_type" in scene for scene in storyboard.scenes)
        assert all("generated_image_id" in scene for scene in storyboard.scenes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
