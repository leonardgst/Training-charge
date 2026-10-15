# Suivi de charge U19

Application web de suivi de la charge d'entraînement et de l'état de forme des joueurs d'un centre de formation de football (catégorie U19). Après chaque séance, le préparateur saisit trois RPE par joueur ; chaque joueur dépose ses sensations du jour par un lien personnel, sans compte. Un moteur de calcul unique produit la charge du jour, les charges glissantes et des z-scores où chaque joueur n'est comparé qu'à lui-même.

La version 1 est une démonstration sur **données fictives**. Le dépôt est public : aucune donnée réelle, jamais.

> **État** : phase 4 (saisie des séances) en cours. Le moteur de calcul est en place (phase 3) ; côté interface, le préparateur se connecte et se déconnecte. Démonstration en ligne : https://u19-load-tracking.vercel.app

## Documentation

| Document | Contenu |
| --- | --- |
| [Cadrage](docs/00-cadrage.md) | Contexte, décisions et phases du projet |
| [Spécifications](docs/01-specifications.md) | Règles fonctionnelles |
| [Architecture](docs/02-architecture.md) | Choix techniques, rôles Postgres, structure du dépôt |
| [Stratégie de tests](docs/03-strategie-tests.md) | Niveaux de tests, CI, cas à couvrir |
| [Déploiement](docs/deploiement.md) | Neon, Vercel, GitHub et emplacement des secrets |
| [Glossaire](docs/glossaire.md) | Vocabulaire métier |
| [ADR](docs/adr/README.md) | Décisions d'architecture |
| [Phase en cours](docs/phases/phase-04-saisie-des-seances.md) | Fiche de la phase 4 |

## Prérequis

Développement dans **WSL 2 (Ubuntu)**, dépôt dans le système de fichiers Linux (pas sous `/mnt/c/`, ni dans un dossier synchronisé).

- [Docker](https://docs.docker.com/engine/install/) avec le plugin Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) : il installe lui-même Python 3.12 (version épinglée dans `.python-version`)
- Git

## Installation

```bash
git clone https://github.com/leonardgst/Training-charge.git
cd Training-charge
uv sync
uv run playwright install --with-deps chromium
cp .env.example .env
```

`playwright install --with-deps` demande les droits `sudo` pour installer les bibliothèques système de Chromium ; il n'est nécessaire que pour les tests de bout en bout.

Ouvre ensuite `.env` et remplace chaque valeur `remplacer-…` par un mot de passe de ton choix, propre à ton poste. Ce fichier est ignoré par Git : ne le commite jamais.

## Base locale

```bash
docker compose up -d db
uv run --env-file .env python manage.py migrate
```

Le conteneur Postgres 16 crée au premier démarrage deux rôles : un rôle de migration (propriétaire du schéma) et un rôle d'exécution (sans droit de modifier le schéma). Les mots de passe sont lus à la création du volume : pour les changer, il faut réinitialiser la base.

```bash
docker compose down -v && docker compose up -d db   # efface les données locales
```

## Lancer l'application

```bash
uv run --env-file .env python manage.py runserver
```

Puis ouvre http://127.0.0.1:8000/. Un visiteur sans session est renvoyé vers la page de connexion.

Pour se connecter, charge d'abord les données de démonstration dans une base vide :

```bash
uv run --env-file .env python manage.py generer_demo
```

La commande crée trois comptes, `prep_u19`, `prep_u17` (préparateurs) et `admin_demo` (administrateur, pour `/admin/`), et affiche une seule fois leur mot de passe commun ; `--mot-de-passe` permet de le choisir. Les pages du staff sont réservées aux préparateurs : `admin_demo` n'y entre pas.

## Tests et qualité

| Action | Commande |
| --- | --- |
| Lint et format | `uv run ruff check . && uv run ruff format --check .` |
| Typage | `uv run mypy .` |
| Tests unitaires (sans base) | `uv run pytest tests/unit` |
| Tests d'intégration (base locale démarrée) | `uv run --env-file .env pytest tests/integration` |
| Tests de bout en bout | `uv run --env-file .env pytest tests/e2e` |
| Couverture | `uv run --env-file .env pytest tests/unit tests/integration --cov=suivi --cov-branch` |

Les tests d'accès et de calcul tournent sur un vrai Postgres, jamais sur un simulacre. Le dossier `tests/smoke` ne se lance qu'après un déploiement, avec `SMOKE_URL` (voir le [déploiement](docs/deploiement.md)).

## Intégration continue

Chaque PR et chaque fusion dans `main` lancent six jobs : `qualite`, `tests`, `migrations`, `e2e`, `audit` et `build`. Ils sont tous obligatoires : un ruleset interdit de fusionner une PR dont un job échoue, et de pousser directement sur `main`. Chaque PR du dépôt obtient une preview sur une branche Neon dédiée ; la production n'est déployée qu'après l'approbation du mainteneur.

## Conventions

Voir [CLAUDE.md](CLAUDE.md) : branches courtes depuis `main`, Conventional Commits en français, une PR relisible en moins de 20 minutes, tests et documentation dans la même PR que le code.
