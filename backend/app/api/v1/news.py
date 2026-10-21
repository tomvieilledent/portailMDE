import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import CurrentUser, SessionDep, require_permission
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
    limit: Annotated[int, Query(ge=1, le=200)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: str | None = None,
    category: str | None = None,
):
    items, total = service.list_articles(
        session, limit=limit, offset=offset, search=search, category=category
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("/news", response_model=ArticleRead, status_code=201)
def create_article(body: ArticleCreate, session: SessionDep, _: NewsManager):
    return service.create_article(session, body)


@router.post("/news/sync", response_model=SyncResult)
def sync_news(session: SessionDep, _: NewsManager):
    return SyncResult(created=service.sync_all(session))


@router.get("/news/saved", response_model=list[SavedArticleRead])
def saved_articles(session: SessionDep, current: CurrentUser):
    return service.list_saved(session, current.id)


@router.delete("/news/saved/{saved_id}", status_code=204)
def unsave_article(saved_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    service.unsave(session, current.id, saved_id)
    return Response(status_code=204)


@router.get("/news/{article_id}", response_model=ArticleRead)
def read_article(article_id: uuid.UUID, session: SessionDep, _: CurrentUser):
    return service.get_article(session, article_id)


@router.delete("/news/{article_id}", status_code=204)
def delete_article(article_id: uuid.UUID, session: SessionDep, _: NewsManager):
    service.delete_article(session, article_id)
    return Response(status_code=204)


@router.put("/news/{article_id}/save", response_model=SavedArticleRead)
def save_article(article_id: uuid.UUID, session: SessionDep, current: CurrentUser):
    return service.save_article(session, current.id, article_id)


@router.get("/content/{key}", response_model=ContentRead)
def read_content(key: str, session: SessionDep):
    """Contenu public (page d'accueil) : accessible sans authentification."""
    return ContentRead(key=key, value=site_content.get_content(session, key))


@router.put("/content/{key}", response_model=ContentRead)
def update_content(key: str, body: ContentUpdate, session: SessionDep, _: NewsManager):
    return ContentRead(key=key, value=site_content.set_content(session, key, body.value))
