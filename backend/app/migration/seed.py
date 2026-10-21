"""Données de démonstration et création du premier administrateur."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.core.permissions import validate_permissions
from app.core.security import hash_password
from app.migration import seed_assets as assets
from app.models import (
    Company,
    Conversation,
    ConversationParticipant,
    Event,
    Invitation,
    Message,
    NewsArticle,
    Notification,
    Training,
    TrainingEnrollment,
    TrainingSession,
    User,
)
from app.models.enums import (
    ConversationKind,
    InvitationStatus,
    SessionStatus,
    UserRole,
)


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
    """Retourne l'utilisateur correspondant à l'email, en le créant s'il n'existe pas."""
    user = session.scalar(select(User).where(func.lower(User.email) == email))
    if not user:
        user = User(email=email, password_hash=hash_password(password), **fields)
        session.add(user)
        session.flush()
    return user


# (nom, description, lieu, type, couleur, forme du logo ou None si sans logo, site web)
COMPANIES = [
    (
        "Atelier Lumière",
        "Studio de design graphique et d'identité visuelle.",
        "Rodez",
        "company",
        "#e07a1f",
        "circle",
        "https://atelier-lumiere.example",
    ),
    (
        "AgriTech Aveyron",
        "Capteurs connectés pour l'agriculture de précision.",
        "Rodez",
        "company",
        "#5da020",
        "square",
        "https://agritech-aveyron.example",
    ),
    (
        "Conseil & Co",
        "Accompagnement RH et gestion pour les TPE.",
        "Onet-le-Château",
        "company",
        "#2563eb",
        "diamond",
        None,
    ),
    (
        "Formations Sud",
        "Organisme de formation professionnelle.",
        "Rodez",
        "trainer",
        "#7c3aed",
        "bars",
        "https://formations-sud.example",
    ),
    (
        "Brasserie des Causses",
        "Brasserie artisanale et circuits courts.",
        "Millau",
        "company",
        "#b45309",
        "circle",
        "https://brasserie-causses.example",
    ),
    (
        "NumériSud",
        "Développement web et applications mobiles.",
        "Rodez",
        "company",
        "#0891b2",
        "square",
        "https://numerisud.example",
    ),
    (
        "Cabinet Delmas",
        "Expertise comptable et gestion de patrimoine.",
        "Rodez",
        "company",
        "#475569",
        None,
        None,
    ),
    (
        "Éco-Bâti 12",
        "Rénovation énergétique et éco-construction.",
        "Villefranche-de-Rouergue",
        "company",
        "#15803d",
        "diamond",
        None,
    ),
    (
        "Rouergue Robotique",
        "Robots collaboratifs pour l'industrie locale.",
        "Rodez",
        "company",
        "#dc2626",
        "bars",
        "https://rouergue-robotique.example",
    ),
    (
        "Coach & Cap",
        "Coaching de dirigeants et d'équipes.",
        "Rodez",
        "trainer",
        "#db2777",
        None,
        None,
    ),
    (
        "Crédit Mutuel Rodez",
        "Partenaire bancaire de la Maison de l'Économie.",
        "Rodez",
        "partner",
        "#1d4ed8",
        "square",
        None,
    ),
    (
        "Ancienne Fabrique",
        "Entreprise hébergée jusqu'en 2023 (désactivée).",
        "Rodez",
        "company",
        "#6b7280",
        None,
        None,
    ),
]

FIRST = [
    "Léa",
    "Hugo",
    "Sofia",
    "Karim",
    "Manon",
    "Lucas",
    "Camille",
    "Nathan",
    "Inès",
    "Théo",
    "Chloé",
    "Maxime",
    "Jade",
    "Antoine",
    "Zoé",
    "Romain",
    "Clara",
    "Julien",
    "Emma",
    "Paul",
    "Sarah",
    "Adrien",
    "Louise",
    "Mathis",
    "Anaïs",
    "Baptiste",
    "Eva",
    "Quentin",
    "Lina",
    "Florian",
    "Margaux",
    "Étienne",
    "Salomé",
    "Victor",
    "Noémie",
    "Gabriel",
    "Alice",
    "Damien",
    "Océane",
    "Samir",
    "Elsa",
    "Thomas",
    "Yasmine",
    "Benoît",
    "Clémence",
    "Axel",
]
LAST = [
    "Martin",
    "Bernard",
    "Petit",
    "Roux",
    "Durand",
    "Moreau",
    "Laurent",
    "Simon",
    "Michel",
    "Lefebvre",
    "Garcia",
    "David",
    "Bertrand",
    "Morel",
    "Fournier",
    "Girard",
    "Bonnet",
    "Dupont",
    "Lambert",
    "Fontaine",
    "Rousseau",
    "Vincent",
    "Muller",
    "Faure",
    "Andre",
    "Mercier",
    "Blanc",
    "Guerin",
    "Boyer",
    "Garnier",
    "Chevalier",
    "Francois",
    "Legrand",
    "Gauthier",
    "Perrin",
    "Robin",
    "Clement",
    "Morin",
    "Nicolas",
    "Henry",
    "Roussel",
    "Mathieu",
    "Gautier",
    "Masson",
    "Marchand",
    "Duval",
]
JOBS = [
    "Directeur·rice",
    "Développeur·se",
    "Responsable commercial",
    "Chargé·e de communication",
    "Comptable",
    "Ingénieur·e",
    "Designer",
    "Consultant·e",
    "Chef de projet",
    "Assistant·e de direction",
    "Technicien·ne",
]
COLORS = [
    "#5da020",
    "#e07a1f",
    "#2563eb",
    "#7c3aed",
    "#0891b2",
    "#dc2626",
    "#db2777",
    "#15803d",
    "#b45309",
]


def _ascii(text: str) -> str:
    """Minuscules sans accent, pour construire les adresses e-mail."""
    table = str.maketrans("àâäéèêëîïôöùûüç·", "aaaeeeeiioouuuc.")
    return text.lower().translate(table).replace("..", ".").strip(".")


def _at(days: int, hour: int, minute: int = 0) -> datetime:
    """Date/heure (UTC) décalée de ``days`` jours par rapport à aujourd'hui."""
    base = datetime.now(UTC).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base + timedelta(days=days)


