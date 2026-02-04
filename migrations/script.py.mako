"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    schema_upgrades()
    data_upgrades()


def downgrade() -> None:
    data_downgrades()
    schema_downgrades()


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    ${upgrades if upgrades else "pass"}


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    ${downgrades if downgrades else "pass"}


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
