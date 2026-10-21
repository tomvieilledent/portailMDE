"""Gestion des utilisateurs : comptes, profil, rôles, mots de passe et images."""

import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import Permission, can_manage_company, has_permission
from app.core.security import hash_password, verify_password
from app.models import Company, Message, Notification, User
from app.models.enums import UserRole
from app.services import storage
from app.services.mailer import send_later


def get_user(session: Session, user_id: uuid.UUID) -> User:
    """Retourne un utilisateur non supprimé, ou lève une erreur s'il est introuvable."""
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError("Utilisateur introuvable")
    return user


def get_user_for(session: Session, actor: User, user_id: uuid.UUID) -> User:
    """Profil complet : réservé à soi-même, aux gestionnaires d'utilisateurs et admins d'entreprise."""
    user = get_user(session, user_id)
    if user.id != actor.id:
        _ensure_manageable(actor, user)
    return user


def list_users(
    session: Session, *, limit: int, offset: int, search: str | None = None
) -> tuple[list[User], int]:
    """Liste les utilisateurs avec recherche par email ou nom."""
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
    """Crée un compte, vérifie les droits de l'acteur et envoie l'email de bienvenue."""
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
    from app.core.config import get_settings
    from app.emails import templates

    send_later(
        user.email,
        *templates.welcome(user.first_name or user.email, get_settings().frontend_url),
    )
    return user


def update_profile(session: Session, user: User, data) -> User:
    """Met à jour le profil d'un utilisateur."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.commit()
    return user


def update_user(session: Session, actor: User, target_id: uuid.UUID, data) -> User:
    """Met à jour le profil d'un utilisateur (lui-même ou un gestionnaire)."""
    target = get_user(session, target_id)
    if actor.id != target.id:
        _ensure_manageable(actor, target)
    return update_profile(session, target, data)


def change_password(session: Session, user: User, current: str, new: str) -> None:
    """Change le mot de passe après vérification du mot de passe actuel."""
    if not verify_password(current, user.password_hash):
        raise AppError("Mot de passe actuel incorrect")
    user.password_hash = hash_password(new)
    session.commit()


def _active_super_admins(session: Session) -> int:
    """Compte les super administrateurs actifs."""
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
    """Refuse de retirer le dernier super administrateur actif."""
    if (
        target.role == UserRole.SUPER_ADMIN
        and target.is_active
        and _active_super_admins(session) <= 1
    ):
        raise ForbiddenError("Impossible de retirer le dernier super administrateur actif")


def set_active(session: Session, actor: User, target_id: uuid.UUID, active: bool) -> User:
    """Active ou désactive un compte (jamais le dernier super administrateur actif)."""
    target = get_user(session, target_id)
    _ensure_manageable(actor, target)
    if not active:
        _ensure_not_last_super_admin(session, target)
    target.is_active = active
    session.commit()
    return target


def delete_user(session: Session, actor: User, target_id: uuid.UUID) -> None:
    """Supprime logiquement un compte (jamais le sien ni le dernier super administrateur)."""
    target = get_user(session, target_id)
    if target.id == actor.id:
        raise ForbiddenError("Vous ne pouvez pas supprimer votre propre compte")
    _ensure_manageable(actor, target)
    _ensure_not_last_super_admin(session, target)
    _anonymize(session, target)


def delete_own_account(session: Session, user: User) -> None:
    """Efface le compte de l'utilisateur courant (droit à l'effacement)."""
    _ensure_not_last_super_admin(session, user)
    _anonymize(session, user)


def _anonymize(session: Session, target: User) -> None:
    """Suppression logique + anonymisation des données personnelles, messages et fichiers associés."""
    old_files = [target.avatar_path, target.business_card_path]
    target.deleted_at = datetime.now(UTC)
    target.is_active = False
    target.email = f"deleted-{target.id}@anonymise.portail-mde.fr"
    target.password_hash = hash_password(secrets.token_urlsafe(32))
    target.first_name = "Utilisateur supprimé"
    target.last_name = None
    target.job_title = None
    target.phone = None
    target.avatar_path = None
    target.business_card_path = None
    session.execute(delete(Notification).where(Notification.recipient_id == target.id))
    now = target.deleted_at
    for message in session.scalars(select(Message).where(Message.author_id == target.id)):
        if message.file_path:
            old_files.append(message.file_path)
        message.content = ""
        message.file_path = None
        message.file_name = None
        message.author_id = None
        message.deleted_at = message.deleted_at or now
    session.commit()
    for path in old_files:
        storage.delete_file(path)


def export_personal_data(session: Session, user: User) -> dict:
    """Rassemble les données personnelles de l'utilisateur (droit d'accès et de portabilité)."""
    messages = session.scalars(
        select(Message).where(Message.author_id == user.id, Message.deleted_at.is_(None))
    ).all()
    notifications = session.scalars(
        select(Notification).where(Notification.recipient_id == user.id)
    ).all()
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "profile": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "job_title": user.job_title,
            "phone": user.phone,
            "avatar_path": user.avatar_path,
            "business_card_path": user.business_card_path,
            "role": user.role,
            "company_id": str(user.company_id) if user.company_id else None,
            "created_at": user.created_at.isoformat(),
        },
        "messages": [
            {
                "conversation_id": str(m.conversation_id),
                "content": m.content,
                "file_name": m.file_name,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "notifications": [
            {"content": n.content, "kind": n.kind, "created_at": n.created_at.isoformat()}
            for n in notifications
        ],
    }


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
    """Accorde ou retire le statut d'administrateur d'entreprise."""
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
