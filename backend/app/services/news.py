"""Actualités : CRUD, favoris et synchronisation des flux RSS."""

import logging
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from time import mktime

import feedparser
import httpx
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.models import NewsArticle, SavedArticle

logger = logging.getLogger(__name__)

# Sources de veille économique (réglementation et vie des entreprises).
RSS_SOURCES = [
    {
        "name": "Net-Entreprises",
        "category": "réglementation",
        "url": "https://www.net-entreprises.fr/actualites/rss/",
    },
    {
        "name": "Ministère du Travail",
        "category": "réglementation",
        "url": "https://travail-emploi.gouv.fr/rss.xml",
    },
    {"name": "Douanes", "category": "réglementation", "url": "https://www.douane.gouv.fr/rss.xml"},
    {"name": "INPI", "category": "réglementation", "url": "https://www.inpi.fr/rss.xml"},
    {
        "name": "Journal Officiel",
        "category": "réglementation",
        "url": "https://www.legifrance.gouv.fr/feeds/jorf",
    },
    {"name": "BOFiP", "category": "réglementation", "url": "https://bofip.impots.gouv.fr/rss.xml"},
]
MAX_ENTRIES_PER_FEED = 20
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; portailMDE/1.0)"}

Fetcher = Callable[[str], str]


def http_fetch(url: str) -> str:
    """Télécharge le contenu d'un flux par HTTP."""
    return httpx.get(url, headers=_HEADERS, timeout=10, follow_redirects=True).text


# --- Lecture / écriture -------------------------------------------------------------------


def list_articles(
    session: Session,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    category: str | None = None,
) -> tuple[list[NewsArticle], int]:
    """Liste les articles, du plus récent au plus ancien, avec recherche et filtre par catégorie."""
    query = select(NewsArticle)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(NewsArticle.title.ilike(pattern), NewsArticle.summary.ilike(pattern))
        )
    if category:
        query = query.where(NewsArticle.category == category)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = session.scalars(
        query.order_by(NewsArticle.published_at.desc().nulls_last(), NewsArticle.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total


def get_article(session: Session, article_id: uuid.UUID) -> NewsArticle:
    """Retourne un article ou lève une erreur s'il est introuvable."""
    article = session.get(NewsArticle, article_id)
    if not article:
        raise NotFoundError("Article introuvable")
    return article


def create_article(session: Session, data) -> NewsArticle:
    """Crée un article ; l'URL doit être unique."""
    if data.url and session.scalar(select(NewsArticle.id).where(NewsArticle.url == data.url)):
        raise ConflictError("Un article avec cette URL existe déjà")
    article = NewsArticle(**data.model_dump())
    session.add(article)
    session.commit()
    return article


def delete_article(session: Session, article_id: uuid.UUID) -> None:
    """Supprime un article."""
    session.delete(get_article(session, article_id))
    session.commit()


# --- Favoris ------------------------------------------------------------------------------


def save_article(session: Session, user_id: uuid.UUID, article_id: uuid.UUID) -> SavedArticle:
    """Enregistre une copie de l'article parmi les favoris de l'utilisateur."""
    article = get_article(session, article_id)
    existing = session.scalar(
        select(SavedArticle).where(
            SavedArticle.user_id == user_id, SavedArticle.article_id == article.id
        )
    )
    if existing:
        return existing
    saved = SavedArticle(
        user_id=user_id,
        article_id=article.id,
        title=article.title,
        source=article.source,
        summary=article.summary,
        url=article.url,
        category=article.category,
        published_at=article.published_at,
    )
    session.add(saved)
    session.commit()
    return saved


def list_saved(session: Session, user_id: uuid.UUID) -> list[SavedArticle]:
    """Liste les articles enregistrés par l'utilisateur, du plus récent au plus ancien."""
    return list(
        session.scalars(
            select(SavedArticle)
            .where(SavedArticle.user_id == user_id)
            .order_by(SavedArticle.saved_at.desc())
        ).all()
    )


def unsave(session: Session, user_id: uuid.UUID, saved_id: uuid.UUID) -> None:
    """Retire un article des favoris de l'utilisateur."""
    saved = session.get(SavedArticle, saved_id)
    if not saved or saved.user_id != user_id:
        raise NotFoundError("Favori introuvable")
    session.delete(saved)
    session.commit()


# --- Synchronisation RSS ------------------------------------------------------------------


def _strip_html(text: str) -> str:
    """Retire les balises HTML et normalise les espaces."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()


def _parse_date(parsed) -> datetime | None:
    """Convertit une date de flux en datetime UTC (``None`` si invalide)."""
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(mktime(parsed), tz=UTC)
    except (OverflowError, ValueError):
        return None


def _import_feed(session: Session, source: dict, fetch: Fetcher) -> int:
    """Importe les nouveaux articles d'un flux ; retourne le nombre d'articles créés."""
    feed = feedparser.parse(fetch(source["url"]))
    created = 0
    for entry in feed.entries[:MAX_ENTRIES_PER_FEED]:
        url = str(entry.get("link") or "").strip()[:512]
        title = str(entry.get("title") or "").strip()
        summary = _strip_html(str(entry.get("summary") or entry.get("description") or ""))
        if not url or not title or not summary:
            continue
        if session.scalar(select(NewsArticle.id).where(NewsArticle.url == url)):
            continue
        session.add(
            NewsArticle(
                title=title[:500],
                source=source["name"],
                summary=summary[:2000],
                url=url,
                category=source["category"],
                published_at=_parse_date(entry.get("published_parsed")),
            )
        )
        created += 1
    session.commit()
    return created


def purge_old(session: Session) -> int:
    """Supprime les articles plus anciens que la durée de conservation ; retourne leur nombre."""
    cutoff = datetime.now(UTC) - timedelta(days=get_settings().news_retention_days)
    result = session.execute(delete(NewsArticle).where(NewsArticle.created_at < cutoff))
    session.commit()
    return result.rowcount


def sync_all(
    session: Session, fetch: Fetcher = http_fetch, sources: list[dict] | None = None
) -> int:
    """Purge les vieux articles puis importe les flux. Une source en erreur n'arrête pas les autres."""
    purge_old(session)
    total = 0
    for source in sources or RSS_SOURCES:
        try:
            total += _import_feed(session, source, fetch)
        except Exception as exc:
            session.rollback()
            logger.warning("Synchronisation de %s impossible : %s", source["name"], exc)
    return total
