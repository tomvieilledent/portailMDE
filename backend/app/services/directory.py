import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, User
from app.models.enums import CompanyKind
from app.schemas.directory import CompanyCard


def search_people(
    session: Session,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    company_id: uuid.UUID | None = None,
) -> tuple[list[User], int]:
    """Personnes actives dont l'entreprise (si elle existe) est active."""
    query = (
        select(User)
        .outerjoin(Company, User.company_id == Company.id)
        .where(
            User.deleted_at.is_(None),
            User.is_active.is_(True),
            or_(Company.id.is_(None), (Company.is_active.is_(True) & Company.deleted_at.is_(None))),
        )
    )
    if company_id:
        query = query.where(User.company_id == company_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                User.job_title.ilike(pattern),
                Company.name.ilike(pattern),
            )
        )
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(
        query.options(joinedload(User.company))
        .order_by(User.last_name, User.first_name, User.email)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total


def search_companies(
    session: Session,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    kind: CompanyKind | None = None,
) -> tuple[list[CompanyCard], int]:
    members = (
        select(User.company_id, func.count().label("n"))
        .where(User.deleted_at.is_(None), User.is_active.is_(True))
        .group_by(User.company_id)
        .subquery()
    )
    query = (
        select(Company, func.coalesce(members.c.n, 0))
        .outerjoin(members, members.c.company_id == Company.id)
        .where(Company.deleted_at.is_(None), Company.is_active.is_(True))
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Company.name.ilike(pattern), Company.description.ilike(pattern)))
    if kind:
        query = query.where(Company.kind == kind)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.execute(query.order_by(Company.name).limit(limit).offset(offset)).all()
    cards = [
        CompanyCard.model_validate({**company.__dict__, "member_count": count})
        for company, count in rows
    ]
    return cards, total
