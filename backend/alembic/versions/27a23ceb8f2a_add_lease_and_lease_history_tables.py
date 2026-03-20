"""add lease and lease_history tables

Revision ID: 27a23ceb8f2a
Revises: ddca2296df99
Create Date: 2026-03-20 10:01:18.707358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27a23ceb8f2a'
down_revision: Union[str, Sequence[str], None] = 'ddca2296df99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "t_lease",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lease_number", sa.String(20), unique=True, nullable=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("m_property.id"), nullable=False, index=True),
        sa.Column("parent_case_id", sa.Integer, sa.ForeignKey("t_lease.id"), nullable=True),
        sa.Column("renewal_seq", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_latest_case", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("property_sub_type", sa.String(20), nullable=False),
        sa.Column("lessee_name", sa.String(200), nullable=False),
        sa.Column("lessee_address", sa.String(300), nullable=False),
        sa.Column("lessee_contact", sa.String(300), nullable=True),
        sa.Column("purpose", sa.String(500), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("leased_area", sa.String(100), nullable=True),
        sa.Column("annual_rent", sa.Integer, nullable=True),
        sa.Column("override_flag", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("override_reason", sa.Text, nullable=True),
        sa.Column("payment_method", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("delete_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_t_lease_parent_case_id", "t_lease", ["parent_case_id"])
    op.create_index("ix_t_lease_status", "t_lease", ["status"])

    op.create_table(
        "t_lease_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("target_id", sa.Integer, nullable=False, index=True),
        sa.Column("operation_type", sa.String(20), nullable=False),
        sa.Column("snapshot", sa.Text, nullable=False),
        sa.Column("changed_by", sa.Integer, nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reason", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("t_lease_history")
    op.drop_table("t_lease")
