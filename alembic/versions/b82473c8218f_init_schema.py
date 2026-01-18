"""Init schema

Revision ID: b82473c8218f
Revises:
Create Date: 2026-01-13 21:17:04.194980

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b82473c8218f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Таблица USERS
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("custom_countries", sa.String(), nullable=True),
        sa.Column("config_limit", sa.Integer(), nullable=False, server_default="10"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # 2. Таблица RAW_CONFIGS (Сырые данные)
    op.create_table(
        "raw_configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("full_link", sa.Text(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 3. Таблица CONFIGS (Готовые ключи)
    # Полностью соответствует модели из models/config.py
    op.create_table(
        "configs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        # Основные данные идентификации
        sa.Column("uuid", sa.String(), nullable=False),
        sa.Column("link", sa.Text(), nullable=False),
        # Метаданные
        sa.Column("name", sa.String(), nullable=True, server_default="NoName"),
        sa.Column("source", sa.String(), nullable=True, server_default="unknown"),
        # Сетевые параметры
        sa.Column("host", sa.String(), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("protocol", sa.String(), nullable=True, server_default="vless"),
        sa.Column("security", sa.String(), nullable=True, server_default="none"),
        sa.Column("sni", sa.String(), nullable=True),
        # Статистика и Гео
        sa.Column("ping", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("flag", sa.String(), nullable=True),
        sa.Column("tier", sa.Integer(), nullable=True, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Индексы для скорости (как в модели)
    op.create_index(op.f("ix_configs_uuid"), "configs", ["uuid"], unique=True)
    op.create_index(op.f("ix_configs_country"), "configs", ["country"], unique=False)
    op.create_index(op.f("ix_configs_ping"), "configs", ["ping"], unique=False)
    op.create_index(op.f("ix_configs_tier"), "configs", ["tier"], unique=False)
    # Составной индекс для меню
    op.create_index("ix_configs_tier_ping", "configs", ["tier", "ping"])


def downgrade() -> None:
    op.drop_index("ix_configs_tier_ping", table_name="configs")
    op.drop_index(op.f("ix_configs_tier"), table_name="configs")
    op.drop_index(op.f("ix_configs_ping"), table_name="configs")
    op.drop_index(op.f("ix_configs_country"), table_name="configs")
    op.drop_index(op.f("ix_configs_uuid"), table_name="configs")
    op.drop_table("configs")
    op.drop_table("raw_configs")
    op.drop_table("users")
