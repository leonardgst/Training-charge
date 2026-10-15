# CLAUDE.md — Suivi de charge U19

## 1. Contexte

Application web de suivi de la charge d'entraînement et de l'état de forme des joueurs d'un centre de formation de football (catégorie U19). Après chaque séance, le préparateur saisit trois RPE par joueur ; chaque joueur dépose ses sensations du jour par un lien personnel, sans compte. Un moteur de calcul unique produit la charge du jour, la CE courte, la CE longue et des z-scores où chaque joueur n'est comparé qu'à lui-même, pour « Forme actuelle » et la fiche joueur. La V1 est une démonstration sur données fictives, et le dépôt est public : aucune donnée réelle, jamais. Le cadrage et ses décisions sont dans [docs/00-cadrage.md](docs/00-cadrage.md) ; le vocabulaire dans [docs/glossaire.md](docs/glossaire.md).

## 2. Stack

Python 3.12 · Django 5.2 LTS · PostgreSQL 16 · gabarits Django, Pico CSS et JavaScript sans framework · Vega-Lite · uv · Ruff · mypy et `django-stubs` · pytest, `pytest-django`, `pytest-cov`, Playwright (Chromium) · GitHub Actions · Vercel Hobby et Neon Free. Détail et justifications : [docs/02-architecture.md](docs/02-architecture.md).

## 3. Commandes

Elles arrivent avec les PR de la phase 1 ; la colonne de droite dit à partir de quand elles fonctionnent. Développement dans WSL 2, dépôt dans le système de fichiers Linux.

