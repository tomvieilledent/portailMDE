"""Tests des emails transactionnels : mot de passe oublié, bienvenue, invitation, échappement HTML."""

import re

from app.services import mailer

API = "/api/v1"


def token_from(mail):
    """Extrait le jeton du lien contenu dans l'email."""
    return re.search(r"token=([\w.\-]+)", mail.text).group(1)


def test_forgot_password_sends_link(client, make_user, mail_outbox):
    """Le mot de passe oublié envoie un email avec un lien de réinitialisation."""
    make_user("a@x.fr", first_name="Ada")
    assert client.post(f"{API}/auth/forgot-password", json={"email": "A@x.fr"}).status_code == 204
    assert len(mail_outbox) == 1
    mail = mail_outbox[0]
    assert mail.to == "a@x.fr" and "Ada" in mail.text and "/reset-password?token=" in mail.text
    assert "<a href=" in mail.html


def test_forgot_password_unknown_or_inactive_is_silent(client, make_user, mail_outbox):
    """Un compte inconnu ou inactif ne déclenche aucun email ni erreur."""
    make_user("off@x.fr", is_active=False)
    for email in ("nobody@x.fr", "off@x.fr"):
        assert client.post(f"{API}/auth/forgot-password", json={"email": email}).status_code == 204
    assert mail_outbox == []


def test_reset_password_flow_and_single_use(client, make_user, mail_outbox):
    """La réinitialisation fonctionne et le lien n'est utilisable qu'une fois."""
    make_user("a@x.fr")
    client.post(f"{API}/auth/forgot-password", json={"email": "a@x.fr"})
    token = token_from(mail_outbox[0])
    body = {"token": token, "new_password": "brandnewpass1"}
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 204
    login = client.post(f"{API}/auth/login", json={"email": "a@x.fr", "password": "brandnewpass1"})
    assert login.status_code == 200
    # le lien ne sert qu'une fois
    assert client.post(f"{API}/auth/reset-password", json=body).status_code == 401


def test_reset_rejects_garbage_and_wrong_token_type(client, make_user, login):
    """La réinitialisation refuse un jeton invalide ou de mauvais type."""
    make_user("a@x.fr")
    access = login("a@x.fr")["Authorization"].split()[1]
    for token in ("garbage", access):
        response = client.post(
            f"{API}/auth/reset-password", json={"token": token, "new_password": "brandnewpass1"}
        )
        assert response.status_code == 401


def test_reset_rejects_short_password(client):
    """La réinitialisation refuse un mot de passe trop court."""
    response = client.post(
        f"{API}/auth/reset-password", json={"token": "x", "new_password": "short"}
    )
    assert response.status_code == 422


def test_welcome_email_on_user_creation(client, make_user, login, mail_outbox):
    """Un email de bienvenue est envoyé à la création d'un utilisateur."""
    from app.models.enums import UserRole

    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    client.post(
        f"{API}/users",
        headers=login("root@x.fr"),
        json={"email": "new@x.fr", "password": "password123", "first_name": "Nina"},
    )
    assert [m.to for m in mail_outbox] == ["new@x.fr"]
    assert "Bienvenue" in mail_outbox[0].subject


def test_invitation_email(client, make_user, login, mail_outbox):
    """Un email est envoyé aux invités d'un événement."""
    make_user("o@x.fr", first_name="Olga")
    guest = make_user("g@x.fr")
    client.post(
        f"{API}/events",
        headers=login("o@x.fr"),
        json={"title": "Afterwork", "event_date": "2026-11-05", "invitee_ids": [str(guest.id)]},
    )
    assert [m.to for m in mail_outbox] == ["g@x.fr"]
    assert "Afterwork" in mail_outbox[0].subject and "Olga" in mail_outbox[0].text


def test_html_is_escaped():
    """Le HTML des emails échappe les valeurs injectées."""
    from app.emails import templates

    _, _, html = templates.invitation("x", "<script>", "a&b", "http://l")
    assert "<script>" not in html and "a&amp;b" in html


def test_smtp_failure_does_not_raise(monkeypatch):
    """Un échec SMTP ne lève pas d'exception."""
    monkeypatch.setenv("MAIL_BACKEND", "smtp")
    monkeypatch.setenv("MAIL_HOST", "127.0.0.1")
    monkeypatch.setenv("MAIL_PORT", "1")
    from app.core.config import get_settings

    get_settings.cache_clear()
    mailer.send_email("a@x.fr", "Sujet", "Texte")
