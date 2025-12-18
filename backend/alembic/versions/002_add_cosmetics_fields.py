"""Add cosmetics-specific fields to products table

Revision ID: 002_cosmetics
Revises: 001_initial
Create Date: 2025-12-11

This migration adds fields for cosmetics products:
- product_category: Product type (serum, cream, toner, etc.)
- key_ingredients: JSON array of ingredient objects with name, effect, category
- suitable_skin_types: JSON array of skin types (dry, oily, etc.)
- skin_concerns: JSON array of skin concerns (acne, wrinkles, etc.)
- texture_type: Product texture (cream, gel, serum, etc.)
- finish_type: After-application finish (matte, dewy, etc.)
- certifications: JSON array of certification objects
- clinical_results: JSON array of clinical test results
- volume_ml: Product size in milliliters
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "002_cosmetics"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add cosmetics category
    op.add_column(
        "products",
        sa.Column("product_category", sa.String(50), nullable=True),
    )
    op.create_index("ix_products_product_category", "products", ["product_category"])

    # Add key ingredients (MVP)
    op.add_column(
        "products",
        sa.Column(
            "key_ingredients",
            mysql.JSON(),
            nullable=False,
            server_default="[]",
            comment="[{name, name_ko, effect, category, concentration, is_hero}]",
        ),
    )

    # Add skin compatibility (MVP)
    op.add_column(
        "products",
        sa.Column(
            "suitable_skin_types",
            mysql.JSON(),
            nullable=False,
            server_default="[]",
            comment="dry, oily, combination, normal, sensitive, all",
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "skin_concerns",
            mysql.JSON(),
            nullable=False,
            server_default="[]",
            comment="acne, pores, wrinkles, dark_spots, dullness, etc.",
        ),
    )

    # Add texture & sensory (MVP)
    op.add_column(
        "products",
        sa.Column(
            "texture_type",
            sa.String(50),
            nullable=True,
            comment="cream, gel, serum, oil, water, milk, balm, foam, etc.",
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "finish_type",
            sa.String(50),
            nullable=True,
            comment="matte, dewy, satin, natural, luminous, velvet, glossy",
        ),
    )

    # Add certifications & clinical (Phase 2)
    op.add_column(
        "products",
        sa.Column(
            "certifications",
            mysql.JSON(),
            nullable=False,
            server_default="[]",
            comment="[{name, grade, details, badge_icon}]",
        ),
    )

    op.add_column(
        "products",
        sa.Column(
            "clinical_results",
            mysql.JSON(),
            nullable=False,
            server_default="[]",
            comment="[{metric, result, test_period, sample_size, source}]",
        ),
    )

    # Add volume
    op.add_column(
        "products",
        sa.Column(
            "volume_ml",
            sa.Integer(),
            nullable=True,
            comment="Product size in milliliters",
        ),
    )


def downgrade() -> None:
    # Remove all added columns in reverse order
    op.drop_column("products", "volume_ml")
    op.drop_column("products", "clinical_results")
    op.drop_column("products", "certifications")
    op.drop_column("products", "finish_type")
    op.drop_column("products", "texture_type")
    op.drop_column("products", "skin_concerns")
    op.drop_column("products", "suitable_skin_types")
    op.drop_column("products", "key_ingredients")
    op.drop_index("ix_products_product_category", table_name="products")
    op.drop_column("products", "product_category")
