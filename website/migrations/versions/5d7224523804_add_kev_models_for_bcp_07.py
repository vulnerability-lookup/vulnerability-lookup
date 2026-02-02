"""Add KEV models for BCP-07

Revision ID: 5d7224523804
Revises: 27e392cc8997
Create Date: 2026-01-26 11:49:00.286633

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "5d7224523804"
down_revision = "27e392cc8997"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "kev_entry",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("vuln_id", sa.String(length=100), nullable=False),
        sa.Column("exploited", sa.Boolean(), nullable=False),
        sa.Column(
            "status_reason",
            sa.Enum(
                "confirmed",
                "suspected",
                "disputed",
                "historical",
                "unknown",
                name="kev_exploitation_status_enum",
            ),
            nullable=False,
        ),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "characteristics", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("timestamps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("vulnerability_lookup_origin", sa.UUID(), nullable=False),
        sa.Column(
            "creation_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("uuid"),
    )
    with op.batch_alter_table("kev_entry", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_kev_entry_creation_timestamp"),
            ["creation_timestamp"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_kev_entry_vuln_id"), ["vuln_id"], unique=False
        )

    op.create_table(
        "kev_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.UUID(), nullable=True),
        sa.Column(
            "evidence_type",
            sa.Enum(
                "incident_response",
                "telemetry",
                "honeypot",
                "sinkhole",
                "vendor_report",
                "research_report",
                "unknown",
                name="kev_evidence_type_enum",
            ),
            nullable=False,
        ),
        sa.Column(
            "signal",
            sa.Enum(
                "in_the_wild_attempts",
                "successful_exploitation",
                "confirmed_compromise",
                "mass_scanning",
                "weaponized_exploit_available",
                name="kev_evidence_signal_enum",
            ),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=500), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "gcve_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("kev_entry_uuid", sa.UUID(), nullable=False),
        sa.Column(
            "creation_timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["kev_entry_uuid"], ["kev_entry.uuid"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    with op.batch_alter_table("kev_evidence", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_kev_evidence_kev_entry_uuid"),
            ["kev_entry_uuid"],
            unique=False,
        )

    with op.batch_alter_table("organization", schema=None) as batch_op:
        batch_op.alter_column("gcve_pull", existing_type=sa.BOOLEAN(), nullable=True)

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "failed_otp_attempts", existing_type=sa.INTEGER(), nullable=True
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "failed_otp_attempts", existing_type=sa.INTEGER(), nullable=False
        )

    with op.batch_alter_table("organization", schema=None) as batch_op:
        batch_op.alter_column("gcve_pull", existing_type=sa.BOOLEAN(), nullable=False)

    with op.batch_alter_table("kev_evidence", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_kev_evidence_kev_entry_uuid"))

    op.drop_table("kev_evidence")
    with op.batch_alter_table("kev_entry", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_kev_entry_vuln_id"))
        batch_op.drop_index(batch_op.f("ix_kev_entry_creation_timestamp"))

    op.drop_table("kev_entry")
