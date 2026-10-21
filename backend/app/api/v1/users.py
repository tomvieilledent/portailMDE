import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, SessionDep, require_permission, require_super_admin
from app.core.permissions import Permission
from app.schemas.common import Page
from app.schemas.user import (
    CompanyAdminUpdate,
    PasswordChange,
    RoleUpdate,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services import users as service

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=Page[UserRead],
    dependencies=[Depends(require_permission(Permission.MANAGE_USERS))],
)
def list_users(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
):
    items, total = service.list_users(session, limit=limit, offset=offset, search=search)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, session: SessionDep, current: CurrentUser):
    return service.create_user(session, current, body)


@router.get("/me", response_model=UserRead)
def read_me(current: CurrentUser):
    return current


@router.patch("/me", response_model=UserRead)
def update_me(body: UserUpdate, session: SessionDep, current: CurrentUser):
    return service.update_profile(session, current, body)


@router.post("/me/password", status_code=204)
def change_my_password(body: PasswordChange, session: SessionDep, current: CurrentUser):
    service.change_password(session, current, body.current_password, body.new_password)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: uuid.UUID, session: SessionDep, _: CurrentUser):
    return service.get_user(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, body: UserUpdate, session: SessionDep, current: CurrentUser):
    return service.update_user(session, current, user_id, body)


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.set_active(session, current, user_id, False)


@router.post("/{user_id}/reactivate", response_model=UserRead)
def reactivate_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.set_active(session, current, user_id, True)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    service.delete_user(session, current, user_id)
    return Response(status_code=204)


@router.put("/{user_id}/role", response_model=UserRead, dependencies=[Depends(require_super_admin)])
def set_role(user_id: uuid.UUID, body: RoleUpdate, session: SessionDep):
    return service.set_role(session, user_id, body)


@router.put("/{user_id}/company-admin", response_model=UserRead)
def set_company_admin(
    user_id: uuid.UUID, body: CompanyAdminUpdate, session: SessionDep, current: CurrentUser
):
    return service.set_company_admin(session, current, user_id, body.is_company_admin)
