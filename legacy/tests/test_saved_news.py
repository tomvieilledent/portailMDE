"""Tests for per-user saved articles (bookmarks) and rolling-month persistence."""

from datetime import datetime, timedelta, timezone

import pytest


def _create_article(client, headers, title='Réforme TVA 2026', url='https://example.com/a'):
    resp = client.post('/news', headers=headers, json={
        'title': title,
        'source': 'Test Source',
        'summary': 'Résumé de test',
        'url': url,
        'category': 'réglementation',
    })
    assert resp.status_code == 201
    return resp.get_json()['news_item']


def test_save_article_by_news_id_snapshots_fields(seeded_context):
    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])

    resp = client.post('/news/saved', headers=seeded_context['member_headers'],
                       json={'news_id': article['id']})
    assert resp.status_code == 201
    saved = resp.get_json()['saved']
    assert saved['news_id'] == article['id']
    assert saved['title'] == article['title']
    assert saved['url'] == article['url']
    assert saved['category'] == 'réglementation'
    assert saved['saved_at']


def test_save_requires_auth(seeded_context):
    client = seeded_context['client']
    resp = client.post('/news/saved', json={'title': 'x'})
    assert resp.status_code == 401


def test_save_is_idempotent_per_user(seeded_context):
    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])
    h = seeded_context['member_headers']

    first = client.post('/news/saved', headers=h, json={'news_id': article['id']})
    second = client.post('/news/saved', headers=h, json={'news_id': article['id']})
    assert first.get_json()['saved']['id'] == second.get_json()['saved']['id']

    listing = client.get('/news/saved', headers=h).get_json()['items']
    assert len(listing) == 1


def test_list_is_scoped_to_user(seeded_context):
    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])
    client.post('/news/saved', headers=seeded_context['member_headers'],
                json={'news_id': article['id']})

    member_items = client.get('/news/saved', headers=seeded_context['member_headers']).get_json()['items']
    other_items = client.get('/news/saved', headers=seeded_context['company_admin_headers']).get_json()['items']
    assert len(member_items) == 1
    assert other_items == []


def test_save_unknown_article_without_title_returns_404(seeded_context):
    client = seeded_context['client']
    resp = client.post('/news/saved', headers=seeded_context['member_headers'],
                       json={'news_id': 'does-not-exist'})
    assert resp.status_code == 404


def test_save_with_explicit_snapshot(seeded_context):
    client = seeded_context['client']
    resp = client.post('/news/saved', headers=seeded_context['member_headers'], json={
        'title': 'Article externe',
        'url': 'https://example.com/ext',
        'source': 'Externe',
    })
    assert resp.status_code == 201
    assert resp.get_json()['saved']['title'] == 'Article externe'


def test_delete_saved_article(seeded_context):
    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])
    h = seeded_context['member_headers']
    saved = client.post('/news/saved', headers=h, json={'news_id': article['id']}).get_json()['saved']

    resp = client.delete(f"/news/saved/{saved['id']}", headers=h)
    assert resp.status_code == 200
    assert client.get('/news/saved', headers=h).get_json()['items'] == []


def test_cannot_delete_other_users_saved_article(seeded_context):
    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])
    saved = client.post('/news/saved', headers=seeded_context['member_headers'],
                       json={'news_id': article['id']}).get_json()['saved']

    resp = client.delete(f"/news/saved/{saved['id']}",
                         headers=seeded_context['company_admin_headers'])
    assert resp.status_code == 404


def test_saved_article_survives_rolling_month_purge(app_bundle, seeded_context):
    """A bookmarked article stays visible after the source row is purged."""
    from backend.persistence.db import SessionLocal
    from backend.persistence.models import News as ORMNews

    client = seeded_context['client']
    article = _create_article(client, seeded_context['admin_headers'])
    h = seeded_context['member_headers']
    client.post('/news/saved', headers=h, json={'news_id': article['id']})

    # Simulate the rolling-month purge deleting the original article.
    db = SessionLocal()
    try:
        old = datetime.now(timezone.utc) - timedelta(days=40)
        row = db.query(ORMNews).filter(ORMNews.id == article['id']).first()
        row.created_at = old
        db.commit()
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        db.query(ORMNews).filter(ORMNews.created_at < cutoff).delete()
        db.commit()
    finally:
        db.close()

    # Article gone from public feed, but still in the user's bookmarks with its link.
    assert client.get(f"/news/{article['id']}").status_code == 404
    items = client.get('/news/saved', headers=h).get_json()['items']
    assert len(items) == 1
    assert items[0]['url'] == article['url']
