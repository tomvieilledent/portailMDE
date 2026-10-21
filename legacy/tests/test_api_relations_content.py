import pytest

from backend.api.errors import ERROR_CODES
from tests.helpers import assert_error, make_text


def test_conversation_and_message_flow(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_id = seeded_context['member_user']['id']

    create_conversation = client.post('/conversations', headers=admin_headers, json={
        'participant_ids': [seeded_context['admin_user']['id'], member_id],
    })
    assert create_conversation.status_code == 201
    conversation = create_conversation.get_json()['conversation']
    conversation_id = conversation['id']
    assert member_id in conversation['participant_ids']

    list_conversations = client.get('/conversations', headers=admin_headers)
    assert list_conversations.status_code == 200
    assert len(list_conversations.get_json()['conversations']) >= 1

    get_conversation = client.get(
        f'/conversations/{conversation_id}', headers=admin_headers)
    assert get_conversation.status_code == 200

    add_participant = client.patch(f'/conversations/{conversation_id}', headers=admin_headers, json={
        'participant_id': 'new-participant-id',
        'action': 'add',
    })
    assert add_participant.status_code == 200
    assert 'new-participant-id' in add_participant.get_json()[
        'conversation']['participant_ids']

    remove_participant = client.patch(f'/conversations/{conversation_id}', headers=admin_headers, json={
        'participant_id': 'new-participant-id',
        'action': 'remove',
    })
    assert remove_participant.status_code == 200
    assert 'new-participant-id' not in remove_participant.get_json()[
        'conversation']['participant_ids']

    create_message = client.post(f'/conversations/{conversation_id}/messages', headers=admin_headers, json={
        'content': 'Hello team',
    })
    assert create_message.status_code == 201
    message = create_message.get_json()['message']
    message_id = message['id']
    assert message['content'] == 'Hello team'

    list_conversation_messages = client.get(
        f'/conversations/{conversation_id}/messages', headers=admin_headers)
    assert list_conversation_messages.status_code == 200
    assert len(list_conversation_messages.get_json()['messages']) >= 1

    list_messages = client.get(
        '/messages', headers=admin_headers, query_string={'conversation_id': conversation_id})
    assert list_messages.status_code == 200
    assert len(list_messages.get_json()['messages']) >= 1

    list_by_author = client.get('/messages', headers=admin_headers,
                                query_string={'author_id': seeded_context['admin_user']['id']})
    assert list_by_author.status_code == 200
    assert len(list_by_author.get_json()['messages']) >= 1

    delete_message = client.delete(
        f'/messages/{message_id}', headers=admin_headers)
    assert delete_message.status_code == 200
    assert delete_message.get_json() == {'msg': 'message deleted'}

    missing_message = client.delete(
        f'/messages/{message_id}', headers=admin_headers)
    assert_error(missing_message, 404, ERROR_CODES['NOT_FOUND'])

    delete_conversation = client.delete(
        f'/conversations/{conversation_id}', headers=admin_headers)
    assert delete_conversation.status_code == 200
    assert delete_conversation.get_json(
    ) == {'msg': 'conversation deactivated'}


def test_group_conversation_title_and_rename(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_id = seeded_context['member_user']['id']

    # Create a named group chat.
    created = client.post('/conversations', headers=admin_headers, json={
        'title': '  Équipe Projet  ',
        'participant_ids': [member_id],
    })
    assert created.status_code == 201
    conversation = created.get_json()['conversation']
    assert conversation['title'] == 'Équipe Projet'  # trimmed
    conversation_id = conversation['id']

    # The list endpoint exposes the title plus enriched fields.
    listed = client.get('/conversations', headers=admin_headers).get_json()['conversations']
    mine = next(c for c in listed if c['id'] == conversation_id)
    assert mine['title'] == 'Équipe Projet'
    assert 'unread' in mine and 'last_message' in mine

    # Rename via PATCH.
    renamed = client.patch(f'/conversations/{conversation_id}', headers=admin_headers,
                           json={'title': 'Comité de pilotage'})
    assert renamed.status_code == 200
    assert renamed.get_json()['conversation']['title'] == 'Comité de pilotage'

    # Clearing the title (empty string) is allowed.
    cleared = client.patch(f'/conversations/{conversation_id}', headers=admin_headers,
                           json={'title': ''})
    assert cleared.status_code == 200
    assert cleared.get_json()['conversation']['title'] is None

    # A non-string title is rejected.
    bad = client.patch(f'/conversations/{conversation_id}', headers=admin_headers,
                       json={'title': 123})
    assert_error(bad, 400, ERROR_CODES['VALIDATION_ERROR'])


def test_group_management_restricted_to_creator(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']        # creator
    member_headers = seeded_context['member_headers']      # invited guest
    admin_id = seeded_context['admin_user']['id']
    member_id = seeded_context['member_user']['id']
    company_admin_id = seeded_context['company_admin_user']['id']

    # Admin creates the group and is recorded as its creator.
    created = client.post('/conversations', headers=admin_headers, json={
        'title': 'Projet',
        'participant_ids': [member_id],
    })
    conversation = created.get_json()['conversation']
    conversation_id = conversation['id']
    assert conversation['creator_id'] == admin_id

    # A guest cannot rename the group.
    assert_error(client.patch(f'/conversations/{conversation_id}', headers=member_headers,
                              json={'title': 'Pirate'}),
                 403, ERROR_CODES['FORBIDDEN'])

    # A guest cannot add a member.
    assert_error(client.patch(f'/conversations/{conversation_id}', headers=member_headers,
                              json={'participant_id': company_admin_id, 'action': 'add'}),
                 403, ERROR_CODES['FORBIDDEN'])

    # A guest cannot remove another member.
    assert_error(client.patch(f'/conversations/{conversation_id}', headers=member_headers,
                              json={'participant_id': admin_id, 'action': 'remove'}),
                 403, ERROR_CODES['FORBIDDEN'])

    # But a guest CAN remove themselves (leave the group).
    left = client.patch(f'/conversations/{conversation_id}', headers=member_headers,
                        json={'participant_id': member_id, 'action': 'remove'})
    assert left.status_code == 200
    assert member_id not in left.get_json()['conversation']['participant_ids']

    # The creator retains full control (re-add, rename).
    readded = client.patch(f'/conversations/{conversation_id}', headers=admin_headers,
                           json={'participant_id': member_id, 'action': 'add'})
    assert readded.status_code == 200
    assert member_id in readded.get_json()['conversation']['participant_ids']
    renamed = client.patch(f'/conversations/{conversation_id}', headers=admin_headers,
                           json={'title': 'Comité'})
    assert renamed.get_json()['conversation']['title'] == 'Comité'


def test_conversation_rest_enforces_membership(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']
    # outsider = company admin, deliberately NOT a participant
    outsider_headers = seeded_context['company_admin_headers']
    admin_id = seeded_context['admin_user']['id']
    member_id = seeded_context['member_user']['id']

    created = client.post('/conversations', headers=admin_headers, json={
        'participant_ids': [admin_id, member_id],
    })
    assert created.status_code == 201
    conversation_id = created.get_json()['conversation']['id']

    # A member posts a message in the conversation.
    posted = client.post(f'/conversations/{conversation_id}/messages',
                         headers=member_headers, json={'content': 'private'})
    assert posted.status_code == 201
    message_id = posted.get_json()['message']['id']

    # The outsider is masked behind 404 on every conversation route.
    assert_error(client.get(f'/conversations/{conversation_id}',
                            headers=outsider_headers), 404, ERROR_CODES['NOT_FOUND'])
    assert_error(client.get(f'/conversations/{conversation_id}/messages',
                            headers=outsider_headers), 404, ERROR_CODES['NOT_FOUND'])
    assert_error(client.post(f'/conversations/{conversation_id}/messages',
                             headers=outsider_headers, json={'content': 'intrusion'}),
                 404, ERROR_CODES['NOT_FOUND'])
    assert_error(client.patch(f'/conversations/{conversation_id}', headers=outsider_headers,
                              json={'participant_id': 'x', 'action': 'add'}),
                 404, ERROR_CODES['NOT_FOUND'])
    assert_error(client.delete(f'/conversations/{conversation_id}',
                               headers=outsider_headers), 404, ERROR_CODES['NOT_FOUND'])
    assert_error(client.get('/messages', headers=outsider_headers,
                            query_string={'conversation_id': conversation_id}),
                 404, ERROR_CODES['NOT_FOUND'])

    # The conversation never appears in the outsider's own listing.
    outsider_list = client.get('/conversations', headers=outsider_headers)
    assert outsider_list.status_code == 200
    assert all(c['id'] != conversation_id
               for c in outsider_list.get_json()['conversations'])

    # Reading another user's messages by author_id is forbidden.
    assert_error(client.get('/messages', headers=outsider_headers,
                            query_string={'author_id': member_id}),
                 403, ERROR_CODES['FORBIDDEN'])

    # Only the author may delete their message.
    assert_error(client.delete(f'/messages/{message_id}', headers=outsider_headers),
                 404, ERROR_CODES['NOT_FOUND'])
    assert client.delete(f'/messages/{message_id}',
                         headers=member_headers).status_code == 200


def test_conversation_read_and_unread_flow(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']
    outsider_headers = seeded_context['company_admin_headers']
    admin_id = seeded_context['admin_user']['id']
    member_id = seeded_context['member_user']['id']

    conversation_id = client.post('/conversations', headers=admin_headers, json={
        'participant_ids': [admin_id, member_id],
    }).get_json()['conversation']['id']

    # Member sends two messages; admin authors none here.
    for _ in range(2):
        posted = client.post(f'/conversations/{conversation_id}/messages',
                             headers=member_headers, json={'content': 'hi'})
        assert posted.status_code == 201
        assert posted.get_json()['message']['is_read'] is False

    # Admin has 2 unread; the author (member) has 0. These are conversation
    # messages, so the direct-message ``by_sender`` breakdown stays empty.
    assert client.get('/messages/unread', headers=admin_headers).get_json() == {
        'unread': 2, 'conversations': 2, 'direct': 0, 'by_sender': {}}
    assert client.get('/messages/unread', headers=member_headers).get_json()[
        'unread'] == 0
    # An outsider sees nothing.
    assert client.get('/messages/unread', headers=outsider_headers).get_json()[
        'unread'] == 0

    # Outsider cannot mark the conversation read.
    assert_error(client.post(f'/conversations/{conversation_id}/read',
                             headers=outsider_headers), 404, ERROR_CODES['NOT_FOUND'])

    # Admin marks the whole conversation read.
    mark = client.post(f'/conversations/{conversation_id}/read', headers=admin_headers)
    assert mark.status_code == 200
    assert mark.get_json() == {'updated': 2}
    assert client.get('/messages/unread', headers=admin_headers).get_json()[
        'unread'] == 0
    # Idempotent: nothing left to mark.
    assert client.post(f'/conversations/{conversation_id}/read',
                       headers=admin_headers).get_json() == {'updated': 0}

    # A fresh message is unread again, and can be marked read one by one.
    new_id = client.post(f'/conversations/{conversation_id}/messages',
                         headers=member_headers, json={'content': 'again'}
                         ).get_json()['message']['id']
    assert client.get('/messages/unread', headers=admin_headers).get_json()[
        'unread'] == 1
    read_one = client.post(f'/messages/{new_id}/read', headers=admin_headers)
    assert read_one.status_code == 200
    assert read_one.get_json()['message']['is_read'] is True
    assert client.get('/messages/unread', headers=admin_headers).get_json()[
        'unread'] == 0
    # Outsider may not mark an individual message in a conversation they're not in.
    assert_error(client.post(f'/messages/{new_id}/read', headers=outsider_headers),
                 404, ERROR_CODES['NOT_FOUND'])


def test_message_soft_delete_and_presence(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = seeded_context['member_headers']
    admin_id = seeded_context['admin_user']['id']
    member_id = seeded_context['member_user']['id']

    conversation_id = client.post('/conversations', headers=admin_headers, json={
        'participant_ids': [admin_id, member_id],
    }).get_json()['conversation']['id']

    message_id = client.post(f'/conversations/{conversation_id}/messages',
                             headers=member_headers, json={'content': 'oops'}
                             ).get_json()['message']['id']

    # Visible and counted before deletion.
    assert len(client.get(f'/conversations/{conversation_id}/messages',
                          headers=admin_headers).get_json()['messages']) == 1
    assert client.get('/messages/unread', headers=admin_headers).get_json()[
        'unread'] == 1

    # Only the author can delete; here the author (member) soft-deletes it.
    assert_error(client.delete(f'/messages/{message_id}', headers=admin_headers),
                 404, ERROR_CODES['NOT_FOUND'])
    assert client.delete(f'/messages/{message_id}',
                         headers=member_headers).status_code == 200

    # Gone from listings and unread counts; a second delete 404s.
    assert client.get(f'/conversations/{conversation_id}/messages',
                      headers=admin_headers).get_json()['messages'] == []
    assert client.get('/messages/unread', headers=admin_headers).get_json()[
        'unread'] == 0
    assert_error(client.delete(f'/messages/{message_id}', headers=member_headers),
                 404, ERROR_CODES['NOT_FOUND'])

    # No sockets connected in this test → nobody online.
    presence = client.get('/presence', headers=admin_headers)
    assert presence.status_code == 200
    assert presence.get_json() == {'online': []}


def test_notifications_flow(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_id = seeded_context['member_user']['id']

    create_notification = client.post('/notifications', headers=admin_headers, json={
        'recipient_id': member_id,
        'content': 'You have a new assignment',
    })
    assert create_notification.status_code == 201
    notification = create_notification.get_json()['notification']
    notification_id = notification['id']
    assert notification['recipient_id'] == member_id
    assert notification['is_read'] is False

    list_notifications = client.get(
        '/notifications', headers=admin_headers, query_string={'recipient_id': member_id})
    assert list_notifications.status_code == 200
    assert len(list_notifications.get_json()['notifications']) >= 1

    filtered_notifications = client.get(
        '/notifications', headers=admin_headers, query_string={'recipient_id': member_id, 'is_read': 'false'})
    assert filtered_notifications.status_code == 200
    assert len(filtered_notifications.get_json()['notifications']) >= 1

    mark_read = client.patch(
        f'/notifications/{notification_id}', headers=admin_headers, json={'is_read': True})
    assert mark_read.status_code == 200
    assert mark_read.get_json()['notification']['is_read'] is True

    delete_notification = client.delete(
        f'/notifications/{notification_id}', headers=admin_headers)
    assert delete_notification.status_code == 200
    assert delete_notification.get_json() == {'msg': 'notification deleted'}

    missing_notification = client.delete(
        f'/notifications/{notification_id}', headers=admin_headers)
    assert_error(missing_notification, 404, ERROR_CODES['NOT_FOUND'])


def test_news_flow_and_sync(seeded_context, monkeypatch):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    public_list = client.get('/news')
    assert public_list.status_code == 200
    assert 'items' in public_list.get_json()

    missing_title = client.post('/news', headers=admin_headers, json={})
    assert_error(missing_title, 400, ERROR_CODES['BAD_REQUEST'])

    create_news = client.post('/news', headers=admin_headers, json={
        'title': 'Release note',
        'source': 'Internal',
        'summary': 'Backend is ready',
        'url': 'https://example.com/news/release-note',
    })
    assert create_news.status_code == 201
    news_item = create_news.get_json()['news_item']
    news_id = news_item['id']
    assert news_item['title'] == 'Release note'

    get_news = client.get(f'/news/{news_id}')
    assert get_news.status_code == 200
    assert get_news.get_json()['news_item']['id'] == news_id

    # Sync is implemented but pulls external RSS via the optional `feedparser`
    # dependency. Inject a stub module so the endpoint contract is tested
    # deterministically, without network access or that dependency.
    import sys
    import types
    stub = types.ModuleType('backend.services.news_sync')
    stub.sync_all = lambda: 3  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, 'backend.services.news_sync', stub)
    sync_news = client.post('/news/sync', headers=admin_headers)
    assert sync_news.status_code == 200
    assert sync_news.get_json() == {'synced': 3}

    delete_news = client.delete(f'/news/{news_id}', headers=admin_headers)
    assert delete_news.status_code == 200
    assert delete_news.get_json() == {'msg': 'news item deleted'}


def test_formation_user_flow(seeded_context):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']
    member_headers = {'Authorization': f"Bearer {seeded_context['member_login']['access_token']}"}
    member_id = seeded_context['member_user']['id']

    training = client.post('/trainings', headers=admin_headers, json={
        'title': 'Python Advanced',
    }).get_json()['training']
    training_id = training['id']

    # express interest (no session scheduled yet)
    interest = client.post(f'/trainings/{training_id}/interest', headers=member_headers)
    assert interest.status_code == 201
    assert interest.get_json()['interest']['type'] == 'interested'

    # admin can see interested users
    interested = client.get(f'/trainings/{training_id}/interested', headers=admin_headers)
    assert interested.status_code == 200
    assert len(interested.get_json()['interested']) >= 1

    # admin creates a session
    session_resp = client.post(f'/trainings/{training_id}/sessions', headers=admin_headers, json={
        'start_date': '2027-01-10T09:00:00',
        'end_date': '2027-01-12T17:00:00',
        'max_participants': 10,
        'location': 'Paris',
    })
    assert session_resp.status_code == 201
    session_id = session_resp.get_json()['session']['id']

    # admin invites the member (programmed sessions are invitation-gated)
    client.post('/invitations', headers=admin_headers, json={
        'target_type': 'session', 'target_id': session_id,
        'invitee_ids': [member_id],
    })

    # member enrolls — interest is auto-upgraded to enrolled
    enroll = client.post(f'/training-sessions/{session_id}/enroll', headers=member_headers)
    assert enroll.status_code == 201
    enrollment = enroll.get_json()['enrollment']
    assert enrollment['type'] == 'enrolled'
    assert enrollment['session_id'] == session_id
    relation_id = enrollment['id']

    # user sees their trainings
    user_trainings = client.get(f'/users/{member_id}/trainings', headers=admin_headers)
    assert user_trainings.status_code == 200
    assert len(user_trainings.get_json()['enrollments']) >= 1

    current_user_trainings = client.get('/me/trainings', headers=member_headers)
    assert current_user_trainings.status_code == 200
    assert len(current_user_trainings.get_json()['enrollments']) >= 1

    # admin marks session as completed → enrollment auto-completed
    complete = client.patch(f'/training-sessions/{session_id}', headers=admin_headers, json={
        'status': 'completed',
    })
    assert complete.status_code == 200

    completions = client.get('/trainings/completions', headers=admin_headers)
    assert completions.status_code == 200
    assert len(completions.get_json()['completions']) >= 1

    # admin revokes completion
    revoke = client.patch(f'/formation-users/{relation_id}', headers=admin_headers)
    assert revoke.status_code == 200
    assert revoke.get_json()['formation_user']['type'] == 'enrolled'

    # admin deletes the relation
    delete_relation = client.delete(f'/formation-users/{relation_id}', headers=admin_headers)
    assert delete_relation.status_code == 200
    assert delete_relation.get_json() == {'msg': 'enrollment deleted'}


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({}, 404, ERROR_CODES['NOT_FOUND']),
        ({'participant_id': ''}, 404, ERROR_CODES['NOT_FOUND']),
        ({'participant_id': 'x', 'action': 'invalid'},
         404, ERROR_CODES['NOT_FOUND']),
    ],
)
def test_conversation_patch_invalid_cases(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    # create a conversation to operate on
    conv = client.post('/conversations', headers=admin_headers,
                       json={}).get_json()['conversation']

    response = client.patch(
        f"/conversations/{conv['id']}", headers=admin_headers, json=payload)
    assert_error(response, status, code)


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({}, 400, ERROR_CODES['VALIDATION_ERROR']),
        ({'content': ''}, 400, ERROR_CODES['VALIDATION_ERROR']),
    ],
)
def test_conversation_messages_post_invalid(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    conv = client.post('/conversations', headers=admin_headers,
                       json={}).get_json()['conversation']
    response = client.post(
        f"/conversations/{conv['id']}/messages", headers=admin_headers, json=payload)
    assert_error(response, status, code)


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'recipient_id': '', 'content': 'Hi'},
         400, ERROR_CODES['BAD_REQUEST']),
        ({'recipient_id': 'some-id', 'content': ''},
         400, ERROR_CODES['BAD_REQUEST']),
    ],
)
def test_notifications_post_field_validation(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    response = client.post(
        '/notifications', headers=admin_headers, json=payload)
    assert_error(response, status, code)


@pytest.mark.parametrize(
    'payload, status, code',
    [
        ({}, 400, ERROR_CODES['BAD_REQUEST']),
        ({'title': ''}, 400, ERROR_CODES['BAD_REQUEST']),
    ],
)
def test_news_post_field_validation(seeded_context, payload, status, code):
    client = seeded_context['client']
    admin_headers = seeded_context['admin_headers']

    response = client.post('/news', headers=admin_headers, json=payload)
    assert_error(response, status, code)


def test_training_interest_missing_training(seeded_context):
    client = seeded_context['client']
    member_headers = {'Authorization': f"Bearer {seeded_context['member_login']['access_token']}"}

    response = client.post('/trainings/nonexistent-id/interest', headers=member_headers)
    assert_error(response, 404, ERROR_CODES['NOT_FOUND'])
