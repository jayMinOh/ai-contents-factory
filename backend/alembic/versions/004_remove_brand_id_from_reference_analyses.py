"""Remove brand_id from reference_analyses table.

Revision ID: 004_remove_brand_id
Revises: 003_reference_analyses
Create Date: 2025-12-11

Brand association will be handled at VideoProject level, not at ReferenceAnalysis level.
This allows reusing the same analysis for multiple brands/products.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_remove_brand_id"
down_revision: Union[str, None] = "003_reference_analyses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the brand_id index
    op.drop_index("ix_reference_analyses_brand_id", table_name="reference_analyses")
    # Drop the column
    op.drop_column("reference_analyses", "brand_id")


def downgrade() -> None:
    # Add the column back
    op.add_column(
        "reference_analyses",
        sa.Column("brand_id", sa.String(36), nullable=True),
    )
    # Re-create index
    op.create_index("ix_reference_analyses_brand_id", "reference_analyses", ["brand_id"])
