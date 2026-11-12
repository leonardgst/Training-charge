---
name: livrer-pr
description: Livre une PR selon les conventions du projet, de la branche à la CI verte, puis demande la fusion. À utiliser pour ouvrir ou mettre à jour toute PR.
argument-hint: "[numéro de la PR dans la fiche de phase, par exemple 5.1]"
---

# Livrer une PR

PR visée : $ARGUMENTS. Son titre, son contenu et ses tests sont dans la fiche de la phase en cours (`CLAUDE.md`, section 9).

## 1. Branche

`git fetch origin main`, puis `git switch -c <type>/<nom-court> origin/main`. Le type (`feature`, `fix`, `docs`, `chore`) et le nom disent ce que contient la branche.

## 2. Travail

- Une correction de bug commence par un test qui échoue : garde sa sortie pour la PR.
- Pour un calcul, une migration ou un parcours navigateur, délègue aux agents `moteur`, `migrations` ou `testeur-e2e`.
- Commits Conventional Commits en français, à l'impératif, dont le message décrit exactement le contenu ; trailer `Co-Authored-By` de Claude.

## 3. Vérifications locales

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run pytest tests/unit -q
docker compose up -d db
uv run --env-file .env pytest tests/integration -q   # si le code ou la base change
uv run --env-file .env pytest tests/e2e -q           # si une page change
```

## 4. Documentation dans la même PR

- Fiche de la phase : ligne de la PR à « En revue », puis lien une fois la PR ouverte ; écarts au plan s'il y en a.
- Une ligne datée dans `docs/journal.md` pour la session.
- Une ADR pour toute décision non triviale (skill `nouvelle-adr`).
- Aucun lien vers un fichier absent : `uv run pytest tests/unit/test_liens_documentation.py -q`.

## 5. Relecture

Agent `relecteur` sur la branche ; agent `gardien-acces` en plus si la PR touche une vue, une URL, un middleware, `suivi/acces.py`, une migration ou les réglages. Corrige chaque point bloquant avant d'ouvrir la PR.

## 6. PR

`git push -u origin <branche>`, puis `gh pr create` avec le modèle `.github/pull_request_template.md` rempli en entier : quoi, pourquoi (lien vers la fiche), commandes exécutées avec leur sortie, ce qui n'est pas fait, cases de vérification.

## 7. CI et preview

- `gh pr checks <numéro> --watch`. Si un job est rouge : agent `ops` (skill `diagnostic`), correction, nouvelle poussée, jusqu'au vert.
- Si la PR change une page : skill `recette-preview`.

## 8. Fusion

Demande la fusion au mainteneur avec un résumé de trois lignes et l'état de la CI. `gh pr merge` demande toujours son accord : ne le contourne jamais. Après la fusion, la fiche passe la PR à « Fusionnée » dans la PR suivante.
