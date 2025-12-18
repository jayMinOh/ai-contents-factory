"""
Unit and integration tests for Storyboard API endpoints.

Tests cover:
- Storyboard generation (reference_structure, ai_optimized modes)
- Get active storyboard
- Get storyboard versions
- Update scene
- Create scene
- Delete scene
- Reorder scenes
"""

import uuid
from datetime import datetime
from typing import List

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard
from app.models.video_project import VideoProject
from app.models.brand import Brand
from app.models.product import Product
from app.schemas.studio import (
    SceneSchema,
    StoryboardResponse,
)


@pytest.fixture
async def brand(db: AsyncSession):
    """Create test brand."""
    brand = Brand(
        id=str(uuid.uuid4()),
        name="Test Brand",
        description="Test brand for storyboard API tests",
        industry="Technology",
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@pytest.fixture
async def product(db: AsyncSession, brand):
    """Create test product."""
    product = Product(
        id=str(uuid.uuid4()),
        brand_id=brand.id,
        name="Test Product",
        description="Test product for storyboard API tests",
        product_category="Software",
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@pytest.fixture
async def video_project(db: AsyncSession, brand, product):
    """Create test video project."""
    project = VideoProject(
        id=str(uuid.uuid4()),
        title="Test Project",
        description="Test project for storyboard API tests",
        brand_id=brand.id,
        product_id=product.id,
        reference_analysis_id=None,
        target_duration=60,
        aspect_ratio="16:9",
        status="draft",
        current_step=2,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


class TestStoryboardGenerate:
    """Test storyboard generation endpoints."""

    @pytest.mark.asyncio
    async def test_generate_storyboard_reference_structure(
        self, client: AsyncClient, video_project
    ):
        """Test POST /projects/{project_id}/storyboard/generate with reference_structure mode."""
        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/generate",
            json={"mode": "reference_structure"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"]
        assert data["video_project_id"] == video_project.id
        assert data["generation_mode"] == "reference_structure"
        assert isinstance(data["scenes"], list)
        assert len(data["scenes"]) > 0
        assert data["version"] == 1
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_generate_storyboard_ai_optimized(
        self, client: AsyncClient, video_project
    ):
        """Test POST /projects/{project_id}/storyboard/generate with ai_optimized mode."""
        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/generate",
            json={"mode": "ai_optimized"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["generation_mode"] == "ai_optimized"
        assert isinstance(data["scenes"], list)

    @pytest.mark.asyncio
    async def test_generate_storyboard_invalid_mode(
        self, client: AsyncClient, video_project
    ):
        """Test POST with invalid mode raises validation error."""
        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/generate",
            json={"mode": "invalid_mode"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_generate_storyboard_project_not_found(self, client: AsyncClient):
        """Test POST with non-existent project returns 404."""
        response = await client.post(
            f"/api/v1/studio/projects/{str(uuid.uuid4())}/storyboard/generate",
            json={"mode": "reference_structure"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStoryboardGet:
    """Test storyboard retrieval endpoints."""

    @pytest.mark.asyncio
    async def test_get_active_storyboard(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test GET /projects/{project_id}/storyboard returns active version."""
        # Create storyboard
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {
                    "scene_number": 1,
                    "scene_type": "hook",
                    "title": "Opening Hook",
                    "description": "Engaging opening",
                    "duration_seconds": 3.0,
                }
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.get(
            f"/api/v1/studio/projects/{video_project.id}/storyboard"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == storyboard.id
        assert data["is_active"] is True
        assert len(data["scenes"]) == 1

    @pytest.mark.asyncio
    async def test_get_active_storyboard_not_found(
        self, client: AsyncClient, video_project
    ):
        """Test GET storyboard when none exists returns 404."""
        response = await client.get(
            f"/api/v1/studio/projects/{video_project.id}/storyboard"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_storyboard_versions(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test GET /projects/{project_id}/storyboard/versions returns all versions."""
        # Create multiple versions
        storyboard_v1 = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[{"scene_number": 1, "scene_type": "hook", "title": "Hook", "description": "Desc"}],
            version=1,
            is_active=False,
        )
        storyboard_v2 = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {"scene_number": 1, "scene_type": "hook", "title": "Hook", "description": "Desc"},
                {"scene_number": 2, "scene_type": "problem", "title": "Problem", "description": "Desc"},
            ],
            version=2,
            is_active=True,
            previous_version_id=storyboard_v1.id,
        )
        db.add(storyboard_v1)
        db.add(storyboard_v2)
        await db.commit()

        response = await client.get(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/versions"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert any(v["version"] == 1 for v in data)
        assert any(v["version"] == 2 for v in data)

    @pytest.mark.asyncio
    async def test_get_storyboard_versions_project_not_found(
        self, client: AsyncClient
    ):
        """Test GET versions for non-existent project returns 404."""
        response = await client.get(
            f"/api/v1/studio/projects/{str(uuid.uuid4())}/storyboard/versions"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSceneUpdate:
    """Test scene update endpoints."""

    @pytest.mark.asyncio
    async def test_update_scene_creates_new_version(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test PUT /projects/{project_id}/storyboard/scenes/{scene_number} creates new version."""
        # Create initial storyboard
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {
                    "scene_number": 1,
                    "scene_type": "hook",
                    "title": "Original Title",
                    "description": "Original description",
                    "duration_seconds": 3.0,
                }
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        # Update scene
        response = await client.put(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/1",
            json={
                "title": "Updated Title",
                "description": "Updated description",
                "duration_seconds": 4.0,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["version"] == 2
        assert data["is_active"] is True
        assert data["scenes"][0]["title"] == "Updated Title"
        assert data["scenes"][0]["duration_seconds"] == 4.0

    @pytest.mark.asyncio
    async def test_update_nonexistent_scene(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test updating non-existent scene returns 404."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.put(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/999",
            json={"title": "New Title"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_scene_partial_fields(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test updating only some scene fields."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {
                    "scene_number": 1,
                    "scene_type": "hook",
                    "title": "Original Title",
                    "description": "Description",
                    "narration_script": "Original script",
                    "duration_seconds": 3.0,
                }
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.put(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/1",
            json={"title": "New Title"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Title should be updated
        assert data["scenes"][0]["title"] == "New Title"
        # Other fields should remain unchanged
        assert data["scenes"][0]["narration_script"] == "Original script"


class TestSceneCreate:
    """Test scene creation endpoints."""

    @pytest.mark.asyncio
    async def test_create_scene_append_at_end(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test POST /projects/{project_id}/storyboard/scenes appends new scene."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {
                    "scene_number": 1,
                    "scene_type": "hook",
                    "title": "Scene 1",
                    "description": "Description 1",
                    "duration_seconds": 3.0,
                }
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes",
            json={
                "scene_type": "problem",
                "title": "Scene 2",
                "description": "Description 2",
                "duration_seconds": 4.0,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["scenes"]) == 2
        assert data["scenes"][1]["scene_number"] == 2
        assert data["scenes"][1]["scene_type"] == "problem"

    @pytest.mark.asyncio
    async def test_create_scene_insert_after(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test creating scene with insert_after parameter."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {"scene_number": 1, "scene_type": "hook", "title": "Scene 1", "description": "Desc"},
                {"scene_number": 2, "scene_type": "solution", "title": "Scene 2", "description": "Desc"},
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes",
            json={
                "scene_type": "problem",
                "title": "Problem Scene",
                "description": "Between hook and solution",
                "insert_after": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["scenes"]) == 3
        # New scene should be at position 2
        assert data["scenes"][1]["title"] == "Problem Scene"

    @pytest.mark.asyncio
    async def test_create_scene_validation_error(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test creating scene with invalid data raises validation error."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.post(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes",
            json={
                "scene_type": "invalid_type",
                "title": "Test Scene",
                "description": "Test",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestSceneDelete:
    """Test scene deletion endpoints."""

    @pytest.mark.asyncio
    async def test_delete_scene(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test DELETE /projects/{project_id}/storyboard/scenes/{scene_number}."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {"scene_number": 1, "scene_type": "hook", "title": "Scene 1", "description": "D"},
                {"scene_number": 2, "scene_type": "problem", "title": "Scene 2", "description": "D"},
                {"scene_number": 3, "scene_type": "solution", "title": "Scene 3", "description": "D"},
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.delete(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/2"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify scene was deleted
        get_response = await client.get(
            f"/api/v1/studio/projects/{video_project.id}/storyboard"
        )
        data = get_response.json()
        assert len(data["scenes"]) == 2
        # After deletion, scene titles should be 1 and 3, but renumbered to 1 and 2
        scene_titles = {s["title"] for s in data["scenes"]}
        assert "Scene 1" in scene_titles
        assert "Scene 3" in scene_titles
        assert "Scene 2" not in scene_titles

    @pytest.mark.asyncio
    async def test_delete_nonexistent_scene(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test deleting non-existent scene returns 404."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.delete(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/999"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSceneReorder:
    """Test scene reordering endpoints."""

    @pytest.mark.asyncio
    async def test_reorder_scenes(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test PUT /projects/{project_id}/storyboard/scenes/reorder."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {"scene_number": 1, "scene_type": "hook", "title": "Scene 1", "description": "D"},
                {"scene_number": 2, "scene_type": "problem", "title": "Scene 2", "description": "D"},
                {"scene_number": 3, "scene_type": "solution", "title": "Scene 3", "description": "D"},
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        # Reorder to 3, 1, 2
        response = await client.put(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/reorder",
            json={"scene_order": [3, 1, 2]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["version"] == 2
        # Verify order changed - scenes maintain their original order structure
        # but their scene_numbers are renumbered
        scene_titles = [s["title"] for s in data["scenes"]]
        # Scene 3 (Solution) should now be first
        assert scene_titles[0] == "Scene 3"
        assert scene_titles[1] == "Scene 1"
        assert scene_titles[2] == "Scene 2"

    @pytest.mark.asyncio
    async def test_reorder_invalid_order(
        self, client: AsyncClient, video_project, db: AsyncSession
    ):
        """Test reorder with invalid scene numbers returns error."""
        storyboard = Storyboard(
            id=str(uuid.uuid4()),
            video_project_id=video_project.id,
            generation_mode="reference_structure",
            scenes=[
                {"scene_number": 1, "scene_type": "hook", "title": "Scene 1", "description": "D"},
                {"scene_number": 2, "scene_type": "problem", "title": "Scene 2", "description": "D"},
            ],
            version=1,
            is_active=True,
        )
        db.add(storyboard)
        await db.commit()

        response = await client.put(
            f"/api/v1/studio/projects/{video_project.id}/storyboard/scenes/reorder",
            json={"scene_order": [1, 999]},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
