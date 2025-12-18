"""
Services module for the AI Video Marketing Platform.

This module exports all service functions for easy imports throughout the application.
"""

from app.services.brand_service import (
    create_brand,
    delete_brand,
    get_brand,
    list_brands,
    update_brand,
)
from app.services.product_service import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)

__all__ = [
    # Brand service functions
    "create_brand",
    "get_brand",
    "list_brands",
    "update_brand",
    "delete_brand",
    # Product service functions
    "create_product",
    "get_product",
    "list_products",
    "update_product",
    "delete_product",
]
