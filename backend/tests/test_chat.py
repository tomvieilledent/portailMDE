"""Tests de la messagerie : conversations directes et de groupe, messages, pièces jointes et WebSocket."""

import io

import pytest

API = "/api/v1"


@pytest.fixture
def trio(make_user):
    """Trois utilisateurs (a, b, c) pour les scénarios de conversation."""
    return make_user("a@x.fr"), make_user("b@x.fr"), make_user("c@x.fr")


def direct(client, headers, other):
    """Crée une conversation directe avec un autre utilisateur."""
    return client.post(
        f"{API}/conversations", headers=headers, json={"kind": "direct", "user_id": str(other.id)}
    )


def test_direct_conversation_is_reused(client, trio, login):
    """Une conversation directe existante est réutilisée, quel que soit l'initiateur."""
    a, b, _ = trio
    first = direct(client, login("a@x.fr"), b)
    assert first.status_code == 201
    again = direct(client, login("a@x.fr"), b)
    reverse = direct(client, login("b@x.fr"), a)
    assert first.json()["id"] == again.json()["id"] == reverse.json()["id"]


def test_direct_with_self_or_unknown_rejected(client, trio, login):
    """Une conversation avec soi-même ou un inconnu est rejetée."""
    a, _, _ = trio
    assert direct(client, login("a@x.fr"), a).status_code == 400
    body = {"kind": "direct", "user_id": "00000000-0000-0000-0000-000000000000"}
    assert (
        client.post(f"{API}/conversations", headers=login("a@x.fr"), json=body).status_code == 404
    )


def test_group_validation(client, trio, login):
    """La création d'un groupe sans données valides est rejetée (422)."""
    headers = login("a@x.fr")
    assert (
        client.post(f"{API}/conversations", headers=headers, json={"kind": "group"}).status_code
        == 422
    )


def test_send_list_and_unread(client, trio, login):
    """Envoi, liste des messages et compteur de messages non lus."""
    a, b, _ = trio
    conv = direct(client, login("a@x.fr"), b).json()
    ha, hb = login("a@x.fr"), login("b@x.fr")
    url = f"{API}/conversations/{conv['id']}"
    for text in ("un", "deux"):
        assert client.post(f"{url}/messages", headers=ha, data={"content": text}).status_code == 201
    listing = client.get(f"{API}/conversations", headers=hb).json()
    assert listing[0]["unread_count"] == 2
    assert listing[0]["last_message"]["content"] == "deux"
    assert client.get(f"{API}/conversations", headers=ha).json()[0]["unread_count"] == 0
    messages = client.get(f"{url}/messages", headers=hb).json()
    assert [m["content"] for m in messages] == ["deux", "un"]
    assert messages[0]["author"]["id"] == str(a.id)
    assert client.post(f"{url}/read", headers=hb).status_code == 204
    assert client.get(f"{API}/conversations", headers=hb).json()[0]["unread_count"] == 0


def test_non_participant_gets_404(client, trio, login):
    """Un non-participant reçoit 404 sur la conversation."""
    _, b, _ = trio
    conv = direct(client, login("a@x.fr"), b).json()
    url = f"{API}/conversations/{conv['id']}"
    hc = login("c@x.fr")
    assert client.get(url, headers=hc).status_code == 404
    assert client.get(f"{url}/messages", headers=hc).status_code == 404
    assert client.post(f"{url}/messages", headers=hc, data={"content": "hi"}).status_code == 404


def test_empty_message_rejected(client, trio, login):
    """Un message vide est rejeté (400)."""
    _, b, _ = trio
    conv = direct(client, login("a@x.fr"), b).json()
    response = client.post(f"{API}/conversations/{conv['id']}/messages", headers=login("a@x.fr"))
    assert response.status_code == 400


def test_attachment_download_restricted_to_participants(client, trio, login):
    """Le téléchargement d'une pièce jointe est réservé aux participants."""
    _, b, _ = trio
    ha = login("a@x.fr")
    conv = direct(client, ha, b).json()
    sent = client.post(
        f"{API}/conversations/{conv['id']}/messages",
        headers=ha,
        files={"file": ("notes.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    ).json()
    assert sent["file_name"] == "notes.pdf" and sent["file_url"].endswith("/file")
    assert client.get(sent["file_url"], headers=login("b@x.fr")).content == b"%PDF-1.4"
    assert client.get(sent["file_url"], headers=login("c@x.fr")).status_code == 404
    assert client.get(sent["file_url"]).status_code == 401
    assert client.get(f"/uploads/{sent['id']}").status_code == 404


def test_delete_message_author_only(client, trio, login):
    """Seul l'auteur peut supprimer son message."""
    _, b, _ = trio
    ha, hb = login("a@x.fr"), login("b@x.fr")
    conv = direct(client, ha, b).json()
    msg = client.post(
        f"{API}/conversations/{conv['id']}/messages", headers=ha, data={"content": "x"}
    ).json()
    assert client.delete(f"{API}/messages/{msg['id']}", headers=hb).status_code == 403
    assert client.delete(f"{API}/messages/{msg['id']}", headers=ha).status_code == 204
    assert client.get(f"{API}/conversations/{conv['id']}/messages", headers=ha).json() == []


def test_group_lifecycle(client, trio, login):
    """Cycle de vie d'un groupe : renommage, ajout et retrait de participants."""
    a, b, c = trio
    ha, hb = login("a@x.fr"), login("b@x.fr")
    body = {"kind": "group", "title": "Équipe", "user_ids": [str(b.id)]}
    group = client.post(f"{API}/conversations", headers=ha, json=body).json()
    url = f"{API}/conversations/{group['id']}"
    assert len(group["participants"]) == 2
    # seul le créateur gère le groupe
    assert client.patch(url, headers=hb, json={"title": "X"}).status_code == 403
    assert client.patch(url, headers=ha, json={"title": "Renommé"}).json()["title"] == "Renommé"
    added = client.post(f"{url}/participants", headers=ha, json={"user_ids": [str(c.id)]})
    assert len(added.json()["participants"]) == 3
    assert client.get(url, headers=login("c@x.fr")).status_code == 200
    # un membre peut quitter, le créateur peut retirer
    assert client.delete(f"{url}/participants/{b.id}", headers=hb).status_code == 204
    assert client.get(url, headers=hb).status_code == 404
    assert client.delete(f"{url}/participants/{c.id}", headers=ha).status_code == 204


def test_websocket_requires_valid_token(client):
    """Le WebSocket refuse un jeton invalide."""
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect), client.websocket_connect(f"{API}/ws?token=bad"):
        pass


def test_websocket_receives_new_message(client, trio, login):
    """Le WebSocket reçoit les nouveaux messages en temps réel."""
    _, b, _ = trio
    ha = login("a@x.fr")
    token_b = login("b@x.fr")["Authorization"].split()[1]
    conv = direct(client, ha, b).json()
    with client.websocket_connect(f"{API}/ws?token={token_b}") as ws:
        ws.send_text("ping")
        assert ws.receive_json() == {"type": "pong"}
        client.post(
            f"{API}/conversations/{conv['id']}/messages", headers=ha, data={"content": "yo"}
        )
        event = ws.receive_json()
    assert event["type"] == "message.new"
    assert event["message"]["content"] == "yo"
