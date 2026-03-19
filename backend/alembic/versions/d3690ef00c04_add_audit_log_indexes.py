"""add audit_log indexes

Revision ID: d3690ef00c04
Revises: b269014132c7
Create Date: 2026-03-19 23:52:43.804506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3690ef00c04'
down_revision: Union[str, Sequence[str], None] = 'b269014132c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("idx_audit_log_target", "t_audit_log", ["target_table", "target_id"])
    op.create_index("idx_audit_log_user", "t_audit_log", ["user_id"])
    op.create_index("idx_audit_log_time", "t_audit_log", ["performed_at"])
    op.create_index("idx_audit_log_target_time", "t_audit_log", ["target_table", "target_id", "performed_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_log_target_time")
    op.drop_index("idx_audit_log_time")
    op.drop_index("idx_audit_log_user")
    op.drop_index("idx_audit_log_target")
