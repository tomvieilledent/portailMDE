"""Lien d'une formation

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-21 18:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ajoute le lien (page de la formation, inscription, brochure…) aux formations."""
    op.add_column("trainings", sa.Column("link", sa.String(length=512), nullable=True))


def downgrade() -> None:
    """Retire le lien des formations."""
    op.drop_column("trainings", "link")
