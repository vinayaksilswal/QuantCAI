"""initial_schema

Revision ID: f77129b3393a
Revises: 
Create Date: 2026-05-28 13:52:27.421208

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f77129b3393a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Idempotent table and type creation."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Safely retrieve existing enums in the PostgreSQL database
    existing_enums = conn.execute(sa.text(
        "SELECT t.typname FROM pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typtype = 'e'"
    )).scalars().all()

    # Helper function to create enum safely
    def safe_create_enum(name, values):
        if name not in existing_enums:
            postgresql.ENUM(*values, name=name).create(conn)

    # 1. Create Enums
    safe_create_enum('user_role_enum', ('admin', 'developer', 'learner', 'enterprise_user'))
    safe_create_enum('org_plan_enum', ('starter', 'pro', 'enterprise'))
    safe_create_enum('contract_type_enum', ('monthly', 'annual'))
    safe_create_enum('sub_plan_enum', ('free', 'pro', 'enterprise'))
    safe_create_enum('sub_status_enum', ('active', 'past_due', 'cancelled', 'trialing'))
    safe_create_enum('api_key_tier_enum', ('free', 'pro', 'enterprise'))
    safe_create_enum('usage_event_type_enum', ('tutor_query', 'simulation_run', 'pqc_scan', 'api_call'))

    # Helper function to check index existence
    def index_exists(table_name, idx_name):
        if table_name not in existing_tables:
            return False
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == idx_name for idx in indexes)

    # 2. Create organizations table
    if 'organizations' not in existing_tables:
        op.create_table(
            'organizations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('domain', sa.String(length=255), nullable=True),
            sa.Column('plan', postgresql.ENUM('starter', 'pro', 'enterprise', name='org_plan_enum', create_type=False), nullable=False),
            sa.Column('contract_type', postgresql.ENUM('monthly', 'annual', name='contract_type_enum', create_type=False), nullable=False),
            sa.Column('pqc_scan_quota', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('domain')
        )
    if not index_exists('organizations', 'ix_organizations_domain'):
        op.create_index('ix_organizations_domain', 'organizations', ['domain'], unique=True)

    # 3. Create users table
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password', sa.String(length=255), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('role', postgresql.ENUM('admin', 'developer', 'learner', 'enterprise_user', name='user_role_enum', create_type=False), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
            sa.Column('org_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('verification_sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('stripe_customer_id')
        )
    if not index_exists('users', 'ix_users_email'):
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
    if not index_exists('users', 'ix_users_stripe_customer_id'):
        op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True)
    if not index_exists('users', 'ix_users_org_id'):
        op.create_index('ix_users_org_id', 'users', ['org_id'], unique=False)

    # 4. Create subscriptions table
    if 'subscriptions' not in existing_tables:
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('org_id', sa.Integer(), nullable=True),
            sa.Column('plan', postgresql.ENUM('free', 'pro', 'enterprise', name='sub_plan_enum', create_type=False), nullable=False),
            sa.Column('status', postgresql.ENUM('active', 'past_due', 'cancelled', 'trialing', name='sub_status_enum', create_type=False), nullable=False),
            sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
            sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('stripe_subscription_id')
        )
    if not index_exists('subscriptions', 'ix_subscriptions_org_id'):
        op.create_index('ix_subscriptions_org_id', 'subscriptions', ['org_id'], unique=False)
    if not index_exists('subscriptions', 'ix_subscriptions_stripe_subscription_id'):
        op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'], unique=True)
    if not index_exists('subscriptions', 'ix_subscriptions_user_id'):
        op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'], unique=False)

    # 5. Create api_keys table
    if 'api_keys' not in existing_tables:
        op.create_table(
            'api_keys',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('key_hash', sa.String(length=255), nullable=False),
            sa.Column('label', sa.String(length=255), nullable=False),
            sa.Column('tier', postgresql.ENUM('free', 'pro', 'enterprise', name='api_key_tier_enum', create_type=False), nullable=False),
            sa.Column('requests_today', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='1000'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key_hash')
        )
    if not index_exists('api_keys', 'ix_api_keys_key_hash'):
        op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)
    if not index_exists('api_keys', 'ix_api_keys_user_id'):
        op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False)

    # 6. Create usage_events table
    if 'usage_events' not in existing_tables:
        op.create_table(
            'usage_events',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('api_key_id', sa.Integer(), nullable=True),
            sa.Column('event_type', postgresql.ENUM('tutor_query', 'simulation_run', 'pqc_scan', 'api_call', name='usage_event_type_enum', create_type=False), nullable=False),
            sa.Column('credits_used', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('usage_events', 'idx_usage_events_api_key_id'):
        op.create_index('idx_usage_events_api_key_id', 'usage_events', ['api_key_id'], unique=False)
    if not index_exists('usage_events', 'idx_usage_events_user_id_created_at'):
        op.create_index('idx_usage_events_user_id_created_at', 'usage_events', ['user_id', 'created_at'], unique=False)

    # 7. Create consent_records table
    if 'consent_records' not in existing_tables:
        op.create_table(
            'consent_records',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('purpose', sa.String(length=255), nullable=False),
            sa.Column('granted', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('consent_records', 'ix_consent_records_user_id'):
        op.create_index('ix_consent_records_user_id', 'consent_records', ['user_id'], unique=False)

    # 8. Create audit_logs table
    if 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(length=255), nullable=False),
            sa.Column('table_name', sa.String(length=255), nullable=False),
            sa.Column('record_id', sa.Integer(), nullable=False),
            sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
    if not index_exists('audit_logs', 'ix_audit_logs_user_id'):
        op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove tables and enums safely."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop tables in reverse order of creation
    tables_to_drop = ['audit_logs', 'consent_records', 'usage_events', 'api_keys', 'subscriptions', 'users', 'organizations']
    for table in tables_to_drop:
        if table in existing_tables:
            op.drop_table(table)

    # Drop enums safely
    existing_enums = conn.execute(sa.text(
        "SELECT t.typname FROM pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typtype = 'e'"
    )).scalars().all()

    enums_to_drop = ['user_role_enum', 'org_plan_enum', 'contract_type_enum', 'sub_plan_enum', 'sub_status_enum', 'api_key_tier_enum', 'usage_event_type_enum']
    for enum_name in enums_to_drop:
        if enum_name in existing_enums:
            op.execute(sa.text(f"DROP TYPE {enum_name}"))
