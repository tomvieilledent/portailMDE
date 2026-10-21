"""Tests de la migration des données depuis l'ancienne base, de la création d'admin et du jeu de démo."""

import sqlite3
import uuid

import bcrypt
import pytest
from sqlalchemy import func, select

from app import cli
from app.core.errors import ConflictError
from app.migration.legacy import LegacyImporter
from app.migration.seed import create_admin, seed_demo
from app.models import (
    Company,
    Conversation,
    Event,
    Invitation,
    Message,
    Notification,
    SavedArticle,
    SiteContent,
    Training,
    TrainingEnrollment,
    TrainingSession,
    User,
)

API = "/api/v1"
ids = {
    name: str(uuid.uuid4())
    for name in "co admin staff alice bob tr se ev inv conv msg msg2 note news".split()
}

SCHEMA = """
CREATE TABLE companies (id TEXT PRIMARY KEY, name TEXT, description TEXT, location TEXT,
  website_link TEXT, company_picture TEXT, kind TEXT, is_active BOOLEAN);
CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT, password_hash TEXT, first_name TEXT,
  last_name TEXT, job_title TEXT, phone TEXT, profile_picture TEXT, business_card TEXT,
  is_super_admin BOOLEAN, is_company_admin BOOLEAN, is_staff BOOLEAN, permissions TEXT,
  company_id TEXT, is_active BOOLEAN);
CREATE TABLE trainings (id TEXT PRIMARY KEY, title TEXT, company_id TEXT, description TEXT,
  picture TEXT, category TEXT, type TEXT, documents TEXT, is_active BOOLEAN);
CREATE TABLE training_sessions (id TEXT PRIMARY KEY, training_id TEXT, start_date TEXT,
  end_date TEXT, max_participants INTEGER, location TEXT, link TEXT, status TEXT,
  is_public BOOLEAN, created_by TEXT);
CREATE TABLE formation_users (id TEXT PRIMARY KEY, user_id TEXT, training_id TEXT,
  session_id TEXT, type TEXT, saved BOOLEAN, enrolled_at TEXT, completed_at TEXT);
CREATE TABLE events (id TEXT PRIMARY KEY, title TEXT, date TEXT, time TEXT, color TEXT,
  description TEXT, created_by TEXT, is_public BOOLEAN, is_active BOOLEAN);
CREATE TABLE invitations (id TEXT PRIMARY KEY, target_type TEXT, target_id TEXT,
  inviter_id TEXT, invitee_id TEXT, status TEXT, is_read BOOLEAN, created_at TEXT,
  responded_at TEXT);
CREATE TABLE conversations (id TEXT PRIMARY KEY, title TEXT, creator_id TEXT,
  participant_ids TEXT, is_active BOOLEAN, created_at TEXT);
CREATE TABLE conversation_participants (id TEXT PRIMARY KEY, conversation_id TEXT, user_id TEXT);
CREATE TABLE messages (id TEXT PRIMARY KEY, author_id TEXT, recipient_id TEXT,
  conversation_id TEXT, content TEXT, file_url TEXT, file_name TEXT, is_read BOOLEAN,
  is_active BOOLEAN, created_at TEXT);
CREATE TABLE notifications (id TEXT PRIMARY KEY, recipient_id TEXT, content TEXT,
  is_read BOOLEAN, created_at TEXT);
CREATE TABLE news (id TEXT PRIMARY KEY, title TEXT, source TEXT, summary TEXT, url TEXT,
  category TEXT, published_at TEXT, created_at TEXT);
CREATE TABLE saved_news (id TEXT PRIMARY KEY, user_id TEXT, news_id TEXT, title TEXT,
  source TEXT, summary TEXT, url TEXT, category TEXT, published_at TEXT, saved_at TEXT);
CREATE TABLE site_content (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);
"""


