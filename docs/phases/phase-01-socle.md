# Phase 01 — Socle et chaîne de qualité

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | 2026-10-13 → 2026-10-26 | — | v0.1.0 |

## Objectif

Prouver que la chaîne complète fonctionne (écrire, tester, fusionner, déployer) avant toute fonctionnalité. À la fin de la phase, une page de connexion vide est déployée à une URL publique, et la CI bloque toute PR en échec.

Niveau de collaboration : 4. Les PR 1.3 (rôles Postgres et migrations) et 1.5 (déploiement et migrations sur une base déployée) sont en niveau 3 : Claude Code en mode Manuel, accord avant chaque action. Estimation : 16 heures.

## Livrables

- [ ] Dépôt public dans WSL, hors de tout dossier synchronisé, avec la documentation de cadrage
- [ ] Projet Django 5.2 nettoyé de tout contenu du générateur, refus par défaut, page de connexion minimale
- [ ] Ruff, mypy et pytest configurés, avec un test trivial à chaque niveau (unitaire, intégration, bout en bout)
- [ ] Base locale reproductible (`docker compose`) avec les rôles de migration et d'exécution
- [ ] CI complète (`qualite`, `tests`, `migrations`, `e2e`, `audit`, `build`), obligatoire par ruleset
- [ ] Preview par PR sur une branche Neon ; production derrière l'environnement `production` et ton approbation
- [ ] README d'installation, de lancement et de test

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 1.1 | `docs: ajouter le cadrage et la configuration de travail` | `docs/`, `CLAUDE.md`, `CHANGELOG.md`, modèle de PR, `.gitignore`, `.claude/settings.json` | Aucun : la CI n'existe pas encore | En revue | — |
| 1.2 | `chore: initialiser le projet Django` | uv, Django 5.2, projet `config`, application `suivi`, réglages par variables d'environnement, français et Europe/Paris, `LoginRequiredMiddleware`, connexion minimale, contrôle de santé, Ruff, mypy, `.env.example` | Unitaires : liens de la documentation, redirection d'un visiteur vers la connexion | À faire | — |
| 1.3 | `chore: fournir la base locale et les rôles Postgres` | `compose.yaml`, script de création des rôles, droits par défaut, `pytest-django` | Intégration : migrations depuis zéro, rôle d'exécution sans droit sur le schéma, aucun droit à `PUBLIC` | À faire | — |
| 1.4 | `chore: ajouter la chaîne d'intégration continue` | Workflow à six jobs, Playwright, pip-audit, gitleaks ; ruleset complet sur `main` | Bout en bout : connexion sur ordinateur et téléphone ; intégration : squelette de A1 sur le catalogue des routes | À faire | — |
| 1.5 | `chore: déployer les previews et la production` | Projets Vercel et Neon, branche Neon par PR, environnement `production`, migrations par le rôle de migration, en-têtes de sécurité | Test de fumée après déploiement ; `check --deploy` | À faire | — |
| 1.6 | `docs: compléter le README et démontrer le blocage` | README ; PR de démonstration avec un test en échec, bloquée puis fermée sans fusion | Recette : clone neuf | À faire | — |

## Critères de fin (Definition of Done)

- [ ] Toutes les PR de la phase sont fusionnées, CI verte
- [ ] Cas de test de la phase au vert : D3 (migrations depuis zéro, encore sans données de démonstration) ; squelette de A1
- [ ] Une PR avec un test en échec est bloquée, démonstration faite et liée ci-dessous
- [ ] L'application est joignable à une URL publique
- [ ] Un clone neuf s'installe, se lance et passe ses tests avec les seules commandes du README
- [ ] Le dépôt est hors de tout dossier synchronisé
- [ ] Recette manuelle faite
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 2

## Recette manuelle

À dérouler par toi, sur l'environnement déployé. Note le résultat à côté de chaque ligne.

- [ ] L'URL de production s'ouvre en HTTPS sur ordinateur et sur téléphone.
- [ ] La racine redirige vers la page de connexion, en français, sans titre, page ni logo du générateur.
- [ ] Une adresse inexistante renvoie une page d'erreur sobre, sans trace de débogage.
- [ ] L'administration demande une connexion.
- [ ] Après 15 minutes sans visite, le premier affichage prend moins de 10 secondes. Durée mesurée : …
- [ ] La preview d'une PR s'ouvre sur ton téléphone.
- [ ] Le déploiement en production a attendu ton approbation dans l'environnement `production`.
- [ ] Une poussée directe sur `main` est refusée par GitHub.
- [ ] La PR de démonstration affiche une CI rouge et un bouton de fusion bloqué. Lien : …
- [ ] Un clone neuf, dans un nouveau dossier de WSL, passe `uv sync` puis tous les tests avec les seules commandes du README. Durée : …
- [ ] `pwd` dans le dépôt donne un chemin sous `/home/`, pas sous `/mnt/c/`.
- [ ] Aucun fichier `.env` n'est suivi par Git (`git ls-files | grep .env` ne renvoie que `.env.example`).

## Décisions prises (liens vers les ADR)

- [ADR-0001](../adr/0001-depot-public-et-protection-de-main.md) — Dépôt public et protection de `main`
- [ADR-0002](../adr/0002-django-et-rendu-serveur.md) — Django et rendu côté serveur
- [ADR-0003](../adr/0003-hebergement-vercel-et-neon.md) — Hébergement sur Vercel et Neon
- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès applicatif et refus par défaut

## Écarts par rapport au plan

- PR 1.1 : `main` a été créée a posteriori par un commit vide (`chore: initialiser le dépôt`). Le lot de cadrage avait été commité et poussé sur `docs/cadrage`, première branche du dépôt ; son commit a été reposé sur `main` pour pouvoir ouvrir la PR.
- PR 1.1 : ajout de `.gitattributes` (`* text=auto eol=lf`) pour normaliser les fins de ligne en LF, le travail se faisant sous Windows.
- Le dépôt est nommé `Training-charge` ; le cadrage laissait ce nom à choisir.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
