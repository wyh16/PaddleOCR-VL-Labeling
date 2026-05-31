-- 002_grant_annotation_platform.sql
-- Purpose: grant connect/schema/table/sequence privileges on annotation_platform.
-- Prerequisite: 001_create_roles.sql has completed.
-- Run this while connected to database annotation_platform.

\set ON_ERROR_STOP on
\encoding UTF8

DO $$
BEGIN
    IF current_database() <> 'annotation_platform' THEN
        RAISE EXCEPTION 'Current database is %, expected annotation_platform.', current_database();
    END IF;
END
$$;

-- Database CONNECT
GRANT CONNECT ON DATABASE annotation_platform TO grp_annotation_ddl;
GRANT CONNECT ON DATABASE annotation_platform TO grp_annotation_rw;
GRANT CONNECT ON DATABASE annotation_platform TO grp_annotation_ro;

-- Schema privileges
GRANT USAGE ON SCHEMA public TO grp_annotation_ddl;
GRANT USAGE ON SCHEMA public TO grp_annotation_rw;
GRANT USAGE ON SCHEMA public TO grp_annotation_ro;
GRANT CREATE ON SCHEMA public TO grp_annotation_ddl;

-- Existing table privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO grp_annotation_rw;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grp_annotation_ro;

-- Existing sequence privileges
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO grp_annotation_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO grp_annotation_ro;
