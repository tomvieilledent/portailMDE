from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import health
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.services.storage import PUBLIC_UPLOAD_CATEGORIES, upload_root


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name)
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
        app.mount(f"/uploads/{category}", StaticFiles(directory=directory), name=category)
    return app


app = create_app()
