"""SQLAlchemy models for AIPackager v3."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Package(Base):
    """Package model representing uploaded installer files."""

    __tablename__ = "packages"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Timestamps
    upload_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        Enum("uploading", "processing", "completed", "failed", name="package_status"),
        default="uploading",
        nullable=False,
    )
    current_step: Mapped[str] = mapped_column(
        String(50), default="upload", nullable=False
    )
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # User input
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text)

    # 5-Stage Pipeline Results
    generated_script: Mapped[Optional[dict]] = mapped_column(JSON)
    hallucination_report: Mapped[Optional[dict]] = mapped_column(JSON)
    pipeline_metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    corrections_applied: Mapped[Optional[list]] = mapped_column(JSON)

    # Relationship to metadata
    package_metadata: Mapped[Optional["Metadata"]] = relationship(
        "Metadata",
        back_populates="package",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation of Package."""
        return f"Package(id={self.id!r}, filename={self.filename!r}, status={self.status!r})"


class Metadata(Base):
    """Metadata model for extracted installer information."""

    __tablename__ = "metadata"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign key to package
    package_id: Mapped[UUID] = mapped_column(ForeignKey("packages.id"), nullable=False)

    # MSI/EXE metadata fields
    product_name: Mapped[Optional[str]] = mapped_column(String(255))
    version: Mapped[Optional[str]] = mapped_column(String(50))
    publisher: Mapped[Optional[str]] = mapped_column(String(255))
    install_date: Mapped[Optional[str]] = mapped_column(String(50))
    uninstall_string: Mapped[Optional[str]] = mapped_column(String(500))
    estimated_size: Mapped[Optional[int]] = mapped_column(Integer)

    # Additional metadata fields
    product_code: Mapped[Optional[str]] = mapped_column(String(100))
    upgrade_code: Mapped[Optional[str]] = mapped_column(String(100))
    language: Mapped[Optional[str]] = mapped_column(String(50))
    architecture: Mapped[Optional[str]] = mapped_column(String(20))

    # Relationship to package
    package: Mapped["Package"] = relationship(
        "Package", back_populates="package_metadata"
    )

    def __repr__(self) -> str:
        """String representation of Metadata."""
        return f"Metadata(id={self.id!r}, product_name={self.product_name!r}, version={self.version!r})"
