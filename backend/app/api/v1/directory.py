"""Routes de l'annuaire : recherche de personnes et d'entreprises."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import CompanyKind
from app.schemas.common import Page
from app.schemas.directory import CompanyCard, PersonCard
from app.services import directory as service

router = APIRouter(prefix="/directory", tags=["directory"])


@router.get("/people", response_model=Page[PersonCard])
def people(
    session: SessionDep,
    _: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    company_id: uuid.UUID | None = None,
):
    """Recherche des personnes dans l'annuaire."""
    items, total = service.search_people(
        session, limit=limit, offset=offset, search=search, company_id=company_id
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/companies", response_model=Page[CompanyCard])
def companies(
    session: SessionDep,
    _: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    kind: CompanyKind | None = None,
):
    """Recherche des entreprises dans l'annuaire."""
    items, total = service.search_companies(
        session, limit=limit, offset=offset, search=search, kind=kind
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
