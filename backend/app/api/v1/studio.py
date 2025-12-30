"""
Video Studio API endpoints for project and scene management.
"""

import logging
import time
import traceback
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Brand, Product, ReferenceAnalysis, SceneImage, VideoProject, Storyboard
from app.models.scene_video import SceneVideo
from app.services.video_generator import get_video_generator, SceneInput, SceneVideoResult
from app.services.video_generator.video_concatenator import get_video_concatenator
from app.schemas.studio import (
    ExtendedVideoGenerationRequest,
    ExtendedVideoGenerationResponse,
    ExtendedVideoGenerationStatusResponse,
    MarketingImageGenerateRequest,
    ProductImageEditRequest,
    ProductSceneComposeRequest,
    SceneCreateRequest,
    SceneImageCreate,
    SceneImageGenerate,
    SceneImageResponse,
    SceneImageUpdate,
    SceneSchema,
    SceneUpdateRequest,
    ScenesReorderRequest,
    SceneVideoGenerateRequest,
    SceneVideoResponse,
    SceneVideoStatus,
    StoryboardGenerateRequest,
    StoryboardResponse,
    VideoConcatenateRequest,
    VideoProjectCreate,
    VideoProjectResponse,
    VideoProjectSummary,
    VideoProjectUpdate,
)
from app.schemas.sns import (
    SNSDownloadRequest,
    SNSDownloadResponse,
    SNSExtractImagesRequest,
    SNSExtractImagesResponse,
    SNSImageInfo,
    SNSParseRequest,
    SNSParseResponse,
)

router = APIRouter()


# ========== Video Project Endpoints ==========

