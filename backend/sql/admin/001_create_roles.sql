-- 001_create_roles.sql
-- Purpose: create role groups and login users for annotation_platform.
-- Run as: postgres superuser (or a role with CREATEROLE).
-- Notes:
-- 1) Passwords must be passed with psql -v variables.
-- 2) This file uses ASCII only to avoid Windows codepage issues.

\set ON_ERROR_STOP on
\encoding UTF8

\if :{?migrator_password}
\else
\echo 'ERROR: missing -v migrator_password=...'
\quit 1
\endif

\if :{?app_password}
\else
\echo 'ERROR: missing -v app_password=...'
\quit 1
\endif

\if :{?readonly_password}
\else
\echo 'ERROR: missing -v readonly_password=...'
\quit 1
\endif

-- Optional minimum-length checks (12+)
SELECT (char_length(:'migrator_password') >= 12) AS ok_migrator \gset
\if :ok_migrator
\else
\echo 'ERROR: migrator_password must be at least 12 characters.'
\quit 1
\endif

SELECT (char_length(:'app_password') >= 12) AS ok_app \gset
\if :ok_app
\else
\echo 'ERROR: app_password must be at least 12 characters.'
\quit 1
\endif

SELECT (char_length(:'readonly_password') >= 12) AS ok_readonly \gset
\if :ok_readonly
\else
\echo 'ERROR: readonly_password must be at least 12 characters.'
\quit 1
\endif

-- Create group roles if they do not exist.
SELECT 'CREATE ROLE grp_annotation_ddl NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grp_annotation_ddl')
\gexec

SELECT 'CREATE ROLE grp_annotation_rw NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grp_annotation_rw')
\gexec

SELECT 'CREATE ROLE grp_annotation_ro NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'grp_annotation_ro')
\gexec

-- Create login roles if they do not exist.
SELECT format('CREATE ROLE annotation_migrator LOGIN PASSWORD %L', :'migrator_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'annotation_migrator')
\gexec

SELECT format('CREATE ROLE annotation_app LOGIN PASSWORD %L', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'annotation_app')
\gexec

SELECT format('CREATE ROLE annotation_readonly LOGIN PASSWORD %L', :'readonly_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'annotation_readonly')
\gexec

-- Enforce least-privilege attributes and rotate passwords (idempotent).
SELECT format(
    'ALTER ROLE annotation_migrator WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L',
    :'migrator_password'
)
\gexec

SELECT format(
    'ALTER ROLE annotation_app WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L',
    :'app_password'
)
\gexec

SELECT format(
    'ALTER ROLE annotation_readonly WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L',
    :'readonly_password'
)
\gexec

-- Membership bindings (idempotent).
GRANT grp_annotation_ddl TO annotation_migrator;
GRANT grp_annotation_rw TO annotation_app;
GRANT grp_annotation_ro TO annotation_readonly;
