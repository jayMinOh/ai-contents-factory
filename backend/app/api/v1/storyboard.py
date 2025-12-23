"""
Storyboard Generation API endpoint.

Provides a new storyboard generation endpoint that uses Gemini to generate
storyboards based on content type, purpose, and either prompt or reference analysis.

Endpoint: POST /api/v1/storyboard/generate
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Brand, Product, ReferenceAnalysis
from app.schemas.storyboard import (
    StoryboardGenerateV2Request,
    StoryboardGenerateV2Response,
    StoryboardSlide,
    ConceptGenerateRequest,
    ConceptGenerateResponse,
)
from app.services.storyboard_generator_v2 import get_storyboard_generator_v2
from app.services.concept_generator import get_concept_generator


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate",
    response_model=StoryboardGenerateV2Response,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a storyboard",
    description="""
Generate a storyboard using AI (Gemini) based on content type, purpose, and method.

**Content Types:**
- `single`: Single image that tells the complete story
- `carousel`: Multi-slide swipeable content (5-10 slides)
- `story`: Vertical format optimized for mobile (3-7 slides)

**Purposes:**
- `ad`: Advertising focused on product benefits and CTA
- `info`: Informational/educational content
- `lifestyle`: Emotional, authentic, lifestyle-focused content

**Methods:**
- `reference`: Generate based on reference analysis data
- `prompt`: Generate based on free-form text prompt

For `method='reference'`, provide `reference_id` and optionally `selected_items`.
For `method='prompt'`, provide a `prompt` string.
For `purpose='ad'`, it's recommended to provide `brand_id` and `product_id`.
""",
)
async def generate_storyboard(
    request: StoryboardGenerateV2Request,
    accept_language: Optional[str] = Header(default="ko", alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a storyboard using Gemini AI.

    This endpoint creates a complete storyboard with slides, visual prompts
    for image generation, and text overlays based on the specified parameters.
    """

    # Validate request based on method
    if request.method == "prompt" and not request.prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prompt is required when method is 'prompt'",
        )

    if request.method == "reference" and not request.reference_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reference_id is required when method is 'reference'",
        )

    # Parse language from Accept-Language header
    language = request.language or accept_language.split(",")[0].split("-")[0]
    logger.info(
        f"Generating storyboard: content_type={request.content_type}, "
        f"purpose={request.purpose}, method={request.method}, language={language}"
    )

    # Fetch brand info if provided
    brand_info = None
    if request.brand_id:
        result = await db.execute(select(Brand).where(Brand.id == request.brand_id))
        brand = result.scalar_one_or_none()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand not found: {request.brand_id}",
            )
        brand_info = {
            "name": brand.name,
            "description": brand.description,
            "tone_and_manner": brand.tone_and_manner,
            "target_audience": brand.target_audience,
            "usp": brand.usp,
            "keywords": brand.keywords or [],
            "industry": brand.industry,
        }
        logger.info(f"Loaded brand: {brand.name}")

    # Fetch product info if provided
    product_info = None
    if request.product_id:
        result = await db.execute(select(Product).where(Product.id == request.product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {request.product_id}",
            )
        product_info = {
            "name": product.name,
            "description": product.description,
            "image_description": product.image_description,
            "product_category": product.product_category,
            "features": product.features or [],
            "benefits": product.benefits or [],
            "key_ingredients": product.key_ingredients or [],
            "suitable_skin_types": product.suitable_skin_types or [],
            "skin_concerns": product.skin_concerns or [],
            "texture_type": product.texture_type,
            "finish_type": product.finish_type,
        }
        logger.info(f"Loaded product: {product.name}")

    # Fetch reference analysis if using reference method
    reference_analysis = None
    if request.method == "reference" and request.reference_id:
        result = await db.execute(
            select(ReferenceAnalysis).where(ReferenceAnalysis.id == request.reference_id)
        )
        ref = result.scalar_one_or_none()
        if not ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reference analysis not found: {request.reference_id}",
            )
        if ref.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reference analysis is not completed: status={ref.status}",
            )
        reference_analysis = {
            "segments": ref.segments or [],
            "hook_points": ref.hook_points or [],
            "edge_points": ref.edge_points or [],
            "emotional_triggers": ref.emotional_triggers or [],
            "pain_points": ref.pain_points or [],
            "selling_points": ref.selling_points or [],
            "recommendations": ref.recommendations or [],
            "cta_analysis": ref.cta_analysis,
            "structure_pattern": ref.structure_pattern,
        }
        logger.info(f"Loaded reference analysis: {ref.title}")

    # Convert selected_items to dict if provided
    selected_items = None
    if request.selected_items:
        selected_items = request.selected_items.model_dump(exclude_none=True)

    # Generate storyboard using Gemini
    try:
        generator = get_storyboard_generator_v2()
        result = await generator.generate(
            content_type=request.content_type,
            purpose=request.purpose,
            method=request.method,
            prompt=request.prompt,
            brand_info=brand_info,
            product_info=product_info,
            reference_analysis=reference_analysis,
            selected_items=selected_items,
            language=language,
            aspect_ratio=request.aspect_ratio,
        )

        logger.info(
            f"Storyboard generated successfully: id={result['storyboard_id']}, "
            f"slides={result['total_slides']}"
        )

        # Convert slides to proper schema format
        slides = []
        for slide_data in result.get("slides", []):
            # Ensure section_type is valid
            section_type = slide_data.get("section_type", "transition")
            valid_types = {"hook", "problem", "solution", "benefit", "cta", "intro", "outro", "transition", "feature"}
            if section_type not in valid_types:
                # Map common variations
                type_map = {
                    "opening": "hook",
                    "attention": "hook",
                    "pain_point": "problem",
                    "agitation": "problem",
                    "call_to_action": "cta",
                    "closing": "outro",
                    "end": "outro",
                }
                section_type = type_map.get(section_type.lower(), "transition")

            slides.append(
                StoryboardSlide(
                    slide_number=slide_data.get("slide_number", len(slides) + 1),
                    section_type=section_type,
                    title=slide_data.get("title", ""),
                    description=slide_data.get("description", ""),
                    visual_prompt=slide_data.get("visual_prompt", ""),
                    visual_prompt_display=slide_data.get("visual_prompt_display"),
                    text_overlay=slide_data.get("text_overlay"),
                    narration_script=slide_data.get("narration_script"),
                    duration_seconds=slide_data.get("duration_seconds", 3.0),
                )
            )

        return StoryboardGenerateV2Response(
            storyboard_id=result["storyboard_id"],
            slides=slides,
            total_slides=len(slides),
            storyline=result.get("storyline", ""),
            content_type=result["content_type"],
            purpose=result["purpose"],
            generation_method=result["generation_method"],
        )

    except ValueError as e:
        logger.error(f"Storyboard generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Storyboard generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storyboard generation failed: {str(e)}",
        )


