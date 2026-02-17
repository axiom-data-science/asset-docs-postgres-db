# Create user and database
psql --username "$POSTGRES_USER" <<'EOF'
-- CREATE DATABASE asset_docs OWNER asset_docs;
-- ALTER USER asset_docs CREATEDB;

ALTER DATABASE asset_docs SET session_preload_libraries = 'safeupdate';
EOF

# echo "Loading table_version into asset_docs";
# pgxn load --username "$POSTGRES_USER" -d asset_docs table_version

# operations within the target database
psql --username "$POSTGRES_USER" asset_docs <<'EOF'

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_jsonschema";
CREATE EXTENSION IF NOT EXISTS "table_version";


CREATE SCHEMA IF NOT EXISTS asset_docs AUTHORIZATION asset_docs;

-- Set the search path for each of the users
ALTER ROLE asset_docs SET search_path TO "asset_docs",public;

CREATE TABLE IF NOT EXISTS asset_docs.document (
    "uuid" uuid NOT NULL DEFAULT uuid_generate_v4(),
    "owner_sub" VARCHAR(64) NOT NULL,
    "lock_sub" VARCHAR(64) NULL,
    "locked_at" timestamptz NULL,
    "subs_for_update" jsonb NOT NULL DEFAULT '[]'::jsonb,
    "roles_for_update" jsonb NOT NULL DEFAULT '[]'::jsonb,
    "data" jsonb NOT NULL DEFAULT '{}'::jsonb,
    "attrs" jsonb NOT NULL DEFAULT '{}'::jsonb,
    "json_schema" jsonb NOT NULL DEFAULT '{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"dummy_schema.json","title":"Dummy Schema","description":"A dummy schema","type":"object"}'::jsonb,
    "created_at" timestamptz NOT NULL DEFAULT now(),
    "updated_at" timestamptz NOT NULL DEFAULT now(),
    "type" varchar(256) NOT NULL DEFAULT '',
    "label" varchar(256) NOT NULL DEFAULT '',
    "description" text NOT NULL DEFAULT '',
    "comments" text NOT NULL DEFAULT '',
    CONSTRAINT document_pkey PRIMARY KEY (uuid)
);

ALTER TABLE asset_docs.document ENABLE ROW LEVEL SECURITY;

SELECT table_version.ver_enable_versioning('asset_docs', 'document');

INSERT INTO asset_docs.document (
    "owner_sub",
    "data",
    "type",
    "label",
    "description",
    "comments"
) VALUES (
    'josh@axds.co',
    '{"hey":"there"}'::jsonb,
    'test_type',
    'test_label',
    'test_description',
    'test_comment'
);

EOF