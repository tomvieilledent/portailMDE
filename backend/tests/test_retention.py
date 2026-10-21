"""Tests de la purge de conservation des données personnelles."""

from datetime import UTC, datetime, timedelta

from app.models import Notification, User
from app.services import retention


def test_purge_old_notifications(session, make_user):
    """Les notifications au-delà de la durée de conservation sont supprimées."""
    user: User = make_user()
    old = Notification(
        recipient_id=user.id, content="vieille", created_at=datetime.now(UTC) - timedelta(days=400)
    )
    recent = Notification(recipient_id=user.id, content="récente")
    session.add_all([old, recent])
    session.commit()
    result = retention.purge_personal_data(session)
    assert result["notifications"] == 1
    assert [n.content for n in session.query(Notification).all()] == ["récente"]
