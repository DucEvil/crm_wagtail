#!/usr/bin/env bash
set -euo pipefail

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 \
  --set app_db="$POSTGRES_DB" \
  --set app_user="$APP_DB_USER" \
  --set app_password="$APP_DB_PASSWORD" \
  --set analytics_user="$ANALYTICS_DB_USER" \
  --set analytics_password="$ANALYTICS_DB_PASSWORD" \
  --set meta_user="$SUPERSET_META_USER" \
  --set meta_password="$SUPERSET_META_PASSWORD" <<'SQL'
CREATE ROLE :"analytics_user" LOGIN PASSWORD :'analytics_password';
ALTER ROLE :"analytics_user" SET default_transaction_read_only = on;
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password';
ALTER DATABASE :"app_db" OWNER TO :"app_user";
GRANT ALL ON SCHEMA public TO :"app_user";
CREATE ROLE :"meta_user" LOGIN PASSWORD :'meta_password';
SQL

psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 \
  --set meta_db="$SUPERSET_META_DB" \
  --set meta_user="$SUPERSET_META_USER" <<'SQL'
CREATE DATABASE :"meta_db" OWNER :"meta_user";
SQL
