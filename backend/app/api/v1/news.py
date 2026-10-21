"""Routes des actualités : articles, articles enregistrés et contenus éditoriaux du site."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.core.config import get_settings
from app.core.permissions import Permission
from app.models import User
from app.schemas.common import Page
from app.schemas.news import (
    ArticleCreate,
    ArticleRead,
    ContentRead,
    ContentUpdate,
    SavedArticleRead,
    SyncResult,
)
from app.services import news as service
from app.services import site_content

router = APIRouter(tags=["news"])
NewsManager = Annotated[User, Depends(require_permission(Permission.MANAGE_NEWS))]


@router.get("/news", response_model=Page[ArticleRead])
def list_news(
    session: SessionDep,
    _: CurrentUser,
    background: BackgroundTasks,
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    category: str | None = None,
    since: datetime | None = None,
):
    """Liste les actualités ; une base vide déclenche d'elle-même une synchronisation des flux."""
    items, total = service.list_articles(
        session, limit=limit, offset=offset, search=search, category=category, since=since
    )
    if total == 0 and not (search or category or since or offset):
        if get_settings().news_sync_enabled and service.is_empty(session):
            background.add_task(service.sync_in_background)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/news", response_model=ArticleRead, status_code=201)
def create_article(body: ArticleCreate, session: SessionDep, _: NewsManager):
    """Crée un article d'actualité."""
    return service.create_article(session, body)


@router.post("/news/sync", response_model=SyncResult)
def sync_news(session: SessionDep, _: NewsManager):
    """Lance la synchronisation des flux d'actualités externes."""
    return SyncResult(created=service.sync_all(session))


@router.get("/news/saved", response_model=list[SavedArticleRead])
def saved_articles(session: SessionDep, current: CurrentUser):
    """Liste les articles enregistrés par l'utilisateur courant."""
    return service.list_saved(session, current.id)


@router.delete("/news/saved/{saved_id}", status_code=204)
def unsave_article(saved_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Retire un article des articles enregistrés."""
    service.unsave(session, current.id, saved_id)
    return Response(status_code=204)


@router.get("/news/{article_id}", response_model=ArticleRead)
def read_article(article_id: uuid.UUID, session: SessionDep, _: CurrentUser):
    """Retourne un article d'actualité."""
    return service.get_article(session, article_id)


@router.delete("/news/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, session: SessionDep, _: NewsManager):
    """Supprime un article d'actualité."""
    service.delete_article(session, article_id)
    return Response(status_code=204)


@router.put("/news/{article_id}/save", response_model=SavedArticleRead)
def save_article(article_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    """Enregistre un article pour l'utilisateur courant."""
    return service.save_article(session, current.id, article_id)


@router.get("/content/{key}", response_model=ContentRead)
def read_content(key: str, session: SessionDep):
    """Contenu public (page d'accueil) : accessible sans authentification."""
    return ContentRead(key=key, value=site_content.get_content(session, key))


@router.put("/content/{key}", response_model=ContentRead)
def update_content(key: str, body: ContentUpdate, session: SessionDep, _: NewsManager):
    """Met à jour un contenu éditorial du site."""
    return ContentRead(key=key, value=site_content.set_content(session, key, body.value))
