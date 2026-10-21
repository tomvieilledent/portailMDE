"""Formations de démonstration : catalogue, sessions, inscriptions et demandes en attente.

Idempotent : une formation déjà présente (même titre) est mise à jour (lien, description, visuel),
ses sessions ne sont créées que si elle n'en a pas encore.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.migration import seed_assets as assets
from app.models import (
    Company,
    Invitation,
    Training,
    TrainingEnrollment,
    TrainingSession,
    User,
)
from app.models.enums import SessionStatus

LONG = (
    "{intro}\n\nObjectifs\n- {a}\n- {b}\n- {c}\n\nProgramme\nMatin : apports théoriques et "
    "études de cas tirées de vos entreprises. Après-midi : mise en pratique en sous-groupes, "
    "retours individuels du formateur et plan d'action personnalisé.\n\nPublic et prérequis\n"
    "Dirigeants, associés et collaborateurs des entreprises de la Maison de l'Économie. Aucun "
    "prérequis ; apportez un cas concret à travailler. Les supports sont remis à l'issue de "
    "la session."
)

# (titre, catégorie, type, propriétaire, couleur, visuel, active, lien, [intro, a, b, c])
CATALOGUE = [
    (
        "Réussir son pitch",
        "Communication",
        "atelier",
        "Formations Sud",
        "#7c3aed",
        True,
        True,
        "https://formations-sud.example/pitch",
        [
            "Structurer et présenter son projet en cinq minutes devant des financeurs.",
            "Construire un récit clair",
            "Maîtriser sa prise de parole",
            "Répondre aux objections",
        ],
    ),
    (
        "Comptabilité pour dirigeants",
        "Gestion",
        "formation",
        "Cabinet Delmas",
        "#475569",
        True,
        True,
        "https://cabinet-delmas.example/formation",
        [
            "Lire un bilan, suivre sa trésorerie et piloter avec quelques indicateurs fiables.",
            "Comprendre bilan et compte de résultat",
            "Anticiper sa trésorerie",
            "Choisir ses indicateurs",
        ],
    ),
    (
        "Marketing digital pour TPE",
        "Marketing",
        "formation",
        "NumériSud",
        "#0891b2",
        True,
        True,
        None,
        [
            "Gagner en visibilité en ligne avec un budget limité.",
            "Définir sa cible",
            "Choisir ses canaux",
            "Mesurer ses résultats",
        ],
    ),
    (
        "Management d'équipe",
        "Management",
        "formation",
        "Coach & Cap",
        "#db2777",
        False,
        True,
        "https://coach-et-cap.example/management",
        [
            "Poser un cadre, déléguer et donner du feedback au quotidien.",
            "Fixer des objectifs clairs",
            "Animer ses réunions",
            "Gérer les tensions",
        ],
    ),
    (
        "Négocier avec ses fournisseurs",
        "Commercial",
        "atelier",
        "Formations Sud",
        "#b45309",
        False,
        True,
        None,
        [
            "Préparer une négociation et défendre sa marge sans abîmer la relation.",
            "Préparer ses arguments",
            "Connaître ses marges de manœuvre",
            "Conclure un accord durable",
        ],
    ),
    (
        "Financer sa première levée",
        "Finance",
        "atelier",
        "Crédit Mutuel Rodez",
        "#1d4ed8",
        True,
        True,
        "https://example.org/levee",
        [
            "Panorama des financements : prêts d'honneur, subventions, investisseurs.",
            "Choisir le bon financement",
            "Monter son dossier",
            "Préparer les rendez-vous",
        ],
    ),
    (
        "Excel avancé",
        "Bureautique",
        "formation",
        "Formations Sud",
        "#15803d",
        False,
        True,
        None,
        [
            "Tableaux croisés dynamiques, formules avancées et automatisations simples.",
            "Fiabiliser ses tableaux",
            "Analyser vite",
            "Automatiser les tâches répétitives",
        ],
    ),
    (
        "Droit du travail (archivée)",
        "Juridique",
        "formation",
        "Cabinet Delmas",
        "#6b7280",
        False,
        False,
        None,
        [
            "Contrats, durée du travail, ruptures : l'essentiel pour un premier employeur.",
            "Choisir un contrat",
            "Respecter la durée du travail",
            "Sécuriser une rupture",
        ],
    ),
    # Formations sans session programmée : elles reçoivent des demandes d'intérêt.
    (
        "Rédiger un cahier des charges",
        "Gestion de projet",
        "atelier",
        "Coach & Cap",
        "#0f766e",
        True,
        True,
        "https://example.org/cahier-des-charges",
        [
            "Cadrer un projet avec un prestataire sans zone d'ombre.",
            "Formaliser le besoin",
            "Prioriser les fonctionnalités",
            "Suivre la recette",
        ],
    ),
    (
        "Cybersécurité pour dirigeants",
        "Numérique",
        "formation",
        "NumériSud",
        "#9333ea",
        False,
        True,
        None,
        [
            "Protéger ses données et réagir à une attaque quand on n'a pas de service informatique.",
            "Repérer les menaces courantes",
            "Sauvegarder correctement",
            "Préparer un plan de réaction",
        ],
    ),
    (
        "Prise de parole en public",
        "Communication",
        "atelier",
        "Formations Sud",
        "#ea580c",
        False,
        True,
        None,
        [
            "Gagner en aisance à l'oral, en réunion comme en conférence.",
            "Gérer son trac",
            "Capter l'attention",
            "Conclure avec impact",
        ],
    ),
]

# (indice formation, décalage en jours, durée en heures, statut, public, lieu, lien)
SESSIONS = [
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

# Demandes en attente (indice formation → indices des membres intéressés ; 0 = Léa)
INTERESTED = {8: [0, 6, 7, 8, 9, 10], 9: [1, 11, 12], 10: []}


def _at(days: int, hour: int) -> datetime:
    """Date/heure (UTC) décalée de ``days`` jours par rapport à aujourd'hui."""
    now = datetime.now(UTC).replace(hour=hour, minute=0, second=0, microsecond=0)
    return now + timedelta(days=days)


