import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import Permission, can_manage_company, has_permission
from app.core.security import hash_password, verify_password
from app.models import Company, User
from app.models.enums import UserRole
from app.services import storage


def get_user(session: Session, user_id: uuid.UUID) -> User:
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError("Utilisateur introuvable")
    return user


def list_users(
    session: Session, *, limit: int, offset: int, search: str | None = None
) -> tuple[list[User], int]:
    query = select(User).where(User.deleted_at.is_(None))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.email.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
            )
        )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(
        query.order_by(User.last_name, User.first_name, User.email).limit(limit).offset(offset)
    ).all()
    return list(items), total


def _ensure_manageable(actor: User, target: User) -> None:
    """Qui peut agir sur ``target`` : gestionnaire d'utilisateurs ou admin de son entreprise."""
    if target.role == UserRole.SUPER_ADMIN and actor.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Action interdite sur un super administrateur")
    if has_permission(actor, Permission.MANAGE_USERS):
        return
    same_company = bool(actor.company_id and actor.company_id == target.company_id)
    if not (actor.is_company_admin and same_company):
        raise ForbiddenError("Droits insuffisants")


def create_user(session: Session, actor: User, data) -> User:
    privileged_role = data.role != UserRole.MEMBER
    if privileged_role and actor.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Seul un super administrateur peut créer ce type de compte")
    if not has_permission(actor, Permission.MANAGE_USERS):
        # Un admin d'entreprise ne crée que des membres de sa propre entreprise.
        if not can_manage_company(actor, data.company_id):
            raise ForbiddenError("Droits insuffisants")
    if data.company_id and not session.get(Company, data.company_id):
        raise NotFoundError("Entreprise introuvable")
    email = data.email.lower()
    if session.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise ConflictError("Cet email est déjà utilisé")
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        job_title=data.job_title,
        phone=data.phone,
        company_id=data.company_id,
        is_company_admin=data.is_company_admin,
        role=data.role,
        permissions=data.permissions if data.role == UserRole.STAFF else [],
    )
    session.add(user)
    session.commit()
    return user


def update_profile(session: Session, user: User, data) -> User:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.commit()
    return user


def update_user(session: Session, actor: User, target_id: uuid.UUID, data) -> User:
    target = get_user(session, target_id)
    if actor.id != target.id:
        _ensure_manageable(actor, target)
    return update_profile(session, target, data)


def change_password(session: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise AppError("Mot de passe actuel incorrect")
    user.password_hash = hash_password(new)
    session.commit()


def _active_super_admins(session: Session) -> int:
    return (
        session.scalar(
            select(func.count()).where(
                User.role == UserRole.SUPER_ADMIN,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        or 0
    )


def _ensure_not_last_super_admin(session: Session, target: User) -> None:
    if (
        target.role == UserRole.SUPER_ADMIN
        and target.is_active
        and _active_super_admins(session) <= 1
    ):
        raise ForbiddenError("Impossible de retirer le dernier super administrateur actif")


def set_active(session: Session, actor: User, target_id: uuid.UUID, active: bool) -> User:
    target = get_user(session, target_id)
    _ensure_manageable(actor, target)
    if not active:
        _ensure_not_last_super_admin(session, target)
    target.is_active = active
    session.commit()
    return target


def delete_user(session: Session, actor: User, target_id: uuid.UUID) -> None:
    target = get_user(session, target_id)
    if target.id == actor.id:
        raise ForbiddenError("Vous ne pouvez pas supprimer votre propre compte")
    _ensure_manageable(actor, target)
    _ensure_not_last_super_admin(session, target)
    target.deleted_at = datetime.now(UTC)
    target.is_active = False
    session.commit()


def set_role(session: Session, target_id: uuid.UUID, data) -> User:
    """Réservé au super admin (contrôlé par la route)."""
    target = get_user(session, target_id)
    if data.role != UserRole.SUPER_ADMIN:
        _ensure_not_last_super_admin(session, target)
    target.role = data.role
    target.permissions = data.permissions if data.role == UserRole.STAFF else []
    session.commit()
    return target


def set_company_admin(session: Session, actor: User, target_id: uuid.UUID, value: bool) -> User:
    target = get_user(session, target_id)
    _ensure_manageable(actor, target)
    if value and not target.company_id:
        raise AppError("L'utilisateur n'est rattaché à aucune entreprise")
    target.is_company_admin = value
    session.commit()
    return target


def set_image(session: Session, actor: User, target: User, field: str, file, category: str) -> User:
    """Remplace l'image (avatar, carte de visite) de ``target`` ; ancien fichier supprimé."""
    if actor.id != target.id:
        _ensure_manageable(actor, target)
    new_path = storage.save_image(file, category)
    old_path = getattr(target, field)
    setattr(target, field, new_path)
    session.commit()
    storage.delete_file(old_path)
    return target