@pytest.fixture
def legacy_url(tmp_path):
    """Crée une base SQLite de l'ancienne application et retourne son URL."""
    path = tmp_path / "legacy.db"
    old_hash = bcrypt.hashpw(b"ancien-mdp-123", bcrypt.gensalt(4)).decode()
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    run = db.execute
    run(
        "INSERT INTO companies VALUES (?,?,?,?,?,?,?,?)",
        (
            ids["co"],
            "Acme",
            "Desc",
            "Rodez",
            "https://acme.fr",
            "/uploads/companies/logo.png",
            "company",
            1,
        ),
    )
    users = [
        (ids["admin"], "Admin@Old.fr", old_hash, "Ada", "Admin", 1, 0, 0, "", None),
        (
            ids["staff"],
            "staff@old.fr",
            old_hash,
            "Sam",
            "Staff",
            0,
            0,
            1,
            "manage_news,manage_users",
            None,
        ),
        (ids["alice"], "alice@old.fr", old_hash, "Alice", "A", 0, 1, 0, "", ids["co"]),
        (ids["bob"], "bob@old.fr", old_hash, "Bob", "B", 0, 0, 0, "", ids["co"]),
        (str(uuid.uuid4()), "ALICE@old.fr", old_hash, "Doublon", "X", 0, 0, 0, "", None),
    ]
    for u in users:
        run(
            "INSERT INTO users (id,email,password_hash,first_name,last_name,is_super_admin,"
            "is_company_admin,is_staff,permissions,company_id,is_active,profile_picture) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,1,'/uploads/users/profile_pictures/a.png')",
            u,
        )
    run(
        "INSERT INTO trainings VALUES (?,?,?,?,?,?,?,?,?)",
        (ids["tr"], "Excel", ids["co"], "d", None, "Bureautique", "atelier", '["x.pdf"]', 1),
    )
    run(
        "INSERT INTO training_sessions VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            ids["se"],
            ids["tr"],
            "2026-11-10T09:00:00",
            "2026-11-10T17:00:00",
            5,
            "Salle",
            None,
            "upcoming",
            1,
            ids["admin"],
        ),
    )
    run(
        "INSERT INTO formation_users VALUES (?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            ids["bob"],
            ids["tr"],
            ids["se"],
            "enrollment",
            0,
            "2026-10-01T10:00:00",
            None,
        ),
    )
    run(
        "INSERT INTO formation_users VALUES (?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), ids["alice"], ids["tr"], None, "interest", 1, None, None),
    )
    run(
        "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)",
        (ids["ev"], "Afterwork", "2026-11-05", "18:30", "blue", "Bar", ids["admin"], 1, 1),
    )
    run(
        "INSERT INTO invitations VALUES (?,?,?,?,?,?,?,?,?)",
        (
            ids["inv"],
            "event",
            ids["ev"],
            ids["admin"],
            ids["bob"],
            "accepted",
            1,
            "2026-10-01T10:00:00",
            "2026-10-02T10:00:00",
        ),
    )
    run(
        "INSERT INTO invitations VALUES (?,?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            "training",
            ids["tr"],
            ids["admin"],
            ids["bob"],
            "pending",
            0,
            None,
            None,
        ),
    )
    run(
        "INSERT INTO conversations VALUES (?,?,?,?,?,?)",
        (
            ids["conv"],
            "Équipe",
            ids["alice"],
            f"{ids['alice']},{ids['bob']},{ids['staff']}",
            1,
            "2026-10-01T10:00:00",
        ),
    )
    run(
        "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            ids["msg"],
            ids["alice"],
            None,
            ids["conv"],
            "Bonjour le groupe",
            None,
            None,
            1,
            1,
            "2026-10-01T11:00:00",
        ),
    )
    run(
        "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            ids["msg2"],
            ids["alice"],
            ids["bob"],
            None,
            "Message direct ancien",
            None,
            None,
            0,
            1,
            "2026-10-01T12:00:00",
        ),
    )
    run(
        "INSERT INTO notifications VALUES (?,?,?,?,?)",
        (ids["note"], ids["bob"], "Hello", 0, "2026-10-01T10:00:00"),
    )
    run(
        "INSERT INTO news VALUES (?,?,?,?,?,?,?,?)",
        (
            ids["news"],
            "TVA",
            "BOFiP",
            "résumé",
            "https://ex.fr/tva",
            "fiscalité",
            "2026-10-01T00:00:00",
            "2026-10-01T00:00:00",
        ),
    )
    run(
        "INSERT INTO saved_news VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            str(uuid.uuid4()),
            ids["bob"],
            str(uuid.uuid4()),
            "Archivé",
            None,
            None,
            None,
            None,
            None,
            "2026-10-02T00:00:00",
        ),
    )
    run("INSERT INTO site_content VALUES (?,?,?)", ("landing", '{"slogan": "Ancien slogan"}', None))
    db.commit()
    db.close()
    return f"sqlite:///{path}"


def test_full_import(session, legacy_url):
    """L'import complet reprend toutes les entités de l'ancienne base."""
    counts = LegacyImporter(legacy_url, session).run()
    assert counts["companies"] == 1
    assert counts["users"] == 4 and counts["users_ignorés_email_dupliqué"] == 1
    assert counts["invitations"] == 1 and counts["invitations_ignorées"] == 1

    admin = session.get(User, uuid.UUID(ids["admin"]))
    assert admin.email == "admin@old.fr" and admin.role == "super_admin"
    staff = session.get(User, uuid.UUID(ids["staff"]))
    assert staff.role == "staff" and staff.permissions == ["manage_news", "manage_users"]
    alice = session.get(User, uuid.UUID(ids["alice"]))
    assert alice.is_company_admin and alice.company_id == uuid.UUID(ids["co"])
    assert alice.avatar_path == "avatars/a.png"

    assert session.get(Company, uuid.UUID(ids["co"])).logo_path == "logos/logo.png"
    training = session.get(Training, uuid.UUID(ids["tr"]))
    assert training.kind == "atelier" and training.documents == ["trainings/x.pdf"]
    assert session.get(TrainingSession, uuid.UUID(ids["se"])).max_participants == 5
    enrollments = {e.user_id: e for e in session.scalars(select(TrainingEnrollment))}
    assert enrollments[uuid.UUID(ids["bob"])].enrolled_at is not None
    assert enrollments[uuid.UUID(ids["alice"])].interested is True
    event = session.get(Event, uuid.UUID(ids["ev"]))
    assert str(event.event_time) == "18:30:00" and event.is_public
    assert session.get(Invitation, uuid.UUID(ids["inv"])).status == "accepted"
    assert session.get(Notification, uuid.UUID(ids["note"])).content == "Hello"
    assert session.scalar(select(func.count()).select_from(SavedArticle)) == 1
    assert session.get(SiteContent, "landing").value == {"slogan": "Ancien slogan"}


