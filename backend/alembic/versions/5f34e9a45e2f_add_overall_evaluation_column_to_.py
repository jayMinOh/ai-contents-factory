"""Add overall_evaluation column to reference_analyses

Revision ID: 5f34e9a45e2f
Revises: d1e2f3a4b5c6
Create Date: 2025-12-26 15:07:46.008747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f34e9a45e2f'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Only add overall_evaluation column
    op.add_column('reference_analyses', sa.Column('overall_evaluation', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('reference_analyses', 'overall_evaluation')
