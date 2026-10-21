"""Monthly agenda export — a printable sheet of the coming month's events.

Collects the *public* agenda events and *public* training sessions of a given
month and renders a self-contained, print-ready HTML sheet. The sheet is stored
under ``uploads/exports/`` so it can be downloaded/printed from the Gestion
tab. A scheduled job regenerates next month's sheet on the 25th (see
``backend/api/app.py``).
"""

import base64
import html
import json
import logging
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from backend.api.uploads import UPLOAD_ROOT, ensure_upload_dirs
from backend.persistence.services import (
    EventService, TrainingService, TrainingSessionService)

logger = logging.getLogger(__name__)

EXPORT_DIR = UPLOAD_ROOT / 'exports'
LOGO_PATH = Path(__file__).resolve().parent / 'assets' / 'logo-rodez.png'


@lru_cache(maxsize=1)
def _logo_data_uri():
    """Return the Rodez logo as a base64 data URI, or ``None`` if unavailable."""
    try:
        encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode('ascii')
        return f'data:image/png;base64,{encoded}'
    except OSError:
        logger.warning('Agenda export logo not found at %s', LOGO_PATH)
        return None

MONTHS_FR = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
             'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
WEEKDAYS_FR = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi',
               'samedi', 'dimanche']

event_service = EventService()
session_service = TrainingSessionService()
training_service = TrainingService()


