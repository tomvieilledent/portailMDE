import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import CompanyKind


class CompanyBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    logo_path: str | None


class PersonCard(BaseModel):
    """Fiche trombinoscope d'une personne."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str | None
    last_name: str | None
    job_title: str | None
    email: str
    phone: str | None
    avatar_path: str | None
    business_card_path: str | None
    company: CompanyBrief | None


class CompanyCard(BaseModel):
    """Fiche annuaire d'une entreprise."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    location: str | None
    website_url: str | None
    logo_path: str | None
    kind: CompanyKind
    member_count: int
