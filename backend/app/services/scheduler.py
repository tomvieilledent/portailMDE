"""Tâches planifiées (synchronisation des actualités)."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services import news

logger = logging.getLogger(__name__)


def run_news_sync() -> None:
    """Tâche planifiée : synchronise les actualités et journalise le résultat."""
    with SessionLocal() as session:
        created = news.sync_all(session)
    logger.info("Synchronisation des actualités : %d nouveaux articles", created)


def start_scheduler() -> BackgroundScheduler | None:
    """Démarre le planificateur si la synchronisation est activée ; retourne ``None`` sinon."""
    settings = get_settings()
    if not settings.news_sync_enabled:
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_news_sync, "interval", minutes=settings.news_sync_interval_minutes, id="news_sync"
    )
    scheduler.start()
    return scheduler
