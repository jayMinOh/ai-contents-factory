"""Change thumbnail_url column from TEXT to MEDIUMTEXT.

This migration addresses the 65KB size limitation of MySQL TEXT type.
Large base64-encoded images or lengthy URLs may exceed this limit.
MEDIUMTEXT supports up to 16MB, which is sufficient for base64 images.

Revision ID: 5ed583cbafa1
Revises: df6fa7991040
Create Date: 2025-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '5ed583cbafa1'
down_revision: Union[str, None] = 'df6fa7991040'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade thumbnail_url from TEXT (65KB) to MEDIUMTEXT (16MB).

    This change allows storing larger base64-encoded images directly
    in the thumbnail_url field without hitting MySQL's TEXT size limit.
    """
    op.execute('ALTER TABLE reference_analyses MODIFY COLUMN thumbnail_url MEDIUMTEXT')


def downgrade() -> None:
    """Revert thumbnail_url from MEDIUMTEXT back to TEXT.

    WARNING: This downgrade may cause data truncation if any thumbnail_url
    values exceed 65KB. Data loss may occur for large base64 images.
    """
    op.alter_column(
        'reference_analyses',
        'thumbnail_url',
        existing_type=sa.Text(),
        type_=sa.Text(),
        mysql_modify_type='TEXT',
        existing_nullable=True
    )
