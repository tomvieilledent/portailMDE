"""Environnement Alembic : configuration des migrations en ligne et hors ligne."""

from logging.config import fileConfig

from sqlalchemy import create_engine

import app.models  # noqa: F401  (enregistre les modèles dans les métadonnées)
from alembic import context
from app.core.config import get_settings
from app.db.base import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url() -> str:
    """Retourne l'URL de la base (configuration Alembic, sinon paramètres de l'application)."""
    return config.get_main_option("sqlalchemy.url") or get_settings().database_url


def run_migrations_offline() -> None:
    """Exécute les migrations en mode hors ligne (génère le SQL sans connexion)."""
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode en ligne, via une connexion à la base."""
    connectable = create_engine(_url())
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
