"""added new failed_otp_attempts user attribute

Revision ID: 27e392cc8997
Revises: bfa50a337842
Create Date: 2025-12-04 15:45:42.776437

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "27e392cc8997"
down_revision = "bfa50a337842"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add the column as nullable (required so the table can be altered)
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("failed_otp_attempts", sa.Integer(), nullable=True)
        )

    # 2. Set default value for existing rows
    op.execute('UPDATE "user" SET failed_otp_attempts = 0')

    # 3. Make the column non-nullable now that all rows have a value
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "failed_otp_attempts",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("failed_otp_attempts")
