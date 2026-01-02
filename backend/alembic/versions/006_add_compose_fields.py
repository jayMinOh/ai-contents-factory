"""Add compose fields to image_projects table.

Revision ID: 006_compose_fields
Revises: 005_add_users_table
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006_compose_fields"
down_revision = "005_add_users_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add compose_image_temp_ids column to image_projects table
    op.add_column(
        "image_projects",
        sa.Column("compose_image_temp_ids", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("image_projects", "compose_image_temp_ids")
