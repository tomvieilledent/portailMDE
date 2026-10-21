"""Point d'entrée FastAPI : création de l'application, middlewares, routes et fichiers statiques."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.api import health
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.services.scheduler import start_scheduler
from app.services.storage import PUBLIC_UPLOAD_CATEGORIES, upload_root

_INLINE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp")


class UploadFiles(StaticFiles):
    """Fichiers publics : images affichées en ligne, tout autre document forcé en téléchargement."""

    async def get_response(self, path: str, scope) -> Response:
        """Ajoute ``nosniff`` et ``Content-Disposition: attachment`` hors images."""
        response = await super().get_response(path, scope)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if not path.lower().endswith(_INLINE_EXTENSIONS):
            response.headers["Content-Disposition"] = "attachment"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Cycle de vie de l'application : démarre puis arrête le planificateur de tâches."""
    scheduler = start_scheduler()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    """Construit l'application FastAPI (CORS, gestion des erreurs, routeurs, dossiers d'uploads publics)."""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(api_router)
    # Seules les catégories publiques sont servies directement ; les pièces jointes du chat
    # passent par un endpoint authentifié.
    for category in PUBLIC_UPLOAD_CATEGORIES:
        directory = upload_root() / category
        directory.mkdir(parents=True, exist_ok=True)
        app.mount(f"/uploads/{category}", UploadFiles(directory=directory), name=category)
    return app


app = create_app()
