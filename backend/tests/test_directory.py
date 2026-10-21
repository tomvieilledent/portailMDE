"""Tests de l'annuaire : recherche des personnes et liste des entreprises."""

API = "/api/v1/directory"


def test_requires_auth(client):
    """L'annuaire exige une authentification."""
    assert client.get(f"{API}/people").status_code == 401


def test_people_search_and_company_filter(client, make_user, make_company, login):
    """Recherche de personnes et filtre par entreprise."""
    acme, zeta = make_company("Acme"), make_company("Zeta")
    make_user("me@x.fr", first_name="Moi", last_name="Zzz", company_id=acme.id)
    make_user(
        "a@x.fr", first_name="Ada", last_name="Lovelace", job_title="Ingénieure", company_id=acme.id
    )
    make_user("b@x.fr", first_name="Bob", last_name="Martin", company_id=zeta.id)
    make_user("solo@x.fr", first_name="Solo", last_name="Indep")
    headers = login("me@x.fr")
    assert client.get(f"{API}/people", headers=headers).json()["total"] == 4
    by_job = client.get(f"{API}/people", headers=headers, params={"search": "ingé"}).json()
    assert [p["email"] for p in by_job["items"]] == ["a@x.fr"]
    assert by_job["items"][0]["company"]["name"] == "Acme"
    by_company_name = client.get(f"{API}/people", headers=headers, params={"search": "zeta"}).json()
    assert [p["email"] for p in by_company_name["items"]] == ["b@x.fr"]
    filtered = client.get(
        f"{API}/people", headers=headers, params={"company_id": str(acme.id)}
    ).json()
    assert filtered["total"] == 2


def test_people_hides_inactive_users_and_companies(client, make_user, make_company, login):
    """Les utilisateurs et entreprises inactifs sont masqués."""
    dead = make_company("Dead", is_active=False)
    make_user("me@x.fr")
    make_user("off@x.fr", is_active=False)
    make_user("orphan@x.fr", company_id=dead.id)
    emails = [
        p["email"] for p in client.get(f"{API}/people", headers=login("me@x.fr")).json()["items"]
    ]
    assert emails == ["me@x.fr"]


def test_people_never_exposes_credentials(client, make_user, login):
    """Les données sensibles ne sont jamais exposées."""
    make_user("me@x.fr")
    person = client.get(f"{API}/people", headers=login("me@x.fr")).json()["items"][0]
    assert not {"password_hash", "role", "permissions"} & set(person)


def test_companies_with_member_count(client, make_user, make_company, login):
    """Les entreprises sont listées avec leur nombre de membres actifs."""
    acme = make_company("Acme", kind="partner")
    make_company("Hidden", is_active=False)
    make_company("Other")
    make_user("me@x.fr", company_id=acme.id)
    make_user("b@x.fr", company_id=acme.id)
    make_user("gone@x.fr", company_id=acme.id, is_active=False)
    headers = login("me@x.fr")
    page = client.get(f"{API}/companies", headers=headers).json()
    assert [c["name"] for c in page["items"]] == ["Acme", "Other"]
    assert page["items"][0]["member_count"] == 2 and page["items"][1]["member_count"] == 0
    partners = client.get(f"{API}/companies", headers=headers, params={"kind": "partner"}).json()
    assert partners["total"] == 1
