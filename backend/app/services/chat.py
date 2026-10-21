"""Logique métier de la messagerie : conversations directes/groupes, messages, non-lus."""

import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.models import Conversation, ConversationParticipant, Message, User
from app.models.enums import ConversationKind, UserRole
from app.schemas.chat import ConversationRead, MessageRead, UserBrief
from app.services import notifications, storage


def _active_users(session: Session, ids: list[uuid.UUID]) -> list[User]:
    """Retourne les utilisateurs actifs demandés, ou lève une erreur si l'un d'eux est introuvable."""
    users = session.scalars(
        select(User).where(User.id.in_(ids), User.deleted_at.is_(None), User.is_active.is_(True))
    ).all()
    if len(users) != len(set(ids)):
        raise NotFoundError("Un ou plusieurs utilisateurs sont introuvables")
    return list(users)


def get_conversation(session: Session, conversation_id: uuid.UUID, actor: User) -> Conversation:
    """Retourne la conversation si ``actor`` y participe (sinon 404, pour ne rien révéler)."""
    conversation = session.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.participants))
    )
    if not conversation or not any(p.user_id == actor.id for p in conversation.participants):
        raise NotFoundError("Conversation introuvable")
    return conversation


def participant_ids(conversation: Conversation) -> list[uuid.UUID]:
    """Retourne les identifiants des participants d'une conversation."""
    return [p.user_id for p in conversation.participants]


def create_direct(session: Session, actor: User, other_id: uuid.UUID) -> Conversation:
    """Crée (ou retrouve) la conversation directe entre l'utilisateur et un autre."""
    if other_id == actor.id:
        raise AppError("Impossible de discuter avec soi-même")
    _active_users(session, [other_id])
    existing = session.scalar(
        select(Conversation)
        .join(ConversationParticipant)
        .where(Conversation.kind == ConversationKind.DIRECT)
        .group_by(Conversation.id)
        .having(
            func.count() == 2,
            func.count().filter(ConversationParticipant.user_id.in_([actor.id, other_id])) == 2,
        )
    )
    if existing:
        return existing
    conversation = Conversation(kind=ConversationKind.DIRECT, creator_id=actor.id)
    conversation.participants = [
        ConversationParticipant(user_id=actor.id),
        ConversationParticipant(user_id=other_id),
    ]
    session.add(conversation)
    session.commit()
    return conversation


def create_group(
    session: Session, actor: User, title: str, user_ids: list[uuid.UUID]
) -> Conversation:
    """Crée une conversation de groupe et notifie les membres ajoutés."""
    members = set(user_ids) | {actor.id}
    _active_users(session, list(members))
    conversation = Conversation(kind=ConversationKind.GROUP, title=title, creator_id=actor.id)
    conversation.participants = [ConversationParticipant(user_id=uid) for uid in members]
    session.add(conversation)
    session.commit()
    _notify_added(session, conversation, actor, list(members - {actor.id}))
    return conversation


def _ensure_group_owner(conversation: Conversation, actor: User) -> None:
    """Vérifie que la conversation est un groupe et que l'utilisateur en est le créateur."""
    if conversation.kind != ConversationKind.GROUP:
        raise AppError("Cette opération ne concerne que les groupes")
    if conversation.creator_id != actor.id and actor.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Seul le créateur du groupe peut faire cela")


def _notify_added(session: Session, conversation: Conversation, actor: User, user_ids) -> None:
    """Notifie les utilisateurs ajoutés à un groupe."""
    notifications.notify(
        session,
        user_ids,
        f"{notifications.display_name(actor)} vous a ajouté au groupe « {conversation.title} »",
        kind="conversation",
        data={"conversation_id": str(conversation.id)},
    )


def rename_group(session: Session, conversation: Conversation, actor: User, title: str):
    """Renomme un groupe (réservé à son créateur)."""
    _ensure_group_owner(conversation, actor)
    conversation.title = title
    session.commit()
    return conversation


