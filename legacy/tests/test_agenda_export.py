"""Tests for event/session public visibility and the monthly agenda export."""

import pytest

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error


@pytest.fixture()
def export_dir(monkeypatch, tmp_path):
    """Redirect stored export sheets to a temp folder."""
    from backend.services import agenda_export
    target = tmp_path / 'exports'
    target.mkdir()
    monkeypatch.setattr(agenda_export, 'EXPORT_DIR', target)
    return target


def test_public_event_is_visible_to_everyone(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']

    client.post('/events', headers=admin_headers, json={
        'title': 'Réunion publique', 'date': '2030-03-10', 'is_public': True})
    client.post('/events', headers=admin_headers, json={
        'title': 'Réunion privée', 'date': '2030-03-11', 'is_public': False})

    resp = client.get('/events', headers=member_headers)
    titles = [e['title'] for e in resp.get_json()['events']]
    assert 'Réunion publique' in titles
    assert 'Réunion privée' not in titles


def test_export_forbidden_for_non_super_admin(seeded_context, export_dir):
    client = seeded_context['client']
    resp = client.get('/exports/monthly', headers=seeded_context['member_headers'])
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])
    resp = client.post('/exports/monthly', headers=seeded_context['member_headers'],
                       json={'year': 2030, 'month': 3})
    assert_error(resp, 403, ERROR_CODES['FORBIDDEN'])


def test_export_generates_sheet_with_only_public_items(seeded_context, export_dir):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    client.post('/events', headers=admin_headers, json={
        'title': 'Public A', 'date': '2030-03-05', 'time': '09:00', 'is_public': True})
    client.post('/events', headers=admin_headers, json={
        'title': 'Public B', 'date': '2030-03-20', 'is_public': True})
    client.post('/events', headers=admin_headers, json={
        'title': 'Privé', 'date': '2030-03-15', 'is_public': False})
    # Event outside the target month must be excluded.
    client.post('/events', headers=admin_headers, json={
        'title': 'Autre mois', 'date': '2030-04-01', 'is_public': True})

    gen = client.post('/exports/monthly', headers=admin_headers,
                      json={'year': 2030, 'month': 3})
    assert gen.status_code == 201
    export = gen.get_json()['export']
    assert export['count'] == 2
    assert export['month'] == 3 and export['year'] == 2030

    # The file exists and lists the public events but not the private one.
    sheet = (export_dir / export['filename']).read_text(encoding='utf-8')
    assert 'Public A' in sheet
    assert 'Public B' in sheet
    assert 'Privé' not in sheet
    assert 'Autre mois' not in sheet

    listing = client.get('/exports/monthly', headers=admin_headers)
    assert listing.status_code == 200
    filenames = [e['filename'] for e in listing.get_json()['exports']]
    assert export['filename'] in filenames


def test_export_defaults_to_next_month(seeded_context, export_dir):
    client = seeded_context['client']
    from backend.services import agenda_export
    year, month = agenda_export.next_month()

    gen = client.post('/exports/monthly', headers=seeded_context['admin_headers'],
                      json={})
    assert gen.status_code == 201
    export = gen.get_json()['export']
    assert (export['year'], export['month']) == (year, month)


def test_export_rejects_invalid_month(seeded_context, export_dir):
    client = seeded_context['client']
    resp = client.post('/exports/monthly', headers=seeded_context['admin_headers'],
                       json={'year': 2030, 'month': 13})
    assert_error(resp, 400, ERROR_CODES['BAD_REQUEST'])


def test_export_keeps_deleted_items_as_trace(seeded_context, export_dir):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    created = client.post('/events', headers=admin_headers, json={
        'title': 'Événement archivé', 'date': '2030-03-09', 'is_public': True})
    event_id = created.get_json()['event']['id']

    first = client.post('/exports/monthly', headers=admin_headers,
                        json={'year': 2030, 'month': 3})
    assert first.get_json()['export']['count'] == 1

    # The event disappears from the database…
    client.delete(f'/events/{event_id}', headers=admin_headers)

    # …but regenerating keeps it as a trace, and adds any new one.
    client.post('/events', headers=admin_headers, json={
        'title': 'Nouvel événement', 'date': '2030-03-18', 'is_public': True})
    regen = client.post('/exports/monthly', headers=admin_headers,
                        json={'year': 2030, 'month': 3})
    export = regen.get_json()['export']
    assert export['count'] == 2

    sheet = (export_dir / export['filename']).read_text(encoding='utf-8')
    assert 'Événement archivé' in sheet
    assert 'Nouvel événement' in sheet
