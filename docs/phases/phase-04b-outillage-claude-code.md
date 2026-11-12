# Phase 4 bis — Outillage de Claude Code

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | — | — | — |

## Objectif

Claude Code travaille seul dans VS Code connecté à WSL 2, de la branche à la CI verte, avec un accès à Neon et à Vercel. Tu ne valides plus que la fusion, la production et les garde-fous ([ADR-0019](../adr/0019-autonomie-de-claude-code.md), [guide](../outillage-claude-code.md)).

Phase ajoutée le 2026-11-12 à ta demande, hors du découpage du cadrage (section 8). Elle ne change pas l'application : pas de version, donc pas de tag. Niveau de collaboration : 4 jusqu'à la fusion de la PR 4b.1, puis 5. Estimation : 4 heures, dont 1 pour tes étapes.

## Livrables

- [ ] Poste : VS Code connecté à WSL 2, extension Claude Code
- [ ] Jeton GitHub de Claude, limité au dépôt
- [ ] Serveurs MCP de Neon et de Vercel, derrière le hook `garde_plateformes.py`
- [ ] Réglages du niveau 5, `CLAUDE.md` à jour
- [ ] Sous-agents et skills du projet

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 4b.1 | `chore: configurer l'autonomie de Claude Code` | ADR-0019, guide, fiche, réglages, hook des plateformes, `.mcp.json`, `CLAUDE.md` | Tests unitaires du hook et des règles essentielles | En revue | — |
| 4b.2 | `chore: ajouter les sous-agents et les skills du projet` | Six sous-agents, six skills | Format des sous-agents et des skills | Prévue | — |
| 4b.3 | `ci: épingler les actions et ajouter Dependabot` | Actions épinglées par empreinte de commit, `.github/dependabot.yml` ; menée par Claude, workflows poussés par toi | CI verte | Prévue | — |

## Tes étapes

- [ ] Clore la phase 4 : recette avec une séance de 25 joueurs chronométrée
- [ ] Mettre en place le poste ([guide, section 2](../outillage-claude-code.md#2-mise-en-place-du-poste))
- [ ] Créer le jeton GitHub de Claude et le connecter dans WSL ([guide, section 4](../outillage-claude-code.md#4-accès-github))
- [ ] Exporter `NEON_PROJECT_ID` dans `~/.bashrc` ; ajouter l'identifiant de la branche `production` au fichier des branches protégées
- [ ] Première session : approuver les serveurs du projet, authentifier Neon et Vercel dans `/mcp`
- [ ] Vercel : donner à `DJANGO_SECRET_KEY` une valeur Preview distincte de la valeur Production
- [ ] Compléter la liste de lecture Vercel du hook

## Critères de fin (Definition of Done)

- [ ] PR 4b.1 à 4b.3 fusionnées, CI verte
- [ ] `claude mcp list` montre Neon et Vercel connectés, sans variable manquante
- [ ] Hook essayé en session réelle : une lecture passe, `run_sql` sur `production` demande l'accord, `delete_branch` sur `production` est refusé
- [ ] GitHub refuse au jeton de Claude la poussée d'un workflow et l'approbation d'un déploiement de production
- [ ] Essai à blanc : la PR 4b.3 menée par Claude sans intervention jusqu'à la demande de fusion, hors poussée des workflows
- [ ] Documentation à jour : fiche, journal, `CLAUDE.md`

## Décisions prises (liens vers les ADR)

- [ADR-0019](../adr/0019-autonomie-de-claude-code.md) — Autonomie de Claude Code et accès aux plateformes

## Écarts par rapport au plan

- Phase ajoutée hors du cadrage (section 8), à ta demande le 2026-11-12, après l'analyse de l'infrastructure.
- Le cadrage (section 9.1) interdit à Claude de fusionner une PR. L'ADR-0019 le permet après ton accord explicite dans la session.
- Ranger `VERCEL_TOKEN` et `NEON_API_KEY` dans un environnement GitHub, proposé le 2026-11-12, est abandonné : le jeton de Claude ne peut pas modifier un workflow, et un environnement sans relecteur ne protégerait pas les previews (ADR-0019, conséquences).
