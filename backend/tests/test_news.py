"""Tests des actualités : synchronisation RSS, filtres, droits, favoris et contenu de la page d'accueil."""

from datetime import UTC, datetime, timedelta

from app.models import NewsArticle
from app.models.enums import UserRole
from app.services import news as service

API = "/api/v1"

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Nouvelle loi</title><link>https://ex.fr/1</link>
<description>&lt;p&gt;Résumé &lt;b&gt;important&lt;/b&gt;&lt;/p&gt;</description>
<pubDate>Mon, 05 Oct 2026 10:00:00 GMT</pubDate></item>
<item><title>Sans résumé</title><link>https://ex.fr/2</link></item>
</channel></rss>"""


def editor(make_user, login):
    """Crée un éditeur d'actualités et retourne ses en-têtes."""
    make_user("ed@x.fr", role=UserRole.STAFF, permissions=["manage_news"])
    return login("ed@x.fr")


def test_sync_imports_cleans_and_dedupes(session):
    """La synchronisation importe, nettoie le HTML et dédoublonne."""
    sources = [{"name": "Test", "category": "réglementation", "url": "u"}]
    assert service.sync_all(session, fetch=lambda _: RSS, sources=sources) == 1
    assert service.sync_all(session, fetch=lambda _: RSS, sources=sources) == 0
    article = session.query(NewsArticle).one()
    assert article.summary == "Résumé important"
    assert article.source == "Test" and article.published_at.year == 2026


def test_sync_survives_failing_source(session):
    """Une source en échec n'empêche pas la synchronisation des autres."""

    def fetch(url):
        """Simule la récupération d'un flux, en échec pour la source « bad »."""
        if url == "bad":
            raise RuntimeError("réseau")
        return RSS

    sources = [
        {"name": "Bad", "category": "c", "url": "bad"},
        {"name": "Good", "category": "c", "url": "good"},
    ]
    assert service.sync_all(session, fetch=fetch, sources=sources) == 1


def test_sync_purges_old_articles(session):
    """La synchronisation purge les articles anciens."""
    old = NewsArticle(title="Vieux", created_at=datetime.now(UTC) - timedelta(days=40))
    session.add_all([old, NewsArticle(title="Récent")])
    session.commit()
    service.sync_all(session, fetch=lambda _: "", sources=[])
    assert [a.title for a in session.query(NewsArticle).all()] == ["Récent"]


def test_list_filters(client, make_user, login, session):
    """Liste des actualités avec filtres par catégorie et recherche."""
    make_user()
    session.add_all(
        [
            NewsArticle(title="TVA 2026", category="fiscalité"),
            NewsArticle(title="Embauche", category="social", summary="contrat"),
        ]
    )
    session.commit()
    headers = login()
    assert client.get(f"{API}/news", headers=headers).json()["total"] == 2
    assert (
        client.get(f"{API}/news", headers=headers, params={"category": "social"}).json()["total"]
        == 1
    )
    assert client.get(f"{API}/news", headers=headers, params={"search": "tva"}).json()["total"] == 1
    assert client.get(f"{API}/news").status_code == 401


def test_manage_news_permissions(client, make_user, login):
    """La gestion des actualités exige la permission dédiée."""
    make_user()
    body = {"title": "Info", "url": "https://ex.fr/x"}
    assert client.post(f"{API}/news", headers=login(), json=body).status_code == 403
    make_user("ed@x.fr", role=UserRole.STAFF, permissions=["manage_news"])
    headers = login("ed@x.fr")
    created = client.post(f"{API}/news", headers=headers, json=body)
    assert created.status_code == 201
    assert client.post(f"{API}/news", headers=headers, json=body).status_code == 409
    assert client.delete(f"{API}/news/{created.json()['id']}", headers=headers).status_code == 204
    assert client.delete(f"{API}/news/{created.json()['id']}", headers=headers).status_code == 404


def test_sync_endpoint(client, make_user, login, monkeypatch):
    """L'endpoint de synchronisation renvoie le nombre d'articles créés."""
    monkeypatch.setattr(service, "RSS_SOURCES", [])
    headers = editor(make_user, login)
    assert client.post(f"{API}/news/sync", headers=headers).json() == {"created": 0}


