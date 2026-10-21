"""Point d'entrée WebSocket des événements temps réel."""

import time
import uuid
from urllib.parse import urlsplit

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.security import InvalidTokenError, decode_token
from app.models import User
from app.services import auth as auth_service
from app.services.realtime import manager

router = APIRouter()

MAX_MESSAGE_CHARS = 1024
MAX_MESSAGES_PER_MINUTE = 60


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session: SessionDep, token: str = ""):
    """Flux d'événements temps réel. Authentification : ``/ws?token=<access_token>``."""
    if not _origin_allowed(websocket):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user = _authenticate(session, token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id: uuid.UUID = user.id
    session.close()  # libère la connexion : le socket peut rester ouvert longtemps
    await manager.connect(user_id, websocket)
    window_start, received = time.monotonic(), 0
    try:
        while True:
            # Le serveur pousse les événements ; on lit seulement pour détecter la fermeture
            # et répondre aux « ping » applicatifs.
            message = await websocket.receive_text()
            now = time.monotonic()
            if now - window_start >= 60:
                window_start, received = now, 0
            received += 1
            if len(message) > MAX_MESSAGE_CHARS or received > MAX_MESSAGES_PER_MINUTE:
                await websocket.close(code=status.WS_1009_MESSAGE_TOO_BIG)
                break
            if message == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)


def _origin_allowed(websocket: WebSocket) -> bool:
    """Accepte l'absence d'Origin (clients non navigateurs), l'origine du site ou celle de l'hôte."""
    origin = websocket.headers.get("origin")
    if origin is None:
        return True
    settings = get_settings()
    if origin in (*settings.cors_origins, settings.frontend_url.rstrip("/")):
        return True
    return urlsplit(origin).netloc == websocket.headers.get("host")


def _authenticate(session, token: str) -> User | None:
    """Retourne l'utilisateur correspondant au jeton d'accès, ou ``None`` s'il est invalide."""
    try:
        payload = decode_token(token, "access")
    except InvalidTokenError:
        return None
    if auth_service.is_revoked(session, payload["jti"]):
        return None
    user = session.get(User, payload["sub"])
    if not user or not user.is_active or user.deleted_at is not None or user.must_change_password:
        return None
    if not auth_service.session_is_current(user, payload):
        return None
    return user
