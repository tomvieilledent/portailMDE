"""Tests de l'API des utilisateurs : profil, mot de passe, création, droits, désactivation et rôles."""

from app.models.enums import UserRole

API = "/api/v1/users"


def new_user(**overrides):
    """Construit le corps d'une requête de création d'utilisateur."""
    return {"email": "new@example.fr", "password": "password123", **overrides}


def test_me_read_and_update(client, make_user, login):
    """Lecture et mise à jour de son propre profil."""
    make_user(first_name="Ada")
    headers = login()
    assert client.get(f"{API}/me", headers=headers).json()["first_name"] == "Ada"
    response = client.patch(f"{API}/me", headers=headers, json={"job_title": "CTO"})
    assert response.status_code == 200
    assert response.json()["job_title"] == "CTO"


def test_change_password(client, make_user, login):
    """Changement de mot de passe."""
    make_user()
    headers = login()
    bad = client.post(
        f"{API}/me/password",
        headers=headers,
        json={"current_password": "x", "new_password": "newpassword1"},
    )
    assert bad.status_code == 400
    ok = client.post(
        f"{API}/me/password",
        headers=headers,
        json={"current_password": "password123", "new_password": "newpassword1"},
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    # L'ancienne session est révoquée ; la nouvelle paire fonctionne.
    assert client.get(f"{API}/me", headers=headers).status_code == 401
    new_headers = {"Authorization": f"Bearer {ok.json()['access_token']}"}
    assert client.get(f"{API}/me", headers=new_headers).status_code == 200
    login(password="newpassword1")


def test_list_requires_manage_users(client, make_user, login):
    """La liste des utilisateurs exige la permission dédiée."""
    make_user()
    assert client.get(API, headers=login()).status_code == 403


def test_list_with_search_and_pagination(client, make_user, login):
    """Liste des utilisateurs avec recherche et pagination."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN, last_name="Zed")
    make_user("a@x.fr", last_name="Alpha")
    make_user("b@x.fr", last_name="Beta")
    headers = login("root@x.fr")
    page = client.get(API, headers=headers, params={"limit": 2}).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    found = client.get(API, headers=headers, params={"search": "alp"}).json()
    assert [u["email"] for u in found["items"]] == ["a@x.fr"]


def test_super_admin_creates_user(client, make_user, login):
    """Le super admin crée un utilisateur."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    response = client.post(API, headers=login("root@x.fr"), json=new_user(email="New@Example.fr"))
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.fr"
    assert "password" not in response.json() and "password_hash" not in response.json()
    duplicate = client.post(API, headers=login("root@x.fr"), json=new_user())
    assert duplicate.status_code == 409


def test_company_admin_creates_member_in_own_company_only(client, make_user, make_company, login):
    """Un admin d'entreprise ne crée des membres que dans la sienne."""
    mine, other = make_company("Mine"), make_company("Other")
    make_user("boss@x.fr", company_id=mine.id, is_company_admin=True)
    headers = login("boss@x.fr")
    ok = client.post(API, headers=headers, json=new_user(company_id=str(mine.id)))
    assert ok.status_code == 201
    ko = client.post(API, headers=headers, json=new_user(email="o@x.fr", company_id=str(other.id)))
    assert ko.status_code == 403
    escalate = client.post(
        API, headers=headers, json=new_user(email="s@x.fr", company_id=str(mine.id), role="staff")
    )
    assert escalate.status_code == 403


def test_member_cannot_create(client, make_user, login):
    """Un simple membre ne peut pas créer d'utilisateur."""
    make_user()
    assert client.post(API, headers=login(), json=new_user()).status_code == 403


def test_staff_cannot_touch_super_admin(client, make_user, login):
    """Le staff ne peut pas agir sur un super admin."""
    root = make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    make_user("staff@x.fr", role=UserRole.STAFF, permissions=["manage_users"])
    headers = login("staff@x.fr")
    assert client.post(f"{API}/{root.id}/deactivate", headers=headers).status_code == 403
    assert client.delete(f"{API}/{root.id}", headers=headers).status_code == 403


def test_deactivate_reactivate_and_login(client, make_user, login):
    """Désactivation, réactivation et effet sur la connexion."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    target = make_user("t@x.fr")
    headers = login("root@x.fr")
    assert (
        client.post(f"{API}/{target.id}/deactivate", headers=headers).json()["is_active"] is False
    )
    bad = client.post("/api/v1/auth/login", json={"email": "t@x.fr", "password": "password123"})
    assert bad.status_code == 401
    assert client.post(f"{API}/{target.id}/reactivate", headers=headers).json()["is_active"] is True


def test_company_admin_manages_only_own_company(client, make_user, make_company, login):
    """Un admin d'entreprise ne gère que les utilisateurs de son entreprise."""
    mine, other = make_company("Mine"), make_company("Other")
    make_user("boss@x.fr", company_id=mine.id, is_company_admin=True)
    colleague = make_user("c@x.fr", company_id=mine.id)
    stranger = make_user("s@x.fr", company_id=other.id)
    headers = login("boss@x.fr")
    assert client.post(f"{API}/{colleague.id}/deactivate", headers=headers).status_code == 200
    assert client.post(f"{API}/{stranger.id}/deactivate", headers=headers).status_code == 403


def test_cannot_remove_last_super_admin(client, make_user, login):
    """Impossible de retirer le dernier super admin."""
    root = make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    headers = login("root@x.fr")
    assert client.post(f"{API}/{root.id}/deactivate", headers=headers).status_code == 403
    demote = client.put(f"{API}/{root.id}/role", headers=headers, json={"role": "member"})
    assert demote.status_code == 403


def test_delete_is_soft(client, make_user, login, session):
    """La suppression d'un utilisateur est logique."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    target = make_user("t@x.fr")
    headers = login("root@x.fr")
    assert client.delete(f"{API}/{target.id}", headers=headers).status_code == 204
    assert client.get(f"{API}/{target.id}", headers=headers).status_code == 404
    session.refresh(target)
    assert target.deleted_at is not None


def test_set_role_super_admin_only(client, make_user, login):
    """Seul le super admin peut changer les rôles."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    target = make_user("t@x.fr")
    body = {"role": "staff", "permissions": ["manage_news"]}
    assert client.put(f"{API}/{target.id}/role", headers=login("root@x.fr"), json=body).json()[
        "permissions"
    ] == ["manage_news"]
    make_user("m@x.fr")
    assert (
        client.put(f"{API}/{target.id}/role", headers=login("m@x.fr"), json=body).status_code == 403
    )
    invalid = {"role": "staff", "permissions": ["fly"]}
    assert (
        client.put(f"{API}/{target.id}/role", headers=login("root@x.fr"), json=invalid).status_code
        == 422
    )


def test_deleted_user_cannot_login(client, make_user, login):
    """Un utilisateur supprimé ne peut plus se connecter."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    target = make_user("t@x.fr")
    client.delete(f"{API}/{target.id}", headers=login("root@x.fr"))
    bad = client.post("/api/v1/auth/login", json={"email": "t@x.fr", "password": "password123"})
    assert bad.status_code == 401


def test_export_own_data(client, make_user, login):
    """L'utilisateur exporte ses données personnelles."""
    make_user(first_name="Ada", phone="0102030405")
    response = client.get(f"{API}/me/export", headers=login())
    assert response.status_code == 200
    assert response.json()["profile"]["first_name"] == "Ada"


def test_delete_own_account_anonymizes(client, make_user, login, session):
    """L'auto-suppression anonymise les données personnelles."""
    make_user("root@x.fr", role=UserRole.SUPER_ADMIN)
    target = make_user("t@x.fr", first_name="Ada", phone="0102030405", job_title="CTO")
    headers = login("t@x.fr")
    assert client.delete(f"{API}/me", headers=headers).status_code == 204
    session.refresh(target)
    assert target.deleted_at is not None
    assert target.email != "t@x.fr"
    assert target.phone is None and target.job_title is None and target.last_name is None
    assert target.first_name != "Ada"


def test_read_other_user_requires_rights(client, make_user, login):
    """Un membre ne peut pas lire le profil complet d'un autre utilisateur, mais lit le sien."""
    me = make_user(email="me@example.fr")
    other = make_user(email="other@example.fr")
    headers = login(email="me@example.fr")
    assert client.get(f"{API}/{other.id}", headers=headers).status_code == 403
    assert client.get(f"{API}/{me.id}", headers=headers).status_code == 200
