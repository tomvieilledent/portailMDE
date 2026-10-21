"""Tests des événements : visibilité, droits, filtre par dates, invitations et export iCalendar."""

API = "/api/v1"


def make_event(client, headers, **overrides):
    """Crée un événement via l'API avec des valeurs par défaut."""
    body = {"title": "Afterwork", "event_date": "2026-11-05", **overrides}
    return client.post(f"{API}/events", headers=headers, json=body)


def test_create_and_read(client, make_user, login):
    """Création et lecture d'un événement."""
    make_user()
    headers = login()
    created = make_event(client, headers, event_time="18:30:00", is_public=True)
    assert created.status_code == 201
    assert created.json()["event_time"] == "18:30:00"
    assert client.get(f"{API}/events/{created.json()['id']}", headers=headers).status_code == 200


def test_private_event_visibility(client, make_user, login):
    """Un événement privé n'est visible que de l'organisateur et des invités."""
    owner, guest, stranger = make_user("o@x.fr"), make_user("g@x.fr"), make_user("s@x.fr")
    event = make_event(client, login("o@x.fr"), invitee_ids=[str(guest.id)]).json()
    url = f"{API}/events/{event['id']}"
    assert client.get(url, headers=login("g@x.fr")).status_code == 200
    assert client.get(url, headers=login("s@x.fr")).status_code == 404
    assert client.get(f"{API}/events", headers=login("s@x.fr")).json() == []
    assert len(client.get(f"{API}/events", headers=login("g@x.fr")).json()) == 1
    assert owner and stranger


def test_public_event_visible_to_all(client, make_user, login):
    """Un événement public est visible de tous."""
    make_user("o@x.fr")
    make_user("s@x.fr")
    make_event(client, login("o@x.fr"), is_public=True)
    assert len(client.get(f"{API}/events", headers=login("s@x.fr")).json()) == 1


def test_staff_sees_everything_and_edits(client, make_user, login):
    """Le staff voit et modifie tous les événements."""
    from app.models.enums import UserRole

    make_user("o@x.fr")
    make_user("st@x.fr", role=UserRole.STAFF, permissions=["manage_trainings"])
    event = make_event(client, login("o@x.fr")).json()
    headers = login("st@x.fr")
    assert len(client.get(f"{API}/events", headers=headers).json()) == 1
    assert (
        client.patch(
            f"{API}/events/{event['id']}", headers=headers, json={"title": "Z"}
        ).status_code
        == 200
    )


def test_only_owner_can_edit_or_delete(client, make_user, login):
    """Seul le propriétaire peut modifier ou supprimer un événement."""
    make_user("o@x.fr")
    make_user("g@x.fr")
    event = make_event(client, login("o@x.fr"), is_public=True).json()
    url = f"{API}/events/{event['id']}"
    hg = login("g@x.fr")
    assert client.patch(url, headers=hg, json={"title": "Z"}).status_code == 403
    assert client.delete(url, headers=hg).status_code == 403
    assert client.delete(url, headers=login("o@x.fr")).status_code == 204
    assert client.get(url, headers=login("o@x.fr")).status_code == 404


def test_date_range_filter(client, make_user, login):
    """Filtrage des événements par plage de dates."""
    make_user()
    headers = login()
    make_event(client, headers, event_date="2026-11-05")
    make_event(client, headers, event_date="2026-12-05")
    found = client.get(f"{API}/events", headers=headers, params={"start": "2026-12-01"}).json()
    assert [e["event_date"] for e in found] == ["2026-12-05"]


def test_invitation_flow(client, make_user, login):
    """Parcours d'invitation : envoi, doublon ignoré, réponse."""
    make_user("o@x.fr")
    guest = make_user("g@x.fr")
    ho, hg = login("o@x.fr"), login("g@x.fr")
    event = make_event(client, ho).json()
    invited = client.post(
        f"{API}/events/{event['id']}/invitations", headers=ho, json={"user_ids": [str(guest.id)]}
    )
    assert invited.status_code == 201 and len(invited.json()) == 1
    # une seconde invitation identique est ignorée
    again = client.post(
        f"{API}/events/{event['id']}/invitations", headers=ho, json={"user_ids": [str(guest.id)]}
    )
    assert again.json() == []
    inbox = client.get(f"{API}/invitations/me", headers=hg).json()
    assert inbox[0]["status"] == "pending" and inbox[0]["target_title"] == "Afterwork"
    answered = client.post(
        f"{API}/invitations/{inbox[0]['id']}/respond", headers=hg, json={"status": "accepted"}
    )
    assert answered.json()["status"] == "accepted" and answered.json()["responded_at"]
    assert (
        client.get(f"{API}/invitations/me", headers=hg, params={"status": "pending"}).json() == []
    )
    assert len(client.get(f"{API}/events/{event['id']}/invitations", headers=ho).json()) == 1


def test_cannot_answer_someone_elses_invitation(client, make_user, login):
    """Impossible de répondre à l'invitation d'autrui ou avec un statut invalide."""
    make_user("o@x.fr")
    guest = make_user("g@x.fr")
    make_user("s@x.fr")
    ho = login("o@x.fr")
    event = make_event(client, ho, invitee_ids=[str(guest.id)]).json()
    invitation = client.get(f"{API}/invitations/me", headers=login("g@x.fr")).json()[0]
    bad = client.post(
        f"{API}/invitations/{invitation['id']}/respond",
        headers=login("s@x.fr"),
        json={"status": "accepted"},
    )
    assert bad.status_code == 404
    pending = client.post(
        f"{API}/invitations/{invitation['id']}/respond",
        headers=login("g@x.fr"),
        json={"status": "pending"},
    )
    assert pending.status_code == 400
    assert event


def test_ics_export(client, make_user, login):
    """L'export iCalendar produit des dates et un titre correctement formatés."""
    make_user()
    headers = login()
    make_event(client, headers, title="Réunion; importante", event_time="09:00:00")
    response = client.get(f"{API}/events/export.ics", headers=headers)
    assert response.headers["content-type"].startswith("text/calendar")
    assert "DTSTART:20261105T090000" in response.text
    assert "SUMMARY:Réunion" + chr(92) + "; importante" in response.text


def test_pdf_export_is_a_valid_poster(client, make_user, login):
    """L'export PDF produit un document PDF avec les événements du mois."""
    make_user("pdf@x.fr")
    headers = login("pdf@x.fr")
    client.post(
        f"{API}/events",
        headers=headers,
        json={"title": "Afterwork", "event_date": "2026-11-12", "event_time": "18:30:00"},
    )
    response = client.get(
        f"{API}/events/export.pdf",
        headers=headers,
        params={"start": "2026-11-01", "end": "2026-11-30"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    empty = client.get(
        f"{API}/events/export.pdf",
        headers=headers,
        params={"start": "2027-02-01", "end": "2027-02-28"},
    )
    assert empty.content.startswith(b"%PDF")
