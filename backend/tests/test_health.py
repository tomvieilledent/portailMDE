"""Tests de la route de santé et du format uniforme des erreurs."""


def test_health(client):
    """La route /health répond « ok »."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_not_found_uses_error_shape(client):
    """Une route inconnue renvoie le format d'erreur NOT_FOUND."""
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_shape(client):
    """Une erreur de validation renvoie le format VALIDATION_ERROR."""
    from fastapi import FastAPI

    app = client.app
    assert isinstance(app, FastAPI)

    @app.get("/_echo/{n}")
    def echo(n: int):
        """Route de test renvoyant l'entier reçu."""
        return {"n": n}

    response = client.get("/_echo/abc")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unhandled_error_shape(client):
    """Une erreur non gérée renvoie le format INTERNAL_ERROR."""

    @client.app.get("/_boom")
    def boom():
        """Route de test qui lève une exception."""
        raise RuntimeError("boom")

    response = client.get("/_boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