@router.post(
    "/generate-concept",
    response_model=ConceptGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI concept suggestion for single image content",
    description="""
Generate an AI-powered concept suggestion for single image content types.
This is a "Light Storyboard" that provides visual concept, copy suggestion,
and style recommendations before generating a single image.

**Content Types:**
- `single`: Single square image (1:1) for feed posts
- `story`: Single vertical image (9:16) for stories

**Purposes:**
- `ad`: Advertising focused on product benefits and CTA
- `info`: Informational/educational content
- `lifestyle`: Emotional, authentic, lifestyle-focused content

The concept is generated based on:
- Reference analysis data (hooks, selling points, emotional triggers)
- Optional brand and product context
- User-selected elements from reference analysis

Response includes:
- `visual_concept`: Korean description of layout and composition
- `copy_suggestion`: Korean hooking text based on reference analysis
- `style_recommendation`: Korean style description based on purpose
- `visual_prompt`: English prompt optimized for AI image generation
""",
)
async def generate_concept(
    request: ConceptGenerateRequest,
    accept_language: Optional[str] = Header(default="ko", alias="Accept-Language"),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI concept suggestion for single image content.

    This endpoint creates a "Light Storyboard" with visual concept, copy suggestion,
    style recommendation, and a ready-to-use visual prompt for image generation.

    Supports two modes:
    - reference: Based on reference analysis data (traditional mode)
    - upload: Based on uploaded product/reference images (new mode)
    """

    # Parse language from Accept-Language header
    language = request.language or accept_language.split(",")[0].split("-")[0]
    generation_mode = request.generation_mode or "reference"

    logger.info(
        f"Generating concept: content_type={request.content_type}, "
        f"purpose={request.purpose}, mode={generation_mode}, language={language}"
    )

    reference_analysis = None
    uploaded_images = None

    if generation_mode == "reference":
        # Reference mode: Fetch reference analysis (required)
        if not request.reference_analysis_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reference_analysis_id is required for reference mode",
            )

        result = await db.execute(
            select(ReferenceAnalysis).where(ReferenceAnalysis.id == request.reference_analysis_id)
        )
        ref = result.scalar_one_or_none()
        if not ref:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reference analysis not found: {request.reference_analysis_id}",
            )
        if ref.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reference analysis is not completed: status={ref.status}",
            )

        reference_analysis = {
            "segments": ref.segments or [],
            "hook_points": ref.hook_points or [],
            "edge_points": ref.edge_points or [],
            "emotional_triggers": ref.emotional_triggers or [],
            "pain_points": ref.pain_points or [],
            "selling_points": ref.selling_points or [],
            "recommendations": ref.recommendations or [],
            "cta_analysis": ref.cta_analysis,
            "structure_pattern": ref.structure_pattern,
        }
        logger.info(f"Loaded reference analysis: {ref.title}")

    else:
        # Upload mode: Use uploaded reference images or prompt
        has_images = request.reference_image_urls and len(request.reference_image_urls) > 0
        has_prompt = request.user_prompt and len(request.user_prompt.strip()) > 0

        if not has_images and not has_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either reference_image_urls or user_prompt is required for upload mode",
            )

        uploaded_images = {
            "reference_image_urls": request.reference_image_urls or [],
            "user_prompt": request.user_prompt,
        }
        logger.info(f"Upload mode: {len(request.reference_image_urls or [])} reference images, prompt={'yes' if has_prompt else 'no'}")

    # Fetch brand info if provided
    brand_info = None
    if request.brand_id:
        result = await db.execute(select(Brand).where(Brand.id == request.brand_id))
        brand = result.scalar_one_or_none()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Brand not found: {request.brand_id}",
            )
        brand_info = {
            "name": brand.name,
            "description": brand.description,
            "tone_and_manner": brand.tone_and_manner,
            "target_audience": brand.target_audience,
            "usp": brand.usp,
            "keywords": brand.keywords or [],
            "industry": brand.industry,
        }
        logger.info(f"Loaded brand: {brand.name}")

    # Fetch product info if provided
    product_info = None
    if request.product_id:
        result = await db.execute(select(Product).where(Product.id == request.product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {request.product_id}",
            )
        product_info = {
            "name": product.name,
            "description": product.description,
            "image_description": product.image_description,
            "product_category": product.product_category,
            "features": product.features or [],
            "benefits": product.benefits or [],
            "key_ingredients": product.key_ingredients or [],
            "suitable_skin_types": product.suitable_skin_types or [],
            "skin_concerns": product.skin_concerns or [],
            "texture_type": product.texture_type,
            "finish_type": product.finish_type,
        }
        logger.info(f"Loaded product: {product.name}")

    # Convert selected_items to dict if provided
    selected_items = None
    if request.selected_items:
        selected_items = request.selected_items.model_dump(exclude_none=True)

    # Generate concept using Gemini
    try:
        generator = get_concept_generator()
        result = await generator.generate(
            content_type=request.content_type,
            purpose=request.purpose,
            reference_analysis=reference_analysis,
            uploaded_images=uploaded_images,
            brand_info=brand_info,
            product_info=product_info,
            selected_items=selected_items,
            language=language,
        )

        logger.info(
            f"Concept generated successfully: id={result['concept_id']}, "
            f"content_type={result['content_type']}"
        )

        return ConceptGenerateResponse(
            concept_id=result["concept_id"],
            visual_concept=result.get("visual_concept", ""),
            copy_suggestion=result.get("copy_suggestion", ""),
            style_recommendation=result.get("style_recommendation", ""),
            visual_prompt=result.get("visual_prompt", ""),
            visual_prompt_display=result.get("visual_prompt_display"),
            text_overlay_suggestion=result.get("text_overlay_suggestion"),
            content_type=result["content_type"],
            purpose=result["purpose"],
        )

    except ValueError as e:
        logger.error(f"Concept generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Concept generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concept generation failed: {str(e)}",
        )


__all__ = ["router"]
