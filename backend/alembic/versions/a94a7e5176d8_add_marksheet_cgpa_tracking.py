"""add marksheet cgpa tracking

Revision ID: a94a7e5176d8
Revises: c4f2a8b31e9d
Create Date: 2026-10-23 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a94a7e5176d8"
down_revision: Union[str, Sequence[str], None] = "c4f2a8b31e9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "marksheets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("stored_filename", sa.String(length=255), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("extracted_cgpa", sa.Float(), nullable=True),
        sa.Column("matched_label", sa.String(length=100), nullable=True),
        sa.Column("validation_score", sa.Float(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_marksheets_id"), "marksheets", ["id"], unique=False)
    op.create_index(op.f("ix_marksheets_student_id"), "marksheets", ["student_id"], unique=False)

    op.create_table(
        "student_cgpa_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("old_cgpa", sa.Float(), nullable=True),
        sa.Column("new_cgpa", sa.Float(), nullable=False),
        sa.Column("marksheet_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="MARKSHEET"),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["marksheet_id"], ["marksheets.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_student_cgpa_history_id"), "student_cgpa_history", ["id"], unique=False)
    op.create_index(op.f("ix_student_cgpa_history_student_id"), "student_cgpa_history", ["student_id"], unique=False)

    op.add_column("students", sa.Column("cgpa", sa.Float(), nullable=True))
    op.add_column("students", sa.Column("cgpa_source", sa.String(length=20), nullable=True))
    op.add_column("students", sa.Column("cgpa_verified_at", sa.DateTime(), nullable=True))
    op.add_column("students", sa.Column("current_marksheet_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_students_current_marksheet_id"), "students", ["current_marksheet_id"], unique=False)
    op.create_foreign_key(
        "fk_students_current_marksheet_id_marksheets",
        "students",
        "marksheets",
        ["current_marksheet_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        sa.text(
            "UPDATE students SET cgpa_source = 'LEGACY' WHERE cgpa IS NOT NULL AND cgpa_source IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_constraint("fk_students_current_marksheet_id_marksheets", "students", type_="foreignkey")
    op.drop_index(op.f("ix_students_current_marksheet_id"), table_name="students")
    op.drop_column("students", "current_marksheet_id")
    op.drop_column("students", "cgpa_verified_at")
    op.drop_column("students", "cgpa_source")
    op.drop_column("students", "cgpa")

    op.drop_index(op.f("ix_student_cgpa_history_student_id"), table_name="student_cgpa_history")
    op.drop_index(op.f("ix_student_cgpa_history_id"), table_name="student_cgpa_history")
    op.drop_table("student_cgpa_history")

    op.drop_index(op.f("ix_marksheets_student_id"), table_name="marksheets")
    op.drop_index(op.f("ix_marksheets_id"), table_name="marksheets")
    op.drop_table("marksheets")
