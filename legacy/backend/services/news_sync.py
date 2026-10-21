"""Daily sync of French economic news — réglementation et vie des entreprises.

Sources actives (RSS presse spécialisée) :
    réglementation  — Figaro Entreprises, BFM Entreprises, Le Monde Éco, Challenges, Capital
Sources officielles (best-effort, souvent bloquées) :
    réglementation  — Journal Officiel, BOFiP, URSSAF
"""

import logging
from datetime import datetime, timedelta, timezone
from time import mktime

import feedparser
import requests

from backend.persistence.db import SessionLocal
from backend.persistence.models import News as ORMNews
from backend.persistence.services.facades.news_facade_sql import NewsFacade

logger = logging.getLogger(__name__)

TIMEOUT = 10

RSS_SOURCES = [
    {
        'name': 'Net-Entreprises',
        'category': 'réglementation',
        'url': 'https://www.net-entreprises.fr/actualites/rss/',
        'check_url': True,
    },
    {
        'name': 'Ministère du Travail',
        'category': 'réglementation',
        'url': 'https://travail-emploi.gouv.fr/rss.xml',
        'check_url': False,  # bloque les HEAD/GET Python (TLS fingerprinting)
    },
    {
        'name': 'Douanes',
        'category': 'réglementation',
        'url': 'https://www.douane.gouv.fr/rss.xml',
        'check_url': True,  # vraies 404 sur les vieilles URLs
    },
    {
        'name': 'INPI',
        'category': 'réglementation',
        'url': 'https://www.inpi.fr/rss.xml',
        'check_url': True,
    },
    {
        'name': 'Journal Officiel',
        'category': 'réglementation',
        'url': 'https://www.legifrance.gouv.fr/feeds/jorf',
        'check_url': False,
    },
    {
        'name': 'BOFiP',
        'category': 'réglementation',
        'url': 'https://bofip.impots.gouv.fr/rss.xml',
        'check_url': False,
    },
]


def _parse_date(parsed_time):
    if not parsed_time:
        return None
    try:
        return datetime.fromtimestamp(mktime(parsed_time), tz=timezone.utc)
    except Exception:
        return None


_HEAD_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def _url_reachable(url):
    """Return True if the URL responds with a 2xx or 3xx status code."""
    try:
        r = requests.head(url, timeout=5, headers=_HEAD_HEADERS, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False


def _strip_html(text):
    import re
    return re.sub(r'<[^>]+>', ' ', text).strip()


def _fetch_rss(source, facade):
    try:
        resp = requests.get(source['url'], timeout=TIMEOUT,
                            headers=_HEAD_HEADERS)
        feed = feedparser.parse(resp.text)
    except Exception as exc:
        logger.warning("RSS %s: %s", source['name'], exc)
        return 0

    count = 0
    for entry in feed.entries[:20]:
        url = str(entry.get('link') or '').strip()
        if not url or facade.url_exists(url):
            continue
        title = str(entry.get('title') or '').strip()
        if not title:
            continue
        raw_summary = str(entry.get('summary') or entry.get('description') or '').strip()
        summary = _strip_html(raw_summary)
        # skip articles without body
        if not summary:
            continue
        # skip articles with broken URLs (only for sources where check_url=True)
        if source.get('check_url') and not _url_reachable(url):
            logger.info("RSS %s: skipping unreachable %s", source['name'], url)
            continue
        facade.create(
            title=title[:500],
            source=source['name'],
            summary=summary[:2000],
            url=url,
            published_at=_parse_date(entry.get('published_parsed')),
            category=source['category'],
        )
        count += 1
    return count


def sync_all():
    """Purge articles older than 30 days then fetch all sources."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    db = SessionLocal()
    try:
        db.query(ORMNews).filter(ORMNews.created_at < cutoff).delete()
        db.commit()
    finally:
        db.close()

    facade = NewsFacade()
    total = 0
    for source in RSS_SOURCES:
        try:
            n = _fetch_rss(source, facade)
            logger.info("news_sync: %s → %d new items", source['name'], n)
            total += n
        except Exception as exc:
            logger.error("news_sync: %s failed — %s", source['name'], exc)
    return total
