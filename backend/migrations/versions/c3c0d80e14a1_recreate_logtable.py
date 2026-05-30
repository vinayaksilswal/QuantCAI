"""recreate_logtable

Revision ID: c3c0d80e14a1
Revises: b1da0534721a
Create Date: 2026-05-30 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3c0d80e14a1'
down_revision: Union[str, Sequence[str], None] = 'b1da0534721a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create logtable safely if not exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'logtable' not in existing_tables:
        op.create_table(
            'logtable',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text("TIMEZONE('utc', NOW())"), nullable=False),
            sa.Column('level', sa.String(length=20), nullable=False),
            sa.Column('logger_name', sa.String(length=100), nullable=True),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('module', sa.String(length=100), nullable=True),
            sa.Column('function', sa.String(length=100), nullable=True),
            sa.Column('line_number', sa.Integer(), nullable=True),
            sa.Column('request_method', sa.String(length=10), nullable=True),
            sa.Column('request_path', sa.String(length=500), nullable=True),
            sa.Column('request_ip', sa.String(length=50), nullable=True),
            sa.Column('response_status', sa.Integer(), nullable=True),
            sa.Column('exception', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_logtable_id'), 'logtable', ['id'], unique=False)
        op.create_index(op.f('ix_logtable_level'), 'logtable', ['level'], unique=False)
        op.create_index(op.f('ix_logtable_timestamp'), 'logtable', ['timestamp'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'logtable' in existing_tables:
        op.drop_index(op.f('ix_logtable_id'), table_name='logtable')
        op.drop_index(op.f('ix_logtable_level'), table_name='logtable')
        op.drop_index(op.f('ix_logtable_timestamp'), table_name='logtable')
        op.drop_table('logtable')
