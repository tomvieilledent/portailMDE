import pytest

from app.models.enums import UserRole

API = "/api/v1"
START = "2026-11-10T09:00:00+00:00"
END = "2026-11-10T17:00:00+00:00"


@pytest.fixture
def manager(make_user, login):
    make_user("mgr@x.fr", role=UserRole.STAFF, permissions=["manage_trainings"])
    return login("mgr@x.fr")


def new_training(client, headers, **kw):
    return client.post(f"{API}/trainings", headers=headers, json={"title": "Excel", **kw}).json()


def new_session(client, headers, training, **kw):
    body = {"start_at": START, "end_at": END, "max_participants": 2, "is_public": True, **kw}
    return client.post(f"{API}/trainings/{training['id']}/sessions", headers=headers, json=body)


def test_catalog_permissions(client, make_user, login, manager):
    make_user()
    assert client.post(f"{API}/trainings", headers=login(), json={"title": "X"}).status_code == 403
    created = client.post(
        f"{API}/trainings", headers=manager, json={"title": "Excel", "kind": "atelier"}
    )
    assert created.status_code == 201
    assert (
        client.get(f"{API}/trainings", headers=login(), params={"kind": "atelier"}).json()["total"]
        == 1
    )
    assert (
        client.get(f"{API}/trainings", headers=login(), params={"search": "zzz"}).json()["total"]
        == 0
    )


def test_inactive_training_hidden(client, make_user, login, manager):
    make_user()
    training = new_training(client, manager)
    client.post(f"{API}/trainings/{training['id']}/deactivate", headers=manager)
    assert client.get(f"{API}/trainings", headers=login()).json()["total"] == 0
    assert client.get(f"{API}/trainings/{training['id']}", headers=login()).status_code == 404
    assert client.get(f"{API}/trainings/{training['id']}", headers=manager).status_code == 200


def test_update_and_delete(client, manager):
    training = new_training(client, manager)
    url = f"{API}/trainings/{training['id']}"
    assert client.patch(url, headers=manager, json={"title": "Word"}).json()["title"] == "Word"
    assert client.delete(url, headers=manager).status_code == 204
    assert client.get(url, headers=manager).status_code == 404


def test_session_validation(client, manager):
    training = new_training(client, manager)
    bad = new_session(client, manager, training, start_at=END, end_at=START)
    assert bad.status_code == 422
    assert new_session(client, manager, training, max_participants=0).status_code == 422


def test_interest_toggle(client, make_user, login, manager):
    make_user()
    training = new_training(client, manager)
    url = f"{API}/trainings/{training['id']}/interest"
    assert client.put(url, headers=login()).status_code == 204
    assert client.put(url, headers=login()).status_code == 204
    assert len(client.get(f"{url[:-9]}/interested", headers=manager).json()) == 1
    assert client.delete(url, headers=login()).status_code == 204
    assert client.get(f"{url[:-9]}/interested", headers=manager).json() == []


def test_enroll_capacity_and_unenroll(client, make_user, login, manager):
    for email in ("a@x.fr", "b@x.fr", "c@x.fr"):
        make_user(email)
    training = new_training(client, manager)
    ts = new_session(client, manager, training, max_participants=2).json()
    url = f"{API}/training-sessions/{ts['id']}/enroll"
    assert client.post(url, headers=login("a@x.fr")).status_code == 201
    assert client.post(url, headers=login("a@x.fr")).status_code == 409
    assert client.post(url, headers=login("b@x.fr")).status_code == 201
    full = client.post(url, headers=login("c@x.fr"))
    assert full.status_code == 409 and "complète" in full.json()["error"]["message"]
    view = client.get(f"{API}/training-sessions/{ts['id']}", headers=login("a@x.fr")).json()
    assert view["enrolled_count"] == 2 and view["is_enrolled"] is True
    assert client.delete(url, headers=login("a@x.fr")).status_code == 204
    assert client.post(url, headers=login("c@x.fr")).status_code == 201
    assert client.delete(url, headers=login("a@x.fr")).status_code == 404


