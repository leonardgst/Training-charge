#!/bin/bash
# Crée les deux rôles et la base (docs/02-architecture.md, « Rôles Postgres »).
#
# - Rôle de migration (DB_USER) : propriétaire de la base et du schéma.
# - Rôle d'exécution (DB_RUNTIME_USER) : SELECT, INSERT, UPDATE, DELETE sur les tables,
#   accordés par défaut à chaque nouvelle table ; aucun droit de modifier le schéma.
# - Aucun droit à PUBLIC.
#
# Les mots de passe sont lus dans l'environnement par psql (\getenv) : ils ne passent
# ni par la ligne de commande ni par le journal.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
\getenv db_name DB_NAME
\getenv mig_user DB_USER
\getenv mig_pw DB_PASSWORD
\getenv run_user DB_RUNTIME_USER
\getenv run_pw DB_RUNTIME_PASSWORD

CREATE ROLE :"mig_user" LOGIN CREATEDB PASSWORD :'mig_pw';
CREATE ROLE :"run_user" LOGIN PASSWORD :'run_pw';

-- Le modèle template1 est configuré avant la création de la base : toute base créée
-- ensuite, dont la base de test de pytest-django, en hérite.
\connect template1
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"run_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"mig_user" IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"run_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"mig_user" IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO :"run_user";
ALTER DEFAULT PRIVILEGES FOR ROLE :"mig_user"
  REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

\connect postgres
CREATE DATABASE :"db_name" OWNER :"mig_user";
REVOKE ALL ON DATABASE :"db_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"db_name" TO :"mig_user", :"run_user";
SQL
