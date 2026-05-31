"""add_root_role

Revision ID: 82fdad317010
Revises: 5a62064f48ec
Create Date: 2026-05-31 00:01:59.886260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82fdad317010'
down_revision: Union[str, Sequence[str], None] = '5a62064f48ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'root'")


def downgrade() -> None:
    """Downgrade schema."""
    pass