def test_cannot_shrink_capacity_below_enrolled(client, make_user, login, manager):
    make_user("a@x.fr")
    make_user("b@x.fr")
    training = new_training(client, manager)
    ts = new_session(client, manager, training).json()
    for email in ("a@x.fr", "b@x.fr"):
        client.post(f"{API}/training-sessions/{ts['id']}/enroll", headers=login(email))
    url = f"{API}/training-sessions/{ts['id']}"
    assert client.patch(url, headers=manager, json={"max_participants": 1}).status_code == 400
    assert client.patch(url, headers=manager, json={"max_participants": 5}).status_code == 200


def test_closed_session_rejects_enrollment(client, make_user, login, manager):
    make_user()
    training = new_training(client, manager)
    ts = new_session(client, manager, training).json()
    client.patch(
        f"{API}/training-sessions/{ts['id']}", headers=manager, json={"status": "cancelled"}
    )
    assert (
        client.post(f"{API}/training-sessions/{ts['id']}/enroll", headers=login()).status_code
        == 400
    )


def test_private_session_needs_invitation(client, make_user, login, manager):
    guest = make_user("g@x.fr")
    make_user("s@x.fr")
    training = new_training(client, manager)
    ts = new_session(client, manager, training, is_public=False).json()
    url = f"{API}/training-sessions/{ts['id']}"
    assert client.get(url, headers=login("g@x.fr")).status_code == 404
    assert client.post(f"{url}/enroll", headers=login("g@x.fr")).status_code == 404
    invited = client.post(f"{url}/invitations", headers=manager, json={"user_ids": [str(guest.id)]})
    assert invited.status_code == 201
    assert client.get(url, headers=login("g@x.fr")).status_code == 200
    assert client.get(url, headers=login("s@x.fr")).status_code == 404
    inbox = client.get(f"{API}/invitations/me", headers=login("g@x.fr")).json()
    assert inbox[0]["session_id"] == ts["id"] and inbox[0]["target_title"] == "Excel"


def test_completion_and_my_trainings(client, make_user, login, manager):
    user = make_user()
    training = new_training(client, manager)
    ts = new_session(client, manager, training).json()
    client.post(f"{API}/training-sessions/{ts['id']}/enroll", headers=login())
    listing = client.get(f"{API}/training-sessions/{ts['id']}/enrollments", headers=manager).json()
    assert len(listing) == 1
    done = client.post(
        f"{API}/training-sessions/{ts['id']}/enrollments/{user.id}/complete", headers=manager
    )
    assert done.json()["completed_at"]
    mine = client.get(f"{API}/trainings/mine", headers=login()).json()
    assert mine[0]["completed_at"] and mine[0]["session_id"] == ts["id"]


def test_session_listing_range(client, make_user, login, manager):
    make_user()
    training = new_training(client, manager)
    new_session(client, manager, training)
    new_session(
        client,
        manager,
        training,
        start_at="2026-12-10T09:00:00+00:00",
        end_at="2026-12-10T10:00:00+00:00",
    )
    found = client.get(
        f"{API}/training-sessions", headers=login(), params={"start": "2026-12-01T00:00:00+00:00"}
    ).json()
    assert len(found) == 1
    assert (
        len(client.get(f"{API}/trainings/{training['id']}/sessions", headers=login()).json()) == 2
    )


def test_picture_and_document_upload(client, manager):
    import io

    training = new_training(client, manager)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 16
    url = f"{API}/trainings/{training['id']}"
    pic = client.put(f"{url}/picture", headers=manager, files={"file": ("a.png", io.BytesIO(png))})
    assert pic.json()["picture_path"].startswith("trainings/")
    doc = client.post(
        f"{url}/documents", headers=manager, files={"file": ("a.pdf", io.BytesIO(b"%PDF"))}
    )
    assert len(doc.json()["documents"]) == 1
