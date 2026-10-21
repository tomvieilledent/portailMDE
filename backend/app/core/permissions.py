"""Rôles et permissions de la plateforme.

- ``super_admin`` : toutes les permissions.
- ``staff`` : sous-ensemble explicite de :class:`Permission` (champ ``users.permissions``).
- ``member`` : aucune permission globale ; peut administrer sa propre entreprise
  s'il est ``is_company_admin``.
"""

import enum
import uuid

from app.models.enums import UserRole
from app.models.user import User


class Permission(enum.StrEnum):
    """Permissions globales attribuables au personnel (staff)."""

    MANAGE_COMPANIES = "manage_companies"
    MANAGE_USERS = "manage_users"
    MANAGE_TRAININGS = "manage_trainings"
    MANAGE_NEWS = "manage_news"


def validate_permissions(values: list[str] | None) -> list[str]:
    """Normalise une liste de permissions (dédoublonnée, ordre conservé).

    Lève ``ValueError`` si une clé est inconnue.
    """
    cleaned: list[str] = []
    for value in values or []:
        key = value.strip()
        if key not in Permission._value2member_map_:
            raise ValueError(f"Permission inconnue : {value!r}")
        if key not in cleaned:
            cleaned.append(key)
    return cleaned


def has_permission(user: User, permission: Permission) -> bool:
    """Indique si l'utilisateur détient la permission (le super administrateur les a toutes)."""
    if user.role == UserRole.SUPER_ADMIN:
        return True
    return user.role == UserRole.STAFF and permission.value in (user.permissions or [])


def is_staff_or_above(user: User) -> bool:
    """Indique si l'utilisateur est membre du personnel ou super administrateur."""
    return user.role in (UserRole.SUPER_ADMIN, UserRole.STAFF)


def can_manage_company(user: User, company_id: uuid.UUID | None) -> bool:
    """Vrai pour qui gère les entreprises, ou pour l'admin de cette entreprise."""
    if has_permission(user, Permission.MANAGE_COMPANIES):
        return True
    return bool(
        company_id and user.is_company_admin and user.company_id and user.company_id == company_id
    )
