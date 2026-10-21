def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_not_found_uses_error_shape(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_validation_error_shape(client):
    from fastapi import FastAPI

    app = client.app
    assert isinstance(app, FastAPI)

    @app.get("/_echo/{n}")
    def echo(n: int):
        return {"n": n}

    response = client.get("/_echo/abc")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unhandled_error_shape(client):
    @client.app.get("/_boom")
    def boom():
        raise RuntimeError("boom")

    response = client.get("/_boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
