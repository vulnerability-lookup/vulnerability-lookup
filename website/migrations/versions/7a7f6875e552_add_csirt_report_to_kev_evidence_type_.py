"""add_csirt_report_to_kev_evidence_type_enum

Revision ID: 7a7f6875e552
Revises: 20ab409b37e4
Create Date: 2026-01-29 14:19:52.654560

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a7f6875e552"
down_revision = "20ab409b37e4"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'csirt_report' to kev_evidence_type_enum
    # PostgreSQL allows adding enum values, but they must be added outside a transaction block
    # Using op.execute with proper enum addition
    op.execute(
        """
        ALTER TYPE kev_evidence_type_enum ADD VALUE IF NOT EXISTS 'csirt_report' AFTER 'vendor_report'
    """
    )


def downgrade():
    # Note: PostgreSQL does not support removing enum values directly
    # To truly remove it, you would need to:
    # 1. Create a new enum type without 'csirt_report'
    # 2. Alter the column to use the new type
    # 3. Drop the old enum type
    # For simplicity, we'll leave the enum value in place on downgrade
    # as it won't cause issues if not used
    pass
