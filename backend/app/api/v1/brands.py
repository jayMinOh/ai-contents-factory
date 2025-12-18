"""
Brand and Product API Endpoints for AI Video Marketing Platform.

Provides RESTful CRUD operations for brand and product management
with SQLAlchemy async database integration.
"""

import logging
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.brand import (
    BrandCreate,
    BrandResponse,
    BrandSummary,
    BrandUpdate,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.services import brand_service, product_service
from app.models import Product

logger = logging.getLogger(__name__)


router = APIRouter()


def _product_to_response(p: Product) -> ProductResponse:
    """Convert Product model to ProductResponse with all cosmetics fields."""
    return ProductResponse(
        id=p.id,
        brand_id=p.brand_id,
        name=p.name,
        description=p.description,
        # Product Image
        image_url=p.image_url,
        image_description=p.image_description,
        # Cosmetics fields
        product_category=p.product_category,
        key_ingredients=p.key_ingredients or [],
        suitable_skin_types=p.suitable_skin_types or [],
        skin_concerns=p.skin_concerns or [],
        texture_type=p.texture_type,
        finish_type=p.finish_type,
        certifications=p.certifications or [],
        clinical_results=p.clinical_results or [],
        volume_ml=p.volume_ml,
        # Legacy fields
        features=p.features or [],
        benefits=p.benefits or [],
        price_range=p.price_range,
        target_segment=p.target_segment,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )


# ========== Brand Endpoints ==========


@router.post("/", response_model=BrandResponse)
async def create_brand(
    brand: BrandCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new brand."""
    created_brand = await brand_service.create_brand(db, brand)
    return BrandResponse(
        id=created_brand.id,
        name=created_brand.name,
        description=created_brand.description,
        logo_url=created_brand.logo_url,
        target_audience=created_brand.target_audience,
        tone_and_manner=created_brand.tone_and_manner,
        usp=created_brand.usp,
        keywords=created_brand.keywords,
        industry=created_brand.industry,
        created_at=created_brand.created_at.isoformat(),
        updated_at=created_brand.updated_at.isoformat(),
        products=[],
    )


@router.get("/", response_model=List[BrandSummary])
async def list_brands(
    db: AsyncSession = Depends(get_db),
):
    """List all brands."""
    return await brand_service.list_brands(db)


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a brand by ID."""
    brand = await brand_service.get_brand(db, brand_id)
    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
        target_audience=brand.target_audience,
        tone_and_manner=brand.tone_and_manner,
        usp=brand.usp,
        keywords=brand.keywords,
        industry=brand.industry,
        created_at=brand.created_at.isoformat(),
        updated_at=brand.updated_at.isoformat(),
        products=[_product_to_response(p) for p in brand.products],
    )


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: str,
    brand_update: BrandUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a brand."""
    updated_brand = await brand_service.update_brand(db, brand_id, brand_update)
    if updated_brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Fetch with products for response
    brand = await brand_service.get_brand(db, brand_id)
    return BrandResponse(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        logo_url=brand.logo_url,
        target_audience=brand.target_audience,
        tone_and_manner=brand.tone_and_manner,
        usp=brand.usp,
        keywords=brand.keywords,
        industry=brand.industry,
        created_at=brand.created_at.isoformat(),
        updated_at=brand.updated_at.isoformat(),
        products=[_product_to_response(p) for p in brand.products],
    )


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a brand and all its products."""
    success = await brand_service.delete_brand(db, brand_id)
    if not success:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand deleted successfully"}


# ========== Product Endpoints ==========


@router.post("/{brand_id}/products", response_model=ProductResponse)
async def create_product(
    brand_id: str,
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new product under a brand."""
    created_product = await product_service.create_product(db, brand_id, product)
    if created_product is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return _product_to_response(created_product)


@router.get("/{brand_id}/products", response_model=List[ProductResponse])
async def list_products(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all products of a brand."""
    products = await product_service.list_products(db, brand_id)
    return [_product_to_response(p) for p in products]


@router.get("/{brand_id}/products/{product_id}", response_model=ProductResponse)
async def get_product(
    brand_id: str,
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a product by ID."""
    product = await product_service.get_product(db, brand_id, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return _product_to_response(product)


@router.put("/{brand_id}/products/{product_id}", response_model=ProductResponse)
async def update_product(
    brand_id: str,
    product_id: str,
    product_update: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    updated_product = await product_service.update_product(
        db, brand_id, product_id, product_update
    )
    if updated_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return _product_to_response(updated_product)


@router.delete("/{brand_id}/products/{product_id}")
async def delete_product(
    brand_id: str,
    product_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a product."""
    success = await product_service.delete_product(db, brand_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}


@router.post("/{brand_id}/products/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    brand_id: str,
    product_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a product image and auto-generate description using AI.

    The image is saved and analyzed by Gemini Vision to generate
    a detailed description for AI image generation.
    """
    from app.services.image_analyzer import get_product_image_analyzer

    # Validate product exists
    product = await product_service.get_product(db, brand_id, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Read file content
    image_data = await file.read()

    # Save image to static directory
    products_dir = os.path.join(settings.TEMP_DIR, "products")
    os.makedirs(products_dir, exist_ok=True)

    ext = file.filename.split(".")[-1] if file.filename else "png"
    filename = f"{product_id}.{ext}"
    filepath = os.path.join(products_dir, filename)

    with open(filepath, "wb") as f:
        f.write(image_data)

    image_url = f"http://localhost:8000/static/products/{filename}"
    logger.info(f"Product image saved: {filepath}")

    # Analyze image with Gemini Vision
    try:
        analyzer = get_product_image_analyzer()
        image_description = await analyzer.analyze(image_data, file.content_type)
        logger.info(f"Image description generated: {image_description[:50]}...")
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        image_description = None

    # Update product with image URL and description
    update_data = ProductUpdate(
        image_url=image_url,
        image_description=image_description,
    )
    updated_product = await product_service.update_product(
        db, brand_id, product_id, update_data
    )

    return _product_to_response(updated_product)
