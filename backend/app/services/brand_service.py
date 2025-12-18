"""
Brand Service Layer for the AI Video Marketing Platform.

Provides CRUD operations for Brand entities using SQLAlchemy 2.0 async patterns.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Brand, Product
from app.schemas.brand import BrandCreate, BrandSummary, BrandUpdate


async def create_brand(db: AsyncSession, brand_data: BrandCreate) -> Brand:
    """
    Create a new brand.

    Args:
        db: Async database session
        brand_data: Brand creation schema with required fields

    Returns:
        Newly created Brand model instance
    """
    brand = Brand(
        id=str(uuid.uuid4()),
        name=brand_data.name,
        description=brand_data.description,
        logo_url=brand_data.logo_url,
        target_audience=brand_data.target_audience,
        tone_and_manner=brand_data.tone_and_manner,
        usp=brand_data.usp,
        keywords=brand_data.keywords,
        industry=brand_data.industry,
    )
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


async def get_brand(db: AsyncSession, brand_id: str) -> Optional[Brand]:
    """
    Retrieve a brand by ID with its products.

    Args:
        db: Async database session
        brand_id: UUID string of the brand to retrieve

    Returns:
        Brand model instance with products loaded, or None if not found
    """
    stmt = (
        select(Brand)
        .options(selectinload(Brand.products))
        .where(Brand.id == brand_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_brands(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[BrandSummary]:
    """
    List all brands with pagination and product counts.

    Args:
        db: Async database session
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return

    Returns:
        List of BrandSummary schemas with product_count calculated
    """
    # Subquery to count products per brand
    product_count_subq = (
        select(Product.brand_id, func.count(Product.id).label("product_count"))
        .group_by(Product.brand_id)
        .subquery()
    )

    # Main query with left join for product count
    stmt = (
        select(
            Brand,
            func.coalesce(product_count_subq.c.product_count, 0).label("product_count"),
        )
        .outerjoin(product_count_subq, Brand.id == product_count_subq.c.brand_id)
        .order_by(Brand.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Convert to BrandSummary schemas
    summaries = []
    for brand, product_count in rows:
        summaries.append(
            BrandSummary(
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
                product_count=product_count,
            )
        )

    return summaries


async def update_brand(
    db: AsyncSession, brand_id: str, update_data: BrandUpdate
) -> Optional[Brand]:
    """
    Update an existing brand.

    Args:
        db: Async database session
        brand_id: UUID string of the brand to update
        update_data: Brand update schema with optional fields

    Returns:
        Updated Brand model instance, or None if not found
    """
    stmt = select(Brand).where(Brand.id == brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if brand is None:
        return None

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(brand, field, value)

    await db.commit()
    await db.refresh(brand)
    return brand


async def delete_brand(db: AsyncSession, brand_id: str) -> bool:
    """
    Delete a brand by ID.

    Cascade deletion will automatically remove associated products.

    Args:
        db: Async database session
        brand_id: UUID string of the brand to delete

    Returns:
        True if brand was deleted, False if not found
    """
    stmt = select(Brand).where(Brand.id == brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if brand is None:
        return False

    await db.delete(brand)
    await db.commit()
    return True
