"""Add executable_names column to Metadata

Revision ID: ff1e00581431
Revises: 206456dfa91c
Create Date: 2025-07-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff1e00581431"
down_revision: Union[str, Sequence[str], None] = "206456dfa91c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "metadata",
        sa.Column("executable_names", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("metadata", "executable_names")
