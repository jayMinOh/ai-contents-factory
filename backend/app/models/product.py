"""
Product ORM model for the AI Video Marketing Platform.

Represents a cosmetics product entity associated with a brand, including
ingredients, skin compatibility, texture attributes, and certifications.
Optimized for AI-powered marketing video script generation.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.brand import Brand


class Product(Base, TimestampMixin):
    """
    Product model representing a cosmetics item under a brand.

    MVP Fields (Phase 1):
        - Basic: id, brand_id, name, description, price_range, target_segment
        - Cosmetics: product_category, key_ingredients, suitable_skin_types,
                    skin_concerns, texture_type, finish_type
        - Legacy: features, benefits (kept for backward compatibility)

    Ingredient Structure (key_ingredients JSON):
        [
            {
                "name": "Niacinamide",
                "name_ko": "나이아신아마이드",
                "effect": "Brightening and pore minimizing",
                "category": "brightening",
                "concentration": "5%",
                "is_hero": true
            }
        ]

    Future Fields (Phase 2+):
        - absorption_speed, scent_profile, sensory_description
        - certifications, clinical_results
        - usage_instructions, recommended_routine_step, volume_ml
    """

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    brand_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # ========== Product Image ==========
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to product image (local or remote)",
    )

    image_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated description of product appearance for image generation",
    )

    # ========== Cosmetics Category ==========
    product_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="serum, cream, toner, essence, oil, mask, cleanser, sunscreen, moisturizer, etc.",
    )

    # ========== Key Ingredients (MVP) ==========
    key_ingredients: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="[{name, name_ko, effect, category, concentration, is_hero}]",
    )

    # ========== Skin Compatibility (MVP) ==========
    suitable_skin_types: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="dry, oily, combination, normal, sensitive, all",
    )

    skin_concerns: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="acne, pores, wrinkles, dark_spots, dullness, redness, dryness, etc.",
    )

    # ========== Texture & Sensory (MVP) ==========
    texture_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="cream, gel, serum, oil, water, milk, balm, foam, etc.",
    )

    finish_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="matte, dewy, satin, natural, luminous, velvet, glossy",
    )

    # ========== Certifications & Clinical (Phase 2) ==========
    certifications: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="[{name, grade, details, badge_icon}]",
    )

    clinical_results: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="[{metric, result, test_period, sample_size, source}]",
    )

    # ========== Additional Info (Phase 2) ==========
    volume_ml: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Product size in milliliters",
    )

    # ========== Legacy Fields (Backward Compatibility) ==========
    features: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    benefits: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    price_range: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    target_segment: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Relationship: Many products belong to one brand
    brand: Mapped["Brand"] = relationship(
        "Brand",
        back_populates="products",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id!r}, name={self.name!r}, brand_id={self.brand_id!r})>"


__all__ = ["Product"]
