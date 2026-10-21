"""Tests des notifications : création, lecture, suppression, diffusion et envoi temps réel."""

from app.models import Notification
from app.models.enums import UserRole

API = "/api/v1"


def test_invitation_creates_notification_and_response_notifies_back(client, make_user, login):
    """Une invitation notifie l'invité et sa réponse notifie l'organisateur."""
    make_user("o@x.fr", first_name="Olga", last_name="Org")
    guest = make_user("g@x.fr", first_name="Gus")
    ho, hg = login("o@x.fr"), login("g@x.fr")
    client.post(
        f"{API}/events",
        headers=ho,
        json={"title": "Afterwork", "event_date": "2026-11-05", "invitee_ids": [str(guest.id)]},
    )
    inbox = client.get(f"{API}/notifications", headers=hg).json()
    assert inbox[0]["content"] == "Olga Org vous invite : Afterwork"
    assert inbox[0]["kind"] == "invitation" and inbox[0]["is_read"] is False
    assert client.get(f"{API}/notifications/unread-count", headers=hg).json() == {"count": 1}
    invitation = client.get(f"{API}/invitations/me", headers=hg).json()[0]
    client.post(
        f"{API}/invitations/{invitation['id']}/respond", headers=hg, json={"status": "accepted"}
    )
    back = client.get(f"{API}/notifications", headers=ho).json()
    assert back[0]["content"] == "Gus a accepté votre invitation"


def test_group_add_notifies_members(client, make_user, login):
    """L'ajout à un groupe notifie les membres ajoutés."""
    make_user("a@x.fr", first_name="Ana")
    b = make_user("b@x.fr")
    body = {"kind": "group", "title": "Équipe", "user_ids": [str(b.id)]}
    client.post(f"{API}/conversations", headers=login("a@x.fr"), json=body)
    inbox = client.get(f"{API}/notifications", headers=login("b@x.fr")).json()
    assert "Équipe" in inbox[0]["content"] and inbox[0]["data"]["conversation_id"]
    assert client.get(f"{API}/notifications", headers=login("a@x.fr")).json() == []


def test_read_and_delete(client, make_user, login, session):
    """Marquage comme lu et suppression des notifications."""
    user = make_user()
    session.add_all([Notification(recipient_id=user.id, content=f"n{i}") for i in range(3)])
    session.commit()
    headers = login()
    items = client.get(f"{API}/notifications", headers=headers).json()
    one = client.post(f"{API}/notifications/{items[0]['id']}/read", headers=headers).json()
    assert one["is_read"] is True
    assert (
        len(
            client.get(f"{API}/notifications", headers=headers, params={"unread_only": True}).json()
        )
        == 2
    )
    assert client.post(f"{API}/notifications/read-all", headers=headers).status_code == 204
    assert client.get(f"{API}/notifications/unread-count", headers=headers).json() == {"count": 0}
    assert (
        client.delete(f"{API}/notifications/{items[1]['id']}", headers=headers).status_code == 204
    )
    assert len(client.get(f"{API}/notifications", headers=headers).json()) == 2


def test_cannot_touch_others_notifications(client, make_user, login, session):
    """Impossible de modifier les notifications d'autrui."""
    a, _ = make_user("a@x.fr"), make_user("b@x.fr")
    note = Notification(recipient_id=a.id, content="secret")
    session.add(note)
    session.commit()
    hb = login("b@x.fr")
    assert client.post(f"{API}/notifications/{note.id}/read", headers=hb).status_code == 404
    assert client.delete(f"{API}/notifications/{note.id}", headers=hb).status_code == 404


def test_broadcast(client, make_user, login):
    """La diffusion d'une annonce est réservée aux éditeurs et atteint les actifs."""
    make_user("a@x.fr")
    make_user("b@x.fr")
    make_user("off@x.fr", is_active=False)
    make_user("ed@x.fr", role=UserRole.STAFF, permissions=["manage_news"])
    assert (
        client.post(
            f"{API}/notifications/broadcast", headers=login("a@x.fr"), json={"content": "Hi"}
        ).status_code
        == 403
    )
    sent = client.post(
        f"{API}/notifications/broadcast",
        headers=login("ed@x.fr"),
        json={"content": "Fermeture lundi"},
    )
    assert sent.status_code == 204
    assert (
        client.get(f"{API}/notifications", headers=login("b@x.fr")).json()[0]["kind"]
        == "announcement"
    )


def test_realtime_push(client, make_user, login):
    """Une notification est poussée en temps réel par WebSocket."""
    make_user("a@x.fr")
    b = make_user("b@x.fr")
    ha = login("a@x.fr")
    token_b = login("b@x.fr")["Authorization"].split()[1]
    with client.websocket_connect(f"{API}/ws?token={token_b}") as ws:
        client.post(
            f"{API}/events",
            headers=ha,
            json={"title": "Live", "event_date": "2026-11-05", "invitee_ids": [str(b.id)]},
        )
        event = ws.receive_json()
    assert event["type"] == "notification.new"
    assert "Live" in event["notification"]["content"]
