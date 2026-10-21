import enum


class UserRole(enum.StrEnum):
    SUPER_ADMIN = "super_admin"
    STAFF = "staff"
    MEMBER = "member"


class CompanyKind(enum.StrEnum):
    COMPANY = "company"
    TRAINER = "trainer"
    PARTNER = "partner"


class TrainingKind(enum.StrEnum):
    FORMATION = "formation"
    ATELIER = "atelier"


class SessionStatus(enum.StrEnum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    DONE = "done"
    CANCELLED = "cancelled"


class ConversationKind(enum.StrEnum):
    DIRECT = "direct"
    GROUP = "group"


class InvitationStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
