"""Données de démonstration et création du premier administrateur."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.core.permissions import validate_permissions
from app.core.security import hash_password
from app.models import Company, Event, NewsArticle, Training, TrainingSession, User
from app.models.enums import UserRole


def create_admin(session: Session, email: str, password: str, *, first_name=None, last_name=None):
    """Crée un super administrateur (premier compte d'une installation vierge)."""
    email = email.lower()
    if session.scalar(select(User.id).where(func.lower(User.email) == email)):
        raise ConflictError(f"Le compte {email} existe déjà")
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        role=UserRole.SUPER_ADMIN,
    )
    session.add(user)
    session.commit()
    return user


def _user(session, email, password, **fields) -> User:
    user = session.scalar(select(User).where(func.lower(User.email) == email))
    if not user:
        user = User(email=email, password_hash=hash_password(password), **fields)
        session.add(user)
        session.flush()
    return user


def seed_demo(session: Session, password: str = "demo-password-1") -> dict[str, int]:
    """Jeu de données de démonstration, idempotent (rejouable sans doublons)."""
    if session.scalar(select(Company.id).where(Company.name == "Atelier Lumière")):
        return {}

    companies = {
        name: Company(name=name, description=desc, location="Rodez", kind=kind)
        for name, desc, kind in [
            ("Atelier Lumière", "Studio de design graphique et d'identité visuelle.", "company"),
            ("AgriTech Aveyron", "Capteurs connectés pour l'agriculture de précision.", "company"),
            ("Conseil & Co", "Accompagnement RH et gestion pour les TPE.", "company"),
            ("Formations Sud", "Organisme de formation professionnelle.", "trainer"),
        ]
    }
    session.add_all(companies.values())
    session.flush()

    admin = _user(
        session,
        "admin@demo.fr",
        password,
        first_name="Alice",
        last_name="Admin",
        role=UserRole.SUPER_ADMIN,
    )
    _user(
        session,
        "staff@demo.fr",
        password,
        first_name="Samuel",
        last_name="Staff",
        role=UserRole.STAFF,
        permissions=validate_permissions(["manage_trainings", "manage_news"]),
    )
    people = [
        ("lea@demo.fr", "Léa", "Martin", "Directrice artistique", "Atelier Lumière", True),
        ("hugo@demo.fr", "Hugo", "Bernard", "Développeur", "Atelier Lumière", False),
        ("sofia@demo.fr", "Sofia", "Petit", "Fondatrice", "AgriTech Aveyron", True),
        ("karim@demo.fr", "Karim", "Roux", "Ingénieur capteurs", "AgriTech Aveyron", False),
        ("manon@demo.fr", "Manon", "Durand", "Consultante RH", "Conseil & Co", True),
    ]
    for email, first, last, job, company, boss in people:
        _user(
            session,
            email,
            password,
            first_name=first,
            last_name=last,
            job_title=job,
            company_id=companies[company].id,
            is_company_admin=boss,
        )

    today = date.today()
    session.add_all(
        [
            Event(
                title="Afterwork des entrepreneurs",
                event_date=today + timedelta(days=7),
                event_time=time(18, 30),
                description="Rencontre conviviale ouverte à tous.",
                is_public=True,
                created_by=admin.id,
            ),
            Event(
                title="Comité d'accompagnement",
                event_date=today + timedelta(days=14),
                event_time=time(9, 0),
                created_by=admin.id,
            ),
        ]
    )
    training = Training(
        title="Réussir son pitch",
        category="Communication",
        kind="atelier",
        description="Structurer et présenter son projet en 5 minutes.",
        company_id=companies["Formations Sud"].id,
    )
    session.add(training)
    session.flush()
    start = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(
        days=10
    )
    session.add(
        TrainingSession(
            training_id=training.id,
            start_at=start,
            end_at=start + timedelta(hours=7),
            max_participants=12,
            location="Salle des Cèdres",
            is_public=True,
            created_by=admin.id,
        )
    )
    session.add(
        NewsArticle(
            title="Bienvenue sur le portail",
            source="MDE",
            category="vie de la pépinière",
            summary="Retrouvez ici l'annuaire, la messagerie, l'agenda et les formations.",
            published_at=datetime.now(UTC),
        )
    )
    session.commit()
    return {"entreprises": len(companies), "utilisateurs": 2 + len(people)}
