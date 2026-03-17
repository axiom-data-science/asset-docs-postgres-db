# asset-docs-postgres-db

A repo to define and track the Postgres/PostGIS requirements for the Docker image supporting Asset Docs Postgres instances.


## Docker Build

```shell
docker build -t asset-docs-postgres-db:latest .
```

...or...

```shell
docker compose build
```

## Run

```shell
docker compose up
```


## JWT Auth Setup

To configure asymmetric JWT validation (using public/private keys to sign and
then later verify a JWT auth header), PostgREST needs to know which public keys
are acceptable when validating a signed JWT.

This is retrieved from Authentik (or your Identity Provider of choice) by
querying the JWKS URL for the relevant app. In the case of Asset Docs, the
keys can be retrieved like so:

```shell
curl --silent "https://ego.srv.axds.co/application/o/asset-docs/jwks/" | jq -Rsa .
```

...which returns an output like:

```
"{\"keys\": [{\"alg\": \"RS256\", \"kid\":...
```

...which is suitable for inclusion in the `.env` file for the
