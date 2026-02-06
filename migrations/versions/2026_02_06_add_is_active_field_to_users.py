"""add is_active field to users

Revision ID: ddfae8adf79b
Revises: 77ca4a3c8afb
Create Date: 2026-02-06 13:03:12.079175

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ddfae8adf79b'
down_revision: str | Sequence[str] | None = '77ca4a3c8afb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    schema_upgrades()
    data_upgrades()


def downgrade() -> None:
    data_downgrades()
    schema_downgrades()


def schema_upgrades() -> None:
    """Добавить поле is_active в таблицу users."""
    op.add_column(
        'users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        ),
    )


def schema_downgrades() -> None:
    """Удалить поле is_active из таблицы users."""
    op.drop_column('users', 'is_active')


def data_upgrades() -> None:
    """Операции с данными не требуются."""
    pass


def data_downgrades() -> None:
    """Операции с данными не требуются."""
    pass
