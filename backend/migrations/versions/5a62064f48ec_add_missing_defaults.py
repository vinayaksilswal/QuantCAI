"""add_missing_defaults

Revision ID: 5a62064f48ec
Revises: c3c0d80e14a1
Create Date: 2026-05-30 23:59:07.195118

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a62064f48ec'
down_revision: Union[str, Sequence[str], None] = 'c3c0d80e14a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('circuits', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('circuits', 'updated_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('refresh_tokens', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('comments', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('comments', 'updated_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('likes', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('posts', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('posts', 'updated_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('courses', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('courses', 'updated_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('notification_requests', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('subscribers', 'created_at', server_default=sa.text("TIMEZONE('utc', NOW())"))
    op.alter_column('subscribers', 'updated_at', server_default=sa.text("TIMEZONE('utc', NOW())"))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('circuits', 'created_at', server_default=None)
    op.alter_column('circuits', 'updated_at', server_default=None)
    op.alter_column('refresh_tokens', 'created_at', server_default=None)
    op.alter_column('comments', 'created_at', server_default=None)
    op.alter_column('comments', 'updated_at', server_default=None)
    op.alter_column('likes', 'created_at', server_default=None)
    op.alter_column('posts', 'created_at', server_default=None)
    op.alter_column('posts', 'updated_at', server_default=None)
    op.alter_column('courses', 'created_at', server_default=None)
    op.alter_column('courses', 'updated_at', server_default=None)
    op.alter_column('notification_requests', 'created_at', server_default=None)
    op.alter_column('subscribers', 'created_at', server_default=None)
    op.alter_column('subscribers', 'updated_at', server_default=None)