def test_saved_articles_survive_purge(client, make_user, login, session):
    """Les articles enregistrés survivent à la purge."""
    make_user()
    article = NewsArticle(title="À garder", url="https://ex.fr/k")
    session.add(article)
    session.commit()
    headers = login()
    first = client.put(f"{API}/news/{article.id}/save", headers=headers).json()
    again = client.put(f"{API}/news/{article.id}/save", headers=headers).json()
    assert first["id"] == again["id"]
    session.delete(article)
    session.commit()
    saved = client.get(f"{API}/news/saved", headers=headers).json()
    assert saved[0]["title"] == "À garder" and saved[0]["article_id"] is None
    assert client.delete(f"{API}/news/saved/{saved[0]['id']}", headers=headers).status_code == 204
    assert client.get(f"{API}/news/saved", headers=headers).json() == []


def test_cannot_unsave_others_favorite(client, make_user, login, session):
    """Impossible de retirer le favori d'un autre utilisateur."""
    make_user("a@x.fr")
    make_user("b@x.fr")
    article = NewsArticle(title="X")
    session.add(article)
    session.commit()
    saved = client.put(f"{API}/news/{article.id}/save", headers=login("a@x.fr")).json()
    assert (
        client.delete(f"{API}/news/saved/{saved['id']}", headers=login("b@x.fr")).status_code == 404
    )


def test_landing_content_public_with_default_and_edit(client, make_user, login):
    """Le contenu de la page d'accueil est public, avec valeur par défaut et édition réservée."""
    default = client.get(f"{API}/content/landing")
    assert default.status_code == 200 and default.json()["value"]["sections"]
    assert client.get(f"{API}/content/unknown").status_code == 404
    make_user()
    assert (
        client.put(f"{API}/content/landing", headers=login(), json={"value": {}}).status_code == 403
    )
    headers = editor(make_user, login)
    edited = client.put(
        f"{API}/content/landing", headers=headers, json={"value": {"slogan": "Nouveau"}}
    )
    assert edited.status_code == 200
    assert client.get(f"{API}/content/landing").json()["value"] == {"slogan": "Nouveau"}


def test_since_filter_keeps_only_todays_news(client, make_user, login, session):
    """Le paramètre `since` ne garde que les articles récents (rubrique « infos du jour »)."""
    make_user("m@x.fr")
    now = datetime.now(UTC)
    session.add_all(
        [
            NewsArticle(title="Frais", published_at=now - timedelta(hours=2)),
            NewsArticle(title="Ancien", published_at=now - timedelta(days=5)),
        ]
    )
    session.commit()
    since = (now - timedelta(hours=24)).isoformat()
    found = client.get(f"{API}/news", headers=login("m@x.fr"), params={"since": since}).json()
    assert [a["title"] for a in found["items"]] == ["Frais"]


def test_empty_news_triggers_background_sync(client, make_user, login, monkeypatch):
    """Une base vide lance toute seule la synchronisation ; pas si un article existe déjà."""
    make_user("m@x.fr")
    calls = []
    monkeypatch.setattr(service, "sync_in_background", lambda: calls.append(1))
    monkeypatch.setenv("NEWS_SYNC_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client.get(f"{API}/news", headers=login("m@x.fr"))
    assert calls == [1]
    get_settings.cache_clear()


def test_customs_feed_keeps_only_regulation(session):
    """Les Douanes ne remontent que de la réglementation, pas les faits divers."""
    rss = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Saisie de 40 kg de cocaïne à Roissy</title><link>https://d.fr/1</link>
<description>Les douaniers ont saisi une cargaison.</description></item>
<item><title>Nouvelle procédure de dédouanement à l'import</title><link>https://d.fr/2</link>
<description>Un décret modifie les formalités déclaratives.</description></item>
<item><title>Journée portes ouvertes</title><link>https://d.fr/3</link>
<description>Venez découvrir nos métiers.</description></item>
</channel></rss>"""
    sources = [
        {"name": "Douanes", "category": "réglementation", "url": "u", "regulatory_only": True}
    ]
    assert service.sync_all(session, fetch=lambda _: rss, sources=sources) == 1
    assert [a.title for a in session.query(NewsArticle).all()] == [
        "Nouvelle procédure de dédouanement à l'import"
    ]
