"""add image model to model config

Revision ID: f2b7a6c9d4e1
Revises: e8c4d2f9a1b3
Create Date: 2026-08-15 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b7a6c9d4e1"
down_revision: Union[str, Sequence[str], None] = "e8c4d2f9a1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_model_config",
        sa.Column("image_model", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_model_config", "image_model")
