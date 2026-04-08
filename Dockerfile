FROM postgres:17.7-trixie

# Based on:
# * http://git.axiom/axiom/webcoos-postgres-db
# * https://github.com/supabase/pg_jsonschema/blob/master/dockerfiles/db/Dockerfile
# * https://github.com/linz/postgresql-tableversion/blob/master/Dockerfile#L21

# postgresql-17-wal2json is required to support live migrations (migrations
# that don't require dump-then-restore workflows that take the database down for a significant
# period of time)
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-17-wal2json \
        pgxnclient \
        ca-certificates \
        gettext-base \
        git \
        build-essential \
        pkg-config \
        libpq-dev \
        postgresql-server-dev-17 \
        curl \
        libreadline6-dev \
        zlib1g-dev \
        libssl-dev \
        libmagic-dev \
        jq \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /home/supa

ENV HOME=/home/supa \
  PATH=/home/supa/.cargo/bin:$PATH
RUN chown postgres:postgres /home/supa
USER postgres

RUN \
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path --profile minimal --default-toolchain stable && \
  rustup --version && \
  rustc --version && \
  cargo --version

# PGX
RUN cargo install cargo-pgrx --version 0.16.1 --locked

RUN cargo pgrx init --pg17 $(which pg_config)

USER root

ADD https://github.com/supabase/pg_jsonschema.git /home/supa/pg_jsonschema

WORKDIR /home/supa/pg_jsonschema
RUN cargo pgrx install && cargo clean

# Install the pgxn package for pg-safeupdate to ensure that we don't
# accidentally nuke entire tables when updating via PostgREST.
RUN pgxn install safeupdate

# Add an extension that allows us to version tables (if required)
ADD https://github.com/axiom-data-science/postgresql-tableversion.git#support-uuid-pkey /home/linz/postgresql-tableversion
WORKDIR /home/linz/postgresql-tableversion
RUN gmake && gmake install

# Add extension that allows for being able to determine mimetype/file type
# based on magic strings
ADD https://github.com/nmandery/pg_byteamagic.git /home/nmandery/pg_byteamagic
WORKDIR /home/nmandery/pg_byteamagic
RUN make && make install

# Remove unnecessary build files
RUN rm -rf /home/supa /home/linz/ /home/nmandery

# RUN chown -R postgres:postgres /home/supa /home/linz /home/nmandery/pg_byteamagic
RUN chown -R postgres:postgres /usr/share/postgresql/17/extension
RUN chown -R postgres:postgres /usr/lib/postgresql/17/lib

# Copies the envsubstr script to be included during init steps
COPY ./docker/env.sh /usr/local/bin/env.sh
RUN chmod ug=rwx,o=rx /usr/local/bin/env.sh

# Custom docker-entrypoint.sh to call env.sh just ahead of db initialization
COPY ./docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod u=rwx,go=rx /usr/local/bin/docker-entrypoint.sh

# Allow the postgres user to write to the initdb.d dir (for template processing)
RUN chown :postgres /docker-entrypoint-initdb.d/
RUN chmod g=rwx /docker-entrypoint-initdb.d/

# Same, but for postinit template dir
RUN mkdir /templates \
    && chown :postgres /templates/ \
    && chown :postgres /templates/ \
    && chmod g=rwx /templates/

COPY --chown=postgres:postgres templates/postinit/*.template /templates/
COPY --chown=postgres:postgres templates/initdb.sh.template /docker-entrypoint-initdb.d/99_initdb.sh.template

WORKDIR /

# Runs as root for init, then drops into postgres
USER root