def _enrollment(session: Session, user: User, training: Training, **fields):
    """Inscription (ou demande) de l'utilisateur ; créée si absente (contrainte d'unicité)."""
    row = session.scalar(
        select(TrainingEnrollment).where(
            TrainingEnrollment.user_id == user.id, TrainingEnrollment.training_id == training.id
        )
    )
    if row is None:
        row = TrainingEnrollment(user_id=user.id, training_id=training.id)
        session.add(row)
    for key, value in fields.items():
        setattr(row, key, value)
    return row


def seed_trainings(
    session: Session, companies: dict[str, Company], admin: User, members: list[User]
) -> dict[str, int]:
    """Crée ou met à jour les formations de démonstration, leurs sessions et leurs demandes."""
    trainings: list[Training] = []
    for i, (title, cat, kind, owner, color, picture, active, link, text) in enumerate(CATALOGUE):
        training = session.scalar(select(Training).where(Training.title == title)) or Training(
            title=title
        )
        training.category, training.kind, training.is_active = cat, kind, active
        training.company_id = companies[owner].id
        training.link = link
        training.description = LONG.format(intro=text[0], a=text[1], b=text[2], c=text[3])
        training.picture_path = (
            assets.training_picture(f"training-{i}", title, color) if picture else None
        )
        session.add(training)
        trainings.append(training)
    session.flush()

    created_sessions: dict[int, TrainingSession] = {}
    for t_idx, offset, hours, status, public, place, link in SESSIONS:
        training = trainings[t_idx]
        if session.scalar(
            select(func.count())
            .select_from(TrainingSession)
            .where(TrainingSession.training_id == training.id)
        ):
            continue
        start = _at(offset, 9)
        sess = TrainingSession(
            training_id=training.id,
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
        session.flush()
        created_sessions.setdefault(t_idx, sess)

    if 2 in created_sessions:  # session complète (3/3)
        for user in members[:3]:
            _enrollment(
                session,
                user,
                trainings[1],
                session_id=created_sessions[2].id,
                enrolled_at=_at(-2, 10),
            )
    if 6 in created_sessions:  # formation terminée
        for user in members[3:6]:
            _enrollment(
                session,
                user,
                trainings[4],
                session_id=created_sessions[6].id,
                enrolled_at=_at(-30, 9),
                completed_at=_at(-20, 17),
            )
    pitch = created_sessions.get(0)
    if pitch is not None:
        session.add(Invitation(session_id=pitch.id, inviter_id=admin.id, invitee_id=members[0].id))

    # Demandes en attente sur les formations sans session
    waiting = 0
    for t_idx, who in INTERESTED.items():
        for m_idx in who:
            _enrollment(session, members[m_idx], trainings[t_idx], interested=True)
            waiting += 1
    session.commit()
    return {"formations": len(trainings), "sessions": len(created_sessions), "demandes": waiting}
