"""Tests de l'authentification : connexion, rafraîchissement et déconnexion."""

from app.core.security import create_token
from app.models.enums import UserRole


def _login(client, email="user@example.fr", password="password123"):
    """Envoie une requête de connexion avec les identifiants donnés."""
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_login_success(client, make_user):
    """Une connexion valide renvoie les jetons d'accès et de rafraîchissement."""
    make_user()
    response = _login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_email_is_case_insensitive(client, make_user):
    """L'email est insensible à la casse lors de la connexion."""
    make_user(email="User@Example.fr")
    assert _login(client, "user@example.FR").status_code == 200


def test_login_wrong_password(client, make_user):
    """Un mauvais mot de passe est refusé (401)."""
    make_user()
    response = _login(client, password="mauvais-mot-de-passe")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_user(client):
    """Un utilisateur inconnu est refusé (401)."""
    assert _login(client, "nobody@example.fr").status_code == 401


def test_login_inactive_user(client, make_user):
    """Un utilisateur désactivé ne peut pas se connecter."""
    make_user(is_active=False)
    assert _login(client).status_code == 401


def test_protected_route_requires_token(client):
    """Une route protégée exige un jeton."""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401


def test_refresh_rotates_tokens(client, make_user):
    """Le rafraîchissement fait tourner les jetons et invalide l'ancien."""
    make_user()
    pair = _login(client).json()
    new_pair = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert new_pair.status_code == 200
    # l'ancien refresh ne peut plus servir
    again = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert again.status_code == 401


def test_refresh_rejects_access_token(client, make_user):
    """Le rafraîchissement refuse un jeton d'accès."""
    make_user()
    pair = _login(client).json()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["access_token"]})
    assert response.status_code == 401


def test_logout_revokes_tokens(client, make_user):
    """La déconnexion révoque les jetons d'accès et de rafraîchissement."""
    make_user()
    pair = _login(client).json()
    headers = {"Authorization": f"Bearer {pair['access_token']}"}
    response = client.post(
        "/api/v1/auth/logout", headers=headers, json={"refresh_token": pair["refresh_token"]}
    )
    assert response.status_code == 204
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 401
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert refresh.status_code == 401


def test_deleted_user_token_rejected(client, make_user, session):
    """Le jeton d'un utilisateur désactivé est rejeté."""
    user = make_user(role=UserRole.MEMBER)
    token, _, _ = create_token(str(user.id), "access")
    user.is_active = False
    session.commit()
    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_login_locked_after_repeated_failures(client, make_user):
    """Après 5 échecs pour un même email, la connexion est verrouillée (429), même avec le bon mot de passe."""
    make_user()
    for _ in range(5):
        assert _login(client, password="mauvais-mot-de-passe").status_code == 401
    assert _login(client).status_code == 429


def test_forgot_password_rate_limited(client):
    """La demande de réinitialisation est limitée par email."""
    for _ in range(3):
        assert (
            client.post("/api/v1/auth/forgot-password", json={"email": "a@example.fr"}).status_code
            == 204
        )
    response = client.post("/api/v1/auth/forgot-password", json={"email": "a@example.fr"})
    assert response.status_code == 429


def test_password_change_revokes_old_tokens(client, make_user):
    """Un jeton émis avant un changement de mot de passe n'est plus accepté."""
    make_user()
    pair = _login(client).json()
    headers = {"Authorization": f"Bearer {pair['access_token']}"}
    changed = client.post(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "password123", "new_password": "newpassword1"},
    )
    assert changed.status_code == 200
    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert refresh.status_code == 401
