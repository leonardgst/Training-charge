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
- [x] Réglages du niveau 5, `CLAUDE.md` à jour
- [x] Sous-agents et skills du projet

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 4b.1 | `chore: configurer l'autonomie de Claude Code` | ADR-0019, guide, fiche, réglages, hook des plateformes, `.mcp.json`, `CLAUDE.md` | Tests unitaires du hook et des règles essentielles | Fusionnée | [#36](https://github.com/leonardgst/Training-charge/pull/36) |
| 4b.2 | `chore: ajouter les sous-agents et les skills du projet` | Six sous-agents (`relecteur`, `gardien-acces`, `moteur`, `migrations`, `testeur-e2e`, `ops`), sept skills, guide et `CLAUDE.md` | En-têtes des sous-agents et des skills ; liens de `.claude/` vérifiés | Fusionnée | [#37](https://github.com/leonardgst/Training-charge/pull/37) |
| 4b.3 | `chore: épingler les actions et ajouter Dependabot` | Actions épinglées par empreinte de commit, `.github/dependabot.yml`, pas de preview pour les PR de Dependabot ; menée par Claude, workflows poussés par toi | Test unitaire de l'épinglage ; CI verte | En revue | — |

## Tes étapes

- [x] Clore la phase 4 : recette avec une séance de 25 joueurs chronométrée (2026-11-12, tag `v0.4.0` ; production déployée le même jour)
- [ ] Mettre en place le poste ([guide, section 2](../outillage-claude-code.md#2-mise-en-place-du-poste))
- [ ] Créer le jeton GitHub de Claude et le connecter dans WSL ([guide, section 4](../outillage-claude-code.md#4-accès-github))
- [ ] Exporter `NEON_PROJECT_ID` dans `~/.bashrc` ; ajouter l'identifiant de la branche `production` au fichier des branches protégées
- [ ] Première session : approuver les serveurs du projet, authentifier Neon et Vercel dans `/mcp`
- [ ] Vercel : donner à `DJANGO_SECRET_KEY` une valeur Preview distincte de la valeur Production
- [ ] Compléter la liste de lecture Vercel du hook
- [ ] Activer les alertes et les mises à jour de sécurité Dependabot du dépôt (réglages, sécurité du code), prévues par l'architecture (section 2) et désactivées

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
- PR 4b.3 : titre en `chore:` au lieu de `ci:`, absent de la liste des types de `CLAUDE.md`.
- PR 4b.3 : pas de preview pour les PR de Dependabot. Elles n'ont pas accès aux secrets des Actions, et `deployer` aurait échoué sur chacune ; la CI, sans secret, les vérifie. Leurs commits (`chore: bump …`) et leurs branches (`dependabot/…`) sortent des conventions de `CLAUDE.md`.
- PR 4b.3 : alertes et correctifs de sécurité Dependabot désactivés sur le dépôt, alors que l'architecture (section 2) les prévoit ; leur activation est un réglage du dépôt, ajouté à tes étapes.
- Ranger `VERCEL_TOKEN` et `NEON_API_KEY` dans un environnement GitHub, proposé le 2026-11-12, est abandonné : le jeton de Claude ne peut pas modifier un workflow, et un environnement sans relecteur ne protégerait pas les previews (ADR-0019, conséquences).
