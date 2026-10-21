"""Routes des utilisateurs : profil, gestion des comptes, rôles, avatar et carte de visite."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, UploadFile

from app.api.deps import (
    CurrentUser,
    PendingUser,
    SessionDep,
    require_permission,
    require_super_admin,
)
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
    """Liste les utilisateurs avec pagination et recherche (gestion des utilisateurs requise)."""
    items, total = service.list_users(session, limit=limit, offset=offset, search=search)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, session: SessionDep, current: CurrentUser):
    """Crée un utilisateur."""
    return service.create_user(session, current, body)


@router.get("/me", response_model=UserRead)
def read_me(current: PendingUser):
    """Retourne le profil de l'utilisateur courant."""
    return current


@router.patch("/me", response_model=UserRead)
def update_me(body: UserUpdate, session: SessionDep, current: CurrentUser):
    """Met à jour le profil de l'utilisateur courant."""
    return service.update_profile(session, current, body)


@router.post("/me/password", status_code=204)
def change_my_password(body: PasswordChange, session: SessionDep, current: PendingUser):
    """Change le mot de passe de l'utilisateur courant."""
    service.change_password(session, current, body.current_password, body.new_password)
    return Response(status_code=204)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: uuid.UUID, session: SessionDep, _: CurrentUser):
    """Retourne le profil d'un utilisateur."""
    return service.get_user(session, user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, body: UserUpdate, session: SessionDep, current: CurrentUser):
    """Met à jour le profil d'un utilisateur."""
    return service.update_user(session, current, user_id, body)


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Désactive un compte utilisateur."""
    return service.set_active(session, current, user_id, False)


@router.post("/{user_id}/reactivate", response_model=UserRead)
def reactivate_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Réactive un compte utilisateur."""
    return service.set_active(session, current, user_id, True)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Supprime un compte utilisateur."""
    service.delete_user(session, current, user_id)
    return Response(status_code=204)


@router.put("/{user_id}/role", response_model=UserRead, dependencies=[Depends(require_super_admin)])
def set_role(user_id: uuid.UUID, body: RoleUpdate, session: SessionDep):
    """Définit le rôle et les permissions d'un utilisateur (super administrateur)."""
    return service.set_role(session, user_id, body)


@router.put("/{user_id}/company-admin", response_model=UserRead)
def set_company_admin(
    user_id: uuid.UUID, body: CompanyAdminUpdate, session: SessionDep, current: CurrentUser
):
    """Accorde ou retire le statut d'administrateur d'entreprise."""
    return service.set_company_admin(session, current, user_id, body.is_company_admin)


@router.put("/me/avatar", response_model=UserRead)
def upload_my_avatar(session: SessionDep, current: CurrentUser, file: UploadFile):
    """Téléverse l'avatar de l'utilisateur courant."""
    return service.set_image(session, current, current, "avatar_path", file, "avatars")


@router.put("/me/business-card", response_model=UserRead)
def upload_my_business_card(session: SessionDep, current: CurrentUser, file: UploadFile):
    """Téléverse la carte de visite de l'utilisateur courant."""
    return service.set_image(
        session, current, current, "business_card_path", file, "business-cards"
    )


@router.put("/{user_id}/avatar", response_model=UserRead)
def upload_avatar(user_id: uuid.UUID, session: SessionDep, current: CurrentUser, file: UploadFile):
    """Téléverse l'avatar d'un utilisateur."""
    target = service.get_user(session, user_id)
    return service.set_image(session, current, target, "avatar_path", file, "avatars")
