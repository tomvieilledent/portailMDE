import uuid

import pytest

from backend.models.conversation_participant import ConversationParticipant


def test_model_requires_ids():
    with pytest.raises(TypeError):
        ConversationParticipant(conversation_id=123, user_id='u1')

    with pytest.raises(TypeError):
        ConversationParticipant(conversation_id='c1', user_id=456)

    with pytest.raises(ValueError):
        ConversationParticipant(conversation_id='   ', user_id='u1')

    with pytest.raises(ValueError):
        ConversationParticipant(conversation_id='c1', user_id='')


def test_facade_crud_flow(app_bundle):
    # Import inside the test so the facade binds to the isolated test DB that
    # app_bundle sets up (re-importing backend.* against a tmp DATABASE_URL).
    # Importing at module level would run against the real data.db instead.
    from backend.persistence.services.facades.conversation_participant_facade_sql import (
        ConversationParticipantFacade,
    )

    facade = ConversationParticipantFacade()

    conv = str(uuid.uuid4())
    u1 = str(uuid.uuid4())
    u2 = str(uuid.uuid4())

    # create two participants in same conversation
    p1 = facade.create(conversation_id=conv, user_id=u1)
    p2 = facade.create(conversation_id=conv, user_id=u2)

    assert p1['conversation_id'] == conv
    assert p1['user_id'] == u1
    assert p2['conversation_id'] == conv
    assert p2['user_id'] == u2

    # list_by_conversation should return both
    lst = facade.list_by_conversation(conv)
    ids = [p['user_id'] for p in lst]
    assert u1 in ids and u2 in ids

    # get by id
    got = facade.get(p1['id'])
    assert got['id'] == p1['id']

    # delete
    assert facade.delete(p1['id']) is True
    assert facade.get(p1['id']) is None

    # delete nonexistent
    assert facade.delete('nonexistent-id') is False
