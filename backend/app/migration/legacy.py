"""Import des données de l'ancienne application (SQLite ou PostgreSQL) vers le nouveau schéma.

Principes :
- les identifiants (UUID) sont conservés, ce qui préserve toutes les relations ;
- l'import est idempotent : une ligne déjà présente (même id) est ignorée ;
- les mots de passe bcrypt sont repris tels quels (re-hachés en Argon2 à la première connexion) ;
- les fichiers envoyés sont copiés si ``uploads_dir`` est fourni.
"""

import json
import logging
import shutil
import uuid
from collections import Counter
from datetime import UTC, date, datetime, time
from pathlib import Path

from sqlalchemy import MetaData, create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    Company,
    Conversation,
    ConversationParticipant,
    Event,
    Invitation,
    Message,
    NewsArticle,
    Notification,
    SavedArticle,
    SiteContent,
    Training,
    TrainingEnrollment,
    TrainingSession,
    User,
)
from app.models.enums import ConversationKind, UserRole

logger = logging.getLogger(__name__)


def _uuid(value) -> uuid.UUID | None:
    """Convertit une valeur en UUID (``None`` si invalide)."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _dt(value) -> datetime | None:
    """Convertit une valeur en datetime avec fuseau UTC par défaut (``None`` si invalide)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _csv(value) -> list[str]:
    """Découpe une chaîne séparée par des virgules en liste de valeurs non vides."""
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def _bool(value, default=False) -> bool:
    """Convertit une valeur en booléen, avec une valeur par défaut si elle est absente."""
    return default if value is None else bool(value)


