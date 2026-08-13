"""add rag trace

Revision ID: d4a7b9c2e1f0
Revises: b8f3c2a6d9e1
Create Date: 2026-08-13 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a7b9c2e1f0"
down_revision: Union[str, Sequence[str], None] = "b8f3c2a6d9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rag_trace",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("rewritten_query", sa.Text(), nullable=True),
        sa.Column("question_type", sa.String(length=50), nullable=True),
        sa.Column("used_knowledge", sa.String(length=10), nullable=False),
        sa.Column("expanded_queries", sa.Text(), nullable=True),
        sa.Column("retrieved_count", sa.Integer(), nullable=True),
        sa.Column("selected_sources", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversation.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rag_trace_conversation_id"),
        "rag_trace",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_rag_trace_user_id"),
        "rag_trace",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_rag_trace_user_id"),
        table_name="rag_trace",
    )
    op.drop_index(
        op.f("ix_rag_trace_conversation_id"),
        table_name="rag_trace",
    )
    op.drop_table("rag_trace")
