"""
ImageProject API endpoints for the AI Video Marketing Platform.

Provides CRUD operations for image projects and image generation.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.services.cloud_storage import cloud_storage
from app.models.image_project import ImageProject
from app.models.generated_image import GeneratedImage
from app.models.product import Product
from app.schemas.image_project import (
    ImageProjectCreate,
    ImageProjectUpdate,
    ImageProjectResponse,
    ImageProjectSummary,
    GenerateImagesRequest,
    GenerateImagesResponse,
    GeneratedImageResponse,
    SelectImageRequest,
    GenerateSingleRequest,
    GenerateSingleResponse,
    ApproveImageRequest,
    ApproveImageResponse,
    RegenerateImageRequest,
    RegenerateImageResponse,
    SetReferenceImageRequest,
    SetReferenceImageResponse,
    GenerateSingleSectionRequest,
    GenerateSingleSectionResponse,
    RegenerateRequest,
    RegenerateSectionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-projects", tags=["Image Projects"])


# ========== Helper Functions ==========

async def load_image_from_url(image_url: str, settings) -> tuple[bytes, str] | tuple[None, None]:
    """
    Load image from various URL formats (local, localhost, cloud).
    Returns (image_bytes, mime_type) or (None, None) if failed.
    """
    import os
    import httpx

    if not image_url:
        return None, None

    image_data = None
    mime_type = "image/png" if ".png" in image_url.lower() else "image/jpeg"

    try:
        # 1. localhost URL → local path
        if image_url.startswith("http://localhost:8000/static/"):
            relative_path = image_url.replace("http://localhost:8000/static/", "")
            image_path = os.path.join(settings.TEMP_DIR, relative_path)
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image_data = f.read()
                logger.info(f"Loaded image from localhost path: {image_path} ({len(image_data)} bytes)")

        # 2. Relative static URL → local path
        elif image_url.startswith("/static/"):
            image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image_data = f.read()
                logger.info(f"Loaded image from static path: {image_path} ({len(image_data)} bytes)")

        # 3. Cloud/External URL → download
        elif image_url.startswith("http"):
            logger.info(f"Downloading image from cloud: {image_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=30.0)
                if response.status_code == 200:
                    image_data = response.content
                    logger.info(f"Downloaded image: {len(image_data)} bytes")
                else:
                    logger.warning(f"Failed to download image: HTTP {response.status_code}")

        # 4. Direct file path
        else:
            if os.path.exists(image_url):
                with open(image_url, "rb") as f:
                    image_data = f.read()
                logger.info(f"Loaded image from path: {image_url} ({len(image_data)} bytes)")

    except Exception as e:
        logger.error(f"Error loading image from {image_url}: {e}")

    return image_data, mime_type if image_data else (None, None)


# ========== CRUD Operations ==========

@router.post("", response_model=ImageProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_image_project(
    project_data: ImageProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new image project."""
    import base64
    import os
    from app.core.config import settings

    project_id = str(uuid.uuid4())

    # Generate title if not provided
    title = project_data.title
    if not title:
        content_type_kr = {"single": "단일", "carousel": "캐러셀", "story": "세로형", "compose": "합성"}
        purpose_kr = {"ad": "광고", "info": "정보", "lifestyle": "라이프스타일", "compose": "편집"}
        title = f"{content_type_kr.get(project_data.content_type, project_data.content_type)} {purpose_kr.get(project_data.purpose, project_data.purpose)} 이미지"

    # Upload reference images to cloud storage if provided
    reference_image_urls = None
    if project_data.reference_images_base64:
        reference_image_urls = []

        for idx, img_data in enumerate(project_data.reference_images_base64):
            try:
                # Decode base64
                image_bytes = base64.b64decode(img_data.data)
                ext = "jpg" if "jpeg" in img_data.mime_type else img_data.mime_type.split("/")[-1]
                filename = f"{project_id}_ref_{idx}.{ext}"
                content_type = img_data.mime_type

                ref_url = cloud_storage.upload_bytes(image_bytes, filename, "references", content_type)
                reference_image_urls.append(ref_url)
                logger.info(f"Uploaded reference image: {filename}, url: {ref_url}")
            except Exception as e:
                logger.error(f"Failed to upload reference image {idx}: {e}")

    project = ImageProject(
        id=project_id,
        title=title,
        content_type=project_data.content_type,
        purpose=project_data.purpose,
        method=project_data.method,
        generation_mode=project_data.generation_mode,
        brand_id=project_data.brand_id,
        product_id=project_data.product_id,
        reference_analysis_id=project_data.reference_analysis_id,
        storyboard_data=project_data.storyboard_data,
        prompt=project_data.prompt if project_data.content_type != "compose" else project_data.compose_prompt,
        aspect_ratio=project_data.aspect_ratio,
        reference_image_urls=reference_image_urls,
        compose_image_temp_ids=project_data.compose_image_temp_ids,
        status="draft",
        current_step=1,
        current_slide=1,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Created image project: {project_id}, reference_images: {len(reference_image_urls or [])}")
    return project


@router.get("", response_model=List[ImageProjectSummary])
async def list_image_projects(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    brand_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List image projects with optional filters."""
    query = select(ImageProject).options(
        selectinload(ImageProject.generated_images)
    ).order_by(ImageProject.created_at.desc())

    if content_type:
        query = query.where(ImageProject.content_type == content_type)
    if status:
        query = query.where(ImageProject.status == status)
    if brand_id:
        query = query.where(ImageProject.brand_id == brand_id)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    # Build response with thumbnail_url from first generated image
    response = []
    for project in projects:
        # Get first generated image URL as thumbnail
        thumbnail_url = None
        if project.generated_images:
            # Sort by slide_number and created_at to get the first image
            sorted_images = sorted(
                project.generated_images,
                key=lambda img: (img.slide_number, img.created_at or datetime.min)
            )
            if sorted_images:
                thumbnail_url = sorted_images[0].image_url

        response.append(ImageProjectSummary(
            id=project.id,
            title=project.title,
            content_type=project.content_type,
            purpose=project.purpose,
            method=project.method,
            status=project.status,
            current_slide=project.current_slide,
            storyboard_data=project.storyboard_data,
            thumbnail_url=thumbnail_url,
            created_at=project.created_at,
            updated_at=project.updated_at,
        ))

    return response


@router.get("/{project_id}", response_model=ImageProjectResponse)
async def get_image_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an image project by ID."""
    query = select(ImageProject).where(ImageProject.id == project_id).options(
        selectinload(ImageProject.generated_images)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    return project


@router.patch("/{project_id}", response_model=ImageProjectResponse)
async def update_image_project(
    project_id: str,
    update_data: ImageProjectUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an image project."""
    query = select(ImageProject).where(ImageProject.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an image project."""
    query = select(ImageProject).where(ImageProject.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    await db.delete(project)
    await db.commit()

    logger.info(f"Deleted image project: {project_id}")


# ========== Image Generation ==========

@router.post("/{project_id}/generate", response_model=GenerateImagesResponse)
async def generate_images(
    project_id: str,
    request: GenerateImagesRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate images for a project slide."""
    from app.services.video_generator.image_generator import get_image_generator
    from app.services.image_editor import get_image_editor
    import base64
    import os
    from app.core.config import settings

    # Get project
    query = select(ImageProject).where(ImageProject.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Check if product has an image
    product = None
    product_image_data = None
    if project.product_id:
        product_query = select(Product).where(Product.id == project.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.image_url:
            # Load product image using helper function
            product_image_data, _ = await load_image_from_url(product.image_url, settings)

    # Update project status
    project.status = "generating"
    await db.commit()

    start_time = time.time()
    generated_images = []

    try:
        # Build enhanced prompt with product info
        prompt = request.prompt
        product_appearance = None
        if product:
            product_info = f"Product: {product.name}"
            if product.product_category:
                product_info += f" ({product.product_category})"
            # Use AI-generated image_description for accurate product appearance
            if product.image_description:
                product_appearance = product.image_description
                product_info += f"\nProduct Appearance: {product.image_description}"
            elif product.description:
                product_appearance = product.description
                product_info += f" - {product.description}"
            prompt = f"{prompt}\n\n{product_info}"

        # Use prompt directly (Gemini understands Korean)
        optimized_prompt = prompt
        logger.info(f"Using prompt directly: {optimized_prompt[:100]}...")

        temp_dir = os.path.join(settings.TEMP_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Generate multiple variants
        for variant_idx in range(request.num_variants):
            logger.info(f"Generating variant {variant_idx + 1}/{request.num_variants}")

            if product_image_data:
                # Use image editor with product reference
                logger.info("Using image editor with product image reference")
                editor = get_image_editor()

                # Determine mime type from product image
                mime_type = "image/jpeg"
                if product.image_url and ".png" in product.image_url.lower():
                    mime_type = "image/png"

                # Build enhanced prompt that emphasizes scene creation with product integration
                product_reference_prompt = f"""Create a marketing image with the following scene description:

{optimized_prompt}

PRODUCT INTEGRATION INSTRUCTIONS:
- The attached image shows the product to feature in this scene
- Generate the COMPLETE SCENE as described above (background, lighting, mood, all visual elements)
- Place the product naturally within this scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity (shape, colors, logo) while matching the scene's lighting and atmosphere
- The scene description is the PRIMARY creative direction - create that environment first, then place the product within it"""

                gen_result = await editor.edit_with_product(
                    edit_prompt=product_reference_prompt,
                    aspect_ratio=request.aspect_ratio or project.aspect_ratio,
                    product_description=product_appearance,
                    images_data=[(product_image_data, mime_type)],
                )
            else:
                # Use standard image generator
                logger.info("Using standard image generator (no product image)")
                generator = get_image_generator("gemini_imagen")
                gen_result = await generator.generate(
                    prompt=optimized_prompt,
                    aspect_ratio=request.aspect_ratio or project.aspect_ratio,
                    purpose=project.purpose,
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                filename = f"{uuid.uuid4()}.{ext}"
                image_bytes = base64.b64decode(image_data)
                content_type = "image/png" if ext == "png" else "image/jpeg"
                image_url = cloud_storage.upload_bytes(image_bytes, filename, "generated", content_type)
                logger.info(f"Uploaded image: {filename}, size: {len(image_bytes)} bytes, url: {image_url}")
            else:
                image_url = f"/placeholder-{project_id}-{request.slide_number}-{variant_idx}.jpg"

            # Create GeneratedImage record
            gen_image = GeneratedImage(
                id=str(uuid.uuid4()),
                image_project_id=project_id,
                slide_number=request.slide_number,
                variant_index=variant_idx,
                image_url=image_url,
                prompt=request.prompt,
                is_selected=False,
                generation_provider="gemini_imagen" if not product_image_data else "gemini_editor",
                generation_duration_ms=int((time.time() - start_time) * 1000 / (variant_idx + 1)),
            )

            db.add(gen_image)
            generated_images.append(gen_image)

        # Update project status
        project.status = "completed" if project.content_type == "single" else "generating"
        await db.commit()

        # Refresh to get created_at
        for img in generated_images:
            await db.refresh(img)

        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Generated {len(generated_images)} images in {total_time}ms")

        return GenerateImagesResponse(
            project_id=project_id,
            slide_number=request.slide_number,
            images=[GeneratedImageResponse.model_validate(img) for img in generated_images],
            generation_time_ms=total_time,
        )

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        project.status = "failed"
        project.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/{project_id}/select", response_model=ImageProjectResponse)
async def select_image(
    project_id: str,
    request: SelectImageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Select an image variant for a slide."""
    # Get project
    query = select(ImageProject).where(ImageProject.id == project_id).options(
        selectinload(ImageProject.generated_images)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Deselect all images for this slide
    for img in project.generated_images:
        if img.slide_number == request.slide_number:
            img.is_selected = (img.variant_index == request.variant_index)

    await db.commit()
    await db.refresh(project)

    return project


@router.get("/{project_id}/images", response_model=List[GeneratedImageResponse])
async def get_project_images(
    project_id: str,
    slide_number: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get generated images for a project."""
    query = select(GeneratedImage).where(GeneratedImage.image_project_id == project_id)

    if slide_number:
        query = query.where(GeneratedImage.slide_number == slide_number)

    query = query.order_by(GeneratedImage.slide_number, GeneratedImage.variant_index)
    result = await db.execute(query)
    images = result.scalars().all()

    return images


# ========== Step-by-Step Generation Workflow Endpoints ==========

@router.post("/{project_id}/generate-section", response_model=GenerateSingleSectionResponse)
async def generate_section(
    project_id: str,
    request: GenerateSingleSectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate images for a single slide/section.

    If use_reference=True and a reference_image_id exists on the project,
    the reference image will be loaded and passed to Gemini with a prompt
    about maintaining style/mood consistency.
    """
    from app.services.video_generator.image_generator import get_image_generator
    from app.services.image_editor import get_image_editor
    import base64
    import os
    from app.core.config import settings

    # Get project with relationships
    query = select(ImageProject).where(ImageProject.id == project_id).options(
        selectinload(ImageProject.generated_images)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Get storyboard data for the slide
    storyboard = project.storyboard_data or {}
    slides = storyboard.get("slides", [])

    if request.slide_number > len(slides):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slide number {request.slide_number} exceeds storyboard slides count ({len(slides)})"
        )

    slide_data = slides[request.slide_number - 1] if slides else {}
    # Priority: request.prompt > visual_prompt > prompt > project.prompt
    slide_prompt = (
        request.prompt  # Explicitly passed prompt has highest priority
        or slide_data.get("visual_prompt")  # From storyboard visual_prompt
        or slide_data.get("prompt")  # From storyboard prompt
        or project.prompt  # Project-level prompt
        or ""
    )
    logger.info(f"Using prompt for slide {request.slide_number}: {slide_prompt[:100] if slide_prompt else 'EMPTY'}...")

    # Load reference image if requested and available
    reference_image_data = None
    reference_mime_type = None
    reference_used = False

    if request.use_reference and project.reference_image_id:
        # Get reference image
        ref_query = select(GeneratedImage).where(GeneratedImage.id == project.reference_image_id)
        ref_result = await db.execute(ref_query)
        ref_image = ref_result.scalar_one_or_none()

        if ref_image and ref_image.image_url:
            reference_image_data, reference_mime_type = await load_image_from_url(ref_image.image_url, settings)
            reference_used = reference_image_data is not None

    # Load product image if available
    product = None
    product_image_data = None
    product_mime_type = None
    if project.product_id:
        product_query = select(Product).where(Product.id == project.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.image_url:
            product_image_data, product_mime_type = await load_image_from_url(product.image_url, settings)

    # Update project status
    project.status = "generating"
    project.current_slide = request.slide_number
    await db.commit()

    start_time = time.time()
    generated_images = []

    try:
        # Build prompt with product info
        prompt = slide_prompt
        product_appearance = None
        if product:
            product_info = f"Product: {product.name}"
            if product.product_category:
                product_info += f" ({product.product_category})"
            if product.image_description:
                product_appearance = product.image_description
                product_info += f"\nProduct Appearance: {product.image_description}"
            elif product.description:
                product_appearance = product.description
                product_info += f" - {product.description}"
            prompt = f"{prompt}\n\n{product_info}"

        # Use prompt directly (Gemini understands Korean)
        optimized_prompt = prompt
        logger.info(f"Using prompt directly: {optimized_prompt[:100]}...")

        temp_dir = os.path.join(settings.TEMP_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Prepare images list for generation
        images_data = []
        if reference_image_data:
            images_data.append((reference_image_data, reference_mime_type))
        if product_image_data:
            images_data.append((product_image_data, product_mime_type))

        # Number of variants to generate
        num_variants = 2 if project.generation_mode == "step_by_step" else 4

        # Generate variants
        for variant_idx in range(num_variants):
            logger.info(f"Generating variant {variant_idx + 1}/{num_variants}")

            if images_data:
                # Use image editor with reference/product images
                editor = get_image_editor()

                # Build enhanced prompt for style consistency
                if reference_used:
                    generation_prompt = f"""{optimized_prompt}

STYLE CONSISTENCY INSTRUCTION: The first attached image is the REFERENCE IMAGE.
- Match the visual style, color palette, lighting, and mood of the reference image
- Maintain consistency in artistic style and atmosphere
- The generated image should feel like part of the same series/campaign"""
                else:
                    generation_prompt = f"""Create a marketing image with the following scene description:

{optimized_prompt}

PRODUCT INTEGRATION INSTRUCTIONS:
- The attached image shows the product to feature in this scene
- Generate the COMPLETE SCENE as described above (background, lighting, mood, all visual elements)
- Place the product naturally within this scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity (shape, colors, logo) while matching the scene's lighting and atmosphere
- The scene description is the PRIMARY creative direction - create that environment first, then place the product within it"""

                gen_result = await editor.edit_with_product(
                    edit_prompt=generation_prompt,
                    aspect_ratio=project.aspect_ratio,
                    product_description=product_appearance,
                    images_data=images_data,
                )
            else:
                # Use standard image generator
                generator = get_image_generator("gemini_imagen")
                gen_result = await generator.generate(
                    prompt=optimized_prompt,
                    aspect_ratio=project.aspect_ratio,
                    purpose=project.purpose,
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                filename = f"{uuid.uuid4()}.{ext}"
                image_bytes = base64.b64decode(image_data)
                content_type = "image/png" if ext == "png" else "image/jpeg"
                image_url = cloud_storage.upload_bytes(image_bytes, filename, "generated", content_type)
                logger.info(f"Uploaded image: {filename}, size: {len(image_bytes)} bytes, url: {image_url}")
            else:
                image_url = f"/placeholder-{project_id}-{request.slide_number}-{variant_idx}.jpg"

            # Create GeneratedImage record
            gen_image = GeneratedImage(
                id=str(uuid.uuid4()),
                image_project_id=project_id,
                slide_number=request.slide_number,
                variant_index=variant_idx,
                image_url=image_url,
                prompt=slide_prompt,
                is_selected=False,
                approval_status="pending",
                is_reference_image=False,
                generation_provider="gemini_editor" if images_data else "gemini_imagen",
                generation_duration_ms=int((time.time() - start_time) * 1000 / (variant_idx + 1)),
            )

            db.add(gen_image)
            generated_images.append(gen_image)

        await db.commit()

        # Refresh to get created_at
        for img in generated_images:
            await db.refresh(img)

        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Generated {len(generated_images)} images in {total_time}ms for slide {request.slide_number}")

        return GenerateSingleSectionResponse(
            project_id=project_id,
            slide_number=request.slide_number,
            images=[GeneratedImageResponse.model_validate(img) for img in generated_images],
            generation_time_ms=total_time,
            reference_image_used=reference_used,
        )

    except Exception as e:
        logger.error(f"Section generation failed: {e}")
        project.status = "failed"
        project.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section generation failed: {str(e)}"
        )


@router.post("/{project_id}/set-reference", response_model=SetReferenceImageResponse)
async def set_reference_image(
    project_id: str,
    request: SetReferenceImageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Set an image as the reference image for style/mood consistency.

    Updates ImageProject.reference_image_id and sets GeneratedImage.is_reference_image = True.
    Also clears the is_reference_image flag on any previous reference image.
    """
    # Get project
    query = select(ImageProject).where(ImageProject.id == project_id).options(
        selectinload(ImageProject.generated_images)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Verify the image exists and belongs to this project
    image_query = select(GeneratedImage).where(
        GeneratedImage.id == request.image_id,
        GeneratedImage.image_project_id == project_id
    )
    image_result = await db.execute(image_query)
    target_image = image_result.scalar_one_or_none()

    if not target_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {request.image_id}"
        )

    # Store previous reference ID
    previous_reference_id = project.reference_image_id

    # Clear is_reference_image flag on all images in this project
    for img in project.generated_images:
        if img.is_reference_image:
            img.is_reference_image = False

    # Set new reference image
    target_image.is_reference_image = True
    target_image.approval_status = "approved"
    project.reference_image_id = request.image_id

    await db.commit()

    logger.info(f"Set reference image {request.image_id} for project {project_id}")

    return SetReferenceImageResponse(
        project_id=project_id,
        reference_image_id=request.image_id,
        previous_reference_id=previous_reference_id,
    )


@router.post("/{project_id}/regenerate-section/{slide_number}", response_model=RegenerateSectionResponse)
async def regenerate_section(
    project_id: str,
    slide_number: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate images for a specific slide.

    Deletes existing images for that slide_number and generates new ones.
    Uses the reference image if one is set on the project.
    """
    from app.services.video_generator.image_generator import get_image_generator
    from app.services.image_editor import get_image_editor
    import base64
    import os
    from app.core.config import settings

    # Get project with images
    query = select(ImageProject).where(ImageProject.id == project_id).options(
        selectinload(ImageProject.generated_images)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Get storyboard data for the slide
    storyboard = project.storyboard_data or {}
    slides = storyboard.get("slides", [])

    if slide_number > len(slides) and slides:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Slide number {slide_number} exceeds storyboard slides count ({len(slides)})"
        )

    slide_data = slides[slide_number - 1] if slides else {}
    # Priority: visual_prompt > prompt > project.prompt
    slide_prompt = (
        slide_data.get("visual_prompt")
        or slide_data.get("prompt")
        or project.prompt
        or ""
    )
    logger.info(f"Regenerating slide {slide_number} with prompt: {slide_prompt[:100] if slide_prompt else 'EMPTY'}...")

    # Delete existing images for this slide
    existing_images = [img for img in project.generated_images if img.slide_number == slide_number]
    deleted_count = len(existing_images)

    for img in existing_images:
        # Don't delete the reference image
        if img.id == project.reference_image_id:
            logger.warning(f"Skipping deletion of reference image {img.id}")
            deleted_count -= 1
            continue

        # Delete the file if it exists
        if img.image_url and img.image_url.startswith("/static/"):
            file_path = os.path.join(settings.TEMP_DIR, img.image_url.replace("/static/", ""))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted image file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete image file {file_path}: {e}")

        await db.delete(img)

    await db.commit()
    logger.info(f"Deleted {deleted_count} existing images for slide {slide_number}")

    # Load reference image if available
    reference_image_data = None
    reference_mime_type = None
    reference_used = False

    if project.reference_image_id:
        ref_query = select(GeneratedImage).where(GeneratedImage.id == project.reference_image_id)
        ref_result = await db.execute(ref_query)
        ref_image = ref_result.scalar_one_or_none()

        if ref_image and ref_image.image_url:
            reference_image_data, reference_mime_type = await load_image_from_url(ref_image.image_url, settings)
            reference_used = reference_image_data is not None

    # Load product image if available
    product = None
    product_image_data = None
    product_mime_type = None
    if project.product_id:
        product_query = select(Product).where(Product.id == project.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.image_url:
            product_image_data, product_mime_type = await load_image_from_url(product.image_url, settings)

    # Update project status
    project.status = "generating"
    project.current_slide = slide_number
    await db.commit()

    start_time = time.time()
    generated_images = []

    try:
        # Build prompt with product info
        prompt = slide_prompt
        product_appearance = None
        if product:
            product_info = f"Product: {product.name}"
            if product.product_category:
                product_info += f" ({product.product_category})"
            if product.image_description:
                product_appearance = product.image_description
                product_info += f"\nProduct Appearance: {product.image_description}"
            elif product.description:
                product_appearance = product.description
                product_info += f" - {product.description}"
            prompt = f"{prompt}\n\n{product_info}"

        # Use prompt directly (Gemini understands Korean)
        optimized_prompt = prompt

        temp_dir = os.path.join(settings.TEMP_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Prepare images list
        images_data = []
        if reference_image_data:
            images_data.append((reference_image_data, reference_mime_type))
        if product_image_data:
            images_data.append((product_image_data, product_mime_type))

        # Number of variants
        num_variants = 2 if project.generation_mode == "step_by_step" else 4

        # Generate variants
        for variant_idx in range(num_variants):
            logger.info(f"Regenerating variant {variant_idx + 1}/{num_variants}")

            if images_data:
                editor = get_image_editor()

                if reference_used:
                    generation_prompt = f"""{optimized_prompt}

STYLE CONSISTENCY INSTRUCTION: The first attached image is the REFERENCE IMAGE.
- Match the visual style, color palette, lighting, and mood of the reference image
- Maintain consistency in artistic style and atmosphere"""
                else:
                    generation_prompt = f"""Create a marketing image with the following scene description:

{optimized_prompt}

PRODUCT INTEGRATION INSTRUCTIONS:
- The attached image shows the product to feature in this scene
- Generate the COMPLETE SCENE as described above (background, lighting, mood, all visual elements)
- Place the product naturally within this scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity (shape, colors, logo) while matching the scene's lighting and atmosphere
- The scene description is the PRIMARY creative direction - create that environment first, then place the product within it"""

                gen_result = await editor.edit_with_product(
                    edit_prompt=generation_prompt,
                    aspect_ratio=project.aspect_ratio,
                    product_description=product_appearance,
                    images_data=images_data,
                )
            else:
                generator = get_image_generator("gemini_imagen")
                gen_result = await generator.generate(
                    prompt=optimized_prompt,
                    aspect_ratio=project.aspect_ratio,
                    purpose=project.purpose,
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                filename = f"{uuid.uuid4()}.{ext}"
                image_bytes = base64.b64decode(image_data)
                content_type = "image/png" if ext == "png" else "image/jpeg"
                image_url = cloud_storage.upload_bytes(image_bytes, filename, "generated", content_type)
                logger.info(f"Uploaded image: {filename}, size: {len(image_bytes)} bytes, url: {image_url}")
            else:
                image_url = f"/placeholder-{project_id}-{slide_number}-{variant_idx}.jpg"

            gen_image = GeneratedImage(
                id=str(uuid.uuid4()),
                image_project_id=project_id,
                slide_number=slide_number,
                variant_index=variant_idx,
                image_url=image_url,
                prompt=slide_prompt,
                is_selected=False,
                approval_status="pending",
                is_reference_image=False,
                generation_provider="gemini_editor" if images_data else "gemini_imagen",
                generation_duration_ms=int((time.time() - start_time) * 1000 / (variant_idx + 1)),
            )

            db.add(gen_image)
            generated_images.append(gen_image)

        await db.commit()

        for img in generated_images:
            await db.refresh(img)

        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"Regenerated {len(generated_images)} images in {total_time}ms for slide {slide_number}")

        return RegenerateSectionResponse(
            project_id=project_id,
            slide_number=slide_number,
            deleted_count=deleted_count,
            new_images=[GeneratedImageResponse.model_validate(img) for img in generated_images],
            generation_time_ms=total_time,
            reference_image_used=reference_used,
        )

    except Exception as e:
        logger.error(f"Section regeneration failed: {e}")
        project.status = "failed"
        project.error_message = str(e)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section regeneration failed: {str(e)}"
        )


# ========== Background Image Generation ==========

async def _run_compose_generation(project, db, settings):
    """
    Handle compose mode image generation.
    Uses uploaded images and enhanced prompt to generate composed image.
    """
    from app.services.image_editor import get_image_editor
    import httpx
    import os

    logger.info(f"Starting compose generation for project {project.id}")

    async def load_image_from_temp_id(temp_id: str) -> tuple:
        """Load image from COS by temp_id."""
        # Try to load from COS (temp_id is UUID, file is in COS temp folder)
        for ext in ["png", "jpg", "jpeg", "webp"]:
            cos_url = f"https://{settings.TENCENT_COS_BUCKET}.cos.{settings.TENCENT_COS_REGION}.myqcloud.com/temp/{temp_id}.{ext}"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(cos_url)
                    if resp.status_code == 200:
                        mime_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                        return (resp.content, mime_type)
            except Exception:
                continue
        return (None, None)

    try:
        # Load images from COS
        compose_images = []
        if project.compose_image_temp_ids:
            for temp_id in project.compose_image_temp_ids:
                img_data, mime_type = await load_image_from_temp_id(temp_id)
                if img_data:
                    compose_images.append((img_data, mime_type))
                    logger.info(f"Loaded compose image: {temp_id}, {len(img_data)} bytes")
                else:
                    logger.warning(f"Compose image not found: {temp_id}")

        if not compose_images:
            logger.error(f"No compose images found for project {project.id}")
            project.status = "failed"
            project.error_message = "업로드된 이미지를 찾을 수 없습니다."
            await db.commit()
            return

        # Get image editor
        editor = get_image_editor()

        # Generate composed image
        logger.info(f"Generating compose image with prompt: {project.prompt[:100] if project.prompt else 'NONE'}...")

        gen_result = await editor.edit_with_product(
            edit_prompt=project.prompt or "",
            images_data=compose_images,
            aspect_ratio=project.aspect_ratio,
        )

        if gen_result and gen_result.image_url:
            # Create generated image record
            generated_image = GeneratedImage(
                id=str(uuid.uuid4()),
                image_project_id=project.id,
                image_url=gen_result.image_url,
                prompt=project.prompt,
                slide_number=1,
                variant_index=0,
                status="completed",
            )
            db.add(generated_image)

            project.status = "completed"
            project.completed_at = datetime.utcnow()
            logger.info(f"Compose generation completed for project {project.id}")
        else:
            project.status = "failed"
            project.error_message = "이미지 생성에 실패했습니다."
            logger.error(f"Compose generation failed for project {project.id}")

        await db.commit()

    except Exception as e:
        logger.error(f"Compose generation error for project {project.id}: {e}")
        project.status = "failed"
        project.error_message = str(e)
        await db.commit()


async def run_background_image_generation(project_id: str):
    """
    Background task to generate all images for a project.
    Similar to reference analysis background processing.
    """
    from app.services.video_generator.image_generator import get_image_generator
    from app.services.image_editor import get_image_editor
    from app.core.database import async_session_factory
    import base64
    import os
    from app.core.config import settings

    logger.info(f"Starting background image generation for project {project_id}")

    async with async_session_factory() as db:
        try:
            # Get project with relationships
            query = select(ImageProject).where(ImageProject.id == project_id).options(
                selectinload(ImageProject.generated_images)
            )
            result = await db.execute(query)
            project = result.scalar_one_or_none()

            if not project:
                logger.error(f"Project not found: {project_id}")
                return

            # Update status to generating
            project.status = "generating"
            await db.commit()

            # Handle compose mode separately
            if project.content_type == "compose":
                await _run_compose_generation(project, db, settings)
                return

            # Get storyboard data
            storyboard = project.storyboard_data or {}
            slides = storyboard.get("slides", [])

            if not slides:
                logger.warning(f"No slides found in storyboard for project {project_id}")
                project.status = "failed"
                project.error_message = "No slides in storyboard"
                await db.commit()
                return

            # Load product image if available
            product = None
            product_image_data = None
            product_mime_type = None
            if project.product_id:
                product_query = select(Product).where(Product.id == project.product_id)
                product_result = await db.execute(product_query)
                product = product_result.scalar_one_or_none()

                if product and product.image_url:
                    product_image_data, product_mime_type = await load_image_from_url(product.image_url, settings)

            # Load reference images if available (for style guidance)
            reference_images_data = []
            if project.reference_image_urls:
                for ref_url in project.reference_image_urls:
                    ref_data, ref_mime = await load_image_from_url(ref_url, settings)
                    if ref_data:
                        reference_images_data.append((ref_data, ref_mime))

                logger.info(f"Total reference images loaded: {len(reference_images_data)}")

            temp_dir = os.path.join(settings.TEMP_DIR, "temp")
            os.makedirs(temp_dir, exist_ok=True)

            total_slides = len(slides)
            generated_count = 0
            is_carousel = project.content_type == "carousel"

            # For carousel: store previous slide images by variant index for continuity
            # prev_variant_images[variant_idx] = (image_bytes, mime_type)
            prev_variant_images: dict = {}

            # Generate images for each slide
            for slide_idx, slide_data in enumerate(slides):
                slide_number = slide_idx + 1
                project.current_slide = slide_number
                await db.commit()

                slide_prompt = (
                    slide_data.get("visual_prompt")
                    or slide_data.get("prompt")
                    or project.prompt
                    or ""
                )
                # 상세 로그: 어떤 프롬프트가 사용되는지 확인
                logger.info(f"=== Slide {slide_number}/{total_slides} ===")
                logger.info(f"[원본] visual_prompt: {slide_data.get('visual_prompt', 'NONE')[:100] if slide_data.get('visual_prompt') else 'NONE'}")
                logger.info(f"[원본] visual_prompt_display: {slide_data.get('visual_prompt_display', 'NONE')[:100] if slide_data.get('visual_prompt_display') else 'NONE'}")
                logger.info(f"[사용] slide_prompt: {slide_prompt[:100] if slide_prompt else 'EMPTY'}")

                # Build prompt with product info
                prompt = slide_prompt
                product_appearance = None
                if product:
                    product_info = f"Product: {product.name}"
                    if product.product_category:
                        product_info += f" ({product.product_category})"
                    if product.image_description:
                        product_appearance = product.image_description
                        product_info += f"\nProduct Appearance: {product.image_description}"
                    elif product.description:
                        product_appearance = product.description
                        product_info += f" - {product.description}"
                    prompt = f"{prompt}\n\n{product_info}"

                # Use prompt directly (Gemini understands Korean, optimization was truncating prompts)
                optimized_prompt = prompt
                logger.info(f"[프롬프트] optimized_prompt: {optimized_prompt[:150] if optimized_prompt else 'EMPTY'}")

                # Generate 2 variants per slide
                num_variants = 2
                start_time = time.time()

                # Store current slide's generated images for next slide reference
                current_variant_images: dict = {}

                for variant_idx in range(num_variants):
                    try:
                        # Prepare images data for this variant
                        images_data = []

                        # Add reference images first (for style guidance) - IMPORTANT for matching user's reference style
                        has_reference_style = False
                        if reference_images_data:
                            for ref_data, ref_mime in reference_images_data:
                                images_data.append((ref_data, ref_mime))
                            has_reference_style = True
                            logger.info(f"Added {len(reference_images_data)} reference images for style guidance")

                        # For carousel: use previous slide's same variant image as reference
                        if is_carousel and slide_number > 1 and variant_idx in prev_variant_images:
                            prev_img_data, prev_mime = prev_variant_images[variant_idx]
                            images_data.append((prev_img_data, prev_mime))
                            logger.info(f"Using previous slide's variant {variant_idx + 1} as reference for continuity")

                        # Add product image if available
                        if product_image_data:
                            images_data.append((product_image_data, product_mime_type))

                        if images_data:
                            editor = get_image_editor()

                            # Different prompt based on whether we have a reference image from previous slide
                            if is_carousel and slide_number > 1 and variant_idx in prev_variant_images:
                                generation_prompt = f"""Continue the visual story with the following new scene:

{optimized_prompt}

VISUAL CONTINUITY INSTRUCTIONS:
- The first attached image is from the PREVIOUS scene - maintain the same visual style, color palette, lighting mood, and artistic direction
- Create a NEW scene as described above, but ensure it feels like a natural continuation
- Keep consistent: art style, color grading, atmosphere, and overall aesthetic
- The new scene should flow naturally from the previous one while depicting the new content

PRODUCT INTEGRATION (if product image attached):
- Place the product naturally within this new scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity while matching the scene's style"""
                            elif has_reference_style:
                                # Has reference images for style guidance
                                generation_prompt = f"""Create a marketing image with the following scene description:

{optimized_prompt}

CRITICAL STYLE REFERENCE INSTRUCTIONS:
- The FIRST attached image(s) are STYLE REFERENCES - you MUST match their visual style, mood, color palette, lighting, and artistic direction
- Analyze the reference images carefully: their color grading, composition style, lighting mood, and overall aesthetic
- Generate the scene as described above BUT in the SAME STYLE as the reference images
- The scene description tells you WHAT to create, the reference images tell you HOW it should look

PRODUCT INTEGRATION INSTRUCTIONS:
- The LAST attached image shows the product to feature in this scene
- Generate the COMPLETE SCENE as described above, matching the reference style
- Place the product naturally within this scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity while matching BOTH the scene's atmosphere AND the reference style"""
                            else:
                                generation_prompt = f"""Create a marketing image with the following scene description:

{optimized_prompt}

PRODUCT INTEGRATION INSTRUCTIONS:
- The attached image shows the product to feature in this scene
- Generate the COMPLETE SCENE as described above (background, lighting, mood, all visual elements)
- Place the product naturally within this scene
- The product should be clearly visible but integrated into the artistic vision
- Preserve the product's key visual identity (shape, colors, logo) while matching the scene's lighting and atmosphere
- The scene description is the PRIMARY creative direction - create that environment first, then place the product within it"""

                            gen_result = await editor.edit_with_product(
                                edit_prompt=generation_prompt,
                                aspect_ratio=project.aspect_ratio,
                                product_description=product_appearance,
                                images_data=images_data,
                            )
                        else:
                            generator = get_image_generator("gemini_imagen")
                            gen_result = await generator.generate(
                                prompt=optimized_prompt,
                                aspect_ratio=project.aspect_ratio,
                                purpose=project.purpose,
                            )

                        # Save generated image
                        image_data = gen_result.get("image_data")
                        result_mime_type = gen_result.get("mime_type", "image/png")

                        if image_data:
                            ext = "png" if "png" in result_mime_type else "jpg"
                            filename = f"{uuid.uuid4()}.{ext}"
                            image_bytes = base64.b64decode(image_data)
                            content_type = "image/png" if ext == "png" else "image/jpeg"
                            image_url = cloud_storage.upload_bytes(image_bytes, filename, "generated", content_type)
                            logger.info(f"Uploaded image: {filename}, size: {len(image_bytes)} bytes, url: {image_url}")

                            # Store this image for next slide's reference (carousel only)
                            if is_carousel:
                                current_variant_images[variant_idx] = (image_bytes, result_mime_type)
                        else:
                            image_url = f"/placeholder-{project_id}-{slide_number}-{variant_idx}.jpg"

                        # Create GeneratedImage record
                        gen_image = GeneratedImage(
                            id=str(uuid.uuid4()),
                            image_project_id=project_id,
                            slide_number=slide_number,
                            variant_index=variant_idx,
                            image_url=image_url,
                            prompt=slide_prompt,
                            is_selected=False,
                            approval_status="pending",
                            is_reference_image=False,
                            generation_provider="gemini_editor" if images_data else "gemini_imagen",
                            generation_duration_ms=int((time.time() - start_time) * 1000 / (variant_idx + 1)),
                        )
                        db.add(gen_image)
                        generated_count += 1

                    except Exception as e:
                        logger.error(f"Failed to generate variant {variant_idx + 1} for slide {slide_number}: {e}")
                        continue

                # Update previous variant images for next slide
                if is_carousel:
                    prev_variant_images = current_variant_images

                await db.commit()

            # Update project status
            project.status = "completed"
            project.current_slide = total_slides
            await db.commit()

            logger.info(f"Background generation completed for project {project_id}: {generated_count} images generated")

        except Exception as e:
            logger.error(f"Background generation failed for project {project_id}: {e}")
            try:
                project.status = "failed"
                project.error_message = str(e)
                await db.commit()
            except:
                pass


from pydantic import BaseModel as PydanticBaseModel


class StartBackgroundGenerationResponse(PydanticBaseModel):
    """Response for starting background generation."""
    project_id: str
    status: str
    message: str
    total_slides: int


@router.post("/{project_id}/generate-background", response_model=StartBackgroundGenerationResponse)
async def start_background_generation(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start background image generation for all slides.
    Returns immediately and generates images in background.
    Poll GET /{project_id} to check status.
    """
    # Get project
    query = select(ImageProject).where(ImageProject.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image project not found: {project_id}"
        )

    # Check storyboard exists (skip for compose mode)
    storyboard = project.storyboard_data or {}
    slides = storyboard.get("slides", [])

    if not slides and project.content_type != "compose":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No storyboard slides found. Generate storyboard first."
        )

    # Update status to pending/generating
    project.status = "generating"
    project.current_slide = 0
    await db.commit()

    # Start background task
    background_tasks.add_task(run_background_image_generation, project_id)

    # For compose mode, total_slides is 1
    total_slides = len(slides) if slides else 1

    return StartBackgroundGenerationResponse(
        project_id=project_id,
        status="generating",
        message=f"Image generation started for {total_slides} slides. Check status with GET /image-projects/{project_id}",
        total_slides=total_slides,
    )


# ========== Image Download Endpoint ==========

@router.get("/images/{image_id}/download")
async def download_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Download a generated image as-is (original size from AI generation).

    The AI generates images at the requested aspect ratio during creation,
    so no post-processing is needed. Returns the original image directly.
    """
    import io
    import os
    from app.core.config import settings

    # Get the generated image record
    image_query = select(GeneratedImage).where(GeneratedImage.id == image_id)
    image_result = await db.execute(image_query)
    gen_image = image_result.scalar_one_or_none()

    if not gen_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {image_id}"
        )

    # Resolve the image file path or URL
    image_url = gen_image.image_url
    image_data = None
    image_path = None

    if image_url.startswith("http"):
        # Download from COS or external URL
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(image_url)
                if resp.status_code == 200:
                    image_data = resp.content
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Failed to download image from URL: {image_url}"
                    )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download image: {str(e)}"
            )
    elif image_url.startswith("/static/"):
        image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
    else:
        image_path = image_url

    if image_path:
        if not os.path.exists(image_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image file not found: {image_url}"
            )
        with open(image_path, "rb") as f:
            image_data = f.read()

    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not load image: {image_url}"
        )

    # Determine content type from URL extension
    ext = os.path.splitext(image_url)[1].lower() if '.' in image_url else '.jpg'
    if ext in ['.jpg', '.jpeg']:
        content_type = 'image/jpeg'
        file_ext = 'jpg'
    else:
        content_type = 'image/png'
        file_ext = 'png'

    # Generate filename
    filename = f"image_{image_id}.{file_ext}"

    logger.info(f"Download image {image_id}: {len(image_data)} bytes (original)")

    return StreamingResponse(
        io.BytesIO(image_data),
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
    )


__all__ = ["router"]
