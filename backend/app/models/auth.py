"""Modèle des jetons d'authentification révoqués."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RevokedToken(Base):
    """Jeton révoqué (déconnexion, rotation du jeton de rafraîchissement), purgeable après ``expires_at``."""

    __tablename__ = "revoked_tokens"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
