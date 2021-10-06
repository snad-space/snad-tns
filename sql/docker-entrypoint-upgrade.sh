#!/bin/sh

while :
do
  sleep 86400
  python3 /fill_table.py tns-catalog-sql
  psql -a -h tns-catalog-sql -U catalog -c 'GRANT SELECT ON ALL TABLES IN SCHEMA public TO app;'
done
