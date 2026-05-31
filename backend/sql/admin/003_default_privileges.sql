-- 003_default_privileges.sql
-- Purpose: set default privileges for future objects created by annotation_migrator.
-- Prerequisite:
-- 1) 001_create_roles.sql
-- 2) 002_grant_annotation_platform.sql
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

-- Future tables created by annotation_migrator
ALTER DEFAULT PRIVILEGES FOR ROLE annotation_migrator IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO grp_annotation_rw;

ALTER DEFAULT PRIVILEGES FOR ROLE annotation_migrator IN SCHEMA public
GRANT SELECT ON TABLES TO grp_annotation_ro;

-- Future sequences created by annotation_migrator
ALTER DEFAULT PRIVILEGES FOR ROLE annotation_migrator IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO grp_annotation_rw;

ALTER DEFAULT PRIVILEGES FOR ROLE annotation_migrator IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO grp_annotation_ro;
