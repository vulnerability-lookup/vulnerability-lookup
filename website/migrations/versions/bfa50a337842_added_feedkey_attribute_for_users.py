"""added feedkey attribute for users

Revision ID: bfa50a337842
Revises: d6d59905a683
Create Date: 2025-07-24 09:53:25.861123

"""

import secrets

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.
revision = "bfa50a337842"
down_revision = "d6d59905a683"
branch_labels = None
depends_on = None


def generate_token() -> str:
    return secrets.token_urlsafe(64)


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("feedkey", sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint(None, ["feedkey"])

    # Populate feedkey for existing users
    bind = op.get_bind()
    session = Session(bind=bind)

    User = sa.table(
        "user",
        sa.column("id", sa.Integer),
        sa.column("feedkey", sa.String),
    )

    # Generate and assign unique feedkeys
    users = session.execute(sa.select(User.c.id)).fetchall()
    for row in users:
        session.execute(
            User.update().where(User.c.id == row.id).values(feedkey=generate_token())
        )

    session.commit()


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_constraint(None, type_="unique")
        batch_op.drop_column("feedkey")
