"""support multiple model configs

Revision ID: e8c4d2f9a1b3
Revises: d4a7b9c2e1f0
Create Date: 2026-08-13 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8c4d2f9a1b3"
down_revision: Union[str, Sequence[str], None] = "d4a7b9c2e1f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_model_config",
        sa.Column("name", sa.String(length=100), nullable=False, server_default="模型配置"),
    )
    op.add_column(
        "user_model_config",
        sa.Column("is_default", sa.String(length=10), nullable=False, server_default="true"),
    )

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index in inspector.get_indexes("user_model_config"):
        if index.get("unique") and index.get("column_names") == ["user_id"]:
            op.drop_index(index["name"], table_name="user_model_config")
            break
    else:
        for constraint in inspector.get_unique_constraints("user_model_config"):
            if constraint.get("column_names") == ["user_id"]:
                op.drop_constraint(
                    constraint["name"],
                    "user_model_config",
                    type_="unique",
                )
                break


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_user_model_config_user_id",
        "user_model_config",
        ["user_id"],
    )
    op.drop_column("user_model_config", "is_default")
    op.drop_column("user_model_config", "name")
