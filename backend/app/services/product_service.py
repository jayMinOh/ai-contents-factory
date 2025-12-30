"""
Product Service Layer for the AI Video Marketing Platform.

Provides CRUD operations for Product entities using SQLAlchemy 2.0 async patterns.
All operations verify brand ownership for data integrity.
"""

import uuid
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Brand, Product
from app.schemas.brand import ProductCreate, ProductUpdate


async def create_product(
    db: AsyncSession, brand_id: str, product_data: ProductCreate
) -> Optional[Product]:
    """
    Create a new product under a brand.

    Args:
        db: Async database session
        brand_id: UUID string of the parent brand
        product_data: Product creation schema with required fields

    Returns:
        Newly created Product model instance, or None if brand not found
    """
    # Verify brand exists
    stmt = select(Brand).where(Brand.id == brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if brand is None:
        return None

    # Convert Pydantic models to dicts for JSON storage
    key_ingredients_data = [
        ing.model_dump() if hasattr(ing, 'model_dump') else ing
        for ing in (product_data.key_ingredients or [])
    ]
    certifications_data = [
        cert.model_dump() if hasattr(cert, 'model_dump') else cert
        for cert in (product_data.certifications or [])
    ]
    clinical_results_data = [
        cr.model_dump() if hasattr(cr, 'model_dump') else cr
        for cr in (product_data.clinical_results or [])
    ]
    # Convert enum values to strings
    suitable_skin_types_data = [
        st.value if hasattr(st, 'value') else st
        for st in (product_data.suitable_skin_types or [])
    ]
    skin_concerns_data = [
        sc.value if hasattr(sc, 'value') else sc
        for sc in (product_data.skin_concerns or [])
    ]

    product = Product(
        id=str(uuid.uuid4()),
        brand_id=brand_id,
        name=product_data.name,
        description=product_data.description,
        # Cosmetics fields
        product_category=product_data.product_category.value if product_data.product_category else None,
        key_ingredients=key_ingredients_data,
        suitable_skin_types=suitable_skin_types_data,
        skin_concerns=skin_concerns_data,
        texture_type=product_data.texture_type.value if product_data.texture_type else None,
        finish_type=product_data.finish_type.value if product_data.finish_type else None,
        certifications=certifications_data,
        clinical_results=clinical_results_data,
        volume_ml=product_data.volume_ml,
        # Legacy fields
        features=product_data.features,
        benefits=product_data.benefits,
        price_range=product_data.price_range,
        target_segment=product_data.target_segment,
    )
    db.add(product)
    await db.commit()
    # Re-query to get database-generated fields (created_at, updated_at)
    # instead of using refresh() which can trigger lazy loading in async context
    stmt = select(Product).where(Product.id == product.id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_product(
    db: AsyncSession, brand_id: str, product_id: str
) -> Optional[Product]:
    """
    Retrieve a product by ID, verifying it belongs to the specified brand.

    Args:
        db: Async database session
        brand_id: UUID string of the parent brand
        product_id: UUID string of the product to retrieve

    Returns:
        Product model instance, or None if not found or wrong brand
    """
    stmt = select(Product).where(
        and_(Product.id == product_id, Product.brand_id == brand_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_products(db: AsyncSession, brand_id: str) -> list[Product]:
    """
    List all products for a specific brand.

    Args:
        db: Async database session
        brand_id: UUID string of the parent brand

    Returns:
        List of Product model instances belonging to the brand
    """
    stmt = (
        select(Product)
        .where(Product.brand_id == brand_id)
        .order_by(Product.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_product(
    db: AsyncSession, brand_id: str, product_id: str, update_data: ProductUpdate
) -> Optional[Product]:
    """
    Update an existing product, verifying brand ownership.

    Args:
        db: Async database session
        brand_id: UUID string of the parent brand
        product_id: UUID string of the product to update
        update_data: Product update schema with optional fields

    Returns:
        Updated Product model instance, or None if not found or wrong brand
    """
    stmt = select(Product).where(
        and_(Product.id == product_id, Product.brand_id == brand_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        return None

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(product, field, value)

    await db.commit()
    # Re-query to get updated timestamp instead of using refresh()
    # which can trigger lazy loading in async context
    stmt = select(Product).where(Product.id == product_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def delete_product(db: AsyncSession, brand_id: str, product_id: str) -> bool:
    """
    Delete a product by ID, verifying brand ownership.

    Args:
        db: Async database session
        brand_id: UUID string of the parent brand
        product_id: UUID string of the product to delete

    Returns:
        True if product was deleted, False if not found or wrong brand
    """
    stmt = select(Product).where(
        and_(Product.id == product_id, Product.brand_id == brand_id)
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if product is None:
        return False

    await db.delete(product)
    await db.commit()
    return True
