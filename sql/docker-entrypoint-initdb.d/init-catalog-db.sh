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
psql -v ON_ERROR_STOP=1 --username catalog --dbname catalog <<-EOSQL
  ALTER TABLE tns ADD PRIMARY KEY ("objid");
  ALTER TABLE tns ADD COLUMN coord spoint;
  UPDATE tns SET coord = spoint("ra" * pi() / 180.0, "declination" * pi() / 180.0);
  ALTER TABLE tns ALTER COLUMN coord SET NOT NULL;
  CREATE INDEX tns_coord_idx ON tns USING GIST (coord);
EOSQL

psql -v ON_ERROR_STOP=1 --username catalog --dbname catalog <<-EOSQL
   VACUUM FULL ANALYZE;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname catalog <<-EOSQL
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO app;
    REVOKE CREATE ON SCHEMA public FROM public;
EOSQL
