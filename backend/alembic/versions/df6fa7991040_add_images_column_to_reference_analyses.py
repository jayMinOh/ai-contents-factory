"""add images column to reference_analyses

Revision ID: df6fa7991040
Revises: efe56902b152
Create Date: 2025-12-19 22:50:26.640479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = 'df6fa7991040'
down_revision: Union[str, None] = 'efe56902b152'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add images column with default empty array
    op.add_column('reference_analyses', sa.Column('images', sa.JSON(), nullable=True, server_default='[]'))

    # Update existing rows to have empty array
    op.execute("UPDATE reference_analyses SET images = '[]' WHERE images IS NULL")

    # Change thumbnail_url from VARCHAR(500) to TEXT for larger base64 images
    op.alter_column('reference_analyses', 'thumbnail_url',
               existing_type=mysql.VARCHAR(length=500),
               type_=sa.Text(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('reference_analyses', 'thumbnail_url',
               existing_type=sa.Text(),
               type_=mysql.VARCHAR(length=500),
               existing_nullable=True)
    op.drop_column('reference_analyses', 'images')