def add_participants(
    session: Session, conversation: Conversation, actor: User, user_ids: list[uuid.UUID]
):
    """Ajoute des participants à un groupe (réservé à son créateur) et les notifie."""
    _ensure_group_owner(conversation, actor)
    current = set(participant_ids(conversation))
    new_ids = [uid for uid in set(user_ids) if uid not in current]
    _active_users(session, new_ids)
    for uid in new_ids:
        conversation.participants.append(ConversationParticipant(user_id=uid))
    session.commit()
    _notify_added(session, conversation, actor, new_ids)
    return conversation


def remove_participant(
    session: Session, conversation: Conversation, actor: User, user_id: uuid.UUID
):
    """Le créateur retire n'importe qui ; chacun peut quitter le groupe."""
    if conversation.kind != ConversationKind.GROUP:
        raise AppError("Cette opération ne concerne que les groupes")
    if user_id != actor.id:
        _ensure_group_owner(conversation, actor)
    participant = next((p for p in conversation.participants if p.user_id == user_id), None)
    if not participant:
        raise NotFoundError("Participant introuvable")
    conversation.participants.remove(participant)
    session.commit()


def mark_read(session: Session, conversation: Conversation, actor: User) -> None:
    """Marque la conversation comme lue pour l'utilisateur."""
    participant = next(p for p in conversation.participants if p.user_id == actor.id)
    participant.last_read_at = datetime.now(UTC)
    session.commit()


def _unread_count(session: Session, conversation: Conversation, actor: User) -> int:
    """Compte les messages non lus de l'utilisateur dans la conversation."""
    participant = next(p for p in conversation.participants if p.user_id == actor.id)
    since = participant.last_read_at or participant.joined_at
    return (
        session.scalar(
            select(func.count()).where(
                Message.conversation_id == conversation.id,
                Message.deleted_at.is_(None),
                Message.created_at > since,
                Message.author_id != actor.id,
            )
        )
        or 0
    )


def _last_message(session: Session, conversation: Conversation) -> Message | None:
    """Retourne le dernier message non supprimé de la conversation."""
    return session.scalar(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
        .limit(1)
    )


def _build_read(
    conversation: Conversation,
    users: list[User],
    last: Message | None,
    unread: int,
) -> ConversationRead:
    """Assemble la représentation de lecture d'une conversation."""
    return ConversationRead(
        id=conversation.id,
        kind=conversation.kind,
        title=conversation.title,
        creator_id=conversation.creator_id,
        participants=[UserBrief.model_validate(u) for u in users],
        last_message=MessageRead.model_validate(last) if last else None,
        unread_count=unread,
        created_at=conversation.created_at,
    )


def to_read(session: Session, conversation: Conversation, actor: User) -> ConversationRead:
    """Construit la représentation de lecture d'une conversation pour l'utilisateur."""
    users = session.scalars(select(User).where(User.id.in_(participant_ids(conversation)))).all()
    last = _last_message(session, conversation)
    return _build_read(conversation, list(users), last, _unread_count(session, conversation, actor))


MAX_CONVERSATIONS = 200