class LegacyImporter:
    """Lit une base héritée via la réflexion SQLAlchemy et alimente la nouvelle base."""

    def __init__(self, source_url: str, session: Session, uploads_dir: Path | None = None):
        """Ouvre la base héritée (réflexion du schéma) et prépare les compteurs d'import."""
        self.engine = create_engine(source_url)
        self.metadata = MetaData()
        self.metadata.reflect(self.engine)
        self.session = session
        self.uploads_dir = uploads_dir
        self.counts: Counter[str] = Counter()
        self.user_ids: set[uuid.UUID] = set()

    # --- Utilitaires ---------------------------------------------------------------------

    def rows(self, table: str) -> list[dict]:
        """Retourne les lignes d'une table héritée (liste vide si la table est absente)."""
        if table not in self.metadata.tables:
            logger.warning("Table héritée absente : %s", table)
            return []
        with self.engine.connect() as conn:
            return [dict(r._mapping) for r in conn.execute(select(self.metadata.tables[table]))]

    def exists(self, model, pk) -> bool:
        """Indique si une ligne de la nouvelle base existe déjà pour cette clé primaire."""
        return self.session.get(model, pk) is not None

    def add(self, label: str, obj) -> None:
        """Ajoute un objet à la session et incrémente le compteur de son type."""
        self.session.add(obj)
        self.counts[label] += 1

    def copy_file(self, legacy_path: str | None, legacy_folder: str, category: str) -> str | None:
        """Copie un fichier vers ``<upload_dir>/<category>/`` ; retourne le nouveau chemin relatif."""
        if not legacy_path:
            return None
        name = Path(str(legacy_path)).name
        if not name or str(legacy_path).startswith(("http://", "https://")):
            return None
        relative = f"{category}/{name}"
        if self.uploads_dir:
            source = self.uploads_dir / legacy_folder / name
            if source.is_file():
                target = Path(get_settings().upload_dir) / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                return relative
            return None
        return relative

    # --- Tables --------------------------------------------------------------------------

    def companies(self) -> None:
        """Importe les entreprises."""
        for row in self.rows("companies"):
            pk = _uuid(row["id"])
            if not pk or self.exists(Company, pk):
                continue
            self.add(
                "companies",
                Company(
                    id=pk,
                    name=row["name"],
                    description=row.get("description"),
                    location=row.get("location"),
                    website_url=row.get("website_link"),
                    logo_path=self.copy_file(row.get("company_picture"), "companies", "logos"),
                    kind=row.get("kind") or "company",
                    is_active=_bool(row.get("is_active"), True),
                ),
            )
        self.session.flush()

    def users(self) -> None:
        """Importe les utilisateurs et leurs rattachements aux entreprises."""
        for row in self.rows("users"):
            pk = _uuid(row["id"])
            if not pk or self.exists(User, pk):
                continue
            if self.session.scalar(
                select(User.id).where(func.lower(User.email) == str(row["email"]).lower())
            ):
                self.counts["users_ignorés_email_dupliqué"] += 1
                continue
            role = (
                UserRole.SUPER_ADMIN
                if row.get("is_super_admin")
                else UserRole.STAFF
                if row.get("is_staff")
                else UserRole.MEMBER
            )
            company_id = _uuid(row.get("company_id"))
            if company_id and not self.exists(Company, company_id):
                company_id = None
            self.add(
                "users",
                User(
                    id=pk,
                    email=str(row["email"]).lower(),
                    password_hash=row["password_hash"],
                    first_name=row.get("first_name"),
                    last_name=row.get("last_name"),
                    job_title=row.get("job_title"),
                    phone=row.get("phone"),
                    avatar_path=self.copy_file(
                        row.get("profile_picture"), "users/profile_pictures", "avatars"
                    ),
                    business_card_path=self.copy_file(
                        row.get("business_card"), "users/business_cards", "business-cards"
                    ),
                    role=role,
                    is_company_admin=_bool(row.get("is_company_admin")),
                    permissions=_csv(row.get("permissions")) if role == UserRole.STAFF else [],
                    is_active=_bool(row.get("is_active"), True),
                    company_id=company_id,
                ),
            )
            self.user_ids.add(pk)
        self.session.flush()
        self.user_ids |= set(self.session.scalars(select(User.id)).all())

    def trainings(self) -> None:
        """Importe les formations."""
        for row in self.rows("trainings"):
            pk = _uuid(row["id"])
            if not pk or self.exists(Training, pk):
                continue
            company_id = _uuid(row.get("company_id"))
            if company_id and not self.exists(Company, company_id):
                company_id = None
            self.add(
                "trainings",
                Training(
                    id=pk,
                    title=row["title"],
                    description=row.get("description"),
                    picture_path=self.copy_file(row.get("picture"), "trainings", "trainings"),
                    category=row.get("category"),
                    kind=row.get("type") or "formation",
                    documents=self._documents(row.get("documents")),
                    company_id=company_id,
                    is_active=_bool(row.get("is_active"), True),
                ),
            )
        self.session.flush()

    def _documents(self, raw) -> list[str]:
        """Convertit les documents d'une formation héritée en chemins copiés."""
        if not raw:
            return []
        try:
            values = json.loads(raw)
            names = values if isinstance(values, list) else [values]
        except (ValueError, TypeError):
            names = _csv(raw)
        documents = []
        for value in names:
            copied = self.copy_file(str(value), "trainings/documents", "trainings")
            if copied:
                documents.append(copied)
        return documents

    def sessions(self) -> None:
        """Importe les sessions de formation."""
        for row in self.rows("training_sessions"):
            pk = _uuid(row["id"])
            training_id = _uuid(row.get("training_id"))
            start, end = _dt(row.get("start_date")), _dt(row.get("end_date"))
            if not pk or self.exists(TrainingSession, pk) or not start or not end:
                continue
            if not training_id or not self.exists(Training, training_id):
                continue
            created_by = _uuid(row.get("created_by"))
            self.add(
                "sessions",
                TrainingSession(
                    id=pk,
                    training_id=training_id,
                    start_at=start,
                    end_at=max(end, start),
                    max_participants=max(int(row.get("max_participants") or 1), 1),
                    location=row.get("location"),
                    link=row.get("link"),
                    status=row.get("status") or "upcoming",
                    is_public=_bool(row.get("is_public")),
                    created_by=created_by if created_by in self.user_ids else None,
                ),
            )
        self.session.flush()

    def enrollments(self) -> None:
        """Importe les inscriptions et marques d'intérêt aux formations."""
        seen: set[tuple[uuid.UUID, uuid.UUID]] = set()
        for row in self.rows("formation_users"):
            pk = _uuid(row["id"])
            user_id, training_id = _uuid(row.get("user_id")), _uuid(row.get("training_id"))
            if not pk or self.exists(TrainingEnrollment, pk):
                continue
            if (
                user_id not in self.user_ids
                or not training_id
                or not self.exists(Training, training_id)
            ):
                continue
            if (user_id, training_id) in seen:
                continue
            seen.add((user_id, training_id))
            session_id = _uuid(row.get("session_id"))
            if session_id and not self.exists(TrainingSession, session_id):
                session_id = None
            self.add(
                "enrollments",
                TrainingEnrollment(
                    id=pk,
                    user_id=user_id,
                    training_id=training_id,
                    session_id=session_id,
                    interested=_bool(row.get("saved")) or row.get("type") == "interest",
                    enrolled_at=_dt(row.get("enrolled_at")) if session_id else None,
                    completed_at=_dt(row.get("completed_at")),
                ),
            )
        self.session.flush()

    def events(self) -> None:
        """Importe les événements de l'agenda."""
        for row in self.rows("events"):
            pk = _uuid(row["id"])
            if not pk or self.exists(Event, pk):
                continue
            try:
                day = date.fromisoformat(str(row["date"]))
                hour = time.fromisoformat(str(row["time"])) if row.get("time") else None
            except ValueError:
                continue
            created_by = _uuid(row.get("created_by"))
            self.add(
                "events",
                Event(
                    id=pk,
                    title=row["title"],
                    description=row.get("description"),
                    event_date=day,
                    event_time=hour,
                    color=row.get("color"),
                    is_public=_bool(row.get("is_public")),
                    created_by=created_by if created_by in self.user_ids else None,
                    deleted_at=None if _bool(row.get("is_active"), True) else datetime.now(UTC),
                ),
            )
        self.session.flush()

    def invitations(self) -> None:
        """Importe les invitations aux événements et aux sessions."""
        for row in self.rows("invitations"):
            pk = _uuid(row["id"])
            inviter, invitee = _uuid(row.get("inviter_id")), _uuid(row.get("invitee_id"))
            target = _uuid(row.get("target_id"))
            kind = row.get("target_type")
            if not pk or self.exists(Invitation, pk):
                continue
            if inviter not in self.user_ids or invitee not in self.user_ids:
                continue
            event_id = target if kind == "event" and self.exists(Event, target) else None
            session_id = (
                target if kind == "session" and self.exists(TrainingSession, target) else None
            )
            if not event_id and not session_id:
                self.counts["invitations_ignorées"] += 1  # invitation à une formation entière
                continue
            self.add(
                "invitations",
                Invitation(
                    id=pk,
                    event_id=event_id,
                    session_id=session_id,
                    inviter_id=inviter,
                    invitee_id=invitee,
                    status=row.get("status") or "pending",
                    is_read=_bool(row.get("is_read")),
                    created_at=_dt(row.get("created_at")) or datetime.now(UTC),
                    responded_at=_dt(row.get("responded_at")),
                ),
            )
        self.session.flush()

    def conversations(self) -> None:
        """Importe les conversations et leurs participants."""
        participants_table = {}
        for row in self.rows("conversation_participants"):
            participants_table.setdefault(row["conversation_id"], set()).add(_uuid(row["user_id"]))

        for row in self.rows("conversations"):
            pk = _uuid(row["id"])
            if not pk or self.exists(Conversation, pk):
                continue
            members = {_uuid(p) for p in _csv(row.get("participant_ids"))} | participants_table.get(
                row["id"], set()
            )
            members = {m for m in members if m in self.user_ids}
            if len(members) < 2:
                continue
            kind = (
                ConversationKind.GROUP
                if row.get("title") or len(members) > 2
                else ConversationKind.DIRECT
            )
            creator = _uuid(row.get("creator_id"))
            conversation = Conversation(
                id=pk,
                kind=kind,
                title=row.get("title"),
                creator_id=creator if creator in self.user_ids else None,
                created_at=_dt(row.get("created_at")) or datetime.now(UTC),
            )
            conversation.participants = [ConversationParticipant(user_id=m) for m in members]
            self.add("conversations", conversation)
        self.session.flush()

    def _direct_between(self, a: uuid.UUID, b: uuid.UUID) -> Conversation:
        """Retourne la conversation directe entre deux utilisateurs, en la créant au besoin."""
        pair = {a, b}
        cache = self.__dict__.setdefault("_direct_cache", {})
        key = frozenset(pair)
        if key not in cache:
            conversation = Conversation(kind=ConversationKind.DIRECT, creator_id=a)
            conversation.participants = [ConversationParticipant(user_id=u) for u in pair]
            self.session.add(conversation)
            self.session.flush()
            self.counts["conversations_directes_créées"] += 1
            cache[key] = conversation
        return cache[key]

    def messages(self) -> None:
        """Importe les messages des conversations."""
        for row in self.rows("messages"):
            pk = _uuid(row["id"])
            author = _uuid(row.get("author_id"))
            if not pk or self.exists(Message, pk) or author not in self.user_ids:
                continue
            conversation_id = _uuid(row.get("conversation_id"))
            if conversation_id and self.exists(Conversation, conversation_id):
                target = conversation_id
            else:
                recipient = _uuid(row.get("recipient_id"))
                if recipient not in self.user_ids or recipient == author:
                    continue
                target = self._direct_between(author, recipient).id
            file_path = (
                self.copy_file(row.get("file_url"), "messages", "messages")
                if row.get("file_url")
                else None
            )
            self.add(
                "messages",
                Message(
                    id=pk,
                    conversation_id=target,
                    author_id=author,
                    content=row.get("content") or "",
                    file_path=file_path,
                    file_name=row.get("file_name") if file_path else None,
                    created_at=_dt(row.get("created_at")) or datetime.now(UTC),
                    deleted_at=None if _bool(row.get("is_active"), True) else datetime.now(UTC),
                ),
            )
        self.session.flush()

    def notifications(self) -> None:
        """Importe les notifications."""
        for row in self.rows("notifications"):
            pk = _uuid(row["id"])
            recipient = _uuid(row.get("recipient_id"))
            if not pk or self.exists(Notification, pk) or recipient not in self.user_ids:
                continue
            self.add(
                "notifications",
                Notification(
                    id=pk,
                    recipient_id=recipient,
                    content=row["content"],
                    is_read=_bool(row.get("is_read")),
                    created_at=_dt(row.get("created_at")) or datetime.now(UTC),
                ),
            )
        self.session.flush()

    def news(self) -> None:
        """Importe les actualités."""
        for row in self.rows("news"):
            pk = _uuid(row["id"])
            url = row.get("url")
            if not pk or self.exists(NewsArticle, pk):
                continue
            if url and self.session.scalar(select(NewsArticle.id).where(NewsArticle.url == url)):
                continue
            self.add(
                "news",
                NewsArticle(
                    id=pk,
                    title=row["title"],
                    source=row.get("source"),
                    summary=row.get("summary"),
                    url=url,
                    category=row.get("category"),
                    published_at=_dt(row.get("published_at")),
                    created_at=_dt(row.get("created_at")) or datetime.now(UTC),
                ),
            )
        self.session.flush()

    def saved_news(self) -> None:
        """Importe les articles enregistrés par les utilisateurs."""
        for row in self.rows("saved_news"):
            pk = _uuid(row["id"])
            user_id = _uuid(row.get("user_id"))
            if not pk or self.exists(SavedArticle, pk) or user_id not in self.user_ids:
                continue
            article_id = _uuid(row.get("news_id"))
            self.add(
                "saved_news",
                SavedArticle(
                    id=pk,
                    user_id=user_id,
                    article_id=article_id
                    if article_id and self.exists(NewsArticle, article_id)
                    else None,
                    title=row["title"],
                    source=row.get("source"),
                    summary=row.get("summary"),
                    url=row.get("url"),
                    category=row.get("category"),
                    published_at=_dt(row.get("published_at")),
                    saved_at=_dt(row.get("saved_at")) or datetime.now(UTC),
                ),
            )
        self.session.flush()

    def site_content(self) -> None:
        """Importe les contenus éditoriaux du site."""
        for row in self.rows("site_content"):
            if self.exists(SiteContent, row["key"]):
                continue
            try:
                value = json.loads(row["value"])
            except (ValueError, TypeError):
                continue
            self.add("site_content", SiteContent(key=row["key"], value=value))
        self.session.flush()

    # --- Orchestration -------------------------------------------------------------------

    def run(self) -> Counter[str]:
        """Importe tout dans l'ordre des dépendances, en une seule transaction."""
        try:
            self.user_ids = set(self.session.scalars(select(User.id)).all())
            self.companies()
            self.users()
            self.trainings()
            self.sessions()
            self.enrollments()
            self.events()
            self.invitations()
            self.conversations()
            self.messages()
            self.notifications()
            self.news()
            self.saved_news()
            self.site_content()
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self.counts
