"""Initial brands and products tables

Revision ID: 001_initial
Revises:
Create Date: 2025-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create brands table
    op.create_table(
        "brands",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("target_audience", sa.String(500), nullable=True),
        sa.Column("tone_and_manner", sa.String(100), nullable=True),
        sa.Column("usp", sa.Text(), nullable=True),
        sa.Column("keywords", mysql.JSON(), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Create index on brands.name
    op.create_index("ix_brands_name", "brands", ["name"])

    # Create products table
    op.create_table(
        "products",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("brand_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("features", mysql.JSON(), nullable=False),
        sa.Column("benefits", mysql.JSON(), nullable=False),
        sa.Column("price_range", sa.String(100), nullable=True),
        sa.Column("target_segment", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["brand_id"],
            ["brands.id"],
            name="fk_products_brand_id",
            ondelete="CASCADE",
        ),
    )

    # Create index on products.brand_id
    op.create_index("ix_products_brand_id", "products", ["brand_id"])


def downgrade() -> None:
    # Drop products table (drops indexes and foreign key automatically)
    op.drop_table("products")

    # Drop brands table (drops index automatically)
    op.drop_table("brands")
