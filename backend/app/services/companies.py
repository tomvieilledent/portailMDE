import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ForbiddenError, NotFoundError
from app.core.permissions import Permission, can_manage_company, has_permission
from app.models import Company, User
from app.models.enums import CompanyKind
from app.services import storage


def get_company(session: Session, company_id: uuid.UUID, actor: User) -> Company:
    company = session.get(Company, company_id)
    if not company or company.deleted_at is not None:
        raise NotFoundError("Entreprise introuvable")
    if not company.is_active and not can_manage_company(actor, company.id):
        raise NotFoundError("Entreprise introuvable")
    return company


def list_companies(
    session: Session,
    actor: User,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    kind: CompanyKind | None = None,
) -> tuple[list[Company], int]:
    query = select(Company).where(Company.deleted_at.is_(None))
    if not has_permission(actor, Permission.MANAGE_COMPANIES):
        query = query.where(Company.is_active.is_(True))
    if search:
        query = query.where(Company.name.ilike(f"%{search.strip()}%"))
    if kind:
        query = query.where(Company.kind == kind)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(query.order_by(Company.name).limit(limit).offset(offset)).all()
    return list(items), total


def create_company(session: Session, data) -> Company:
    company = Company(**data.model_dump())
    session.add(company)
    session.commit()
    return company


def update_company(session: Session, actor: User, company_id: uuid.UUID, data) -> Company:
    company = get_company(session, company_id, actor)
    if not can_manage_company(actor, company.id):
        raise ForbiddenError("Droits insuffisants")
    values = data.model_dump(exclude_unset=True)
    if "kind" in values and not has_permission(actor, Permission.MANAGE_COMPANIES):
        raise ForbiddenError("Seuls les gestionnaires peuvent changer le type")
    for field, value in values.items():
        setattr(company, field, value)
    session.commit()
    return company


def set_active(session: Session, company_id: uuid.UUID, actor: User, active: bool) -> Company:
    company = get_company(session, company_id, actor)
    company.is_active = active
    session.commit()
    return company


def delete_company(session: Session, company_id: uuid.UUID, actor: User) -> None:
    company = get_company(session, company_id, actor)
    company.deleted_at = datetime.now(UTC)
    company.is_active = False
    session.commit()


def list_members(session: Session, company_id: uuid.UUID, actor: User) -> list[User]:
    get_company(session, company_id, actor)
    return list(
        session.scalars(
            select(User)
            .where(User.company_id == company_id, User.deleted_at.is_(None))
            .order_by(User.last_name, User.first_name)
        ).all()
    )


def _get_user(session: Session, user_id: uuid.UUID) -> User:
    user = session.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError("Utilisateur introuvable")
    return user


def add_member(session: Session, actor: User, company_id: uuid.UUID, user_id: uuid.UUID) -> User:
    company = get_company(session, company_id, actor)
    if not has_permission(actor, Permission.MANAGE_COMPANIES):
        raise ForbiddenError("Droits insuffisants")
    user = _get_user(session, user_id)
    user.company_id = company.id
    user.is_company_admin = False
    session.commit()
    return user


def remove_member(session: Session, actor: User, company_id: uuid.UUID, user_id: uuid.UUID) -> None:
    company = get_company(session, company_id, actor)
    if not can_manage_company(actor, company.id):
        raise ForbiddenError("Droits insuffisants")
    user = _get_user(session, user_id)
    if user.company_id != company.id:
        raise NotFoundError("Cet utilisateur n'appartient pas à l'entreprise")
    user.company_id = None
    user.is_company_admin = False
    session.commit()


def set_logo(session: Session, actor: User, company_id: uuid.UUID, file) -> Company:
    company = get_company(session, company_id, actor)
    if not can_manage_company(actor, company.id):
        raise ForbiddenError("Droits insuffisants")
    new_path = storage.save_image(file, "logos")
    old_path = company.logo_path
    company.logo_path = new_path
    session.commit()
    storage.delete_file(old_path)
    return company
