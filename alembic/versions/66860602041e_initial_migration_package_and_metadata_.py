"""Initial migration: Package and Metadata models

Revision ID: 66860602041e
Revises:
Create Date: 2025-06-22 19:35:40.193845

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "66860602041e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("upload_time", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "uploading", "processing", "completed", "failed", name="package_status"
            ),
            nullable=False,
        ),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "metadata",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("publisher", sa.String(length=255), nullable=True),
        sa.Column("install_date", sa.String(length=50), nullable=True),
        sa.Column("uninstall_string", sa.String(length=500), nullable=True),
        sa.Column("estimated_size", sa.Integer(), nullable=True),
        sa.Column("product_code", sa.String(length=100), nullable=True),
        sa.Column("upgrade_code", sa.String(length=100), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=True),
        sa.Column("architecture", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(
            ["package_id"],
            ["packages.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("metadata")
    op.drop_table("packages")
    # ### end Alembic commands ###
