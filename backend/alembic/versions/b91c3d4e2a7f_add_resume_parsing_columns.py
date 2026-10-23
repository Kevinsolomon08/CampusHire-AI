"""add_resume_parsing_columns

Revision ID: b91c3d4e2a7f
Revises: 467126217ffa
Create Date: 2026-09-16 13:30:00.000000

Adds parsed_data, extracted_text, parsing_status, and parsing_error columns
to the resumes table to support AI-powered resume parsing (Phase 2).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b91c3d4e2a7f'
down_revision: Union[str, Sequence[str], None] = '467126217ffa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add resume parsing columns to the resumes table."""
    op.add_column(
        'resumes',
        sa.Column('parsed_data', sa.JSON(), nullable=True),
    )
    op.add_column(
        'resumes',
        sa.Column('extracted_text', sa.Text(), nullable=True),
    )
    op.add_column(
        'resumes',
        sa.Column(
            'parsing_status',
            sa.String(length=20),
            nullable=True,
            server_default='pending',
        ),
    )
    op.add_column(
        'resumes',
        sa.Column('parsing_error', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove resume parsing columns from the resumes table."""
    op.drop_column('resumes', 'parsing_error')
    op.drop_column('resumes', 'parsing_status')
    op.drop_column('resumes', 'extracted_text')
    op.drop_column('resumes', 'parsed_data')
