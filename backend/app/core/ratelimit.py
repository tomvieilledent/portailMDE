"""Limitation de débit en mémoire (fenêtre glissante) pour les routes d'authentification.

L'état est propre à chaque processus : suffisant pour freiner la force brute et le spam d'emails
avec un seul worker ; en multi-instances, compléter par ``limit_req`` côté nginx.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.errors import AppError


class TooManyRequestsError(AppError):
    """Trop de requêtes (429)."""

    status_code = 429
    code = "TOO_MANY_REQUESTS"


class RateLimiter:
    """Autorise au plus ``limit`` événements par clé sur ``window`` secondes."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        """Retire les événements sortis de la fenêtre ; supprime la clé si elle est vide."""
        events = self._events[key]
        while events and events[0] <= now - self.window:
            events.popleft()
        if not events:
            self._events.pop(key, None)
        return events

    def check(self, key: str) -> None:
        """Lève 429 si la clé a atteint la limite (sans enregistrer d'événement)."""
        with self._lock:
            if len(self._prune(key, time.monotonic())) >= self.limit:
                raise TooManyRequestsError("Trop de tentatives, réessayez plus tard")

    def record(self, key: str) -> None:
        """Enregistre un événement pour la clé."""
        with self._lock:
            now = time.monotonic()
            self._prune(key, now)
            self._events[key].append(now)

    def hit(self, key: str) -> None:
        """Vérifie puis enregistre un événement."""
        self.check(key)
        self.record(key)

    def reset(self, key: str | None = None) -> None:
        """Oublie une clé, ou toutes si ``key`` est omis."""
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)


login_ip = RateLimiter(limit=30, window=60)
login_failures = RateLimiter(limit=5, window=15 * 60)  # verrouillage temporaire par email
forgot_ip = RateLimiter(limit=10, window=15 * 60)
forgot_email = RateLimiter(limit=3, window=15 * 60)
reset_ip = RateLimiter(limit=10, window=15 * 60)


def reset_all() -> None:
    """Réinitialise tous les limiteurs (tests)."""
    for limiter in (login_ip, login_failures, forgot_ip, forgot_email, reset_ip):
        limiter.reset()


def client_ip(request: Request) -> str:
    """Adresse du client ; derrière nginx, dernière valeur de ``X-Forwarded-For`` (ajoutée par lui)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"
