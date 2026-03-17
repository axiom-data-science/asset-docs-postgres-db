#!/bin/sh

echo "Injecting runtime environment variables into *.template files..."

VARS_TO_REPLACE="$(printf '${%s} ' $(env | grep -ie "^ADDB_" | cut -d'=' -f1))"

echo "Env vars to replace: $VARS_TO_REPLACE"

DIR_TO_REPLACE="$1";

if [ ! -d "$DIR_TO_REPLACE" ]; then
    echo "Invalid directory $DIR_TO_REPLACE" 1>&2;
    exit 2;
fi


find "$DIR_TO_REPLACE" \
    -type f -iname '*.template' \
    | while read -r line; do \
        envsubst "$VARS_TO_REPLACE" < "$line" > "$line.replaced";

        dn="$( dirname "$line.replaced" )";
        bn="$( basename "$line.replaced" ".template.replaced" )";

        echo "replacing $line with $dn/$bn"
        # cat "$line.replaced";

        # rename to the not-templated name
        #   initdb.sh.template.replaced -> initdb.sh)
        mv -v "$line.replaced" "$dn/$bn"

    done