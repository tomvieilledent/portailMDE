"""Tâches planifiées (actualités, purge de conservation)."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services import news, retention

logger = logging.getLogger(__name__)


def run_news_sync() -> None:
    """Tâche planifiée : synchronise les actualités et journalise le résultat."""
    with SessionLocal() as session:
        created = news.sync_all(session)
    logger.info("Synchronisation des actualités : %d nouveaux articles", created)


def run_retention_purge() -> None:
    """Tâche planifiée : purge les données personnelles échues."""
    with SessionLocal() as session:
        retention.purge_personal_data(session)


def start_scheduler() -> BackgroundScheduler | None:
    """Démarre le planificateur (synchronisation des actualités et purge de conservation)."""
    settings = get_settings()
    if not settings.scheduler_enabled:
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    if settings.news_sync_enabled:
        scheduler.add_job(
            run_news_sync, "interval", minutes=settings.news_sync_interval_minutes, id="news_sync"
        )
    scheduler.add_job(run_retention_purge, "interval", hours=24, id="retention_purge")
    scheduler.start()
    return scheduler
