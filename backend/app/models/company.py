"""Modèle des entreprises (entreprises adhérentes, formateurs et partenaires)."""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CompanyKind


class Company(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Entreprise, formateur ou partenaire, avec ses membres."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    website_url: Mapped[str | None] = mapped_column(String(512))
    logo_path: Mapped[str | None] = mapped_column(String(512))
    kind: Mapped[CompanyKind] = mapped_column(
        String(20),
        nullable=False,
        default=CompanyKind.COMPANY,
        server_default=CompanyKind.COMPANY.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    members: Mapped[list["User"]] = relationship(back_populates="company")  # noqa: F821
