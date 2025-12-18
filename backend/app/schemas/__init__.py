"""
Schemas Package

This module exports all Pydantic schemas for easy imports throughout the application.
"""

from app.schemas.brand import (
    BrandBase,
    BrandCreate,
    BrandResponse,
    BrandSummary,
    BrandUpdate,
    ProductBase,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)

__all__ = [
    # Product schemas
    "ProductBase",
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    # Brand schemas
    "BrandBase",
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandSummary",
]
