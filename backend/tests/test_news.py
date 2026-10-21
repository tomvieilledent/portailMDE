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
    make_user("ed@x.fr", role=UserRole.STAFF, permissions=["manage_news"])
    return login("ed@x.fr")


def test_sync_imports_cleans_and_dedupes(session):
    sources = [{"name": "Test", "category": "réglementation", "url": "u"}]
    assert service.sync_all(session, fetch=lambda _: RSS, sources=sources) == 1
    assert service.sync_all(session, fetch=lambda _: RSS, sources=sources) == 0
    article = session.query(NewsArticle).one()
    assert article.summary == "Résumé important"
    assert article.source == "Test" and article.published_at.year == 2026


def test_sync_survives_failing_source(session):
    def fetch(url):
        if url == "bad":
            raise RuntimeError("réseau")
        return RSS

    sources = [
        {"name": "Bad", "category": "c", "url": "bad"},
        {"name": "Good", "category": "c", "url": "good"},
    ]
    assert service.sync_all(session, fetch=fetch, sources=sources) == 1


def test_sync_purges_old_articles(session):
    old = NewsArticle(title="Vieux", created_at=datetime.now(UTC) - timedelta(days=40))
    session.add_all([old, NewsArticle(title="Récent")])
    session.commit()
    service.sync_all(session, fetch=lambda _: "", sources=[])
    assert [a.title for a in session.query(NewsArticle).all()] == ["Récent"]


def test_list_filters(client, make_user, login, session):
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
    monkeypatch.setattr(service, "RSS_SOURCES", [])
    headers = editor(make_user, login)
    assert client.post(f"{API}/news/sync", headers=headers).json() == {"created": 0}


def test_saved_articles_survive_purge(client, make_user, login, session):
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
