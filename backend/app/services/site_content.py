"""Contenu éditable du site (page d'accueil)."""

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models import SiteContent

DEFAULT_LANDING = {
    "slogan": "De l'idée à la création",
    "subtitle": (
        "La Maison de l'Économie accompagne les entrepreneurs à chaque étape "
        "de leur développement, de l'idée à l'entreprise installée."
    ),
    "sections": [
        {
            "title": "Incubateur",
            "duration": "Jusqu'à 24 mois",
            "description": (
                "Accueille et accompagne les porteurs de projets innovants du concept à la "
                "création. Suivi personnalisé, outils méthodologiques, formations, coaching, "
                "hébergement en open-space et écosystème entrepreneurial complet."
            ),
            "highlight": "De l'idée à la création d'entreprise, étape par étape",
        },
        {
            "title": "Pépinière d'entreprises",
            "duration": "48 mois",
            "description": (
                "Héberge les jeunes entreprises. Bureaux privatifs ou open-space, "
                "accompagnement quotidien, services mutualisés, accès formations et coachs, "
                "appui au recrutement."
            ),
            "highlight": "Un tremplin vers un territoire attractif et dynamique",
        },
        {
            "title": "Hôtel d'entreprises",
            "duration": "Jusqu'à 12 mois",
            "description": (
                "Réservé aux entreprises en fin de parcours pépinière ou à l'accueil temporaire "
                "d'entreprises exogènes. Bureaux fonctionnels et privatifs, services mutualisés, "
                "hébergement simple sans accompagnement."
            ),
            "highlight": "",
        },
    ],
}

DEFAULTS = {"landing": DEFAULT_LANDING}


def get_content(session: Session, key: str) -> dict:
    """Retourne le contenu enregistré pour la clé, ou son contenu par défaut."""
    if key not in DEFAULTS:
        raise NotFoundError("Bloc de contenu inconnu")
    stored = session.get(SiteContent, key)
    return stored.value if stored else DEFAULTS[key]


def set_content(session: Session, key: str, value: dict) -> dict:
    """Enregistre le contenu associé à la clé."""
    if key not in DEFAULTS:
        raise NotFoundError("Bloc de contenu inconnu")
    stored = session.get(SiteContent, key)
    if stored:
        stored.value = value
    else:
        session.add(SiteContent(key=key, value=value))
    session.commit()
    return value
