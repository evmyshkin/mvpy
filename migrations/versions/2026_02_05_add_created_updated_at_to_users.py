"""add_created_updated_at_to_users

Revision ID: 77ca4a3c8afb
Revises: 59be4b661082
Create Date: 2026-02-05 16:45:55.961379

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '77ca4a3c8afb'
down_revision: str | Sequence[str] | None = '59be4b661082'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    schema_upgrades()
    data_upgrades()


def downgrade() -> None:
    data_downgrades()
    schema_downgrades()


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    op.add_column(
        'users',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=False,
        ),
    )


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')


VAL_1 = 'some_val'
VAL_2 = 'another_val'


def data_upgrades() -> None:
    """Optional data upgrades."""
    # op.execute(
    #         sa.text("""
    #         INSERT INTO <table_name> (<column_1>, <column_2>)
    #         VALUES (:val_1, :val_2)
    #         ON CONFLICT (<column_1>) DO NOTHING
    #     """).bindparams(val_1=VAL_1, val_2=VAL_2)
    # )
    pass


def data_downgrades() -> None:
    """Optional data downgrades."""
    # op.execute(
    #         sa.text("""
    #         DELETE FROM <table_name>
    #         WHERE <column_1> = :val_1 AND <column_2> = :val_2
    #     """).bindparams(val_1=VAL_1, val_2=VAL_2)
    # )
    pass
