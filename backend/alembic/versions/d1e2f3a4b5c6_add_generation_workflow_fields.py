"""add_generation_workflow_fields

Add generation workflow fields for step-by-step generation mode.
- GeneratedImage: approval_status, is_reference_image
- ImageProject: generation_mode, reference_image_id, current_slide

Revision ID: d1e2f3a4b5c6
Revises: c461c97b2ba5
Create Date: 2025-12-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c461c97b2ba5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to generated_images table
    op.add_column(
        'generated_images',
        sa.Column('approval_status', sa.String(20), nullable=False, server_default='pending')
    )
    op.add_column(
        'generated_images',
        sa.Column('is_reference_image', sa.Boolean(), nullable=False, server_default='0')
    )

    # Add new columns to image_projects table
    op.add_column(
        'image_projects',
        sa.Column('generation_mode', sa.String(20), nullable=False, server_default='bulk')
    )
    op.add_column(
        'image_projects',
        sa.Column('reference_image_id', sa.String(36), nullable=True)
    )
    op.add_column(
        'image_projects',
        sa.Column('current_slide', sa.Integer(), nullable=False, server_default='1')
    )

    # Add foreign key constraint for reference_image_id
    op.create_foreign_key(
        'fk_image_projects_reference_image',
        'image_projects',
        'generated_images',
        ['reference_image_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for approval_status on generated_images
    op.create_index(
        'ix_generated_images_approval_status',
        'generated_images',
        ['image_project_id', 'approval_status']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_generated_images_approval_status', table_name='generated_images')

    # Drop foreign key constraint
    op.drop_constraint('fk_image_projects_reference_image', 'image_projects', type_='foreignkey')

    # Drop columns from image_projects
    op.drop_column('image_projects', 'current_slide')
    op.drop_column('image_projects', 'reference_image_id')
    op.drop_column('image_projects', 'generation_mode')

    # Drop columns from generated_images
    op.drop_column('generated_images', 'is_reference_image')
    op.drop_column('generated_images', 'approval_status')
