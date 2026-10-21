import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.core.errors import NotFoundError
from app.core.permissions import Permission
from app.models import User
from app.models.enums import CompanyKind
from app.schemas.common import Page
from app.schemas.company import CompanyAdminUpdate, CompanyCreate, CompanyRead
from app.schemas.user import UserRead
from app.services import companies as service

router = APIRouter(prefix="/companies", tags=["companies"])
ManageCompanies = Annotated[User, Depends(require_permission(Permission.MANAGE_COMPANIES))]


@router.get("", response_model=Page[CompanyRead])
def list_companies(
    session: SessionDep,
    current: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    kind: CompanyKind | None = None,
):
    items, total = service.list_companies(
        session, current, limit=limit, offset=offset, search=search, kind=kind
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(body: CompanyCreate, session: SessionDep, _: ManageCompanies):
    return service.create_company(session, body)


@router.get("/me", response_model=CompanyRead)
def my_company(session: SessionDep, current: CurrentUser):
    if not current.company_id:
        raise NotFoundError("Vous n'êtes rattaché à aucune entreprise")
    return service.get_company(session, current.company_id, current)


@router.get("/{company_id}", response_model=CompanyRead)
def read_company(company_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.get_company(session, company_id, current)


@router.patch("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: uuid.UUID, body: CompanyAdminUpdate, session: SessionDep, current: CurrentUser
):
    return service.update_company(session, current, company_id, body)


@router.post("/{company_id}/deactivate", response_model=CompanyRead)
def deactivate_company(company_id: uuid.UUID, session: SessionDep, current: ManageCompanies):
    return service.set_active(session, company_id, current, False)


@router.post("/{company_id}/reactivate", response_model=CompanyRead)
def reactivate_company(company_id: uuid.UUID, session: SessionDep, current: ManageCompanies):
    return service.set_active(session, company_id, current, True)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: uuid.UUID, session: SessionDep, current: ManageCompanies):
    service.delete_company(session, company_id, current)
    return Response(status_code=204)


@router.get("/{company_id}/members", response_model=list[UserRead])
def list_members(company_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.list_members(session, company_id, current)


@router.put("/{company_id}/members/{user_id}", response_model=UserRead)
def add_member(
    company_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep, current: CurrentUser
):
    return service.add_member(session, current, company_id, user_id)


@router.delete("/{company_id}/members/{user_id}", status_code=204)
def remove_member(
    company_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep, current: CurrentUser
):
    service.remove_member(session, current, company_id, user_id)
    return Response(status_code=204)


@router.put("/{company_id}/logo", response_model=CompanyRead)
def upload_logo(company_id: uuid.UUID, session: SessionDep, current: CurrentUser, file: UploadFile):
    return service.set_logo(session, current, company_id, file)
