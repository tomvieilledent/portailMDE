"""Editable site-content API resources (e.g. the public landing page)."""

from flask import request
from flask_jwt_extended import get_jwt_identity

from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.resources._helpers import _can
from backend.persistence.services import SiteContentService, UserService


content_service = SiteContentService()
user_service = UserService()

# Default landing content, served when nothing has been customised yet and used
# as the editing baseline. Only text is stored here; icons/colours stay in the
# frontend, keyed by card position.
DEFAULT_LANDING = {
    'slogan': "De l'idée à la création",
    'subtitle': (
        "La Maison de l'Économie accompagne les entrepreneurs à chaque étape "
        "de leur développement, de l'idée à l'entreprise installée."
    ),
    'sections': [
        {
            'title': 'Incubateur',
            'duration': "Jusqu'à 24 mois",
            'description': (
                'Accueille et accompagne les porteurs de projets innovants du '
                'concept à la création. Suivi personnalisé, outils '
                'méthodologiques, formations, coaching, hébergement en '
                'open-space et écosystème entrepreneurial complet.'
            ),
            'highlight': "De l'idée à la création d'entreprise, étape par étape",
        },
        {
            'title': "Pépinière d'entreprises",
            'duration': '48 mois',
            'description': (
                'Héberge les jeunes entreprises. Bureaux privatifs ou '
                'open-space, accompagnement quotidien, services mutualisés, '
                'accès formations et coachs, appui au recrutement.'
            ),
            'highlight': 'Un tremplin vers un territoire attractif et dynamique',
        },
        {
            'title': "Hôtel d'entreprises",
            'duration': "Jusqu'à 12 mois",
            'description': (
                "Réservé aux entreprises en fin de parcours pépinière ou à "
                "l'accueil temporaire d'entreprises exogènes. Bureaux "
                'fonctionnels et privatifs, services mutualisés, hébergement '
                'simple sans accompagnement.'
            ),
            'highlight': '',
        },
    ],
}

DEFAULTS = {'landing': DEFAULT_LANDING}


class ContentResource(Resource):
    """Read (public) or update (super admin) an editable content block."""

    def get(self, key):
        """Return the content block for *key*, falling back to defaults.

        Public: the landing page is shown to logged-out visitors.

        Args:
            key (str): Content block key (only ``'landing'`` is supported).

        Returns:
            tuple[dict, int]: ``{content}`` and 200, or 404 for unknown keys.
        """
        if key not in DEFAULTS:
            return error_response(ERROR_CODES['NOT_FOUND'], 'unknown content key', 404)
        stored = content_service.facade.get(key)
        return {'content': stored or DEFAULTS[key]}

    @jwt_required()
    def put(self, key):
        """Replace a content block. Restricted to super admins.

        Args:
            key (str): Content block key (only ``'landing'`` is supported).

        Expected JSON body:
            content (dict): The full content document to store.

        Returns:
            tuple[dict, int]: ``{content}`` and 200, or 400/403/404.
        """
        if key not in DEFAULTS:
            return error_response(ERROR_CODES['NOT_FOUND'], 'unknown content key', 404)
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_news'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to edit site content', 403)
        data = request.get_json(silent=True) or {}
        content = data.get('content')
        if not isinstance(content, dict):
            return error_response(
                ERROR_CODES['BAD_REQUEST'], 'content object is required', 400)
        saved = content_service.facade.set(key, content)
        return {'content': saved}
