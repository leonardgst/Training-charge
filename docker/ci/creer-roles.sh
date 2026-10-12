#!/bin/bash
# Crée les rôles et la base du service Postgres de la CI.
# Reprend docker/initdb/01-roles.sh, conçu pour le répertoire d'initialisation du conteneur :
# ici le service est déjà démarré, on exécute donc le même script par psql.
# Variables lues : PGHOST, PGPASSWORD (superutilisateur), DB_*, POSTGRES_USER.
set -euo pipefail
export POSTGRES_USER=postgres
exec "$(dirname "$0")/../initdb/01-roles.sh"
