"""add_interview_fields_round_interviewer_result

Revision ID: 467126217ffa
Revises: a34e25b2e31f
Create Date: 2026-09-15 13:54:12.876077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '467126217ffa'
down_revision: Union[str, Sequence[str], None] = 'a34e25b2e31f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # MySQL handles enums as column types, not separate types like PostgreSQL
    # Add new columns to interviews table with inline ENUM definitions
    op.add_column('interviews', sa.Column('round', sa.Enum('TECHNICAL', 'HR', 'MANAGERIAL', 'ASSESSMENT', 'OTHER', name='interviewround'), nullable=False, server_default='TECHNICAL'))
    op.add_column('interviews', sa.Column('interviewer', sa.String(length=255), nullable=True))
    op.add_column('interviews', sa.Column('result', sa.Enum('PENDING', 'PASSED', 'FAILED', 'NO_SHOW', name='interviewresult'), nullable=False, server_default='PENDING'))
    op.add_column('interviews', sa.Column('location_or_link', sa.String(length=500), nullable=True))
    op.add_column('interviews', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')))
    
    # Remove server defaults after column creation (so new inserts use app defaults)
    op.alter_column('interviews', 'round', server_default=None)
    op.alter_column('interviews', 'result', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove new columns (MySQL automatically drops inline ENUMs when column is dropped)
    op.drop_column('interviews', 'updated_at')
    op.drop_column('interviews', 'location_or_link')
    op.drop_column('interviews', 'result')
    op.drop_column('interviews', 'interviewer')
    op.drop_column('interviews', 'round')
