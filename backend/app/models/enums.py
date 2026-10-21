"""Énumérations métier partagées par les modèles et les schémas."""

import enum


class UserRole(enum.StrEnum):
    """Rôle d'un utilisateur : super administrateur, personnel ou membre."""

    SUPER_ADMIN = "super_admin"
    STAFF = "staff"
    MEMBER = "member"


class CompanyKind(enum.StrEnum):
    """Type d'entreprise : entreprise, formateur ou partenaire."""

    COMPANY = "company"
    TRAINER = "trainer"
    PARTNER = "partner"


class TrainingKind(enum.StrEnum):
    """Type de formation : formation ou atelier."""

    FORMATION = "formation"
    ATELIER = "atelier"


class SessionStatus(enum.StrEnum):
    """Statut d'une session : à venir, en cours, terminée ou annulée."""

    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    DONE = "done"
    CANCELLED = "cancelled"


class ConversationKind(enum.StrEnum):
    """Type de conversation : directe ou de groupe."""

    DIRECT = "direct"
    GROUP = "group"


class InvitationStatus(enum.StrEnum):
    """Statut d'une invitation : en attente, acceptée ou refusée."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
