FROM postgres:17.7-trixie

# Based on:
# * http://git.axiom/axiom/webcoos-postgres-db
# * https://github.com/supabase/pg_jsonschema/blob/master/dockerfiles/db/Dockerfile

# postgresql-17-wal2json is required to support live migrations (migrations
# that don't require dump-then-restore workflows that take the database down for a significant
# period of time)
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql-17-wal2json \
        ca-certificates \
        git \
        build-essential \
        pkg-config \
        libpq-dev \
        postgresql-server-dev-17 \
        curl \
        libreadline6-dev \
        zlib1g-dev \
        libssl-dev \
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

RUN chown -R postgres:postgres /home/supa
RUN chown -R postgres:postgres /usr/share/postgresql/17/extension
RUN chown -R postgres:postgres /usr/lib/postgresql/17/lib

WORKDIR /home/supa

USER postgres