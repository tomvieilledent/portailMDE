"""Changement de mot de passe obligatoire

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-21 12:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajoute le drapeau de mot de passe temporaire aux utilisateurs."""
    op.add_column(
        "users",
        sa.Column("must_change_password", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    """Retire le drapeau de mot de passe temporaire."""
    op.drop_column("users", "must_change_password")
