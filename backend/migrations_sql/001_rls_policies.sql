-- Migration: 001_rls_policies.sql
-- Description: Enable Row-Level Security (RLS) on organizations, subscriptions, api_keys, usage_events, and consent_records.
--              Also configures the 'admin' role to bypass RLS.

-- 1. Ensure columns exist on users table (to align schema with SQLAlchemy models)
ALTER TABLE users ADD COLUMN IF NOT EXISTS org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);

-- 2. Enable RLS and FORCE RLS on target tables (so that even table owners/applications are subject to RLS)
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations FORCE ROW LEVEL SECURITY;

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions FORCE ROW LEVEL SECURITY;

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys FORCE ROW LEVEL SECURITY;

ALTER TABLE usage_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_events FORCE ROW LEVEL SECURITY;

ALTER TABLE consent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE consent_records FORCE ROW LEVEL SECURITY;

-- 3. Create database role 'admin' and 'app_user'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user;
    END IF;
END
$$;
ALTER ROLE admin BYPASSRLS;

-- Grant role memberships to the current connection user so they can switch roles in sessions
DO $$
DECLARE
    curr_user TEXT;
BEGIN
    curr_user := current_user;
    EXECUTE 'GRANT admin TO ' || quote_ident(curr_user);
    EXECUTE 'GRANT app_user TO ' || quote_ident(curr_user);
END
$$;

-- Grant permissions to app_user (to allow executing queries under app_user role)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- 4. Set up Policies

-- ==========================================
-- Table: organizations
-- ==========================================
-- Policy: org members can read org-level data
DROP POLICY IF EXISTS organization_org_member_policy ON organizations;
CREATE POLICY organization_org_member_policy ON organizations
    FOR SELECT
    USING (id = NULLIF(current_setting('app.org_id', true), '')::integer);

-- ==========================================
-- Table: subscriptions
-- ==========================================
-- Policy: users can only SELECT/UPDATE their own rows
DROP POLICY IF EXISTS subscription_user_policy ON subscriptions;
CREATE POLICY subscription_user_policy ON subscriptions
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.user_id', true), '')::integer)
    WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::integer);

-- Policy: org members can read org-level data
DROP POLICY IF EXISTS subscription_org_policy ON subscriptions;
CREATE POLICY subscription_org_policy ON subscriptions
    FOR SELECT
    USING (org_id = NULLIF(current_setting('app.org_id', true), '')::integer);

-- ==========================================
-- Table: api_keys
-- ==========================================
-- Policy: users can only SELECT/UPDATE their own rows
DROP POLICY IF EXISTS api_key_user_policy ON api_keys;
CREATE POLICY api_key_user_policy ON api_keys
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.user_id', true), '')::integer)
    WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::integer);

-- ==========================================
-- Table: usage_events
-- ==========================================
-- Policy: users can only SELECT/UPDATE/INSERT their own rows
DROP POLICY IF EXISTS usage_event_user_policy ON usage_events;
CREATE POLICY usage_event_user_policy ON usage_events
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.user_id', true), '')::integer)
    WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::integer);

-- ==========================================
-- Table: consent_records
-- ==========================================
-- Policy: users can only SELECT/UPDATE their own rows
DROP POLICY IF EXISTS consent_record_user_policy ON consent_records;
CREATE POLICY consent_record_user_policy ON consent_records
    FOR ALL
    USING (user_id = NULLIF(current_setting('app.user_id', true), '')::integer)
    WITH CHECK (user_id = NULLIF(current_setting('app.user_id', true), '')::integer);
