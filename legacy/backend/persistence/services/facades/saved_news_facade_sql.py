"""Saved-news (per-user bookmarks) persistence facade (SQLAlchemy)."""

from datetime import datetime, timezone
from typing import Any

from backend.persistence.models import SavedNews as ORMSavedNews
from backend.persistence.models import News as ORMNews
from ._common_sql import isoformat, normalize_text, session_scope


class SavedNewsFacade:
    """SQLAlchemy-backed facade for per-user saved-article operations."""

    def save(self, user_id, news_id=None, title=None, source=None, summary=None,
             url=None, published_at=None, category=None):
        """Bookmark an article for *user_id*.

        If *news_id* is given and the article still exists, missing fields are
        snapshotted from the ``news`` row. Idempotent: returns the existing
        bookmark if the (user, article) pair is already saved.
        """
        with session_scope() as db:
            if news_id:
                existing: Any = db.query(ORMSavedNews).filter(
                    ORMSavedNews.user_id == user_id,
                    ORMSavedNews.news_id == news_id,
                ).first()
                if existing:
                    return self._to_dict(existing)

                article: Any = db.query(ORMNews).filter(ORMNews.id == news_id).first()
                if article:
                    title = title or article.title
                    source = source or article.source
                    summary = summary or article.summary
                    url = url or article.url
                    category = category or article.category
                    published_at = published_at or article.published_at

            if not title:
                # Can't bookmark: unknown article and no snapshot title provided.
                return None

            saved = ORMSavedNews(
                user_id=user_id,
                news_id=news_id,
                title=normalize_text(title),
                source=normalize_text(source),
                summary=normalize_text(summary),
                url=normalize_text(url),
                category=normalize_text(category),
                published_at=published_at,
                saved_at=datetime.now(timezone.utc),
            )
            db.add(saved)
            db.flush()
            db.refresh(saved)
            return self._to_dict(saved)

    def list_for_user(self, user_id):
        """Return all bookmarks for *user_id*, newest first."""
        with session_scope() as db:
            rows = (db.query(ORMSavedNews)
                    .filter(ORMSavedNews.user_id == user_id)
                    .order_by(ORMSavedNews.saved_at.desc())
                    .all())
            return [self._to_dict(row) for row in rows]

    def delete(self, saved_id, user_id):
        """Remove a bookmark owned by *user_id*. Returns True if deleted."""
        with session_scope() as db:
            saved: Any = db.query(ORMSavedNews).filter(
                ORMSavedNews.id == saved_id,
                ORMSavedNews.user_id == user_id,
            ).first()
            if not saved:
                return False
            db.delete(saved)
            return True

    def _to_dict(self, saved):
        return {
            'id': saved.id,
            'news_id': saved.news_id,
            'title': saved.title,
            'source': saved.source,
            'summary': saved.summary,
            'url': saved.url,
            'category': saved.category,
            'published_at': isoformat(saved.published_at),
            'saved_at': isoformat(saved.saved_at),
        }