def list_conversations(session: Session, actor: User) -> list[ConversationRead]:
    """Liste les conversations de l'utilisateur (les plus récentes d'abord, 200 au maximum).

    Utilisateurs, derniers messages et non-lus sont chargés en une requête chacun.
    """
    last_activity = (
        select(Message.conversation_id, func.max(Message.created_at).label("last_at"))
        .where(Message.deleted_at.is_(None))
        .group_by(Message.conversation_id)
        .subquery()
    )
    conversations = list(
        session.scalars(
            select(Conversation)
            .join(ConversationParticipant)
            .outerjoin(last_activity, last_activity.c.conversation_id == Conversation.id)
            .where(ConversationParticipant.user_id == actor.id)
            .order_by(func.coalesce(last_activity.c.last_at, Conversation.created_at).desc())
            .limit(MAX_CONVERSATIONS)
            .options(selectinload(Conversation.participants))
        ).all()
    )
    if not conversations:
        return []
    ids = [c.id for c in conversations]

    user_ids = {uid for c in conversations for uid in participant_ids(c)}
    users = {u.id: u for u in session.scalars(select(User).where(User.id.in_(user_ids))).all()}

    ranked = (
        select(
            Message.id,
            func.row_number()
            .over(partition_by=Message.conversation_id, order_by=Message.created_at.desc())
            .label("rn"),
        )
        .where(Message.conversation_id.in_(ids), Message.deleted_at.is_(None))
        .subquery()
    )
    last_messages = {
        m.conversation_id: m
        for m in session.scalars(
            select(Message).join(ranked, Message.id == ranked.c.id).where(ranked.c.rn == 1)
        ).all()
    }

    unread_rows = session.execute(
        select(Message.conversation_id, func.count())
        .join(
            ConversationParticipant,
            (ConversationParticipant.conversation_id == Message.conversation_id)
            & (ConversationParticipant.user_id == actor.id),
        )
        .where(
            Message.conversation_id.in_(ids),
            Message.deleted_at.is_(None),
            Message.author_id != actor.id,
            Message.created_at
            > func.coalesce(
                ConversationParticipant.last_read_at, ConversationParticipant.joined_at
            ),
        )
        .group_by(Message.conversation_id)
    ).all()
    unread = {cid: count for cid, count in unread_rows}

    reads = [
        _build_read(
            c,
            [users[uid] for uid in participant_ids(c) if uid in users],
            last_messages.get(c.id),
            unread.get(c.id, 0),
        )
        for c in conversations
    ]
    return reads


def list_messages(
    session: Session,
    conversation: Conversation,
    *,
    limit: int,
    before: datetime | None = None,
) -> list[Message]:
    """Messages du plus récent au plus ancien, paginés par curseur ``before``."""
    query = select(Message).where(
        Message.conversation_id == conversation.id, Message.deleted_at.is_(None)
    )
    if before:
        query = query.where(Message.created_at < before)
    return list(session.scalars(query.order_by(Message.created_at.desc()).limit(limit)).all())


def send_message(
    session: Session,
    conversation: Conversation,
    actor: User,
    content: str,
    file: UploadFile | None = None,
) -> Message:
    """Enregistre un message (texte et/ou pièce jointe) et le marque lu pour son auteur."""
    content = (content or "").strip()
    if not content and file is None:
        raise AppError("Le message est vide")
    if len(content) > 5000:
        raise AppError("Message trop long (5000 caractères maximum)")
    file_path = file_name = None
    if file is not None:
        file_path, file_name = storage.save_document(file, "messages")
    message = Message(
        conversation_id=conversation.id,
        author_id=actor.id,
        content=content,
        file_path=file_path,
        file_name=file_name,
    )
    session.add(message)
    # L'auteur a forcément lu ce qu'il vient d'écrire.
    next(p for p in conversation.participants if p.user_id == actor.id).last_read_at = datetime.now(
        UTC
    )
    session.commit()
    session.refresh(message)
    return message


def get_message(session: Session, message_id: uuid.UUID, actor: User) -> Message:
    """Retourne un message si l'utilisateur participe à sa conversation."""
    message = session.get(Message, message_id)
    if not message or message.deleted_at is not None:
        raise NotFoundError("Message introuvable")
    get_conversation(session, message.conversation_id, actor)
    return message


def delete_message(session: Session, message_id: uuid.UUID, actor: User) -> Message:
    """Supprime logiquement un message (son auteur ou un super administrateur)."""
    message = get_message(session, message_id, actor)
    if message.author_id != actor.id and actor.role != UserRole.SUPER_ADMIN:
        raise ForbiddenError("Vous ne pouvez supprimer que vos messages")
    message.deleted_at = datetime.now(UTC)
    session.commit()
    return message