| Action | Commande | Disponible à partir de |
| --- | --- | --- |
| Installer | `uv sync` puis `uv run playwright install --with-deps chromium` | PR 1.2 (Playwright : PR 1.4) |
| Démarrer la base locale | `docker compose up -d db` | PR 1.3 |
| Réinitialiser la base locale | `docker compose down -v && docker compose up -d db` (demander d'abord) | PR 1.3 |
| Migrer | `uv run --env-file .env python manage.py migrate` | PR 1.3 |
| Lancer | `uv run --env-file .env python manage.py runserver` | PR 1.3 |
| Lint et format | `uv run ruff check . && uv run ruff format --check .` | PR 1.2 |
| Typage | `uv run mypy .` | PR 1.2 |
| Tests unitaires | `uv run pytest tests/unit` | PR 1.2 |
| Tests d'intégration | `uv run --env-file .env pytest tests/integration` | PR 1.3 |
| Tests de bout en bout | `uv run --env-file .env pytest tests/e2e` | PR 1.4 |

## 4. Structure

Arborescence cible : un dossier n'est créé qu'avec son premier fichier. `config/` (réglages Django, `calcul.toml`) · `suivi/` (modèles, `acces.py`, `calculs.py`, vues, gabarits, statiques) · `engine/` (moteur pur, sans Django) · `tests/` (`unit/`, `integration/`, `e2e/`, `reference/`) · `docs/`. Détail : [docs/02-architecture.md](docs/02-architecture.md), section 7.

## 5. Conventions

- **Langue** : français pour la documentation, les commits et les commentaires. Identifiants techniques en anglais, vocabulaire métier en français sans accent, selon le glossaire (`Joueur`, `Seance`, `charge_jour`, `created_at`, `token_hash`).
- **Code** : format Ruff ; typage strict dans `engine/`. `engine/` n'importe jamais Django. Toute requête d'une vue staff passe par `suivi/acces.py`. La date du jour s'obtient par la fonction unique du projet, jamais par `date.today()`.
- **Branches** : courtes, depuis `main` : `feature/`, `fix/`, `docs/`, `chore/` ; supprimées après fusion. Pas de branche `dev`.
- **Commits** : Conventional Commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`), à l'impératif, en français ; le message décrit exactement le contenu.
- **PR** : une unité cohérente, relisible en moins de 20 minutes ; modèle de PR entièrement rempli ; tests et documentation dans la même PR que le code.

## 6. Tests

Stratégie complète : [docs/03-strategie-tests.md](docs/03-strategie-tests.md).

- Chaque PR contient les tests de ce qu'elle ajoute ou modifie, et la CI doit être verte.
- La PR montre la commande exécutée et sa sortie. Une correction de bug commence par un test qui échoue.
- Tests d'accès et de calcul sur un vrai Postgres, jamais sur un simulacre.
- Seuils de couverture : 95 % des branches de `engine/`, 90 % de la validation des saisies.
- **Interdit** : supprimer, désactiver ou assouplir un test sans accord explicite du mainteneur ; recopier une valeur attendue depuis la sortie du code ; modifier `tests/reference/**/attendu.csv` ou `provenance.md`, réservés au mainteneur ; utiliser `xfail` ailleurs que pour les tests du moteur introduits avant leur implémentation (phase 3, toujours `strict=True`).

## 7. Collaboration

- **Niveau 4, par défaut** : tu travailles sur une branche, tu commites, tu pousses la branche et tu ouvres la PR avec `gh`. Le mainteneur relit et fusionne.
- **Niveau 3** : aucune phase n'y est plus en cours. Il ne s'applique que si le mainteneur le redemande pour une PR : plan d'abord, puis accord avant chaque action, session en mode Manuel. La phase 3 (moteur) a été relevée de 3 à 4 par le mainteneur le 2026-10-15, et la phase 4 est entièrement au niveau 4, accès et migrations compris (même date).
- **Jamais** : pousser sur `main`, fusionner une PR, forcer une poussée, lire `.env`, lancer la CLI Vercel ou Neon, agir sur une base déployée, créer une ressource payante.
- **Avec accord seulement** : supprimer un fichier, ajouter une dépendance, réinitialiser la base locale, modifier un workflow de CI.
- Le dépôt est poussé sur GitHub avant chaque session autonome.

## 8. Documentation

- Une décision non triviale donne une ADR dans `docs/adr/`. Une question tranchée met à jour, dans la même PR, les spécifications, l'ADR et les tests.
- La fiche de la phase en cours est mise à jour à chaque fusion. Chaque session ajoute une ligne datée dans [docs/journal.md](docs/journal.md).
- Ne jamais citer un fichier, une section ou une route qui n'existe pas : un test vérifie les liens.
- Clôture de phase : section 10.3 du cadrage (fiche « Terminée », `CHANGELOG.md`, tag annoté, journal, ce fichier pointé vers la phase suivante).
- Rien n'est créé « pour plus tard » ; aucun contenu de générateur ne reste en place ; aucun document n'est supprimé.

## 9. Phase en cours

Phase 5 — Questionnaire joueur : [docs/phases/phase-05-questionnaire-joueur.md](docs/phases/phase-05-questionnaire-joueur.md). Elle commence quand la phase 4 est fermée (recette du mainteneur, tag `v0.4.0`) et que sa fiche est validée par le mainteneur, avec quatre points à trancher : niveau de collaboration (la fiche propose 3 pour les PR 5.1 et 5.2, qui touchent au jeton), `Referrer-Policy` de la page du lien joueur, dépendance du QR code, recette sur un vrai téléphone.

## 10. Interdits et pièges connus

Repris de l'annexe A du cadrage et des choix de la phase 0 :

- **Z-score** : la référence s'arrête à la veille, jamais le point courant. Un écart-type nul donne l'état `NON_CALCULABLE`, jamais une division.
- **Calendrier** : une ligne par joueur et par jour, jours sans séance à 0, jamais une ligne par participation.
- **Brouillons** : une séance en brouillon n'entre dans aucun calcul ; l'adaptateur ne lit que les séances validées et les données datées au plus tard de la date de calcul.
- **Score de sensations** : normaliser chaque indicateur par ses bornes avant d'agréger ; ne jamais additionner des unités différentes.
- **Contraintes** : chaque plage (RPE, durée, bornes d'indicateur) est vérifiée à la saisie et en base.
- **Accès** : aucun droit à `PUBLIC`, aucune fonction `SECURITY DEFINER`, aucune vue sans `security_invoker`. Le jeton joueur n'est jamais stocké ni journalisé en clair.
- **Django** : `is_staff` ouvre l'administration ; un préparateur ne l'a jamais.
- **Tests de bout en bout** : `DJANGO_ALLOW_ASYNC_UNSAFE` n'est activé que pour Playwright.
- **Neon** : le pooler fonctionne par transaction, donc pas de curseur côté serveur ni de connexion persistante en production.
- **Nombres** : comparer avec une tolérance, jamais après arrondi.
- **Vega** : son évaluateur d'expressions par défaut est incompatible avec une politique de sécurité du contenu stricte (phase 6).
- **Referrer-Policy** : `no-referrer` fait envoyer `Origin: null` sur chaque formulaire POST, que le contrôle CSRF de Django refuse ; le site est en `same-origin`, et la page du lien joueur (phase 5) doit en tenir compte.
- **Méthode** : pas de dossier vide, pas de commit au message inexact, pas de branche dont le nom ment sur son contenu.
