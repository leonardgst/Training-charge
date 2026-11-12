---
name: migration
description: Fait évoluer le schéma de la base par une migration Django sûre, compatible avec le code déjà en production, testée en local, en CI et sur la branche Neon de la preview. À utiliser pour tout changement de suivi/models.py.
argument-hint: "[changement de schéma voulu]"
---

# Faire évoluer le schéma

Changement : $ARGUMENTS.

Délègue la conception et la relecture à l'agent `migrations`, puis vérifie avec lui chaque étape.

1. **Compatibilité** : la production est migrée avant le déploiement du code. Le nouveau schéma doit fonctionner avec le code actuellement en production. Un renommage ou une suppression de colonne se fait en deux PR : d'abord le code qui n'en dépend plus, ensuite la migration.
2. **Migration** : `uv run --env-file .env python manage.py makemigrations`, puis relecture du SQL avec `sqlmigrate`.
3. **Base vide** : `docker compose down -v && docker compose up -d db`, puis `migrate` et `generer_demo`, comme le job `migrations` de la CI.
4. **Tests** : contraintes en SQL direct (D1, D2), droits des rôles (`tests/integration/test_roles_postgres.py`), modèle, accès (agent `gardien-acces`).
5. **Documentation** : architecture, section 4 (modèle de données), si une table ou une contrainte change.
6. **Preview** : après la poussée, le job `deployer` applique la migration sur `pr-<numéro>`, copie de la production. Vérifie que l'étape est verte, puis le schéma de cette branche avec les outils Neon, en donnant son `branch_id`.

Jamais : migrer la production toi-même, utiliser `complete_database_migration`, écrire du SQL sur la branche `production`.
