"""Schémas des entreprises."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CompanyKind


class CompanyRead(BaseModel):
    """Entreprise en lecture."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    location: str | None
    website_url: str | None
    logo_path: str | None
    kind: CompanyKind
    is_active: bool
    created_at: datetime


class CompanyCreate(BaseModel):
    """Création d'une entreprise."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    location: str | None = Field(None, max_length=200)
    website_url: str | None = Field(None, max_length=512)
    kind: CompanyKind = CompanyKind.COMPANY


class CompanyUpdate(BaseModel):
    """Modification partielle d'une entreprise."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    location: str | None = Field(None, max_length=200)
    website_url: str | None = Field(None, max_length=512)


class CompanyAdminUpdate(CompanyUpdate):
    """Champs réservés aux gestionnaires d'entreprises."""

    kind: CompanyKind | None = None
