#!/bin/bash
# Script to create Redshift schema

set -e

PGHOST=${PGHOST:-localhost}
PGPORT=${PGPORT:-5439}
PGDATABASE=${PGDATABASE:-retail_dw}
PGUSER=${PGUSER:-admin}
SCHEMA_NAME=${SCHEMA_NAME:-staging}

psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" <<EOF
CREATE SCHEMA IF NOT EXISTS ${SCHEMA_NAME};
GRANT USAGE ON SCHEMA ${SCHEMA_NAME} TO PUBLIC;
EOF

echo "Schema ${SCHEMA_NAME} created successfully"