def test_conversations_and_messages(session, legacy_url):
    """Les conversations et messages sont importés, dont les directs implicites."""
    counts = LegacyImporter(legacy_url, session).run()
    group = session.get(Conversation, uuid.UUID(ids["conv"]))
    assert group.kind == "group" and len(group.participants) == 3
    assert session.get(Message, uuid.UUID(ids["msg"])).content == "Bonjour le groupe"
    # le message direct sans conversation a donné lieu à une conversation directe
    assert counts["conversations_directes_créées"] == 1
    direct_message = session.get(Message, uuid.UUID(ids["msg2"]))
    direct = session.get(Conversation, direct_message.conversation_id)
    assert direct.kind == "direct" and {p.user_id for p in direct.participants} == {
        uuid.UUID(ids["alice"]),
        uuid.UUID(ids["bob"]),
    }


def test_import_is_idempotent(session, legacy_url):
    """Rejouer l'import ne crée aucun doublon."""
    LegacyImporter(legacy_url, session).run()
    second = LegacyImporter(legacy_url, session).run()
    assert sum(v for k, v in second.items() if not k.startswith(("users_", "invitations_"))) == 0
    assert session.scalar(select(func.count()).select_from(User)) == 4
    assert session.scalar(select(func.count()).select_from(Message)) == 2


def test_migrated_users_can_log_in_with_old_password(client, session, legacy_url):
    """Les utilisateurs migrés se connectent avec leur ancien mot de passe."""
    LegacyImporter(legacy_url, session).run()
    response = client.post(
        f"{API}/auth/login", json={"email": "bob@old.fr", "password": "ancien-mdp-123"}
    )
    assert response.status_code == 200
    # le hash bcrypt est remplacé par un hash Argon2 à la première connexion
    session.expire_all()
    assert session.get(User, uuid.UUID(ids["bob"])).password_hash.startswith("$argon2")
    bad = client.post(
        f"{API}/auth/login", json={"email": "bob@old.fr", "password": "mauvais-mdp-123"}
    )
    assert bad.status_code == 401


def test_uploaded_files_are_copied(session, legacy_url, tmp_path):
    """Les fichiers téléversés de l'ancienne application sont copiés."""
    uploads = tmp_path / "old_uploads"
    (uploads / "users" / "profile_pictures").mkdir(parents=True)
    (uploads / "users" / "profile_pictures" / "a.png").write_bytes(b"png")
    LegacyImporter(legacy_url, session, uploads).run()
    alice = session.get(User, uuid.UUID(ids["alice"]))
    assert alice.avatar_path == "avatars/a.png"
    # fichier absent côté source : pas de chemin vers un fichier inexistant
    assert session.get(Company, uuid.UUID(ids["co"])).logo_path is None


def test_create_admin(session):
    """Création d'un super admin, avec refus des doublons."""
    user = create_admin(session, "Root@Site.fr", "motdepasse-solide")
    assert user.email == "root@site.fr" and user.role == "super_admin"
    with pytest.raises(ConflictError):
        create_admin(session, "root@site.fr", "autre-mdp-123")


def test_seed_demo_is_idempotent_and_usable(client, session):
    """Le jeu de démo est idempotent et utilisable."""
    first = seed_demo(session)
    assert first["entreprises"] == 4
    assert seed_demo(session) == {}
    assert session.scalar(select(func.count()).select_from(Company)) == 4
    login = client.post(
        f"{API}/auth/login", json={"email": "lea@demo.fr", "password": "demo-password-1"}
    )
    assert login.status_code == 200


def test_cli_seed_and_refuses_in_production(monkeypatch, capsys):
    """La commande de seed est refusée en production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "s" * 40)
    monkeypatch.setenv("MAIL_BACKEND", "smtp")
    from app.core.config import get_settings

    get_settings.cache_clear()
    assert cli.main(["seed-demo"]) == 1
    assert "Refusé en production" in capsys.readouterr().err
