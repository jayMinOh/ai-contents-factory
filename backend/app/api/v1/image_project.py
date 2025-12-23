"""
ImageProject API endpoints for the AI Video Marketing Platform.

Provides CRUD operations for image projects and image generation.
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
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


# ========== CRUD Operations ==========

@router.post("/", response_model=ImageProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_image_project(
    project_data: ImageProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new image project."""
    project_id = str(uuid.uuid4())

    # Generate title if not provided
    title = project_data.title
    if not title:
        content_type_kr = {"single": "단일", "carousel": "캐러셀", "story": "세로형"}
        purpose_kr = {"ad": "광고", "info": "정보", "lifestyle": "라이프스타일"}
        title = f"{content_type_kr.get(project_data.content_type, project_data.content_type)} {purpose_kr.get(project_data.purpose, project_data.purpose)} 이미지"

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
        prompt=project_data.prompt,
        aspect_ratio=project_data.aspect_ratio,
        status="draft",
        current_step=1,
        current_slide=1,
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(f"Created image project: {project_id}")
    return project


@router.get("/", response_model=List[ImageProjectSummary])
async def list_image_projects(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    brand_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List image projects with optional filters."""
    query = select(ImageProject).order_by(ImageProject.created_at.desc())

    if content_type:
        query = query.where(ImageProject.content_type == content_type)
    if status:
        query = query.where(ImageProject.status == status)
    if brand_id:
        query = query.where(ImageProject.brand_id == brand_id)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    projects = result.scalars().all()

    return projects


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
    from app.services.video_generator.image_generator import get_image_generator, get_prompt_optimizer
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
            # Load product image
            image_url = product.image_url
            image_path = None

            # Handle various URL formats
            if image_url.startswith("http://localhost:8000/static/"):
                # Convert localhost URL to local path: http://localhost:8000/static/products/xxx.png -> storage/products/xxx.png
                relative_path = image_url.replace("http://localhost:8000/static/", "")
                image_path = os.path.join(settings.TEMP_DIR, relative_path)
                logger.info(f"Converted localhost URL to path: {image_url} -> {image_path}")
            elif image_url.startswith("/static/"):
                # Handle relative static URLs: /static/products/xxx.png -> storage/products/xxx.png
                image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            elif image_url.startswith("http"):
                # For external remote URLs, skip for now
                logger.warning(f"External URL not supported: {image_url}")
                image_path = None
            else:
                # Direct file path
                image_path = image_url

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    product_image_data = f.read()
                logger.info(f"Loaded product image: {len(product_image_data)} bytes from {image_path}")
            elif image_path:
                logger.warning(f"Product image file not found: {image_path}")

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

        # Optimize prompt
        optimizer = get_prompt_optimizer()
        optimized_prompt = await optimizer.optimize(prompt)
        logger.info(f"Optimized prompt: {optimized_prompt[:100]}...")

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

                # Build enhanced prompt that emphasizes product preservation
                product_reference_prompt = f"""{optimized_prompt}

CRITICAL INSTRUCTION: The attached image shows the EXACT product that MUST appear in the generated image.
- Preserve the product's exact appearance: shape, colors, logo, text, and all visual details
- The product should be clearly visible and recognizable as the same product
- Do NOT create a generic or different looking product
- Place the product naturally in the scene while maintaining its visual identity"""

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
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                temp_id = str(uuid.uuid4())
                filename = f"{temp_id}.{ext}"

                filepath = os.path.join(temp_dir, filename)
                image_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                image_url = f"/static/temp/{filename}"
            else:
                # Mock fallback
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
    from app.services.video_generator.image_generator import get_image_generator, get_prompt_optimizer
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
    slide_prompt = slide_data.get("prompt", project.prompt or "")

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
            # Load the reference image data
            image_url = ref_image.image_url
            image_path = None

            if image_url.startswith("/static/"):
                image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            elif not image_url.startswith("http"):
                image_path = image_url

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    reference_image_data = f.read()
                reference_mime_type = "image/png" if ".png" in image_path.lower() else "image/jpeg"
                reference_used = True
                logger.info(f"Loaded reference image: {len(reference_image_data)} bytes from {image_path}")

    # Load product image if available
    product = None
    product_image_data = None
    product_mime_type = None
    if project.product_id:
        product_query = select(Product).where(Product.id == project.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.image_url:
            image_url = product.image_url
            image_path = None

            if image_url.startswith("http://localhost:8000/static/"):
                relative_path = image_url.replace("http://localhost:8000/static/", "")
                image_path = os.path.join(settings.TEMP_DIR, relative_path)
            elif image_url.startswith("/static/"):
                image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            elif not image_url.startswith("http"):
                image_path = image_url

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    product_image_data = f.read()
                product_mime_type = "image/png" if ".png" in image_path.lower() else "image/jpeg"
                logger.info(f"Loaded product image: {len(product_image_data)} bytes")

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

        # Optimize prompt
        optimizer = get_prompt_optimizer()
        optimized_prompt = await optimizer.optimize(prompt)
        logger.info(f"Optimized prompt: {optimized_prompt[:100]}...")

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
                    generation_prompt = f"""{optimized_prompt}

CRITICAL INSTRUCTION: The attached image shows the EXACT product that MUST appear in the generated image.
- Preserve the product's exact appearance: shape, colors, logo, text, and all visual details
- The product should be clearly visible and recognizable as the same product"""

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
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                temp_id = str(uuid.uuid4())
                filename = f"{temp_id}.{ext}"

                filepath = os.path.join(temp_dir, filename)
                image_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                image_url = f"/static/temp/{filename}"
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
    from app.services.video_generator.image_generator import get_image_generator, get_prompt_optimizer
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
    slide_prompt = slide_data.get("prompt", project.prompt or "")

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
            image_url = ref_image.image_url
            image_path = None

            if image_url.startswith("/static/"):
                image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            elif not image_url.startswith("http"):
                image_path = image_url

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    reference_image_data = f.read()
                reference_mime_type = "image/png" if ".png" in image_path.lower() else "image/jpeg"
                reference_used = True
                logger.info(f"Loaded reference image for regeneration: {len(reference_image_data)} bytes")

    # Load product image if available
    product = None
    product_image_data = None
    product_mime_type = None
    if project.product_id:
        product_query = select(Product).where(Product.id == project.product_id)
        product_result = await db.execute(product_query)
        product = product_result.scalar_one_or_none()

        if product and product.image_url:
            image_url = product.image_url
            image_path = None

            if image_url.startswith("http://localhost:8000/static/"):
                relative_path = image_url.replace("http://localhost:8000/static/", "")
                image_path = os.path.join(settings.TEMP_DIR, relative_path)
            elif image_url.startswith("/static/"):
                image_path = os.path.join(settings.TEMP_DIR, image_url.replace("/static/", ""))
            elif not image_url.startswith("http"):
                image_path = image_url

            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    product_image_data = f.read()
                product_mime_type = "image/png" if ".png" in image_path.lower() else "image/jpeg"

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

        # Optimize prompt
        optimizer = get_prompt_optimizer()
        optimized_prompt = await optimizer.optimize(prompt)

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
                    generation_prompt = f"""{optimized_prompt}

CRITICAL INSTRUCTION: The attached image shows the EXACT product that MUST appear in the generated image."""

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
                )

            # Save generated image
            image_data = gen_result.get("image_data")
            result_mime_type = gen_result.get("mime_type", "image/png")

            if image_data:
                ext = "png" if "png" in result_mime_type else "jpg"
                temp_id = str(uuid.uuid4())
                filename = f"{temp_id}.{ext}"

                filepath = os.path.join(temp_dir, filename)
                image_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                image_url = f"/static/temp/{filename}"
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


__all__ = ["router"]
