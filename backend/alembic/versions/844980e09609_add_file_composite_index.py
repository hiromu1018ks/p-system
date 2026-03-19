"""add file composite index

Revision ID: 844980e09609
Revises: b7f8a4a58613
Create Date: 2026-03-20 08:03:31.185313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '844980e09609'
down_revision: Union[str, Sequence[str], None] = 'b7f8a4a58613'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index("idx_file_related", "t_file", ["related_type", "related_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_file_related")
