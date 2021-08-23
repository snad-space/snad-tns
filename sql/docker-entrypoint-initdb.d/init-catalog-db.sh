#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  CREATE USER app;
  GRANT CONNECT ON DATABASE catalog TO app;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname catalog <<-EOSQL
        CREATE EXTENSION pg_sphere;
EOSQL

python3 /fill_table.py

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname catalog <<-EOSQL
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO app;
    REVOKE CREATE ON SCHEMA public FROM public;
EOSQL
