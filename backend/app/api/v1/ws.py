import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.api.deps import SessionDep
from app.core.security import InvalidTokenError, decode_token
from app.models import User
from app.services import auth as auth_service
from app.services.realtime import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session: SessionDep, token: str = ""):
    """Flux d'événements temps réel. Authentification : ``/ws?token=<access_token>``."""
    user = _authenticate(session, token)
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id: uuid.UUID = user.id
    session.close()  # libère la connexion : le socket peut rester ouvert longtemps
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Le serveur pousse les événements ; on lit seulement pour détecter la fermeture
            # et répondre aux « ping » applicatifs.
            if await websocket.receive_text() == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)


def _authenticate(session, token: str) -> User | None:
    try:
        payload = decode_token(token, "access")
    except InvalidTokenError:
        return None
    if auth_service.is_revoked(session, payload["jti"]):
        return None
    user = session.get(User, payload["sub"])
    if not user or not user.is_active or user.deleted_at is not None:
        return None
    return user
