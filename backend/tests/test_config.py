import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_refuses_default_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_production_refuses_short_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="trop-court")


def test_production_accepts_strong_secret():
    assert Settings(environment="production", jwt_secret="x" * 40).environment == "production"


def test_development_keeps_default_secret():
    assert Settings(environment="development").jwt_secret
