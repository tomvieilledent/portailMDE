"""Gestionnaire de connexions WebSocket (en mémoire, un seul processus).

Pour plusieurs workers, remplacer par un bus Redis pub/sub.
"""

import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket) -> None:
        self._connections[user_id].discard(websocket)
        if not self._connections[user_id]:
            del self._connections[user_id]

    def is_online(self, user_id: uuid.UUID) -> bool:
        return user_id in self._connections

    async def send_to_users(self, user_ids: list[uuid.UUID], event: dict) -> None:
        for user_id in user_ids:
            for websocket in list(self._connections.get(user_id, ())):
                try:
                    await websocket.send_json(event)
                except Exception:  # connexion morte : nettoyée à la déconnexion
                    self.disconnect(user_id, websocket)


manager = ConnectionManager()


def push(user_ids: list[uuid.UUID], event: dict) -> None:
    """Pousse un événement depuis du code synchrone (route FastAPI exécutée en thread).

    Sans boucle d'événements disponible (script, tâche planifiée), l'envoi est ignoré :
    le client récupérera l'information via l'API REST.
    """
    import anyio.from_thread

    try:
        anyio.from_thread.run(manager.send_to_users, user_ids, event)
    except RuntimeError:
        pass
