"""News endpoints — list, create, sync, retrieve, delete."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.models.news import News as DomainNews
from backend.persistence.services import NewsService, SavedNewsService


news_service = NewsService()
saved_news_service = SavedNewsService()

# Valid category values (mirrors news_sync.SOURCES categories)
VALID_CATEGORIES = {'actualités', 'réglementation', 'vie-entreprises', 'opportunités', 'territoire'}


class NewsListResource(Resource):
    """List news items or create a new one."""

    def get(self):
        """Return a paginated list of news items.

        Query parameters:
            limit (int): Max items to return (default 100).
            category (str): Filter by category (réglementation, vie-entreprises,
                opportunités, territoire).
            source (str): Filter by source name (e.g. BODACC, BOAMP).

        Returns:
            tuple[dict, int]: ``{news}`` and 200.
        """
        limit = request.args.get('limit', default=20, type=int)
        offset = request.args.get('offset', default=0, type=int)
        category = request.args.get('category') or None
        source = request.args.get('source') or None
        return news_service.facade.list(limit=limit, offset=offset, category=category, source=source)

    @jwt_required()
    def post(self):
        """Create a news item manually.

        Expected JSON body:
            title (str): Article headline (required).
            source (str | None): Publisher name.
            summary (str | None): Short summary.
            url (str | None): Link to original article.
            published_at (str | None): ISO 8601 publication datetime.
            category (str | None): One of réglementation, vie-entreprises,
                opportunités, territoire.

        Returns:
            tuple[dict, int]: ``{news_item}`` and 201.
        """
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        if not title:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'title is required', 400)
        try:
            DomainNews(title=title)
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        article = news_service.facade.create(
            title,
            source=data.get('source'),
            summary=data.get('summary'),
            url=data.get('url'),
            published_at=data.get('published_at'),
            category=data.get('category'),
        )
        return {'news_item': article}, 201


class NewsResource(Resource):
    """Retrieve or delete a single news item."""

    def get(self, news_id):
        """Return a news item by id.

        Args:
            news_id (str): News UUID path parameter.

        Returns:
            tuple[dict, int]: ``{news_item}`` and 200, or 404.
        """
        article = news_service.facade.get(news_id)
        if not article:
            return error_response(ERROR_CODES['NOT_FOUND'], 'news item not found', 404)
        return {'news_item': article}

    @jwt_required()
    def delete(self, news_id):
        """Permanently delete a news item.

        Args:
            news_id (str): News UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not news_service.facade.delete(news_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'news item not found', 404)
        return {'msg': 'news item deleted'}


class SavedNewsListResource(Resource):
    """List or create the current user's saved articles (bookmarks)."""

    @jwt_required()
    def get(self):
        """Return the current user's saved articles, newest first.

        Returns:
            tuple[dict, int]: ``{items: [...]}`` and 200.
        """
        items = saved_news_service.facade.list_for_user(get_jwt_identity())
        return {'items': items}

    @jwt_required()
    def post(self):
        """Bookmark an article for the current user.

        Expected JSON body (either reference an existing article or pass a
        full snapshot):
            news_id (str | None): Id of the article to bookmark.
            title (str): Required when no resolvable ``news_id`` is given.
            source, summary, url, category, published_at: Optional snapshot.

        Returns:
            tuple[dict, int]: ``{saved}`` and 201.
        """
        data = request.get_json(silent=True) or {}
        news_id = data.get('news_id')
        title = data.get('title')
        if not news_id and not title:
            return error_response(ERROR_CODES['BAD_REQUEST'],
                                  'news_id or title is required', 400)
        saved = saved_news_service.facade.save(
            get_jwt_identity(),
            news_id=news_id,
            title=title,
            source=data.get('source'),
            summary=data.get('summary'),
            url=data.get('url'),
            published_at=data.get('published_at'),
            category=data.get('category'),
        )
        if saved is None:
            return error_response(ERROR_CODES['NOT_FOUND'],
                                  'article not found', 404)
        return {'saved': saved}, 201


class SavedNewsResource(Resource):
    """Delete one of the current user's saved articles."""

    @jwt_required()
    def delete(self, saved_id):
        """Remove a saved article owned by the current user.

        Args:
            saved_id (str): Saved-article UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not saved_news_service.facade.delete(saved_id, get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'],
                                  'saved article not found', 404)
        return {'msg': 'saved article removed'}


class NewsSyncResource(Resource):
    """Trigger a manual sync of external news sources (admin only)."""

    @jwt_required()
    def post(self):
        """Sync all configured external sources and store new items.

        Returns:
            tuple[dict, int]: ``{synced}`` count and 200.
        """
        from backend.services.news_sync import sync_all
        try:
            count = sync_all()
            return {'synced': count}, 200
        except Exception as exc:
            return error_response(ERROR_CODES['INTERNAL_ERROR'], str(exc), 500)
