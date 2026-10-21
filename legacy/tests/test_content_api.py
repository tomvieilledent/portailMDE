"""API tests for editable site content (landing page)."""

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error


def test_landing_content_defaults_are_public(seeded_context):
    client = seeded_context['client']

    # Public read (no auth) returns the defaults reflecting the requested edits.
    res = client.get('/content/landing')
    assert res.status_code == 200
    content = res.get_json()['content']
    assert content['slogan'] == "De l'idée à la création"
    # "premières années" mention removed from the pépinière card.
    assert 'premières années' not in content['sections'][1]['description']
    assert content['sections'][1]['description'].startswith('Héberge les jeunes entreprises')
    # Hôtel d'entreprises highlight ("Location flexible") removed.
    assert content['sections'][2]['highlight'] == ''

    # Unknown content key is a 404.
    assert client.get('/content/unknown').status_code == 404


def test_landing_content_edit_requires_super_admin(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']        # super admin
    member_headers = seeded_context['member_headers']

    new_content = {
        'slogan': 'Innover ensemble',
        'subtitle': 'Un sous-titre personnalisé',
        'sections': [
            {'title': 'Incubateur', 'duration': '24 mois',
             'description': 'desc', 'highlight': 'hl'},
        ],
    }

    # A non-super-admin cannot edit.
    assert_error(client.put('/content/landing', headers=member_headers,
                            json={'content': new_content}),
                 403, ERROR_CODES['FORBIDDEN'])

    # A super admin can, and the change is persisted and served publicly.
    saved = client.put('/content/landing', headers=admin_headers,
                       json={'content': new_content})
    assert saved.status_code == 200
    assert saved.get_json()['content']['slogan'] == 'Innover ensemble'

    after = client.get('/content/landing').get_json()['content']
    assert after['slogan'] == 'Innover ensemble'
    assert after['sections'][0]['title'] == 'Incubateur'

    # A missing/invalid content body is rejected.
    assert_error(client.put('/content/landing', headers=admin_headers, json={}),
                 400, ERROR_CODES['BAD_REQUEST'])

    # Unknown key is a 404 even for a super admin.
    assert_error(client.put('/content/unknown', headers=admin_headers,
                            json={'content': new_content}),
                 404, ERROR_CODES['NOT_FOUND'])
