# Journal des modifications

Toutes les modifications notables du projet sont consignées ici, au format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les versions suivent la convention du cadrage : `v0.<phase>.0`, puis `v1.0.0` à la mise en service.

## [Non publié]

### Ajouté

- Modèles `Categorie`, `Preparateur` et `Joueur` avec leur migration : contraintes en base (code unique, jours de questionnaire dans la semaine, nom et prénom non vides), archivage par `actif`, `updated_at` et `updated_by`, administration Django réservée au superutilisateur.
- Modèles `Seance` et `Participation` : durée de 1 à 300, RPE de 0 à 10 (ou absents en brouillon), type et statut dans une liste fermée, `validated_at` cohérent avec le statut, une participation par joueur et par séance ; déclencheurs Postgres interdisant une participation incomplète dans une séance validée.

## [0.1.0] - 2026-10-13

Phase 1 : socle et chaîne de qualité.

### Ajouté

- Documentation de cadrage : cadrage anonymisé et synthèse de la phase 0, spécifications, architecture, stratégie de tests, ADR 0001 à 0018, glossaire, journal, fiche de la phase 1.
- `CLAUDE.md`, modèle de PR et permissions de Claude Code.
- `.gitattributes` : fins de ligne normalisées en LF.
- Projet Django 5.2 : projet `config` et application `suivi`, réglages par variables d'environnement (`.env.example`), français et Europe/Paris, refus par défaut des vues (`LoginRequiredMiddleware`), page de connexion minimale, contrôle de santé (`/sante/`).
- Chaîne locale de qualité : uv (Python 3.12), Ruff, mypy avec `django-stubs`, pytest ; tests unitaires des liens de la documentation, des réglages et de l'accès d'un visiteur sans session.
- Base locale : `compose.yaml` (Postgres 16), script d'initialisation des rôles de migration et d'exécution sans droit à `PUBLIC`, réglages `DATABASES` par variables d'environnement ; `pytest-django` et `psycopg` ; tests d'intégration des migrations depuis zéro et des droits des rôles.
- Chaîne d'intégration continue : workflow GitHub Actions à six jobs (`qualite`, `tests`, `migrations`, `e2e`, `audit`, `build`), tests de bout en bout Playwright de la connexion sur ordinateur et téléphone, test d'intégration du catalogue des routes pour un visiteur (A1, squelette), `pip-audit` et gitleaks ; ruleset de `main` actif, six jobs obligatoires.
- Déploiement : réglages HTTPS (`DJANGO_HTTPS`, `DB_SSLMODE`), `vercel.json` (région `fra1`), workflows de preview (branche Neon par PR) et de production (environnement `production`, migrations par le rôle de migration), test de fumée, `check --deploy` dans `qualite`, `docs/deploiement.md`.
- `README.md` : présentation, prérequis, installation, base locale, lancement, tests et intégration continue.

### Modifié

- Permissions de Claude Code : lecture de `.env` refusée aussi par le shell ; auto-mode autorisé et mode par défaut.