def next_month(today=None):
    """Return the ``(year, month)`` of the month following *today*."""
    today = today or datetime.now()
    year, month = today.year, today.month
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _parse_iso(value):
    """Best-effort parse of an ISO datetime string; returns ``datetime`` or None."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def collect(year, month):
    """Return the sheet items for ``year``/``month``, sorted by date/time.

    Includes public agenda events plus every (non-cancelled) formation and
    atelier session scheduled that month.

    Each item is a dict:
    ``{key, date, time, end_time, title, kind, place, detail}`` where ``key`` is
    a stable identity used to merge snapshots across regenerations.
    """
    prefix = f'{year:04d}-{month:02d}'
    items = []

    for e in event_service.facade.list(limit=1000):
        if not e.get('is_public'):
            continue
        if not (e.get('date') or '').startswith(prefix):
            continue
        items.append({
            'key': f"event:{e['id']}",
            'date': e['date'],
            'time': e.get('time') or '',
            'end_time': '',
            'title': e.get('title') or 'Événement',
            'kind': 'Événement',
            'place': '',
            'detail': e.get('description') or e.get('creator') or '',
        })

    # All programmed formations & ateliers of the month are listed, regardless
    # of their public/private flag (that flag only gates in-app visibility).
    training_titles = {}
    for s in session_service.facade.list(limit=1000):
        if s.get('status') == 'cancelled':
            continue
        start = _parse_iso(s.get('start_date'))
        if not start or (start.year, start.month) != (year, month):
            continue
        tid = s.get('training_id')
        if tid not in training_titles:
            training = training_service.facade.get(tid) if tid else None
            training_titles[tid] = training or {}
        training = training_titles[tid]
        kind = 'Atelier' if (training.get('type') == 'atelier') else 'Formation'
        end = _parse_iso(s.get('end_date'))
        items.append({
            'key': f"session:{s['id']}",
            'date': start.strftime('%Y-%m-%d'),
            'time': start.strftime('%H:%M'),
            'end_time': end.strftime('%H:%M') if end else '',
            'title': training.get('title') or 'Formation',
            'kind': kind,
            'place': s.get('location') or '',
            'detail': training.get('description') or '',
        })

    items.sort(key=lambda i: (i['date'], i['time'] or '99:99'))
    return items


# CSS slug per item kind (drives colour theming).
KIND_SLUG = {
    'Formation': 'formation',
    'Atelier': 'atelier',
    'Événement': 'evenement',
}

# Inline location pin (no emoji dependency — renders identically everywhere).
PIN_SVG = ('<svg class="pin" viewBox="0 0 24 24" width="14" height="14" '
           'aria-hidden="true"><path fill="currentColor" d="M12 2C8.1 2 5 5.1 5 9'
           'c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6'
           'a2.5 2.5 0 0 1 0 5.5z"/></svg>')


def _day_parts(date_str):
    """'2026-08-03' -> ('lundi', '03', 'août')."""
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return (date_str, '', '')
    return (WEEKDAYS_FR[d.weekday()], f'{d.day:02d}', MONTHS_FR[d.month])


def render_html(year, month, items=None):
    """Render the printable, poster-style HTML sheet for ``year``/``month``."""
    if items is None:
        items = collect(year, month)
    month_label = f'{MONTHS_FR[month].capitalize()} {year}'
    generated = datetime.now().strftime('%d/%m/%Y à %H:%M')

    # Brand block: logo when available, otherwise a text fallback.
    logo_uri = _logo_data_uri()
    if logo_uri:
        brand_html = (f'<div class="logo"><img src="{logo_uri}" '
                      'alt="Rodez Agglomération"></div>')
    else:
        brand_html = ("<div class=\"brand\"><strong>Maison de l'Économie</strong>"
                      "Rodez Agglomération</div>")

    # Build day-grouped sections of event cards.
    sections = []
    current_day = None
    cards = []

    def flush():
        if current_day is None:
            return
        weekday, dnum, dmonth = _day_parts(current_day)
        sections.append(
            '<section class="day">'
            '<div class="day-date">'
            f'<span class="d-week">{html.escape(weekday)}</span>'
            f'<span class="d-num">{html.escape(dnum)}</span>'
            f'<span class="d-month">{html.escape(dmonth)}</span>'
            '</div>'
            f'<div class="day-cards">{"".join(cards)}</div>'
            '</section>')

    for it in items:
        if it['date'] != current_day:
            flush()
            current_day = it['date']
            cards = []
        slug = KIND_SLUG.get(it['kind'], 'evenement')
        hour = html.escape(it['time'] or '—')
        if it['end_time']:
            hour += f'<span class="c-end">→ {html.escape(it["end_time"])}</span>'
        place = html.escape(it['place'])
        detail = html.escape(it['detail'])
        cards.append(
            f'<article class="card {slug}">'
            f'<div class="c-time">{hour}</div>'
            '<div class="c-body">'
            f'<span class="c-kind">{html.escape(it["kind"])}</span>'
            f'<h3 class="c-title">{html.escape(it["title"])}</h3>'
            + (f'<p class="c-place">{PIN_SVG} {place}</p>' if place else '')
            + (f'<p class="c-detail">{detail}</p>' if detail else '')
            + '</div>'
            '</article>')
    flush()

    body = ('\n'.join(sections) if sections else
            '<div class="empty">Aucun événement public prévu ce mois-ci.</div>')

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Agenda — {html.escape(month_label)}</title>
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; }}
  body {{ font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; color: #14231b;
         background: #eef1ef; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .poster {{ max-width: 820px; margin: 24px auto; background: #fff; border-radius: 18px;
            overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,.12); }}

  /* Header banner */
  .hero {{ position: relative; padding: 34px 40px 28px;
          background: linear-gradient(135deg, #4a7a1a 0%, #7ec843 100%); color: #fff; }}
  .hero .eyebrow {{ font-size: 13px; letter-spacing: .28em; text-transform: uppercase;
                   opacity: .82; font-weight: 600; }}
  .hero h1 {{ margin: 6px 0 0; font-size: 52px; line-height: 1; font-weight: 800;
             text-transform: capitalize; letter-spacing: -.01em; }}
  .hero .brand {{ position: absolute; top: 30px; right: 40px; text-align: right;
                 font-size: 12px; opacity: .9; }}
  .hero .brand strong {{ display: block; font-size: 15px; }}
  .hero .logo {{ position: absolute; top: 28px; right: 40px; background: #fff;
                border-radius: 12px; padding: 10px 14px; box-shadow: 0 4px 14px rgba(0,0,0,.15); }}
  .hero .logo img {{ display: block; height: 48px; width: auto; }}
  .hero .tagline {{ margin-top: 14px; font-size: 14px; opacity: .9; }}

  /* Legend */
  .legend {{ display: flex; gap: 18px; padding: 14px 40px; background: #f7f9f8;
            border-bottom: 1px solid #e6ebe8; font-size: 13px; font-weight: 600; }}
  .legend span {{ display: inline-flex; align-items: center; gap: 7px; color: #3d4b43; }}
  .legend i {{ width: 12px; height: 12px; border-radius: 4px; display: inline-block; }}
  .lg-formation {{ background: #2563eb; }}
  .lg-atelier {{ background: #d97706; }}
  .lg-evenement {{ background: #16a34a; }}

  /* Body */
  .list {{ padding: 22px 40px 8px; }}
  .day {{ display: flex; gap: 20px; padding: 16px 0; border-top: 1px solid #eef1ef; }}
  .day:first-child {{ border-top: none; }}
  .day-date {{ flex: 0 0 76px; text-align: center; padding-top: 4px; }}
  .d-week {{ display: block; font-size: 12px; text-transform: uppercase; letter-spacing: .08em;
            color: #6b7a71; font-weight: 600; }}
  .d-num {{ display: block; font-size: 40px; font-weight: 800; color: #4a7a1a; line-height: 1.05; }}
  .d-month {{ display: block; font-size: 13px; text-transform: capitalize; color: #6b7a71; }}
  .day-cards {{ flex: 1; display: flex; flex-direction: column; gap: 10px; }}

  .card {{ display: flex; gap: 16px; padding: 14px 16px; border-radius: 12px;
          border: 1px solid #e8ece9; border-left: 6px solid #16a34a; background: #f0fdf4;
          break-inside: avoid; }}
  .card .c-time {{ flex: 0 0 84px; font-size: 20px; font-weight: 800; color: #14231b;
                  font-variant-numeric: tabular-nums; }}
  .card .c-end {{ display: block; font-size: 12px; font-weight: 600; color: #6b7a71; margin-top: 2px; }}
  .c-body {{ flex: 1; }}
  .c-kind {{ display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .04em;
            text-transform: uppercase; padding: 2px 10px; border-radius: 999px;
            background: #fff; box-shadow: inset 0 0 0 1px rgba(0,0,0,.05); }}
  .c-kind::before {{ content: ''; display: inline-block; width: 8px; height: 8px;
                    border-radius: 50%; background: currentColor; margin-right: 6px;
                    vertical-align: 1px; }}
  .c-place .pin {{ vertical-align: -2px; margin-right: 2px; }}
  .c-title {{ margin: 6px 0 0; font-size: 20px; font-weight: 700; color: #14231b; }}
  .c-place {{ margin: 5px 0 0; font-size: 14px; color: #3d4b43; font-weight: 600; }}
  .c-detail {{ margin: 4px 0 0; font-size: 13px; color: #6b7a71; }}

  .card.formation {{ border-left-color: #2563eb; background: #eff6ff; }}
  .card.formation .c-kind {{ color: #1e40af; }}
  .card.atelier {{ border-left-color: #d97706; background: #fffbeb; }}
  .card.atelier .c-kind {{ color: #92400e; }}
  .card.evenement {{ border-left-color: #16a34a; background: #f0fdf4; }}
  .card.evenement .c-kind {{ color: #166534; }}

  .empty {{ text-align: center; color: #9aa8a0; padding: 80px 0; font-size: 20px; line-height: 2; }}

  footer {{ padding: 16px 40px 26px; font-size: 11px; color: #9aa8a0; text-align: center; }}
  .print-btn {{ position: fixed; top: 18px; right: 18px; padding: 11px 20px; border: none;
               background: #5da020; color: #fff; border-radius: 10px; font-weight: 700;
               font-size: 14px; cursor: pointer; box-shadow: 0 4px 14px rgba(0,0,0,.2); }}

  @media print {{
    body {{ background: #fff; }}
    .poster {{ margin: 0; max-width: none; border-radius: 0; box-shadow: none; }}
    .print-btn {{ display: none; }}
    .card, .day {{ break-inside: avoid; }}
  }}
  @page {{ size: A4; margin: 12mm; }}
</style>
</head>
<body>
  <button class="print-btn" onclick="window.print()">Imprimer / PDF</button>
  <div class="poster">
    <div class="hero">
      {brand_html}
      <div class="eyebrow">Agenda du mois</div>
      <h1>{html.escape(month_label)}</h1>
      <div class="tagline">Événements &amp; formations ouverts à tous</div>
    </div>
    <div class="legend">
      <span><i class="lg-evenement"></i> Événement</span>
      <span><i class="lg-formation"></i> Formation</span>
      <span><i class="lg-atelier"></i> Atelier</span>
    </div>
    <div class="list">
      {body}
    </div>
    <footer>Maison de l'Économie · Rodez Agglomération — mis à jour le {generated}</footer>
  </div>
</body>
</html>"""