def seed_demo(session: Session, password: str = "demo-password-1") -> dict[str, int]:
    """Jeu de données de démonstration complet, idempotent (rejouable sans doublons).

    Couvre les cas à tester : entreprises avec/sans logo, active/désactivée, de chaque type ;
    utilisateurs avec/sans avatar et carte de visite, administrateurs d'entreprise, staff,
    comptes désactivés ou à mot de passe temporaire ; événements passés/en cours/à venir ;
    formations et sessions de tous statuts ; inscriptions, invitations, messagerie, notifications.
    """
    if session.scalar(select(Company.id).where(Company.name == "Brasserie des Causses")):
        return {}

    # ── Entreprises (logo généré pour celles qui en ont un) ──────────────────────────────
    companies: dict[str, Company] = {}
    for i, (name, desc, place, kind, color, shape, site) in enumerate(COMPANIES):
        company = session.scalar(select(Company).where(Company.name == name)) or Company(name=name)
        company.description, company.location, company.kind = desc, place, kind
        company.website_url = site
        company.is_active = name != "Ancienne Fabrique"
        company.logo_path = assets.logo(f"company-{i}", name, color, shape) if shape else None
        session.add(company)
        companies[name] = company
    session.flush()
    company_list = [c for n, c in companies.items() if n != "Ancienne Fabrique"]

    # ── Comptes de référence ─────────────────────────────────────────────────────────────
    admin = _user(
        session,
        "admin@demo.fr",
        password,
        first_name="Alice",
        last_name="Admin",
        job_title="Directrice de la Maison de l'Économie",
        phone="05 65 00 00 01",
        role=UserRole.SUPER_ADMIN,
    )
    admin.avatar_path = assets.avatar("admin", "Alice", "Admin", "#4a7a1a")
    admin.business_card_path = assets.business_card(
        "admin",
        "Alice Admin",
        "Directrice",
        "Maison de l'Économie",
        "admin@demo.fr",
        "05 65 00 00 01",
        "#4a7a1a",
    )
    staff_full = _user(
        session,
        "staff@demo.fr",
        password,
        first_name="Samuel",
        last_name="Staff",
        job_title="Chargé de mission",
        role=UserRole.STAFF,
        permissions=validate_permissions(["manage_trainings", "manage_news"]),
    )
    staff_full.avatar_path = assets.avatar("staff", "Samuel", "Staff", "#2563eb")
    _user(
        session,
        "staff-entreprises@demo.fr",
        password,
        first_name="Nadia",
        last_name="Gestion",
        job_title="Chargée d'accueil",
        role=UserRole.STAFF,
        permissions=validate_permissions(["manage_companies", "manage_users"]),
    )

    # ── Membres : 42 personnes réparties sur les entreprises actives ─────────────────────
    members: list[User] = []
    for idx in range(42):
        first, last = FIRST[idx], LAST[idx]
        email = "lea@demo.fr" if idx == 0 else f"{_ascii(first)}.{_ascii(last)}@demo.fr"
        company = company_list[idx % len(company_list)]
        user = _user(
            session,
            email,
            password,
            first_name=first,
            last_name=last,
            job_title=None if idx % 9 == 4 else JOBS[idx % len(JOBS)],
            phone=None
            if idx % 7 == 3
            else f"06 {10 + idx:02d} {20 + idx:02d} {30 + idx:02d} {40 + idx:02d}",
            company_id=company.id,
            # un·e administrateur·rice par entreprise (les 11 premiers), quelques co-responsables
            is_company_admin=idx < len(company_list) or idx in (12, 20),
            is_active=idx not in (30, 37),  # 2 comptes désactivés
            must_change_password=idx in (25, 41),  # 2 mots de passe temporaires
        )
        color = COLORS[idx % len(COLORS)]
        user.avatar_path = (
            assets.avatar(f"user-{idx}", first, last, color) if idx % 5 != 2 else None
        )
        if idx % 5 in (0, 1):  # ~40 % ont une carte de visite
            user.business_card_path = assets.business_card(
                f"user-{idx}",
                f"{first} {last}",
                user.job_title or "",
                company.name,
                email,
                user.phone or "",
                color,
            )
        members.append(user)
    # Quelques personnes sans entreprise (cas « non rattaché »)
    for first, last in [("Pierre", "Solo"), ("Marie", "Indépendante")]:
        _user(
            session,
            f"{_ascii(first)}.{_ascii(last)}@demo.fr",
            password,
            first_name=first,
            last_name=last,
            job_title="Porteur de projet",
        )
    session.flush()
    lea = members[0]

    # ── Événements : passés, aujourd'hui, à venir (10+ actuels ou à venir) ───────────────
    today = date.today()
    events_spec = [
        (-12, time(9, 0), "Atelier réseau (passé)", True, None),
        (-3, time(14, 0), "Point d'étape trimestriel (passé)", False, None),
        (0, time(10, 0), "Petit-déjeuner des entrepreneurs", True, "Ouvert à tous, café offert."),
        (0, time(17, 30), "Permanence juridique", False, "Sur rendez-vous."),
        (2, time(12, 15), "Déjeuner partenaires bancaires", False, None),
        (
            4,
            time(18, 30),
            "Afterwork des entrepreneurs",
            True,
            "Rencontre conviviale ouverte à tous.",
        ),
        (7, time(9, 0), "Comité d'accompagnement", False, "Présentation des projets en cours."),
        (
            9,
            time(14, 0),
            "Webinaire : financer sa croissance",
            True,
            "Lien de connexion envoyé la veille.",
        ),
        (13, None, "Journée portes ouvertes", True, "Toute la journée."),
        (16, time(10, 30), "Visite d'un site industriel", False, None),
        (
            21,
            time(18, 0),
            "Conférence : IA et PME",
            True,
            "Amphithéâtre de la Maison de l'Économie.",
        ),
        (30, time(9, 30), "Assemblée générale", False, "Réservée aux entreprises hébergées."),
    ]
    events = []
    for offset, hour, title, public, desc in events_spec:
        ev = Event(
            title=title,
            event_date=today + timedelta(days=offset),
            event_time=hour,
            description=desc,
            is_public=public,
            created_by=admin.id,
        )
        session.add(ev)
        events.append(ev)
    session.flush()

    # ── Formations : avec/sans visuel, formation/atelier, active/inactive ────────────────
    trainings_spec = [
        ("Réussir son pitch", "Communication", "atelier", "Formations Sud", "#7c3aed", True, True),
        (
            "Comptabilité pour dirigeants",
            "Gestion",
            "formation",
            "Cabinet Delmas",
            "#475569",
            True,
            True,
        ),
        (
            "Marketing digital pour TPE",
            "Marketing",
            "formation",
            "NumériSud",
            "#0891b2",
            True,
            True,
        ),
        ("Management d'équipe", "Management", "formation", "Coach & Cap", "#db2777", False, True),
        (
            "Négocier avec ses fournisseurs",
            "Commercial",
            "atelier",
            "Formations Sud",
            "#b45309",
            False,
            True,
        ),
        (
            "Financer sa première levée",
            "Finance",
            "atelier",
            "Crédit Mutuel Rodez",
            "#1d4ed8",
            True,
            True,
        ),
        ("Excel avancé", "Bureautique", "formation", "Formations Sud", "#15803d", False, True),
        (
            "Droit du travail (archivée)",
            "Juridique",
            "formation",
            "Cabinet Delmas",
            "#6b7280",
            False,
            False,
        ),
    ]
    trainings = []
    for i, (title, cat, kind, owner, color, picture, active) in enumerate(trainings_spec):
        tr = Training(
            title=title,
            category=cat,
            kind=kind,
            is_active=active,
            company_id=companies[owner].id,
            description=f"{title} : programme détaillé, supports fournis et mise en pratique.",
            picture_path=assets.training_picture(f"training-{i}", title, color)
            if picture
            else None,
        )
        session.add(tr)
        trainings.append(tr)
    session.flush()

    sessions_spec = [  # (indice formation, décalage jours, durée h, statut, public, lieu, lien)
        (0, 10, 7, SessionStatus.UPCOMING, True, "Salle des Cèdres", None),
        (0, 40, 7, SessionStatus.UPCOMING, True, None, "https://visio.example/pitch"),
        (1, 5, 14, SessionStatus.UPCOMING, True, "Salle Aveyron", None),
        (2, 0, 4, SessionStatus.ONGOING, True, "Espace coworking", None),
        (2, 18, 4, SessionStatus.UPCOMING, False, None, "https://visio.example/marketing"),
        (3, 25, 7, SessionStatus.UPCOMING, True, "Salle des Cèdres", None),
        (4, -20, 3, SessionStatus.DONE, True, "Salle Aveyron", None),
        (5, 8, 3, SessionStatus.CANCELLED, True, "Salle des Cèdres", None),
        (6, 14, 7, SessionStatus.UPCOMING, True, None, "https://visio.example/excel"),
        (7, -60, 7, SessionStatus.DONE, False, "Salle Aveyron", None),
    ]
    sessions = []
    for t_idx, offset, hours, status, public, place, link in sessions_spec:
        start = _at(offset, 9)
        sess = TrainingSession(
            training_id=trainings[t_idx].id,
            start_at=start,
            end_at=start + timedelta(hours=hours),
            max_participants=3 if t_idx == 1 else 12,
            location=place,
            link=link,
            status=status,
            is_public=public,
            created_by=admin.id,
        )
        session.add(sess)
        sessions.append(sess)
    session.flush()

    # Inscriptions : session complète (3/3), intérêt simple, formation terminée
    for user in members[:3]:
        session.add(
            TrainingEnrollment(
                user_id=user.id,
                training_id=trainings[1].id,
                session_id=sessions[2].id,
                enrolled_at=_at(-2, 10),
            )
        )
    session.add(TrainingEnrollment(user_id=lea.id, training_id=trainings[0].id, interested=True))
    session.add(
        TrainingEnrollment(
            user_id=members[5].id,
            training_id=trainings[0].id,
            session_id=sessions[0].id,
            enrolled_at=_at(-1, 9),
        )
    )
    for user in members[3:6]:
        session.add(
            TrainingEnrollment(
                user_id=user.id,
                training_id=trainings[4].id,
                session_id=sessions[6].id,
                enrolled_at=_at(-30, 9),
                completed_at=_at(-20, 17),
            )
        )

    # ── Invitations (en attente / acceptée / refusée) ────────────────────────────────────
    for ev, status in (
        (events[4], InvitationStatus.PENDING),
        (events[6], InvitationStatus.PENDING),
        (events[7], InvitationStatus.ACCEPTED),
        (events[9], InvitationStatus.DECLINED),
    ):
        session.add(
            Invitation(
                event_id=ev.id,
                inviter_id=admin.id,
                invitee_id=lea.id,
                status=status,
                responded_at=None if status == InvitationStatus.PENDING else _at(-1, 11),
            )
        )
    session.add(Invitation(session_id=sessions[0].id, inviter_id=admin.id, invitee_id=lea.id))

    # ── Actualités ───────────────────────────────────────────────────────────────────────
    news = [
        (
            "Bienvenue sur le portail",
            "MDE",
            "vie de la Maison",
            "Retrouvez ici l'annuaire, la messagerie, l'agenda et les formations.",
        ),
        (
            "Nouvelle aide régionale à l'innovation",
            "Région Occitanie",
            "financement",
            "Un dispositif ouvert aux jeunes entreprises jusqu'à fin d'année.",
        ),
        (
            "Aveyron : la création d'entreprises en hausse",
            "Presse locale",
            "économie",
            "Le département enregistre une progression des créations sur un an.",
        ),
        (
            "Atelier cybersécurité pour les TPE",
            "MDE",
            "formation",
            "Un atelier pratique pour protéger ses données.",
        ),
        (
            "Appel à projets transition énergétique",
            "ADEME",
            "innovation",
            "Candidatures ouvertes jusqu'au mois prochain.",
        ),
        (
            "Une entreprise hébergée primée",
            "MDE",
            "vie de la Maison",
            "Félicitations à l'équipe pour ce prix régional.",
        ),
        (
            "Recrutement : les bons réflexes",
            "Conseil & Co",
            "ressources humaines",
            "Cinq conseils pour structurer ses premières embauches.",
        ),
        (
            "Nouveaux horaires de l'accueil",
            "MDE",
            "vie de la Maison",
            "L'accueil est ouvert de 8 h 30 à 18 h.",
        ),
    ]
    for i, (title, source, category, summary) in enumerate(news):
        session.add(
            NewsArticle(
                title=title,
                source=source,
                category=category,
                summary=summary,
                published_at=datetime.now(UTC) - timedelta(days=i * 3),
            )
        )

    # ── Messagerie : une conversation directe et un groupe, avec messages non lus ────────
    direct = Conversation(kind=ConversationKind.DIRECT, creator_id=admin.id)
    group = Conversation(
        kind=ConversationKind.GROUP, title="Entrepreneurs Rodez", creator_id=lea.id
    )
    session.add_all([direct, group])
    session.flush()
    for user in (admin, lea):
        session.add(
            ConversationParticipant(
                conversation_id=direct.id,
                user_id=user.id,
                last_read_at=_at(-1, 9) if user is lea else _at(0, 8),
            )
        )
    for user in [lea, admin, *members[1:5]]:
        session.add(
            ConversationParticipant(
                conversation_id=group.id,
                user_id=user.id,
                last_read_at=_at(-2, 9) if user is lea else _at(0, 8),
            )
        )
    chat = [
        (direct, admin, "Bonjour Léa, avez-vous reçu l'invitation au comité ?", -1, 9),
        (direct, lea, "Oui, merci ! Je confirme ma présence.", -1, 10),
        (direct, admin, "Parfait, à bientôt.", 0, 8),
        (group, lea, "Bonjour à tous, qui vient à l'afterwork jeudi ?", -1, 17),
        (group, members[1], "Présent !", -1, 18),
        (group, members[2], "Je serai en retard mais je viens.", 0, 7),
        (group, members[3], "Quelqu'un connaît un bon imprimeur sur Rodez ?", 0, 8),
    ]
    for conv, author, text, offset, hour in chat:
        session.add(
            Message(
                conversation_id=conv.id,
                author_id=author.id,
                content=text,
                created_at=_at(offset, hour),
            )
        )

    # ── Notifications ────────────────────────────────────────────────────────────────────
    for content, kind, read in (
        ("Alice Admin vous invite à « Déjeuner partenaires bancaires »", "invitation", False),
        ("Nouveau message dans « Entrepreneurs Rodez »", "conversation", False),
        ("Une nouvelle formation est disponible : Marketing digital pour TPE", "annonce", True),
    ):
        session.add(Notification(recipient_id=lea.id, content=content, kind=kind, is_read=read))

    session.commit()
    return {
        "entreprises": len(companies),
        "utilisateurs": 3 + len(members) + 2,
        "evenements": len(events),
        "formations": len(trainings),
        "sessions": len(sessions),
        "actualites": len(news),
    }
