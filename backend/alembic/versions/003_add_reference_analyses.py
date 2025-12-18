"""Add reference_analyses table for storing video analysis results.

Revision ID: 003_reference_analyses
Revises: 002_cosmetics
Create Date: 2025-12-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_reference_analyses"
down_revision: Union[str, None] = "002_cosmetics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reference_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_url", sa.String(1000), nullable=False),
        sa.Column("title", sa.String(255), nullable=False, index=True),
        sa.Column(
            "brand_id",
            sa.String(36),
            sa.ForeignKey("brands.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        # Analysis results (JSON)
        sa.Column("segments", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("hook_points", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("edge_points", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("emotional_triggers", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("pain_points", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("application_points", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("selling_points", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("cta_analysis", sa.JSON, nullable=True),
        sa.Column("structure_pattern", sa.JSON, nullable=True),
        sa.Column("recommendations", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("transcript", sa.Text, nullable=True),
        # User metadata
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Composite index for common query pattern
    op.create_index(
        "ix_reference_analyses_brand_status",
        "reference_analyses",
        ["brand_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_reference_analyses_brand_status", table_name="reference_analyses")
    op.drop_table("reference_analyses")
