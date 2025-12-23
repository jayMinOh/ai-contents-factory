"""add_image_project_and_generated_image_tables

Revision ID: c461c97b2ba5
Revises: 5ed583cbafa1
Create Date: 2025-12-22 08:42:48.077964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'c461c97b2ba5'
down_revision: Union[str, None] = '5ed583cbafa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables already exist in database (created manually or via previous migration)
    # This migration is just for version tracking
    pass


def downgrade() -> None:
    # Not dropping tables as they may contain data
    pass
