"""add_embedding_columns_to_resumes_and_jobs

Revision ID: c4f2a8b31e9d
Revises: b91c3d4e2a7f
Create Date: 2026-09-16 14:00:00.000000

Adds JSON embedding columns to resumes and jobs tables for semantic similarity
scoring.  Also adds a text_hash column so the get-or-generate pattern can
detect when the underlying text has actually changed and avoid unnecessary
re-encoding.

Columns added:
  resumes:
    - embedding      JSON NULL  — serialised float vector from SentenceTransformer
    - embedding_hash TEXT NULL  — SHA-256 of extracted_text; used for cache invalidation

  jobs:
    - embedding      JSON NULL  — serialised float vector from SentenceTransformer
    - embedding_hash TEXT NULL  — SHA-256 of title + description; used for cache invalidation

All columns are nullable so existing rows are fully unaffected.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c4f2a8b31e9d"
down_revision = "b91c3d4e2a7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- resumes ---
    op.add_column(
        "resumes",
        sa.Column("embedding", sa.JSON(), nullable=True),
    )
    op.add_column(
        "resumes",
        sa.Column("embedding_hash", sa.Text(), nullable=True),
    )

    # --- jobs ---
    op.add_column(
        "jobs",
        sa.Column("embedding", sa.JSON(), nullable=True),
    )
    op.add_column(
        "jobs",
        sa.Column("embedding_hash", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("jobs", "embedding_hash")
    op.drop_column("jobs", "embedding")
    op.drop_column("resumes", "embedding_hash")
    op.drop_column("resumes", "embedding")
