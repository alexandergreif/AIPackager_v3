"""Add fields for pipeline state recovery

Revision ID: 24d29e869d63
Revises: 88cc2c77fd7d
Create Date: 2025-06-29 11:06:20.128530

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "24d29e869d63"
down_revision: Union[str, Sequence[str], None] = "88cc2c77fd7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("packages", sa.Column("instruction_result", sa.JSON(), nullable=True))
    op.add_column("packages", sa.Column("rag_documentation", sa.Text(), nullable=True))
    op.add_column("packages", sa.Column("initial_script", sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("packages", "initial_script")
    op.drop_column("packages", "rag_documentation")
    op.drop_column("packages", "instruction_result")
    # ### end Alembic commands ###
