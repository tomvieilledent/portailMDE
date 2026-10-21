"""Tests de l'API des entreprises : droits, visibilité, membres et suppression logique."""

from app.models.enums import UserRole

API = "/api/v1/companies"


def staff(make_user, email="staff@x.fr"):
    """Crée un membre du staff autorisé à gérer les entreprises."""
    return make_user(email, role=UserRole.STAFF, permissions=["manage_companies"])


def test_create_requires_permission(client, make_user, login):
    """La création d'entreprise exige la permission dédiée."""
    owner = make_user()
    body = {"name": "Acme", "owner_id": str(owner.id)}
    assert client.post(API, headers=login(), json=body).status_code == 403


def test_staff_creates_and_lists(client, make_user, login):
    """Le staff crée une entreprise, la recherche et la filtre."""
    staff(make_user)
    owner = make_user("owner@x.fr")
    headers = login("staff@x.fr")
    created = client.post(
        API, headers=headers, json={"name": "Acme", "kind": "partner", "owner_id": str(owner.id)}
    )
    assert created.status_code == 201
    page = client.get(API, headers=headers, params={"search": "acm"}).json()
    assert page["total"] == 1 and page["items"][0]["kind"] == "partner"
    assert client.get(API, headers=headers, params={"kind": "company"}).json()["total"] == 0


def test_owner_is_required(client, make_user, login):
    """Créer une entreprise sans propriétaire est refusé."""
    staff(make_user)
    headers = login("staff@x.fr")
    assert client.post(API, headers=headers, json={"name": "Acme"}).status_code == 422
    unknown = {"name": "Acme", "owner_id": "00000000-0000-0000-0000-000000000000"}
    assert client.post(API, headers=headers, json=unknown).status_code == 404


def test_owner_becomes_company_admin(client, make_user, make_company, session, login):
    """Le propriétaire est rattaché à l'entreprise créée et en devient administrateur."""
    staff(make_user)
    old = make_company("Old")
    owner = make_user("owner@x.fr", company_id=old.id, is_company_admin=True)
    headers = login("staff@x.fr")
    created = client.post(
        API, headers=headers, json={"name": "New", "owner_id": str(owner.id)}
    ).json()
    session.refresh(owner)
    assert str(owner.company_id) == created["id"] and owner.is_company_admin is True
    owner_headers = login("owner@x.fr")
    patched = client.patch(
        f"{API}/{created['id']}", headers=owner_headers, json={"location": "Rodez"}
    )
    assert patched.status_code == 200 and patched.json()["location"] == "Rodez"


def test_inactive_hidden_from_members(client, make_user, make_company, login):
    """Une entreprise désactivée est masquée aux membres."""
    staff(make_user)
    make_user("m@x.fr")
    company = make_company("Ghost")
    client.post(f"{API}/{company.id}/deactivate", headers=login("staff@x.fr"))
    member_headers = login("m@x.fr")
    assert client.get(API, headers=member_headers).json()["total"] == 0
    assert client.get(f"{API}/{company.id}", headers=member_headers).status_code == 404
    assert client.get(f"{API}/{company.id}", headers=login("staff@x.fr")).status_code == 200


def test_my_company(client, make_user, make_company, login):
    """L'endpoint « mon entreprise » renvoie celle de l'utilisateur."""
    company = make_company("Mine")
    make_user(company_id=company.id)
    assert client.get(f"{API}/me", headers=login()).json()["name"] == "Mine"
    make_user("solo@x.fr")
    assert client.get(f"{API}/me", headers=login("solo@x.fr")).status_code == 404


def test_company_admin_edits_own_company_not_kind(client, make_user, make_company, login):
    """Un admin d'entreprise modifie la sienne, mais pas son type."""
    mine, other = make_company("Mine"), make_company("Other")
    make_user(company_id=mine.id, is_company_admin=True)
    headers = login()
    ok = client.patch(f"{API}/{mine.id}", headers=headers, json={"description": "Nouveau"})
    assert ok.status_code == 200 and ok.json()["description"] == "Nouveau"
    assert client.patch(f"{API}/{other.id}", headers=headers, json={"name": "X"}).status_code == 403
    kind = client.patch(f"{API}/{mine.id}", headers=headers, json={"kind": "partner"})
    assert kind.status_code == 403


def test_plain_member_cannot_edit(client, make_user, make_company, login):
    """Un simple membre ne peut pas modifier l'entreprise."""
    company = make_company()
    make_user(company_id=company.id)
    assert (
        client.patch(f"{API}/{company.id}", headers=login(), json={"name": "X"}).status_code == 403
    )


def test_members_management(client, make_user, make_company, login):
    """Ajout, liste et retrait des membres d'une entreprise."""
    staff(make_user)
    company = make_company()
    user = make_user("u@x.fr")
    headers = login("staff@x.fr")
    added = client.put(f"{API}/{company.id}/members/{user.id}", headers=headers)
    assert added.status_code == 200 and added.json()["company_id"] == str(company.id)
    members = client.get(f"{API}/{company.id}/members", headers=headers).json()
    assert [m["email"] for m in members] == ["u@x.fr"]
    assert (
        client.delete(f"{API}/{company.id}/members/{user.id}", headers=headers).status_code == 204
    )
    assert (
        client.delete(f"{API}/{company.id}/members/{user.id}", headers=headers).status_code == 404
    )


def test_company_admin_can_remove_but_not_add(client, make_user, make_company, login):
    """Un admin d'entreprise peut retirer des membres mais pas en ajouter."""
    company = make_company()
    make_user("boss@x.fr", company_id=company.id, is_company_admin=True)
    colleague = make_user("c@x.fr", company_id=company.id)
    outsider = make_user("o@x.fr")
    headers = login("boss@x.fr")
    assert (
        client.put(f"{API}/{company.id}/members/{outsider.id}", headers=headers).status_code == 403
    )
    assert (
        client.delete(f"{API}/{company.id}/members/{colleague.id}", headers=headers).status_code
        == 204
    )


def test_delete_is_soft(client, make_user, make_company, login, session):
    """La suppression d'une entreprise est logique (deleted_at renseigné)."""
    staff(make_user)
    company = make_company()
    headers = login("staff@x.fr")
    assert client.delete(f"{API}/{company.id}", headers=headers).status_code == 204
    assert client.get(f"{API}/{company.id}", headers=headers).status_code == 404
    session.refresh(company)
    assert company.deleted_at is not None


def test_website_url_must_be_http(client, make_user, login):
    """Les URLs non http(s) (ex. javascript:) sont refusées."""
    staff(make_user)
    owner = str(make_user("owner@x.fr").id)
    headers = login("staff@x.fr")
    bad = client.post(
        API,
        headers=headers,
        json={"name": "Acme", "website_url": "javascript:alert(1)", "owner_id": owner},
    )
    assert bad.status_code == 422
    ok = client.post(
        API,
        headers=headers,
        json={"name": "Acme", "website_url": "https://acme.fr", "owner_id": owner},
    )
    assert ok.status_code == 201