@router.post("/projects", response_model=VideoProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: VideoProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new video project."""
    # Validate brand exists
    brand_result = await db.execute(select(Brand).where(Brand.id == project_data.brand_id))
    if not brand_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Brand not found")

    # Validate product exists
    product_result = await db.execute(select(Product).where(Product.id == project_data.product_id))
    if not product_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate reference analysis if provided
    if project_data.reference_analysis_id:
        ref_result = await db.execute(
            select(ReferenceAnalysis).where(ReferenceAnalysis.id == project_data.reference_analysis_id)
        )
        if not ref_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Reference analysis not found")

    project = VideoProject(
        id=str(uuid.uuid4()),
        title=project_data.title,
        description=project_data.description,
        brand_id=project_data.brand_id,
        product_id=project_data.product_id,
        reference_analysis_id=project_data.reference_analysis_id,
        target_duration=project_data.target_duration,
        aspect_ratio=project_data.aspect_ratio,
        status="draft",
        current_step=1,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("/projects", response_model=List[VideoProjectSummary])
async def list_projects(
    brand_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all video projects with optional filtering."""
    query = select(VideoProject).order_by(VideoProject.updated_at.desc())

    if brand_id:
        query = query.where(VideoProject.brand_id == brand_id)
    if status:
        query = query.where(VideoProject.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    return projects


@router.get("/projects/{project_id}", response_model=VideoProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a video project by ID."""
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.patch("/projects/{project_id}", response_model=VideoProjectResponse)
async def update_project(
    project_id: str,
    project_data: VideoProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a video project."""
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a video project."""
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()


# ========== Scene Image Endpoints ==========

@router.post(
    "/projects/{project_id}/scenes/upload-temp",
    status_code=status.HTTP_201_CREATED,
)
async def upload_temp_image(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload image to temporary storage for preview.
    Does NOT save to database. Call /scenes/save to persist.
    """
    import os
    from app.core.config import settings

    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Validate file size (max 50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Save to temp directory
    temp_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{temp_id}.{ext}"

    temp_dir = os.path.join(settings.TEMP_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    filepath = os.path.join(temp_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    preview_url = f"http://localhost:8000/static/temp/{filename}"
    logger.info(f"Temp image saved: {filepath}")

    return {
        "temp_id": temp_id,
        "filename": filename,
        "preview_url": preview_url,
        "mime_type": file.content_type,
    }


@router.post(
    "/projects/{project_id}/scenes/save",
    response_model=SceneImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_scene_image(
    project_id: str,
    scene_number: int,
    temp_id: str,
    filename: str,
    source: str = "uploaded",
    scene_segment_type: Optional[str] = None,
    scene_description: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    generation_prompt: Optional[str] = None,
    generation_provider: Optional[str] = None,
    generation_duration_ms: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Save a temporary image to permanent storage and database.
    Called when user clicks 'Next' or 'Save'.
    """
    import os
    import shutil
    from app.core.config import settings

    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check temp file exists
    temp_path = os.path.join(settings.TEMP_DIR, "temp", filename)
    if not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Temporary image not found")

    # Move to permanent storage
    permanent_dir = os.path.join(settings.TEMP_DIR, "images", project_id)
    os.makedirs(permanent_dir, exist_ok=True)

    image_id = str(uuid.uuid4())
    ext = filename.split(".")[-1]
    new_filename = f"{image_id}.{ext}"
    permanent_path = os.path.join(permanent_dir, new_filename)

    shutil.move(temp_path, permanent_path)
    image_url = f"http://localhost:8000/static/images/{project_id}/{new_filename}"
    logger.info(f"Image saved permanently: {permanent_path}")

    # Deactivate existing active images for this scene
    existing_result = await db.execute(
        select(SceneImage).where(
            SceneImage.video_project_id == project_id,
            SceneImage.scene_number == scene_number,
            SceneImage.is_active == True,
        )
    )
    existing_images = existing_result.scalars().all()
    for img in existing_images:
        img.is_active = False

    # Get latest version number
    version = 1
    if existing_images:
        version = max(img.version for img in existing_images) + 1

    scene_image = SceneImage(
        id=image_id,
        video_project_id=project_id,
        scene_number=scene_number,
        source=source,
        image_url=image_url,
        generation_prompt=generation_prompt,
        generation_provider=generation_provider,
        generation_duration_ms=generation_duration_ms,
        scene_segment_type=scene_segment_type,
        scene_description=scene_description,
        duration_seconds=duration_seconds,
        version=version,
        is_active=True,
        previous_version_id=existing_images[0].id if existing_images else None,
    )

    db.add(scene_image)
    await db.commit()
    await db.refresh(scene_image)

    return scene_image


@router.post(
    "/projects/{project_id}/scenes/generate",
    status_code=status.HTTP_201_CREATED,
)
async def generate_scene_image(
    project_id: str,
    generate_data: SceneImageGenerate,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an AI image for a scene.
    Returns temporary preview URL. Call /scenes/save to persist to database.
    """
    from app.services.video_generator.image_generator import get_image_generator
    import base64
    import os
    from app.core.config import settings

    logger.info(f"=== generate_scene_image called ===")
    logger.info(f"project_id: {project_id}")
    logger.info(f"generate_data: scene_number={generate_data.scene_number}, provider={generate_data.provider}")

    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    logger.info(f"Project found: {project.title}, aspect_ratio: {project.aspect_ratio}")

    # Get brand and product info for context
    context_info = ""
    if project.brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == project.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            context_info += f"Brand: {brand.name}. "

    # Store product info for potential image-based generation
    product_image_data = None
    product_description = None

    if project.product_id:
        product_result = await db.execute(select(Product).where(Product.id == project.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            context_info += f"Product: {product.name}"
            if product.product_category:
                context_info += f" ({product.product_category})"
            context_info += ". "
            # Use AI-generated image description if available (most accurate for image generation)
            if product.image_description:
                context_info += f"Product Appearance: {product.image_description} "
                product_description = product.image_description
            elif product.description:
                # Fallback to product description
                desc = product.description[:100] if len(product.description) > 100 else product.description
                context_info += f"Description: {desc}. "
                product_description = desc

            # Load product image if available
            if product.image_url:
                try:
                    image_path = product.image_url

                    # Convert localhost URL to local path
                    if image_path.startswith("http://localhost:8000/static/"):
                        image_path = image_path.replace("http://localhost:8000/static/", "/static/")
                        logger.info(f"Converted localhost URL to path: {image_path}")

                    # Handle local static files
                    if image_path.startswith("/static/"):
                        local_path = image_path.replace("/static/", f"{settings.TEMP_DIR}/")
                        if os.path.exists(local_path):
                            with open(local_path, "rb") as f:
                                product_image_data = f.read()
                            logger.info(f"Loaded product image from: {local_path}")
                        else:
                            logger.warning(f"Product image file not found: {local_path}")
                    elif image_path.startswith("http"):
                        # Remote URL - skip for now
                        logger.info(f"Product has remote image URL (skipped): {image_path}")
                    else:
                        # Direct file path
                        if os.path.exists(image_path):
                            with open(image_path, "rb") as f:
                                product_image_data = f.read()
                            logger.info(f"Loaded product image from: {image_path}")
                except Exception as e:
                    logger.warning(f"Failed to load product image: {e}")

    logger.info(f"Context info: {context_info[:100]}...")
    logger.info(f"Product image available: {product_image_data is not None}")

    # Generate image using the selected provider
    provider = generate_data.provider or "mock"
    logger.info(f"Using provider: {provider}")

    try:
        prompt = generate_data.prompt or generate_data.scene_description or "Marketing scene"
        aspect_ratio = project.aspect_ratio or "16:9"

        # If we have a product image, use edit_with_product for better results
        if product_image_data and provider == "gemini_imagen":
            logger.info("Using image editor with product image reference...")
            from app.services.image_editor import get_image_editor

            editor = get_image_editor()

            # Build prompt with context
            full_prompt = f"""Create a professional marketing image.
{context_info}

Scene description: {prompt}

IMPORTANT: Feature the product exactly as shown in the reference image.
Maintain the product's exact appearance, colors, shape, and branding.
Place the product naturally in the scene according to the description."""

            gen_result = await editor.edit_with_product(
                edit_prompt=full_prompt,
                aspect_ratio=aspect_ratio,
                product_description=product_description,
                images_data=[(product_image_data, "image/png")],
            )
            logger.info(f"Image generation with product reference successful")
        else:
            # Regular generation without product image
            logger.info("Getting image generator instance...")
            generator = get_image_generator(provider)
            logger.info(f"Generator instance: {type(generator).__name__}")

            # Optimize prompt for image generation (translate to English, make visual-friendly)
            if provider == "gemini_imagen":
                from app.services.video_generator.image_generator import get_prompt_optimizer
                optimizer = get_prompt_optimizer()
                original_prompt = prompt
                # Add context (brand/product info) to prompt for better generation
                prompt_with_context = f"{context_info}\nScene: {prompt}" if context_info else prompt
                prompt = await optimizer.optimize(prompt_with_context)
                logger.info(f"Prompt optimized: '{original_prompt[:30]}...' -> '{prompt[:50]}...'")

            logger.info(f"Calling generate() with prompt: {prompt[:50]}..., aspect_ratio: {aspect_ratio}")

            gen_result = await generator.generate(
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
            logger.info(f"Generation successful: {gen_result.keys()}")
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

    # Save to temp directory (NOT to database)
    temp_id = str(uuid.uuid4())
    image_data = gen_result.get("image_data")
    mime_type = gen_result.get("mime_type", "image/png")
    generation_duration_ms = gen_result.get("generation_time_ms")

    if image_data:
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{temp_id}.{ext}"

        temp_dir = os.path.join(settings.TEMP_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        filepath = os.path.join(temp_dir, filename)
        image_bytes = base64.b64decode(image_data)
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        preview_url = f"http://localhost:8000/static/temp/{filename}"
        logger.info(f"Generated image saved to temp: {filepath}")
    else:
        # For mock provider with URL
        filename = f"{temp_id}.jpg"
        preview_url = gen_result.get("image_url")

    return {
        "temp_id": temp_id,
        "filename": filename,
        "preview_url": preview_url,
        "mime_type": mime_type,
        "generation_time_ms": generation_duration_ms,
        "generation_provider": provider,
        "generation_prompt": prompt,
        "scene_number": generate_data.scene_number,
        "scene_description": generate_data.scene_description,
        "scene_segment_type": generate_data.scene_segment_type,
        "duration_seconds": generate_data.duration_seconds,
    }


@router.get("/projects/{project_id}/scenes", response_model=List[SceneImageResponse])
async def list_scene_images(
    project_id: str,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """List all scene images for a project."""
    query = select(SceneImage).where(SceneImage.video_project_id == project_id)

    if active_only:
        query = query.where(SceneImage.is_active == True)

    query = query.order_by(SceneImage.scene_number, SceneImage.version.desc())
    result = await db.execute(query)
    images = result.scalars().all()

    return images


@router.delete("/projects/{project_id}/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene_image(
    project_id: str,
    scene_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene image."""
    result = await db.execute(
        select(SceneImage).where(
            SceneImage.id == scene_id,
            SceneImage.video_project_id == project_id,
        )
    )
    scene_image = result.scalar_one_or_none()

    if not scene_image:
        raise HTTPException(status_code=404, detail="Scene image not found")

    await db.delete(scene_image)
    await db.commit()


# ========== Storyboard Endpoints ==========


def _calculate_total_duration(scenes: List[dict]) -> float:
    """Calculate total duration of all scenes."""
    return sum(s.get("duration_seconds", 0) for s in scenes)


def _find_scene_index(scenes: List[dict], scene_number: int) -> Optional[int]:
    """Find the index of a scene by its scene_number. Returns None if not found."""
    for i, scene in enumerate(scenes):
        if scene.get("scene_number") == scene_number:
            return i
    return None


def _normalize_storyboard_scenes(scenes: List[dict]) -> List[dict]:
    """
    Normalize AI-generated scene values to match the schema constraints.
    Maps various scene_type and transition_effect values to allowed values.
    """
    # Allowed values from schema
    ALLOWED_SCENE_TYPES = {"hook", "problem", "solution", "benefit", "cta", "transition", "intro", "outro"}
    ALLOWED_TRANSITIONS = {"cut", "fade", "fade_in", "fade_out", "zoom", "slide", "dissolve"}

    # Mapping for scene types
    SCENE_TYPE_MAP = {
        "pain_point": "problem",
        "pain_point_empathy": "problem",
        "pain_point_empathy_1": "problem",
        "pain_point_empathy_2": "problem",
        "call_to_action": "cta",
        "solution_introduction": "solution",
        "benefits_features": "benefit",
        "benefits_and_transformation": "benefit",
        "usp_and_brand_values": "benefit",
        "credibility_brand_values": "benefit",
        "credibility": "benefit",
        "social_proof": "benefit",
        "opening": "hook",
        "attention_grabber": "hook",
        "closing": "outro",
        "end": "outro",
        "urgency": "cta",
        "agitation": "problem",
        "feature": "benefit",
    }

    # Mapping for transition effects
    TRANSITION_MAP = {
        "cross_dissolve": "dissolve",
        "smooth_reveal": "fade_in",
        "zoom_out": "zoom",
        "zoom_in": "zoom",
        "graphic_wipe": "slide",
        "fade_out_in": "fade",
        "slide_left": "slide",
        "slide_right": "slide",
        "wipe": "slide",
        "quick_cut": "cut",
    }

    normalized_scenes = []
    for scene in scenes:
        normalized = scene.copy()

        # Normalize scene_type
        scene_type = scene.get("scene_type", "").lower().replace(" ", "_")
        if scene_type not in ALLOWED_SCENE_TYPES:
            # Try mapping
            mapped = SCENE_TYPE_MAP.get(scene_type)
            if mapped:
                normalized["scene_type"] = mapped
            else:
                # Check if any allowed type is contained in the value
                for allowed in ALLOWED_SCENE_TYPES:
                    if allowed in scene_type:
                        normalized["scene_type"] = allowed
                        break
                else:
                    # Default fallback
                    normalized["scene_type"] = "transition"

        # Normalize transition_effect
        transition = scene.get("transition_effect", "").lower().replace(" ", "_")
        if transition not in ALLOWED_TRANSITIONS:
            mapped = TRANSITION_MAP.get(transition)
            if mapped:
                normalized["transition_effect"] = mapped
            else:
                # Check if any allowed transition is contained in the value
                for allowed in ALLOWED_TRANSITIONS:
                    if allowed in transition:
                        normalized["transition_effect"] = allowed
                        break
                else:
                    # Default fallback
                    normalized["transition_effect"] = "fade"

        normalized_scenes.append(normalized)

    return normalized_scenes


def _generate_mock_scenes(
    mode: str,
    count: int = 6,
    language: str = "ko",
    target_duration: Optional[int] = None,
    brand_name: Optional[str] = None,
    product_name: Optional[str] = None,
    product_description: Optional[str] = None,
) -> List[dict]:
    """
    Generate mock storyboard scenes for testing and demonstration purposes.

    This creates a default storyboard structure with typical marketing video segments.
    In production, this would be replaced by AI-powered scene generation.

    Args:
        mode: Generation mode ('reference_structure' or 'ai_optimized')
        count: Number of scenes to generate (max 6)
        language: Language code for content (ko, en, etc.)
        target_duration: Target total duration in seconds (optional)
        brand_name: Brand name to include in scenes
        product_name: Product name to include in scenes
        product_description: Product description for context

    Returns:
        List of scene dictionaries with all required fields
    """
    scene_types = ["hook", "problem", "solution", "benefit", "cta", "outro"]

    # Calculate per-scene duration based on target
    if target_duration:
        base_duration = target_duration / count
    else:
        base_duration = 5.0  # Default 5 seconds per scene

    # Use placeholders if no brand/product provided
    brand_display = brand_name or "브랜드" if language.startswith("ko") else "Brand"
    product_display = product_name or "제품" if language.startswith("ko") else "Product"

    # Korean content
    if language.startswith("ko"):
        mock_prompts = {
            "hook": f"시청자의 관심을 즉시 끄는 강렬한 오프닝 - {product_display} 소개",
            "problem": f"고객이 겪는 문제점과 고민을 보여줍니다 - {product_display}이 해결할 문제",
            "solution": f"{product_display}을(를) 해결책으로 제시합니다",
            "benefit": f"{product_display} 사용 후 긍정적인 변화와 효과를 보여줍니다",
            "cta": f"{product_display} 구매/체험을 유도하는 콜투액션",
            "outro": f"{brand_display} 메시지와 함께 마무리",
        }
        titles = {
            "hook": "후킹",
            "problem": "문제 제기",
            "solution": "해결책 제시",
            "benefit": "효과/혜택",
            "cta": "행동 유도",
            "outro": "마무리",
        }
        narration_template = "{type} 장면 나레이션 - " + product_display
        visual_template = "{type} 장면 연출 - " + product_display + " 중심"
        music_suggestion = "분위기: 역동적, 장르: 모던"
        subtitle_template = "장면 {num}"
    else:
        # English content (default)
        mock_prompts = {
            "hook": f"Engaging opening that captures attention - Introducing {product_display}",
            "problem": f"Highlight the customer's pain point that {product_display} solves",
            "solution": f"Present {product_display} as the solution",
            "benefit": f"Show the positive outcomes of using {product_display}",
            "cta": f"Call to action - Try {product_display} today",
            "outro": f"Closing scene with {brand_display} message",
        }
        titles = {
            "hook": "Hook",
            "problem": "Problem",
            "solution": "Solution",
            "benefit": "Benefit",
            "cta": "Call to Action",
            "outro": "Outro",
        }
        narration_template = "Narration for {type} scene - " + product_display
        visual_template = "Visual direction for {type} - featuring " + product_display
        music_suggestion = "Mood: dynamic, Genre: Modern"
        subtitle_template = "Scene {num}"

    scenes = []
    for i in range(min(count, len(scene_types))):
        scene_type = scene_types[i]
        # Vary duration slightly for natural feel (hook shorter, benefit/cta longer)
        duration_weights = {"hook": 0.8, "problem": 1.0, "solution": 1.1, "benefit": 1.2, "cta": 1.0, "outro": 0.9}
        scene_duration = round(base_duration * duration_weights.get(scene_type, 1.0), 1)

        scenes.append(
            {
                "scene_number": i + 1,
                "scene_type": scene_type,
                "title": f"{titles.get(scene_type, scene_type.capitalize())}",
                "description": mock_prompts.get(scene_type, f"Description for {scene_type} scene"),
                "narration_script": narration_template.format(type=titles.get(scene_type, scene_type)),
                "visual_direction": visual_template.format(type=titles.get(scene_type, scene_type)),
                "background_music_suggestion": music_suggestion,
                "transition_effect": "fade" if i < count - 1 else "fade_out",
                "subtitle_text": subtitle_template.format(num=i + 1),
                "duration_seconds": scene_duration,
                "generated_image_id": None,
            }
        )

    return scenes


@router.post(
    "/projects/{project_id}/storyboard/generate",
    response_model=StoryboardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_storyboard(
    project_id: str,
    generate_data: StoryboardGenerateRequest,
    accept_language: Optional[str] = Header(default="ko", alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new storyboard for a video project."""
    from app.services.video_generator.storyboard_generator import get_storyboard_generator

    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get brand info for storyboard context
    brand_info = {"name": "Brand", "tone_and_manner": "Professional", "key_values": [], "keywords": []}
    if project.brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == project.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            brand_info = {
                "name": brand.name,
                "description": brand.description or "",
                "tone_and_manner": brand.tone_and_manner or "Professional",
                "key_values": brand.keywords or [],  # Use keywords as key_values
                "keywords": brand.keywords or [],
            }

    # Get product info for storyboard context
    product_info = {"name": "Product", "description": "", "features": [], "benefits": []}
    if project.product_id:
        product_result = await db.execute(select(Product).where(Product.id == project.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            product_info = {
                "name": product.name,
                "description": product.description or product.image_description or "",
                "features": product.features or [],
                "benefits": product.benefits or [],
                "product_category": product.product_category or "",
                "key_ingredients": product.key_ingredients or [],
                "unique_selling_proposition": "",
            }

    logger.info(f"Generating storyboard for brand: {brand_info['name']}, product: {product_info['name']}")

    # Deactivate existing active storyboards for this project
    existing_result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    existing_storyboards = existing_result.scalars().all()
    for sb in existing_storyboards:
        sb.is_active = False

    # Parse language from Accept-Language header (e.g., "ko-KR,ko;q=0.9,en;q=0.8")
    language = accept_language.split(",")[0].split("-")[0] if accept_language else "ko"
    logger.info(f"Generating storyboard with language: {language}, target_duration: {generate_data.target_duration}")

    # Use AI-powered storyboard generation with Gemini
    try:
        generator = get_storyboard_generator("gemini")

        # Build reference analysis context (can be empty if no reference)
        reference_analysis = {
            "segments": [],
            "hook_points": [],
            "pain_points": [],
            "selling_points": [],
            "duration": generate_data.target_duration or 30,
        }

        # If project has reference analysis, load it
        if project.reference_analysis_id:
            ref_result = await db.execute(
                select(ReferenceAnalysis).where(ReferenceAnalysis.id == project.reference_analysis_id)
            )
            ref_analysis = ref_result.scalar_one_or_none()
            if ref_analysis:
                reference_analysis = {
                    "segments": ref_analysis.segments or [],
                    "hook_points": ref_analysis.hook_points or [],
                    "pain_points": ref_analysis.pain_points or [],
                    "selling_points": ref_analysis.selling_points or [],
                    "duration": ref_analysis.duration or generate_data.target_duration or 30,
                }

        storyboard_result = await generator.generate(
            reference_analysis=reference_analysis,
            brand_info=brand_info,
            product_info=product_info,
            mode=generate_data.mode,
            target_duration=generate_data.target_duration,
            language=language,
        )
        scenes = storyboard_result.get("scenes", [])

        # Normalize AI-generated values to match schema
        scenes = _normalize_storyboard_scenes(scenes)
        logger.info(f"AI-generated {len(scenes)} scenes")

    except Exception as e:
        logger.warning(f"AI storyboard generation failed, using mock: {e}")
        # Fallback to mock if AI fails
        scenes = _generate_mock_scenes(
            generate_data.mode,
            language=language,
            target_duration=generate_data.target_duration,
            brand_name=brand_info["name"],
            product_name=product_info["name"],
            product_description=product_info["description"],
        )

    # Create new storyboard
    total_duration = _calculate_total_duration(scenes)
    storyboard = Storyboard(
        id=str(uuid.uuid4()),
        video_project_id=project_id,
        generation_mode=generate_data.mode,
        scenes=scenes,
        total_duration_seconds=total_duration,
        version=1,
        is_active=True,
        previous_version_id=existing_storyboards[0].id if existing_storyboards else None,
    )

    db.add(storyboard)
    await db.commit()
    await db.refresh(storyboard)

    return storyboard


@router.get("/projects/{project_id}/storyboard", response_model=StoryboardResponse)
async def get_active_storyboard(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the currently active storyboard for a project."""
    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get active storyboard
    result = await db.execute(
        select(Storyboard)
        .where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
        .order_by(Storyboard.version.desc())
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=404, detail="Active storyboard not found")

    return storyboard


@router.get("/projects/{project_id}/storyboard/versions", response_model=List[StoryboardResponse])
async def get_storyboard_versions(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all versions of storyboard for a project."""
    # Validate project exists
    result = await db.execute(select(VideoProject).where(VideoProject.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all storyboards ordered by version descending
    result = await db.execute(
        select(Storyboard)
        .where(Storyboard.video_project_id == project_id)
        .order_by(Storyboard.version.desc())
    )
    storyboards = result.scalars().all()

    return storyboards


@router.put("/projects/{project_id}/storyboard/scenes/reorder", response_model=StoryboardResponse)
async def reorder_scenes(
    project_id: str,
    reorder_data: ScenesReorderRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reorder scenes in the active storyboard."""
    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=404, detail="Active storyboard not found")

    # Validate all scene numbers exist
    existing_scene_numbers = {s.get("scene_number") for s in storyboard.scenes}
    requested_scene_numbers = set(reorder_data.scene_order)

    if existing_scene_numbers != requested_scene_numbers:
        raise HTTPException(status_code=400, detail="Invalid scene order: missing or extra scene numbers")

    # Create new ordered scenes list
    scene_map = {s.get("scene_number"): s.copy() for s in storyboard.scenes}
    new_scenes = []
    for new_position, original_scene_number in enumerate(reorder_data.scene_order, 1):
        scene = scene_map[original_scene_number]
        scene["scene_number"] = new_position
        new_scenes.append(scene)

    # Deactivate old storyboard
    storyboard.is_active = False

    # Create new storyboard version
    new_storyboard = Storyboard(
        id=str(uuid.uuid4()),
        video_project_id=project_id,
        generation_mode=storyboard.generation_mode,
        source_reference_analysis_id=storyboard.source_reference_analysis_id,
        scenes=new_scenes,
        total_duration_seconds=_calculate_total_duration(new_scenes),
        version=storyboard.version + 1,
        is_active=True,
        previous_version_id=storyboard.id,
    )

    db.add(new_storyboard)
    await db.commit()
    await db.refresh(new_storyboard)

    return new_storyboard


@router.put("/projects/{project_id}/storyboard/scenes/{scene_number}", response_model=StoryboardResponse)
async def update_scene(
    project_id: str,
    scene_number: int,
    update_data: SceneUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a specific scene in the active storyboard."""
    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=404, detail="Active storyboard not found")

    # Find scene by scene_number
    scene_index = _find_scene_index(storyboard.scenes, scene_number)

    if scene_index is None:
        raise HTTPException(status_code=404, detail=f"Scene number {scene_number} not found")

    # Create new version
    new_scenes = [scene.copy() for scene in storyboard.scenes]
    update_fields = update_data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        if value is not None:
            new_scenes[scene_index][field] = value

    # Deactivate old storyboard
    storyboard.is_active = False

    # Create new storyboard version
    new_storyboard = Storyboard(
        id=str(uuid.uuid4()),
        video_project_id=project_id,
        generation_mode=storyboard.generation_mode,
        source_reference_analysis_id=storyboard.source_reference_analysis_id,
        scenes=new_scenes,
        total_duration_seconds=_calculate_total_duration(new_scenes),
        version=storyboard.version + 1,
        is_active=True,
        previous_version_id=storyboard.id,
    )

    db.add(new_storyboard)
    await db.commit()
    await db.refresh(new_storyboard)

    return new_storyboard


@router.post("/projects/{project_id}/storyboard/scenes", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    project_id: str,
    scene_data: SceneCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a new scene to the active storyboard."""
    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=404, detail="Active storyboard not found")

    # Create new scenes list
    new_scenes = [scene.copy() for scene in storyboard.scenes]

    # Determine insertion position
    if scene_data.insert_after is not None:
        # Insert after specific scene number
        insert_pos = None
        for i, scene in enumerate(new_scenes):
            if scene.get("scene_number") == scene_data.insert_after:
                insert_pos = i + 1
                break

        if insert_pos is None:
            raise HTTPException(status_code=400, detail=f"Scene number {scene_data.insert_after} not found")

        # Create new scene with appropriate numbering
        new_scene_number = insert_pos + 1
        new_scenes.insert(
            insert_pos,
            {
                "scene_number": new_scene_number,
                "scene_type": scene_data.scene_type,
                "title": scene_data.title,
                "description": scene_data.description,
                "narration_script": scene_data.narration_script,
                "visual_direction": scene_data.visual_direction,
                "background_music_suggestion": scene_data.background_music_suggestion,
                "transition_effect": scene_data.transition_effect,
                "subtitle_text": scene_data.subtitle_text,
                "duration_seconds": scene_data.duration_seconds,
                "generated_image_id": None,
            },
        )

        # Renumber scenes after insertion point
        for i in range(insert_pos + 1, len(new_scenes)):
            new_scenes[i]["scene_number"] = i + 1
    else:
        # Append at end
        new_scene_number = len(new_scenes) + 1
        new_scenes.append(
            {
                "scene_number": new_scene_number,
                "scene_type": scene_data.scene_type,
                "title": scene_data.title,
                "description": scene_data.description,
                "narration_script": scene_data.narration_script,
                "visual_direction": scene_data.visual_direction,
                "background_music_suggestion": scene_data.background_music_suggestion,
                "transition_effect": scene_data.transition_effect,
                "subtitle_text": scene_data.subtitle_text,
                "duration_seconds": scene_data.duration_seconds,
                "generated_image_id": None,
            },
        )

    # Deactivate old storyboard
    storyboard.is_active = False

    # Create new storyboard version
    new_storyboard = Storyboard(
        id=str(uuid.uuid4()),
        video_project_id=project_id,
        generation_mode=storyboard.generation_mode,
        source_reference_analysis_id=storyboard.source_reference_analysis_id,
        scenes=new_scenes,
        total_duration_seconds=_calculate_total_duration(new_scenes),
        version=storyboard.version + 1,
        is_active=True,
        previous_version_id=storyboard.id,
    )

    db.add(new_storyboard)
    await db.commit()
    await db.refresh(new_storyboard)

    return new_storyboard


# ========== Marketing Image Production Endpoints (New) ==========


@router.post("/images/analyze")
async def analyze_marketing_image(
    file: UploadFile = File(...),
    accept_language: Optional[str] = Header(None, alias="Accept-Language"),
):
    """
    Analyze an uploaded image using Gemini Vision to understand its content.
    Returns description, detected type (background, product, reference), and elements.
    Descriptions are returned in the language specified by Accept-Language header.
    """
    from app.services.image_analyzer import MarketingImageAnalyzer
    import os
    from app.core.config import settings

    # Parse language from Accept-Language header (e.g., "ko-KR,ko;q=0.9,en-US;q=0.8")
    language = "en"
    if accept_language:
        # Get first language code
        first_lang = accept_language.split(",")[0].split(";")[0].strip()
        language = first_lang.split("-")[0]  # "ko-KR" -> "ko"
    logger.info(f"Analysis language: {language}")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Validate file size (max 50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")

    # Save to temp directory for processing
    temp_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{temp_id}.{ext}"

    temp_dir = os.path.join(settings.TEMP_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    filepath = os.path.join(temp_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    logger.info(f"Marketing image saved for analysis: {filepath}")

    try:
        # Analyze with Gemini Vision
        analyzer = MarketingImageAnalyzer()
        analysis_result = await analyzer.analyze(filepath, language=language)

        return {
            "temp_id": temp_id,
            "filename": filename,
            "preview_url": f"http://localhost:8000/static/temp/{filename}",
            "description": analysis_result.get("description", ""),
            "detected_type": analysis_result.get("detected_type", "unknown"),
            "is_realistic": analysis_result.get("is_realistic", True),
            "elements": analysis_result.get("elements", []),
            "visual_prompt": analysis_result.get("visual_prompt", ""),
        }
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        # Return basic response even if analysis fails
        return {
            "temp_id": temp_id,
            "filename": filename,
            "preview_url": f"http://localhost:8000/static/temp/{filename}",
            "description": "이미지 분석을 수행할 수 없습니다.",
            "detected_type": "unknown",
            "is_realistic": True,  # Default to True for safety
            "elements": [],
            "visual_prompt": "",
        }


@router.post("/images/generate")
async def generate_marketing_image(
    request: MarketingImageGenerateRequest,
):
    """
    Generate a marketing image using uploaded images and user prompt.

    Args:
        request: Request containing images, prompt, and aspect_ratio

    Returns:
        Generated image URL
    """
    from app.services.video_generator.image_generator import get_image_generator, get_prompt_optimizer
    import base64
    import os
    from app.core.config import settings

    images = request.images
    prompt = request.prompt
    aspect_ratio = request.aspect_ratio

    logger.info(f"=== generate_marketing_image called ===")
    logger.info(f"Number of images: {len(images)}")
    logger.info(f"Prompt: {prompt[:100]}...")

    try:
        # Build context from analyzed images - separate products from backgrounds
        product_descriptions = []
        background_descriptions = []
        reference_descriptions = []

        for i, img in enumerate(images, 1):
            if img.analysis:
                analysis = img.analysis
                img_type = analysis.detected_type or "unknown"
                # Use visual_prompt if available (more detailed), otherwise use description
                visual_info = getattr(analysis, 'visual_prompt', None) or analysis.description or ""

                if img_type == "product":
                    product_descriptions.append(visual_info)
                elif img_type == "background":
                    background_descriptions.append(analysis.description or "")
                elif img_type == "reference":
                    reference_descriptions.append(analysis.description or "")

        # Build intelligent prompt based on what images were provided
        prompt_parts = []

        if product_descriptions:
            prompt_parts.append(f"PRODUCT TO FEATURE (render this product exactly as described):\n" + "\n".join(product_descriptions))

        if background_descriptions:
            prompt_parts.append(f"BACKGROUND/SETTING:\n" + "\n".join(background_descriptions))

        if reference_descriptions:
            prompt_parts.append(f"STYLE REFERENCE:\n" + "\n".join(reference_descriptions))

        context_info = "\n\n".join(prompt_parts) if prompt_parts else ""

        # Combine context with user prompt
        full_prompt = f"""{context_info}

USER REQUEST: {prompt}

Create a professional marketing image. If a product is specified, ensure the product appears exactly as described with accurate colors, shape, materials, and branding. Place the product naturally in the scene according to the user's request."""

        # Optimize prompt for image generation
        optimizer = get_prompt_optimizer()
        optimized_prompt = await optimizer.optimize(full_prompt)
        logger.info(f"Optimized prompt: {optimized_prompt[:100]}...")

        # Generate image using Gemini Imagen
        generator = get_image_generator("gemini_imagen")
        gen_result = await generator.generate(
            prompt=optimized_prompt,
            aspect_ratio=aspect_ratio or "1:1",
        )

        # Save generated image to temp directory
        temp_id = str(uuid.uuid4())
        image_data = gen_result.get("image_data")
        mime_type = gen_result.get("mime_type", "image/png")

        if image_data:
            ext = "png" if "png" in mime_type else "jpg"
            filename = f"{temp_id}.{ext}"

            temp_dir = os.path.join(settings.TEMP_DIR, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            filepath = os.path.join(temp_dir, filename)
            image_bytes = base64.b64decode(image_data)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            image_url = f"http://localhost:8000/static/temp/{filename}"
            logger.info(f"Marketing image generated: {filepath}")
        else:
            # For mock provider
            image_url = gen_result.get("image_url", "")

        return {
            "image_id": temp_id,
            "image_url": image_url,
            "generation_time_ms": gen_result.get("generation_time_ms"),
            "optimized_prompt": optimized_prompt,
        }

    except Exception as e:
        logger.error(f"Marketing image generation failed: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/images/edit-with-product")
async def edit_image_with_product(
    request: ProductImageEditRequest,
):
    """
    Generate a new image while preserving the exact appearance of the product.

    This uses Gemini's multimodal image generation to:
    1. Take the product image as input
    2. Generate a new scene based on the prompt
    3. Ensure the product in the output looks exactly like the input

    Use this when you want to place a real product in different marketing contexts
    while maintaining visual consistency.

    Example prompts:
    - "A woman holding this product in a bathroom setting"
    - "This product on a marble countertop with soft lighting"
    - "Close-up shot of someone applying this product"
    """
    from app.services.image_editor import get_image_editor
    import os
    from app.core.config import settings

    logger.info(f"=== edit_image_with_product called ===")
    logger.info(f"image_temp_ids: {request.image_temp_ids}")
    logger.info(f"product_image_temp_id (legacy): {request.product_image_temp_id}")
    logger.info(f"prompt: {request.prompt[:100]}...")

    try:
        temp_dir = os.path.join(settings.TEMP_DIR, "temp")

        # Helper function to find and load image by temp_id
        def find_and_load_image(temp_id: str) -> tuple:
            for ext in ["png", "jpg", "jpeg", "webp"]:
                potential_path = os.path.join(temp_dir, f"{temp_id}.{ext}")
                if os.path.exists(potential_path):
                    mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
                    with open(potential_path, "rb") as f:
                        return f.read(), mime_type
            return None, None

        images_data = []

        # New approach: load all images from image_temp_ids
        if request.image_temp_ids:
            for temp_id in request.image_temp_ids:
                img_data, mime_type = find_and_load_image(temp_id)
                if img_data:
                    images_data.append((img_data, mime_type))
                    logger.info(f"Loaded image {temp_id}: {len(img_data)} bytes, {mime_type}")
                else:
                    logger.warning(f"Image not found: {temp_id}")

        # Legacy fallback: single product_image_temp_id
        elif request.product_image_temp_id:
            img_data, mime_type = find_and_load_image(request.product_image_temp_id)
            if img_data:
                images_data.append((img_data, mime_type))
                logger.info(f"Loaded legacy image: {len(img_data)} bytes, {mime_type}")

        if not images_data:
            raise HTTPException(status_code=404, detail="No images found. Upload images first using /images/analyze")

        logger.info(f"Total images to process: {len(images_data)}")

        # Get the image editor
        editor = get_image_editor()

        # Generate new image with all images
        result = await editor.edit_with_product(
            edit_prompt=request.prompt,
            aspect_ratio=request.aspect_ratio or "16:9",
            product_description=request.product_description,
            images_data=images_data,
        )

        # Save generated image to temp directory
        temp_id = str(uuid.uuid4())
        mime_type = result.get("mime_type", "image/png")
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{temp_id}.{ext}"

        filepath = os.path.join(temp_dir, filename)
        import base64
        image_bytes = base64.b64decode(result["image_data"])
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        image_url = f"http://localhost:8000/static/temp/{filename}"
        logger.info(f"Edited image saved: {filepath}")

        response_data = {
            "image_id": temp_id,
            "image_url": image_url,
            "generation_time_ms": result.get("generation_time_ms"),
            "mime_type": mime_type,
        }
        logger.info(f"Returning response: {response_data}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image edit failed: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Image edit failed: {str(e)}")


@router.post("/images/compose-scene")
async def compose_scene_with_product(
    request: ProductSceneComposeRequest,
):
    """
    Compose a marketing scene with a product placed on a background.

    This is more advanced than edit-with-product:
    - Can use a specific background image
    - Better for product placement on custom backgrounds
    - Handles lighting/shadow matching

    Example prompts:
    - "Place the product in the center of this background with natural shadows"
    - "Show the product being held by hands coming from the right side"
    """
    from app.services.image_editor import get_image_editor
    import os
    from app.core.config import settings

    logger.info(f"=== compose_scene_with_product called ===")
    logger.info(f"product_image_temp_id: {request.product_image_temp_id}")
    logger.info(f"background_image_temp_id: {request.background_image_temp_id}")
    logger.info(f"scene_prompt: {request.scene_prompt[:100]}...")

    try:
        temp_dir = os.path.join(settings.TEMP_DIR, "temp")

        # Find product image
        product_image_path = None
        product_mime_type = None
        for ext in ["png", "jpg", "jpeg", "webp"]:
            potential_path = os.path.join(temp_dir, f"{request.product_image_temp_id}.{ext}")
            if os.path.exists(potential_path):
                product_image_path = potential_path
                product_mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
                break

        if not product_image_path:
            raise HTTPException(status_code=404, detail="Product image not found")

        # Read product image
        with open(product_image_path, "rb") as f:
            product_image_data = f.read()

        # Find and read background image if provided
        background_image_data = None
        background_mime_type = None
        if request.background_image_temp_id:
            for ext in ["png", "jpg", "jpeg", "webp"]:
                potential_path = os.path.join(temp_dir, f"{request.background_image_temp_id}.{ext}")
                if os.path.exists(potential_path):
                    with open(potential_path, "rb") as f:
                        background_image_data = f.read()
                    background_mime_type = f"image/{'jpeg' if ext in ['jpg', 'jpeg'] else ext}"
                    break

        # Get the image editor
        editor = get_image_editor()

        # Compose the scene
        result = await editor.compose_scene(
            product_image_data=product_image_data,
            product_mime_type=product_mime_type,
            background_image_data=background_image_data,
            background_mime_type=background_mime_type,
            scene_prompt=request.scene_prompt,
            aspect_ratio=request.aspect_ratio or "16:9",
            product_description=request.product_description,
        )

        # Save generated image
        temp_id = str(uuid.uuid4())
        mime_type = result.get("mime_type", "image/png")
        ext = "png" if "png" in mime_type else "jpg"
        filename = f"{temp_id}.{ext}"

        filepath = os.path.join(temp_dir, filename)
        import base64
        image_bytes = base64.b64decode(result["image_data"])
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        image_url = f"http://localhost:8000/static/temp/{filename}"
        logger.info(f"Composed scene saved: {filepath}")

        return {
            "image_id": temp_id,
            "image_url": image_url,
            "generation_time_ms": result.get("generation_time_ms"),
            "mime_type": mime_type,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scene composition failed: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Scene composition failed: {str(e)}")


@router.delete("/projects/{project_id}/storyboard/scenes/{scene_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    project_id: str,
    scene_number: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scene from the active storyboard."""
    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=404, detail="Active storyboard not found")

    # Find scene by scene_number
    scene_index = _find_scene_index(storyboard.scenes, scene_number)

    if scene_index is None:
        raise HTTPException(status_code=404, detail=f"Scene number {scene_number} not found")

    # Create new scenes list without deleted scene
    new_scenes = [scene.copy() for scene in storyboard.scenes]
    del new_scenes[scene_index]

    # Renumber remaining scenes
    for i, scene in enumerate(new_scenes):
        scene["scene_number"] = i + 1

    # Deactivate old storyboard
    storyboard.is_active = False

    # Create new storyboard version
    new_storyboard = Storyboard(
        id=str(uuid.uuid4()),
        video_project_id=project_id,
        generation_mode=storyboard.generation_mode,
        source_reference_analysis_id=storyboard.source_reference_analysis_id,
        scenes=new_scenes,
        total_duration_seconds=_calculate_total_duration(new_scenes),
        version=storyboard.version + 1,
        is_active=True,
        previous_version_id=storyboard.id,
    )

    db.add(new_storyboard)
    await db.commit()
    await db.refresh(new_storyboard)

    return new_storyboard


# =============================================================================
# Video Generation Endpoints
# =============================================================================


class VideoGenerateRequest(BaseModel):
    """Request for video generation."""
    provider: str = "mock"  # "veo" or "mock"
    aspect_ratio: str = "16:9"
    mode: str = "per_scene"  # "single" for backward compatibility, "per_scene" for new architecture


class VideoGenerationStatusResponse(BaseModel):
    """Response for video generation status."""
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    operation_id: Optional[str] = None
    error_message: Optional[str] = None
    generation_time_ms: Optional[int] = None


@router.post("/projects/{project_id}/video/generate")
async def generate_video(
    project_id: str,
    request: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a marketing video from the project's storyboard and scene images.

    This endpoint supports two modes:
    - mode="single": Uses existing generate_marketing_video (backward compatible)
    - mode="per_scene": Uses new generate_per_scene_videos for better results (default)

    When using per_scene mode:
    1. Gets the active storyboard
    2. Collects all scene images
    3. Generates individual videos for each scene
    4. Saves SceneVideo records to database for tracking
    5. Returns ExtendedVideoGenerationStatusResponse with scene_videos populated
    """
    import base64
    import os
    from app.core.config import settings

    # Get project
    result = await db.execute(
        select(VideoProject).where(VideoProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=400, detail="No active storyboard found")

    if not storyboard.scenes:
        raise HTTPException(status_code=400, detail="Storyboard has no scenes")

    # Get scene images
    result = await db.execute(
        select(SceneImage).where(
            SceneImage.video_project_id == project_id,
            SceneImage.is_active == True,
        )
    )
    scene_images = {img.scene_number: img for img in result.scalars().all()}
    logger.info(f"Found {len(scene_images)} scene images for project {project_id}: {list(scene_images.keys())}")

    # Get brand and product info for context
    # IMPORTANT: This is passed separately to the video generator
    # The PromptBuilder will handle intelligent integration
    brand_product_context = ""
    if project.brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == project.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            brand_product_context += f"Brand: {brand.name}. "

    if project.product_id:
        product_result = await db.execute(select(Product).where(Product.id == project.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            brand_product_context += f"Product: {product.name}"
            if product.product_category:
                brand_product_context += f" ({product.product_category})"
            brand_product_context += ". "
            if product.image_description:
                brand_product_context += f"Product Appearance: {product.image_description} "
            elif product.description:
                desc = product.description[:150] if len(product.description) > 150 else product.description
                brand_product_context += f"Description: {desc}. "

    logger.info(f"Video generation context: {brand_product_context[:100]}...")
    logger.info(f"Video generation mode: {request.mode}")

    # Build scene inputs with ALL metadata fields from storyboard
    scenes = []
    for scene in storyboard.scenes:
        scene_num = scene.get("scene_number", 0)
        scene_img = scene_images.get(scene_num)

        # Read image data if available
        image_data = None
        if scene_img:
            logger.info(f"Scene {scene_num}: Found SceneImage record, image_url={scene_img.image_url}")
        else:
            logger.warning(f"Scene {scene_num}: No SceneImage record found in scene_images dict")

        if scene_img and scene_img.image_url:
            try:
                # Convert image_url to local file path
                image_path = scene_img.image_url
                if image_path.startswith("http://localhost:8000/static/"):
                    image_path = image_path.replace("http://localhost:8000/static/", f"{settings.TEMP_DIR}/")
                elif image_path.startswith("/static/"):
                    image_path = image_path.replace("/static/", f"{settings.TEMP_DIR}/")

                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    logger.info(f"Loaded scene {scene_num} image from: {image_path}")
                else:
                    logger.warning(f"Scene {scene_num} image file not found: {image_path}")
            except Exception as e:
                logger.warning(f"Failed to read scene image: {e}")

        # Extract scene description - do NOT prepend brand context here
        # The PromptBuilder will handle intelligent brand context integration
        scene_description = scene.get("description", "") or scene.get("visual_direction", "") or scene.get("title", "")

        # Build SceneInput with ALL metadata fields from storyboard
        scenes.append(SceneInput(
            scene_number=scene_num,
            description=scene_description,
            duration_seconds=scene.get("duration_seconds", 3.0),
            image_data=image_data,
            scene_type=scene.get("scene_type") or scene.get("segment_type"),
            narration_script=scene.get("narration_script") or scene.get("narration"),
            visual_direction=scene.get("visual_direction"),
            transition_effect=scene.get("transition_effect") or scene.get("transition"),
            background_music_suggestion=scene.get("background_music_suggestion") or scene.get("music_mood"),
            subtitle_text=scene.get("subtitle_text") or scene.get("overlay_text"),
            title=scene.get("title"),
        ))

    # Get video generator
    try:
        generator = get_video_generator(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate video based on mode
    try:
        if request.mode == "single":
            # Backward compatible: use existing generate_marketing_video
            logger.info("Using single video generation mode (backward compatible)")
            result = await generator.generate_marketing_video(
                scenes=scenes,
                aspect_ratio=request.aspect_ratio,
            )

            # Update project status if completed
            if result.status == "completed":
                project.output_video_url = result.video_url
                project.status = "video_generated"
                await db.commit()

            return VideoGenerationStatusResponse(
                status=result.status,
                video_url=result.video_url,
                operation_id=result.operation_id,
                error_message=result.error_message,
                generation_time_ms=result.generation_time_ms,
            )

        else:
            # Per-scene mode: use new generate_per_scene_videos
            logger.info("Using per-scene video generation mode")
            result = await generator.generate_per_scene_videos(
                scenes=scenes,
                brand_context=brand_product_context,
                aspect_ratio=request.aspect_ratio,
            )

            # Save SceneVideo records to database
            scene_video_statuses = []
            if result.scene_results:
                for scene_result in result.scene_results:
                    # Check if SceneVideo record already exists for this scene
                    existing_result = await db.execute(
                        select(SceneVideo).where(
                            SceneVideo.video_project_id == project_id,
                            SceneVideo.scene_number == scene_result.scene_number,
                            SceneVideo.is_active == True,
                        )
                    )
                    existing_scene_video = existing_result.scalar_one_or_none()

                    if existing_scene_video:
                        # Update existing record
                        existing_scene_video.status = scene_result.status
                        existing_scene_video.video_url = scene_result.video_url
                        existing_scene_video.thumbnail_url = scene_result.thumbnail_url
                        existing_scene_video.duration_seconds = scene_result.duration_seconds
                        existing_scene_video.operation_id = scene_result.operation_id
                        existing_scene_video.error_message = scene_result.error_message
                        existing_scene_video.generation_duration_ms = scene_result.generation_time_ms
                        existing_scene_video.generation_prompt = scene_result.prompt_used
                        scene_video = existing_scene_video
                    else:
                        # Create new SceneVideo record
                        scene_video = SceneVideo(
                            id=str(uuid.uuid4()),
                            video_project_id=project_id,
                            scene_number=scene_result.scene_number,
                            source=request.provider,
                            status=scene_result.status,
                            video_url=scene_result.video_url,
                            thumbnail_url=scene_result.thumbnail_url,
                            duration_seconds=scene_result.duration_seconds,
                            operation_id=scene_result.operation_id,
                            error_message=scene_result.error_message,
                            generation_duration_ms=scene_result.generation_time_ms,
                            generation_prompt=scene_result.prompt_used,
                            generation_provider=request.provider,
                            generation_params={
                                "aspect_ratio": request.aspect_ratio,
                                "mode": request.mode,
                            },
                            version=1,
                            is_active=True,
                        )
                        db.add(scene_video)

                    # Find scene_type from original scene data
                    scene_segment_type = None
                    for scene in storyboard.scenes:
                        if scene.get("scene_number", 0) == scene_result.scene_number:
                            scene_segment_type = scene.get("scene_type") or scene.get("segment_type")
                            break

                    scene_video_statuses.append(SceneVideoStatus(
                        scene_number=scene_result.scene_number,
                        status=scene_result.status,
                        video_url=scene_result.video_url,
                        thumbnail_url=scene_result.thumbnail_url,
                        duration_seconds=scene_result.duration_seconds,
                        operation_id=scene_result.operation_id,
                        error_message=scene_result.error_message,
                        scene_segment_type=scene_segment_type,
                    ))

                await db.commit()

            # Update project status if all scenes completed
            if result.status == "completed":
                project.output_video_url = result.video_url
                project.status = "video_generated"
                await db.commit()

            return ExtendedVideoGenerationStatusResponse(
                status=result.status,
                video_url=result.video_url,
                operation_id=result.operation_id,
                error_message=result.error_message,
                generation_time_ms=result.generation_time_ms,
                scene_videos=scene_video_statuses,
                concatenation_status=None,  # Not yet implemented
                final_video_url=result.video_url if result.status == "completed" else None,
            )

    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/projects/{project_id}/video/status", response_model=VideoGenerationStatusResponse)
async def get_video_status(
    project_id: str,
    operation_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Check the status of video generation.

    If operation_id is provided, checks the specific operation.
    Otherwise, returns the project's current video status.
    """
    # Get project
    result = await db.execute(
        select(VideoProject).where(VideoProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If no operation_id, return current project status
    if not operation_id:
        if project.output_video_url:
            return VideoGenerationStatusResponse(
                status="completed",
                video_url=project.output_video_url,
            )
        else:
            return VideoGenerationStatusResponse(
                status="pending",
            )

    # Check operation status
    try:
        generator = get_video_generator("veo")
        result = await generator.check_generation_status(operation_id)

        # Update project if completed
        if result.status == "completed" and result.video_url:
            project.output_video_url = result.video_url
            project.status = "video_generated"
            await db.commit()

        return VideoGenerationStatusResponse(
            status=result.status,
            video_url=result.video_url,
            operation_id=operation_id,
            error_message=result.error_message,
        )

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/projects/{project_id}/video/generate-preview", response_model=VideoGenerationStatusResponse)
async def generate_video_preview(
    project_id: str,
    scene_number: int,
    request: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a preview video for a single scene.

    Useful for previewing individual scenes before full video generation.
    """
    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=400, detail="No active storyboard found")

    # Find specific scene
    scene = None
    for s in storyboard.scenes:
        if s.get("scene_number") == scene_number:
            scene = s
            break

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_number} not found")

    # Get scene image if available
    result = await db.execute(
        select(SceneImage).where(
            SceneImage.video_project_id == project_id,
            SceneImage.scene_number == scene_number,
            SceneImage.is_current == True,
        )
    )
    scene_img = result.scalar_one_or_none()

    image_data = None
    if scene_img and scene_img.storage_path:
        try:
            with open(scene_img.storage_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to read scene image: {e}")

    # Get video generator
    try:
        generator = get_video_generator(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate preview
    try:
        description = scene.get("description", "") or scene.get("visual_direction", "") or scene.get("title", "")

        if image_data:
            result = await generator.generate_from_image(
                image_data=image_data,
                prompt=description,
                duration_seconds=int(scene.get("duration_seconds", 5)),
                aspect_ratio=request.aspect_ratio,
            )
        else:
            result = await generator.generate_from_prompt(
                prompt=description,
                duration_seconds=int(scene.get("duration_seconds", 5)),
                aspect_ratio=request.aspect_ratio,
            )

        return VideoGenerationStatusResponse(
            status=result.status,
            video_url=result.video_url,
            operation_id=result.operation_id,
            error_message=result.error_message,
            generation_time_ms=result.generation_time_ms,
        )

    except Exception as e:
        logger.error(f"Preview generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.post("/projects/{project_id}/video/generate-scene", response_model=SceneVideoResponse)
async def generate_single_scene_video(
    project_id: str,
    request: SceneVideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate video for a single scene.

    This endpoint generates video for just one scene from the storyboard,
    useful for:
    - Regenerating a specific scene that failed
    - Updating a single scene without regenerating the entire video
    - Preview and iteration on individual scenes

    The generated video is saved to the SceneVideo table for tracking.
    """
    import base64
    import os
    from app.core.config import settings

    # Get project
    result = await db.execute(
        select(VideoProject).where(VideoProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=400, detail="No active storyboard found")

    # Find specific scene
    scene = None
    for s in storyboard.scenes:
        if s.get("scene_number") == request.scene_number:
            scene = s
            break

    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {request.scene_number} not found in storyboard")

    # Get scene image if available
    result = await db.execute(
        select(SceneImage).where(
            SceneImage.video_project_id == project_id,
            SceneImage.scene_number == request.scene_number,
            SceneImage.is_active == True,
        )
    )
    scene_img = result.scalar_one_or_none()

    # Read image data if available
    image_data = None
    if scene_img and scene_img.image_url:
        try:
            image_path = scene_img.image_url
            if image_path.startswith("http://localhost:8000/static/"):
                image_path = image_path.replace("http://localhost:8000/static/", f"{settings.TEMP_DIR}/")
            elif image_path.startswith("/static/"):
                image_path = image_path.replace("/static/", f"{settings.TEMP_DIR}/")

            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"Loaded scene {request.scene_number} image from: {image_path}")
            else:
                logger.warning(f"Scene {request.scene_number} image file not found: {image_path}")
        except Exception as e:
            logger.warning(f"Failed to read scene image: {e}")

    # Get brand and product info for context
    brand_product_context = ""
    if project.brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == project.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            brand_product_context += f"Brand: {brand.name}. "

    if project.product_id:
        product_result = await db.execute(select(Product).where(Product.id == project.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            brand_product_context += f"Product: {product.name}"
            if product.product_category:
                brand_product_context += f" ({product.product_category})"
            brand_product_context += ". "
            if product.image_description:
                brand_product_context += f"Product Appearance: {product.image_description} "
            elif product.description:
                desc = product.description[:150] if len(product.description) > 150 else product.description
                brand_product_context += f"Description: {desc}. "

    # Build SceneInput with ALL metadata fields
    scene_description = scene.get("description", "") or scene.get("visual_direction", "") or scene.get("title", "")
    # Clamp duration to Veo API valid range (4-8 seconds)
    raw_duration = scene.get("duration_seconds", 6.0)
    clamped_duration = max(4.0, min(8.0, float(raw_duration) if raw_duration else 6.0))
    scene_input = SceneInput(
        scene_number=request.scene_number,
        description=scene_description,
        duration_seconds=clamped_duration,
        image_data=image_data,
        scene_type=scene.get("scene_type") or scene.get("segment_type"),
        narration_script=scene.get("narration_script") or scene.get("narration"),
        visual_direction=scene.get("visual_direction"),
        transition_effect=scene.get("transition_effect") or scene.get("transition"),
        background_music_suggestion=scene.get("background_music_suggestion") or scene.get("music_mood"),
        subtitle_text=scene.get("subtitle_text") or scene.get("overlay_text"),
        title=scene.get("title"),
    )

    # Get video generator
    try:
        generator = get_video_generator(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate video for this scene using per_scene_videos with single scene
    try:
        logger.info(f"Generating video for scene {request.scene_number}")
        result = await generator.generate_per_scene_videos(
            scenes=[scene_input],
            brand_context=brand_product_context,
            aspect_ratio=request.aspect_ratio,
        )

        if not result.scene_results or len(result.scene_results) == 0:
            raise HTTPException(status_code=500, detail="No scene result returned from generator")

        scene_result = result.scene_results[0]

        # Check if SceneVideo record already exists for this scene
        existing_result = await db.execute(
            select(SceneVideo).where(
                SceneVideo.video_project_id == project_id,
                SceneVideo.scene_number == request.scene_number,
                SceneVideo.is_active == True,
            )
        )
        existing_scene_video = existing_result.scalar_one_or_none()

        if existing_scene_video:
            # Update existing record and increment version
            existing_scene_video.is_active = False
            await db.flush()

            # Create new version
            new_version = existing_scene_video.version + 1
            scene_video = SceneVideo(
                id=str(uuid.uuid4()),
                video_project_id=project_id,
                scene_number=scene_result.scene_number,
                source=request.provider,
                status=scene_result.status,
                video_url=scene_result.video_url,
                thumbnail_url=scene_result.thumbnail_url,
                duration_seconds=scene_result.duration_seconds,
                operation_id=scene_result.operation_id,
                error_message=scene_result.error_message,
                generation_duration_ms=scene_result.generation_time_ms,
                generation_prompt=scene_result.prompt_used,
                generation_provider=request.provider,
                generation_params={
                    "aspect_ratio": request.aspect_ratio,
                },
                scene_segment_type=scene.get("scene_type") or scene.get("segment_type"),
                version=new_version,
                is_active=True,
            )
            db.add(scene_video)
        else:
            # Create new SceneVideo record
            scene_video = SceneVideo(
                id=str(uuid.uuid4()),
                video_project_id=project_id,
                scene_number=scene_result.scene_number,
                source=request.provider,
                status=scene_result.status,
                video_url=scene_result.video_url,
                thumbnail_url=scene_result.thumbnail_url,
                duration_seconds=scene_result.duration_seconds,
                operation_id=scene_result.operation_id,
                error_message=scene_result.error_message,
                generation_duration_ms=scene_result.generation_time_ms,
                generation_prompt=scene_result.prompt_used,
                generation_provider=request.provider,
                generation_params={
                    "aspect_ratio": request.aspect_ratio,
                },
                scene_segment_type=scene.get("scene_type") or scene.get("segment_type"),
                version=1,
                is_active=True,
            )
            db.add(scene_video)

        await db.commit()
        await db.refresh(scene_video)

        return SceneVideoResponse(
            id=scene_video.id,
            scene_number=scene_video.scene_number,
            source=scene_video.source,
            video_url=scene_video.video_url,
            thumbnail_url=scene_video.thumbnail_url,
            generation_prompt=scene_video.generation_prompt,
            scene_segment_type=scene_video.scene_segment_type,
            duration_seconds=scene_video.duration_seconds,
            status=scene_video.status,
            operation_id=scene_video.operation_id,
            error_message=scene_video.error_message,
            version=scene_video.version,
            is_active=scene_video.is_active,
            created_at=scene_video.created_at,
            updated_at=scene_video.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Scene video generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Scene video generation failed: {str(e)}")


@router.post(
    "/projects/{project_id}/video/concatenate",
    summary="Concatenate scene videos into final video",
    description="Combines all completed scene videos into a single final marketing video with optional transitions.",
)
async def concatenate_scene_videos(
    project_id: str,
    request: VideoConcatenateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Concatenate all completed scene videos for a project into a final marketing video.

    This endpoint:
    1. Verifies the project exists
    2. Fetches all active, completed SceneVideo records ordered by scene_number
    3. Validates at least 2 videos exist for concatenation
    4. Gets transition effects from the storyboard scenes
    5. Calls VideoConcatenator.concatenate() to combine videos
    6. Saves final video URL to project.output_video_url
    7. Returns response with final video URL and metadata

    Args:
        project_id: The project ID to concatenate videos for
        request: Concatenation options (include_transitions, transition_duration_ms)

    Returns:
        Dict with status, video_url, duration_seconds, scene_count, transitions_applied

    Raises:
        404: Project not found
        400: No completed scene videos exist or only 1 video
        500: FFmpeg or processing errors
    """
    logger.info(f"=== concatenate_scene_videos called ===")
    logger.info(f"project_id: {project_id}")
    logger.info(f"include_transitions: {request.include_transitions}, transition_duration_ms: {request.transition_duration_ms}")

    # Step 1: Verify project exists
    result = await db.execute(
        select(VideoProject).where(VideoProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    # Step 2: Fetch all active, completed SceneVideo records ordered by scene_number
    result = await db.execute(
        select(SceneVideo).where(
            SceneVideo.video_project_id == project_id,
            SceneVideo.is_active == True,
            SceneVideo.status == "completed",
        ).order_by(SceneVideo.scene_number)
    )
    scene_videos = result.scalars().all()

    # Step 3: Validate at least 2 videos exist for concatenation
    if not scene_videos:
        logger.warning(f"No completed scene videos found for project: {project_id}")
        raise HTTPException(
            status_code=400,
            detail="No completed scene videos exist for this project"
        )

    if len(scene_videos) < 2:
        logger.warning(f"Only {len(scene_videos)} video(s) found, need at least 2 to concatenate")
        raise HTTPException(
            status_code=400,
            detail="At least 2 completed scene videos are required for concatenation"
        )

    logger.info(f"Found {len(scene_videos)} completed scene videos to concatenate")

    # Step 4: Get transition effects from storyboard scenes
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    # Build a map of scene_number -> transition_effect from storyboard
    transition_map = {}
    if storyboard and storyboard.scenes:
        for scene in storyboard.scenes:
            scene_num = scene.get("scene_number", 0)
            transition_map[scene_num] = scene.get("transition_effect", "fade")
        logger.info(f"Loaded {len(transition_map)} transitions from storyboard")
    else:
        logger.info("No active storyboard found, using default 'fade' transitions")

    # Build scene video data for concatenator
    scene_video_data = []
    for sv in scene_videos:
        if not sv.video_url:
            logger.warning(f"Scene {sv.scene_number} has no video_url, skipping")
            continue

        scene_video_data.append({
            "video_url": sv.video_url,
            "transition_effect": transition_map.get(sv.scene_number, "fade"),
            "duration_seconds": sv.duration_seconds,
        })

    if len(scene_video_data) < 2:
        logger.warning(f"Only {len(scene_video_data)} videos with URLs found")
        raise HTTPException(
            status_code=400,
            detail="At least 2 scene videos with valid URLs are required for concatenation"
        )

    logger.info(f"Prepared {len(scene_video_data)} videos for concatenation")

    # Step 5: Call VideoConcatenator.concatenate()
    try:
        concatenator = get_video_concatenator()
        concat_result = await concatenator.concatenate(
            scene_videos=scene_video_data,
            include_transitions=request.include_transitions if request.include_transitions is not None else True,
            transition_duration_ms=request.transition_duration_ms if request.transition_duration_ms is not None else 500,
        )

        if not concat_result.success:
            logger.error(f"Concatenation failed: {concat_result.error_message}")
            raise HTTPException(
                status_code=500,
                detail=f"Video concatenation failed: {concat_result.error_message}"
            )

        logger.info(f"Concatenation successful: {concat_result.output_url}")

        # Step 6: Save final video URL to project.output_video_url
        project.output_video_url = concat_result.output_url
        project.output_duration = concat_result.duration_seconds
        project.status = "completed"
        await db.commit()

        logger.info(f"Project updated with final video URL: {concat_result.output_url}")

        # Step 7: Return response
        return {
            "status": "completed",
            "video_url": concat_result.output_url,
            "duration_seconds": concat_result.duration_seconds,
            "scene_count": concat_result.scene_count,
            "transitions_applied": concat_result.transitions_applied > 0 if concat_result.transitions_applied else False,
            "processing_time_ms": concat_result.processing_time_ms,
            "error_message": None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video concatenation failed with unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Return failed response
        return {
            "status": "failed",
            "video_url": None,
            "duration_seconds": None,
            "scene_count": len(scene_video_data),
            "transitions_applied": False,
            "processing_time_ms": None,
            "error_message": str(e),
        }


# =============================================================================
# Scene Extension Video Generation Endpoint
# =============================================================================


@router.post(
    "/projects/{project_id}/video/generate-extended",
    response_model=ExtendedVideoGenerationResponse,
)
async def generate_extended_video(
    project_id: str,
    request: ExtendedVideoGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a continuous video using Scene Extension mode.

    This endpoint generates a single continuous video by:
    1. Generating an initial video from the first scene (up to 8 seconds)
    2. Extending the video with subsequent scene prompts using Scene Extension
    3. Continuing until target duration is reached or all scenes are processed

    Scene Extension adds 7 seconds per hop, with a maximum of 20 hops,
    allowing videos up to 148 seconds total (8 initial + 20 x 7 seconds).

    Unlike the per-scene video generation endpoint which creates separate videos
    for each scene and then concatenates them, this endpoint creates a single
    seamless video with smooth transitions between scenes.
    """
    import base64
    import os
    from app.core.config import settings

    start_time = time.time()

    # Step 1: Get project
    result = await db.execute(
        select(VideoProject).where(VideoProject.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Step 2: Get active storyboard
    result = await db.execute(
        select(Storyboard).where(
            Storyboard.video_project_id == project_id,
            Storyboard.is_active == True,
        )
    )
    storyboard = result.scalar_one_or_none()

    if not storyboard:
        raise HTTPException(status_code=400, detail="No active storyboard found")

    if not storyboard.scenes:
        raise HTTPException(status_code=400, detail="Storyboard has no scenes")

    # Step 3: Get scene images
    result = await db.execute(
        select(SceneImage).where(
            SceneImage.video_project_id == project_id,
            SceneImage.is_active == True,
        )
    )
    scene_images = {img.scene_number: img for img in result.scalars().all()}
    logger.info(f"Found {len(scene_images)} scene images for project {project_id}")

    # Step 4: Get brand and product info for context
    brand_product_context = ""
    if project.brand_id:
        brand_result = await db.execute(select(Brand).where(Brand.id == project.brand_id))
        brand = brand_result.scalar_one_or_none()
        if brand:
            brand_product_context += f"Brand: {brand.name}. "

    if project.product_id:
        product_result = await db.execute(select(Product).where(Product.id == project.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            brand_product_context += f"Product: {product.name}"
            if product.product_category:
                brand_product_context += f" ({product.product_category})"
            brand_product_context += ". "
            if product.image_description:
                brand_product_context += f"Product Appearance: {product.image_description} "
            elif product.description:
                desc = product.description[:150] if len(product.description) > 150 else product.description
                brand_product_context += f"Description: {desc}. "

    logger.info(f"Scene Extension context: {brand_product_context[:100]}...")

    # Step 5: Build SceneInput list from storyboard scenes
    scenes = []
    total_scene_duration = 0.0

    for scene in storyboard.scenes:
        scene_num = scene.get("scene_number", 0)
        scene_img = scene_images.get(scene_num)

        # Read image data if available
        image_data = None
        if scene_img and scene_img.image_url:
            try:
                image_path = scene_img.image_url
                if image_path.startswith("http://localhost:8000/static/"):
                    image_path = image_path.replace("http://localhost:8000/static/", f"{settings.TEMP_DIR}/")
                elif image_path.startswith("/static/"):
                    image_path = image_path.replace("/static/", f"{settings.TEMP_DIR}/")

                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    logger.info(f"Loaded scene {scene_num} image for extension")
                else:
                    logger.warning(f"Scene {scene_num} image file not found: {image_path}")
            except Exception as e:
                logger.warning(f"Failed to read scene image for extension: {e}")

        # Extract scene description
        scene_description = scene.get("description", "") or scene.get("visual_direction", "") or scene.get("title", "")
        scene_duration = scene.get("duration_seconds", 3.0)
        total_scene_duration += scene_duration

        # Build SceneInput with ALL metadata fields
        scenes.append(SceneInput(
            scene_number=scene_num,
            description=scene_description,
            duration_seconds=scene_duration,
            image_data=image_data,
            scene_type=scene.get("scene_type") or scene.get("segment_type"),
            narration_script=scene.get("narration_script") or scene.get("narration"),
            visual_direction=scene.get("visual_direction"),
            transition_effect=scene.get("transition_effect") or scene.get("transition"),
            background_music_suggestion=scene.get("background_music_suggestion") or scene.get("music_mood"),
            subtitle_text=scene.get("subtitle_text") or scene.get("overlay_text"),
            title=scene.get("title"),
        ))

    # Step 6: Calculate target duration
    # Use request target_duration_seconds if provided, otherwise calculate from scenes
    target_duration = request.target_duration_seconds
    if target_duration is None:
        # Calculate from total scene durations, capped at 148 seconds
        target_duration = min(int(total_scene_duration), 148)
        # Ensure minimum of 8 seconds
        target_duration = max(target_duration, 8)

    logger.info(f"Scene Extension: {len(scenes)} scenes, target duration: {target_duration}s")

    # Step 7: Get video generator
    provider = request.provider or "veo"
    try:
        generator = get_video_generator(provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 8: Generate extended video
    try:
        logger.info(f"Starting Scene Extension video generation with provider: {provider}")
        result = await generator.generate_extended_video(
            scenes=scenes,
            target_duration_seconds=target_duration,
            brand_context=brand_product_context,
            aspect_ratio=request.aspect_ratio or "16:9",
        )

        generation_time_ms = int((time.time() - start_time) * 1000)

        # Step 9: Update project status if completed
        if result.status == "completed" and result.video_url:
            project.output_video_url = result.video_url
            project.output_duration = result.final_duration_seconds
            project.status = "video_generated"
            await db.commit()
            logger.info(f"Project updated with extended video: {result.video_url}")

        # Step 10: Return response
        return ExtendedVideoGenerationResponse(
            status=result.status,
            video_url=result.video_url,
            initial_duration_seconds=result.initial_duration_seconds,
            final_duration_seconds=result.final_duration_seconds,
            extension_hops_completed=result.extension_hops_completed,
            scenes_processed=result.scenes_processed or len(scenes),
            generation_time_ms=result.generation_time_ms or generation_time_ms,
            error_message=result.error_message,
        )

    except Exception as e:
        logger.error(f"Scene Extension video generation failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        generation_time_ms = int((time.time() - start_time) * 1000)

        return ExtendedVideoGenerationResponse(
            status="failed",
            video_url=None,
            initial_duration_seconds=None,
            final_duration_seconds=None,
            extension_hops_completed=0,
            scenes_processed=0,
            generation_time_ms=generation_time_ms,
            error_message=str(e),
        )


# ========== SNS Parsing and Media Download Endpoints ==========


@router.post("/sns/parse", response_model=SNSParseResponse)
async def parse_sns_url(request: SNSParseRequest):
    """
    Parse an SNS URL and extract metadata.

    Supports Instagram, Facebook, and Pinterest URLs.
    Returns platform information, post/pin IDs, and validation status.
    """
    from app.services.sns_parser import SNSParser, SNSParseError

    parser = SNSParser()

    try:
        # Check if URL is valid first
        is_valid = parser.is_valid_url(request.url)

        if not is_valid:
            return SNSParseResponse(
                platform="unknown",
                post_id=None,
                pin_id=None,
                url=request.url,
                valid=False,
            )

        # Parse the URL to get detailed information
        parsed = await parser.parse_url(request.url)

        return SNSParseResponse(
            platform=parsed.get("platform", "unknown"),
            post_id=parsed.get("post_id"),
            pin_id=parsed.get("pin_id"),
            url=parsed.get("url", request.url),
            valid=True,
        )

    except SNSParseError as e:
        logger.warning(f"SNS parse error for URL {request.url}: {str(e)}")
        return SNSParseResponse(
            platform="unknown",
            post_id=None,
            pin_id=None,
            url=request.url,
            valid=False,
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing SNS URL {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse URL: {str(e)}",
        )


@router.post("/sns/download", response_model=SNSDownloadResponse)
async def download_sns_media(request: SNSDownloadRequest):
    """
    Download media from an SNS URL.

    Downloads images and videos from Instagram, Facebook, or Pinterest posts.
    Returns metadata about downloaded files including paths, sizes, and formats.
    """
    import os
    import tempfile

    from app.services.sns_media_downloader import SNSMediaDownloader, SNSMediaDownloadError

    downloader = SNSMediaDownloader()

    try:
        # Validate URL first
        if not downloader.is_valid_url(request.url):
            return SNSDownloadResponse(
                platform="unknown",
                images=[],
                success=False,
                error_message="Invalid or unsupported SNS URL",
            )

        # Detect platform
        metadata = await downloader.extract_metadata(request.url)
        platform = metadata.get("platform", "unknown")

        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await downloader.download(request.url, temp_dir)

            # Build image info list
            images = []
            for image_path in result.get("images", []):
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    _, ext = os.path.splitext(image_path)
                    file_format = ext.lstrip(".").lower() if ext else "unknown"

                    images.append(
                        SNSImageInfo(
                            url=image_path,
                            size=file_size,
                            format=file_format,
                        )
                    )

            return SNSDownloadResponse(
                platform=platform,
                images=images,
                success=True,
                error_message=None,
            )

    except SNSMediaDownloadError as e:
        logger.warning(f"SNS download error for URL {request.url}: {str(e)}")
        return SNSDownloadResponse(
            platform="unknown",
            images=[],
            success=False,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error downloading from SNS URL {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download media: {str(e)}",
        )


@router.post("/sns/extract-images", response_model=SNSExtractImagesResponse)
async def extract_sns_images(request: SNSExtractImagesRequest):
    """
    Extract images from an SNS URL and return as base64-encoded strings.

    Downloads images from Instagram, Facebook, or Pinterest posts,
    then converts them to base64 for direct use in frontend or further processing.
    """
    import base64
    import tempfile

    from app.services.sns_media_downloader import SNSMediaDownloader, SNSMediaDownloadError

    downloader = SNSMediaDownloader()

    try:
        # Validate URL first
        if not downloader.is_valid_url(request.url):
            return SNSExtractImagesResponse(
                images=[],
                count=0,
                success=False,
                platform=None,
                error_message="Invalid or unsupported SNS URL",
            )

        # Detect platform
        metadata = await downloader.extract_metadata(request.url)
        platform = metadata.get("platform", "unknown")

        # Create temporary directory and extract images
        with tempfile.TemporaryDirectory() as temp_dir:
            image_bytes_list = await downloader.extract_images_from_post(
                request.url,
                temp_dir,
            )

            # Convert to base64
            base64_images = []
            for image_bytes in image_bytes_list:
                if image_bytes and isinstance(image_bytes, bytes):
                    base64_str = base64.b64encode(image_bytes).decode("utf-8")
                    base64_images.append(base64_str)

            return SNSExtractImagesResponse(
                images=base64_images,
                count=len(base64_images),
                success=True,
                platform=platform,
                error_message=None,
            )

    except SNSMediaDownloadError as e:
        logger.warning(f"SNS image extraction error for URL {request.url}: {str(e)}")
        return SNSExtractImagesResponse(
            images=[],
            count=0,
            success=False,
            platform=None,
            error_message=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error extracting images from SNS URL {request.url}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract images: {str(e)}",
        )


__all__ = ["router"]
