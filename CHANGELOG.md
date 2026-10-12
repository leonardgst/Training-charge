# Journal des modifications

Toutes les modifications notables du projet sont consignées ici, au format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les versions suivent la convention du cadrage : `v0.<phase>.0`, puis `v1.0.0` à la mise en service.

## [Non publié]

### Ajouté

- Documentation de cadrage : cadrage anonymisé et synthèse de la phase 0, spécifications, architecture, stratégie de tests, ADR 0001 à 0018, glossaire, journal, fiche de la phase 1.
- `CLAUDE.md`, modèle de PR et permissions de Claude Code.
- `.gitattributes` : fins de ligne normalisées en LF.
- Projet Django 5.2 : projet `config` et application `suivi`, réglages par variables d'environnement (`.env.example`), français et Europe/Paris, refus par défaut des vues (`LoginRequiredMiddleware`), page de connexion minimale, contrôle de santé (`/sante/`).
- Chaîne locale de qualité : uv (Python 3.12), Ruff, mypy avec `django-stubs`, pytest ; tests unitaires des liens de la documentation, des réglages et de l'accès d'un visiteur sans session.
