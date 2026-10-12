# Phase 01 — Socle et chaîne de qualité

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | 2026-10-13 → 2026-10-26 | — | v0.1.0 |

## Objectif

Prouver que la chaîne complète fonctionne (écrire, tester, fusionner, déployer) avant toute fonctionnalité. À la fin de la phase, une page de connexion vide est déployée à une URL publique, et la CI bloque toute PR en échec.

Niveau de collaboration : 4. Les PR 1.3 (rôles Postgres et migrations) et 1.5 (déploiement et migrations sur une base déployée) sont en niveau 3 : Claude Code en mode Manuel, accord avant chaque action. Estimation : 16 heures.

## Livrables

- [x] Dépôt public dans WSL, hors de tout dossier synchronisé, avec la documentation de cadrage
- [ ] Projet Django 5.2 nettoyé de tout contenu du générateur, refus par défaut, page de connexion minimale
- [ ] Ruff, mypy et pytest configurés, avec un test trivial à chaque niveau (unitaire, intégration, bout en bout)
- [x] Base locale reproductible (`docker compose`) avec les rôles de migration et d'exécution
- [ ] CI complète (`qualite`, `tests`, `migrations`, `e2e`, `audit`, `build`), obligatoire par ruleset
- [ ] Preview par PR sur une branche Neon ; production derrière l'environnement `production` et ton approbation
- [ ] README d'installation, de lancement et de test

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 1.1 | `docs: ajouter le cadrage et la configuration de travail` | `docs/`, `CLAUDE.md`, `CHANGELOG.md`, modèle de PR, `.gitignore`, `.claude/settings.json` | Aucun : la CI n'existe pas encore | Fusionnée | [#1](https://github.com/leonardgst/Training-charge/pull/1) |
| 1.2 | `chore: initialiser le projet Django` | uv, Django 5.2, projet `config`, application `suivi`, réglages par variables d'environnement, français et Europe/Paris, `LoginRequiredMiddleware`, connexion minimale, contrôle de santé, Ruff, mypy, `.env.example` | Unitaires : liens de la documentation, redirection d'un visiteur vers la connexion | Fusionnée | [#2](https://github.com/leonardgst/Training-charge/pull/2) |
| 1.3 | `chore: fournir la base locale et les rôles Postgres` | `compose.yaml`, script de création des rôles, droits par défaut, `pytest-django`, `psycopg` | Intégration : migrations depuis zéro, rôle d'exécution sans droit sur le schéma, aucun droit à `PUBLIC` | En revue | [#3](https://github.com/leonardgst/Training-charge/pull/3) |
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
- PR 1.2 : le dépôt de travail est cloné dans WSL (`~/Training-charge`) ; la copie `C:\Training-charge` n'est plus utilisée.
- PR 1.2 : la racine `/` (page d'accueil minimale) et l'administration Django sont routées dès cette PR, pour que les lignes de la recette « la racine redirige vers la connexion » et « l'administration demande une connexion » aient un objet. L'administration garde sa propre page de connexion (`/admin/login/`) ; sa restriction au superutilisateur reste à faire en phase 2 (A6).
- PR 1.2 : le contrôle de santé est dans `suivi/views/sante.py` ; le paquet `views/` accueillera `staff.py` et `joueur.py` ensuite.
- PR 1.2 : aucun réglage de base de données, qui arrivent avec `compose.yaml` et `pytest-django` en PR 1.3. Les tests unitaires utilisent le client de test de Django, initialisé dans `tests/conftest.py`.
- PR 1.2 : Ruff 0.17 vérifie aussi les blocs de code Python des fichiers Markdown, donc `ruff format --check .` couvre la documentation.
- PR 1.3 : ajout de `psycopg[binary]`, pilote Postgres absent du plan ; accord du mainteneur.
- PR 1.3 : en local, `DB_USER` est le rôle de migration et sert à `migrate`, aux tests et à `runserver` ; le rôle d'exécution (`DB_RUNTIME_USER`) n'est exercé que par les tests d'intégration. Les commandes de `CLAUDE.md` restent inchangées, au prix d'un `runserver` local qui ne révèle pas un droit manquant au rôle d'exécution.
- PR 1.3 : le script `docker/initdb/01-roles.sh` configure aussi `template1`, pour que la base de test de `pytest-django` hérite des droits par défaut et de l'absence de droit à `PUBLIC`. Il ne s'exécute qu'à la création du volume : changer un mot de passe impose `docker compose down -v`.
- PR 1.3 : `tests/conftest.py` n'appelle plus `setup_test_environment()`, que `pytest-django` appelle déjà ; mypy reçoit `explicit_package_bases` à cause des deux `conftest.py`.
- PR 1.4 : `check --deploy` n'est pas dans le job `qualite` : les réglages de sécurité de production arrivent en PR 1.5, où il est ajouté. Le job `migrations` se limite à `migrate` et `makemigrations --check`, `generer_demo` n'existant pas encore. Aucun seuil de couverture n'est imposé : `engine/` n'existe pas.
- PR 1.4 : ajout de `pytest-cov`, `pytest-playwright` et `pip-audit` (accord du mainteneur) ; `STATIC_ROOT` ajouté aux réglages pour `collectstatic` ; `docker/ci/creer-roles.sh` réutilise `docker/initdb/01-roles.sh` pour créer les rôles du service Postgres de la CI.
- PR 1.4 : le ruleset sur `main` est créé après le premier passage vert de la CI, pour ne pas exiger des jobs que GitHub n'a jamais vus.
- PR 1.3 : `.claude/settings.json` : règles `deny` étendues à la lecture de `.env` par le shell, `disableAutoMode` retiré et mode par défaut `auto`, à la demande du mainteneur. Le niveau 3 de `CLAUDE.md` reste une règle de comportement : plan et accord avant chaque action sur ses zones, même en auto-mode.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
