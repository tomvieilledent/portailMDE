"""Tests de la validation de la configuration (secret JWT selon l'environnement)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_refuses_default_secret():
    """La production refuse le secret JWT par défaut."""
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_production_refuses_short_secret():
    """La production refuse un secret JWT trop court."""
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="trop-court")


def test_production_accepts_strong_secret():
    """La production accepte un secret JWT robuste."""
    assert Settings(environment="production", jwt_secret="x" * 40).environment == "production"


def test_development_keeps_default_secret():
    """Le développement conserve le secret par défaut."""
    assert Settings(environment="development").jwt_secret


def test_production_refuses_console_mail():
    """La production refuse les backends d'email qui journalisent ou ne livrent pas."""
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="x" * 40, mail_backend="console")
