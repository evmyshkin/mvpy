"""Добавить ролевую модель в систему

Revision ID: 2026_02_07_add_role_model
Revises: 2026_02_06_add_blacklisted_tokens
Create Date: 2026-02-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2026_02_07_add_role_model'
down_revision: str | None = '8ab4b6559839'  # 2026_02_06_add_blacklisted_tokens
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Создать таблицу roles, добавить role_id в users, вставить seed data."""

    # 1. Создать таблицу roles
    op.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)

    # 2. Вставить seed data для ролей (idempotent)
    op.execute("""
        INSERT INTO roles (id, name, description)
        VALUES
            (1, 'user', 'Обычный пользователь системы'),
            (2, 'manager', 'Менеджер с расширенными правами'),
            (3, 'admin', 'Администратор системы')
        ON CONFLICT (id) DO NOTHING;
    """)

    # 3. Добавить колонку role_id в users таблицу
    op.add_column(
        'users',
        sa.Column(
            'role_id',
            sa.Integer(),
            nullable=True,  # Временно nullable для существующих пользователей
        ),
    )

    # 4. Создать FOREIGN KEY constraint
    op.create_foreign_key(
        'fk_users_role_id',
        'users',
        'roles',
        ['role_id'],
        ['id'],
    )

    # 5. Обновить существующих пользователей: присвоить роль "user" (id=1)
    op.execute("""
        UPDATE users
        SET role_id = 1
        WHERE role_id IS NULL;
    """)

    # 6. Сделать role_id NOT NULL после присвоения ролей
    op.alter_column(
        'users',
        'role_id',
        nullable=False,
    )


def downgrade() -> None:
    """Откатить изменения: удалить role_id из users, удалить таблицу roles."""

    # 1. Удалить FOREIGN KEY constraint
    op.drop_constraint('fk_users_role_id', 'users', type_='foreignkey')

    # 2. Удалить колонку role_id из users
    op.drop_column('users', 'role_id')

    # 3. Удалить таблицу roles
    op.execute('DROP TABLE IF EXISTS roles;')
