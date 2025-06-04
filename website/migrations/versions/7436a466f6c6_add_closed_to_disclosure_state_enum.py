"""Add 'closed' to disclosure_state_enum

Revision ID: 7436a466f6c6
Revises: e79218f0a656
Create Date: 2025-05-12 09:30:02.482733

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7436a466f6c6"
down_revision = "e79218f0a656"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE disclosure_state_enum ADD VALUE 'closed'")


def downgrade():
    # Downgrading enum types in PostgreSQL is non-trivial and not supported here.
    # Would require creating a new type without 'closed', migrating data, and renaming.
    pass