def _load_snapshot(year, month):
    """Load the persisted item snapshot for a month, or ``[]`` if none."""
    path = EXPORT_DIR / f'agenda-{year:04d}-{month:02d}.json'
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        logger.warning('Could not read export snapshot %s', path)
        return []


def _merge_items(existing, fresh):
    """Merge freshly-collected items into the existing snapshot.

    Existing entries are kept verbatim (an item that has since disappeared from
    the database stays as a historical trace); only genuinely new items are
    appended. The result is re-sorted by date then time.
    """
    seen = {it.get('key') for it in existing if it.get('key')}
    merged = list(existing)
    for it in fresh:
        if it.get('key') not in seen:
            merged.append(it)
            seen.add(it.get('key'))
    merged.sort(key=lambda i: (i.get('date', ''), i.get('time') or '99:99'))
    return merged


def generate_and_store(year, month):
    """Render and persist the sheet for ``year``/``month``; return its metadata.

    The stored sheet is an append-only archive: regenerating merges any new
    items with those already recorded, so a formation/event that later
    disappears from the database remains on the sheet as a trace.
    """
    ensure_upload_dirs()
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    items = _merge_items(_load_snapshot(year, month), collect(year, month))

    stem = f'agenda-{year:04d}-{month:02d}'
    (EXPORT_DIR / f'{stem}.json').write_text(
        json.dumps(items, ensure_ascii=False), encoding='utf-8')
    document = render_html(year, month, items)
    filename = f'{stem}.html'
    (EXPORT_DIR / filename).write_text(document, encoding='utf-8')
    logger.info('Generated monthly export %s (%d items)', filename, len(items))
    return {
        'year': year,
        'month': month,
        'label': f'{MONTHS_FR[month].capitalize()} {year}',
        'filename': filename,
        'url': f'/uploads/exports/{filename}',
        'count': len(items),
        'generated_at': datetime.now().isoformat(timespec='seconds'),
    }


def _meta_from_file(path: Path):
    stem = path.stem  # agenda-YYYY-MM
    try:
        _, ym = stem.split('agenda-', 1)
        year, month = (int(x) for x in ym.split('-'))
    except (ValueError, IndexError):
        return None
    return {
        'year': year,
        'month': month,
        'label': f'{MONTHS_FR[month].capitalize()} {year}',
        'filename': path.name,
        'url': f'/uploads/exports/{path.name}',
        'generated_at': datetime.fromtimestamp(
            path.stat().st_mtime).isoformat(timespec='seconds'),
    }


def list_exports():
    """Return metadata for every stored sheet, most recent month first."""
    if not EXPORT_DIR.exists():
        return []
    metas = [m for p in EXPORT_DIR.glob('agenda-*.html')
             if (m := _meta_from_file(p))]
    metas.sort(key=lambda m: (m['year'], m['month']), reverse=True)
    return metas


def generate_next_month_if_due(today=None):
    """On the 25th, generate next month's sheet. Returns metadata or ``None``."""
    today = today or datetime.now()
    if today.day != 25:
        return None
    year, month = next_month(today)
    return generate_and_store(year, month)
