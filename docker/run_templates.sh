#!/bin/bash

# Generates .sql from templates then executes the generated .sql files in
# numeric order. Fails immediately and stops .sql file execution upon failure
# coming back from psql

TEMPLATES_DIR="$1"

ADDB_OWNER_USER=${ADDB_OWNER_USER:-}
ADDB_DB_NAME=${ADDB_DB_NAME:-}

if [ -z "$ADDB_OWNER_USER" ]; then
    echo "ADDB_OWNER_USER is unset";
    exit 2;
fi

if [ -z "$ADDB_DB_NAME" ]; then
    echo "ADDB_DB_NAME is unset";
    exit 3;
fi

/usr/local/bin/env.sh "$TEMPLATES_DIR";
TEMPLATES_RET=$?

if [ "$TEMPLATES_RET" -ne '0' ]; then
    echo "Unable to process templates" 1>&2;
    exit 4;
fi

if ! pg_isready --host db -U "${ADDB_OWNER_USER}" --dbname "${ADDB_DB_NAME}" --timeout 5; then
    echo "Postgres not ready in time." 1>&2;
    exit 5;
fi

find /templates/ -maxdepth 1 -type f -iname '*.sql' | sort -n | while read -r line; do
    echo "Executing $line";
    psql -v ON_ERROR_STOP=1 --host db -U "${ADDB_OWNER_USER}" --dbname "${ADDB_DB_NAME}" -f "$line";
    PSQL_RET=$?;
    rm "$line";
    if [ "$PSQL_RET" -ne '0' ]; then
        echo "psql returned $PSQL_RET, stopping execution." 1>&2;
        echo "Cleaning up unused template" 1>&2;
        find "$TEMPLATES_DIR" -maxdepth 1 -type f -iname '*.sql' -delete
        exit 6;
    fi
done;

echo "Final .sql file cleanup" 1>&2;
# Finally, clear any remaining .sql files generated from the templates
find "$TEMPLATES_DIR" -maxdepth 1 -type f -iname '*.sql' -delete
