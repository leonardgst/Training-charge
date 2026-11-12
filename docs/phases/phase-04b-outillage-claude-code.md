# Phase 4 bis — Outillage de Claude Code

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| Terminée | — | 2026-11-12 | — |

## Objectif

Claude Code travaille seul dans VS Code connecté à WSL 2, de la branche à la CI verte, avec un accès à Neon et à Vercel. Tu ne valides plus que la fusion, la production et les garde-fous ([ADR-0019](../adr/0019-autonomie-de-claude-code.md), [guide](../outillage-claude-code.md)).

Phase ajoutée le 2026-11-12 à ta demande, hors du découpage du cadrage (section 8). Elle ne change pas l'application : pas de version, donc pas de tag. Niveau de collaboration : 4 jusqu'à la fusion de la PR 4b.1, puis 5. Estimation : 4 heures, dont 1 pour tes étapes.

## Livrables

- [x] Poste : VS Code connecté à WSL 2, extension Claude Code
- [x] Jeton GitHub de Claude, limité au dépôt
- [x] Serveurs MCP de Neon et de Vercel, derrière le hook `garde_plateformes.py`
- [x] Réglages du niveau 5, `CLAUDE.md` à jour
- [x] Sous-agents et skills du projet

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 4b.1 | `chore: configurer l'autonomie de Claude Code` | ADR-0019, guide, fiche, réglages, hook des plateformes, `.mcp.json`, `CLAUDE.md` | Tests unitaires du hook et des règles essentielles | Fusionnée | [#36](https://github.com/leonardgst/Training-charge/pull/36) |
| 4b.2 | `chore: ajouter les sous-agents et les skills du projet` | Six sous-agents (`relecteur`, `gardien-acces`, `moteur`, `migrations`, `testeur-e2e`, `ops`), sept skills, guide et `CLAUDE.md` | En-têtes des sous-agents et des skills ; liens de `.claude/` vérifiés | Fusionnée | [#37](https://github.com/leonardgst/Training-charge/pull/37) |
| 4b.3 | `chore: épingler les actions et ajouter Dependabot` | Actions épinglées par empreinte de commit, `.github/dependabot.yml`, pas de preview pour les PR de Dependabot ; menée par Claude, workflows poussés par toi | Test unitaire de l'épinglage ; CI verte | Fusionnée | [#40](https://github.com/leonardgst/Training-charge/pull/40) |
| 4b.4 | `chore: protéger la branche Neon production dans le hook des plateformes` | Identifiant `br-…` de `production` dans le fichier des branches protégées | Aucun (identifiant `br-…` non testé) | Fusionnée | [#41](https://github.com/leonardgst/Training-charge/pull/41) |
| 4b.5 | `chore: compléter la liste des outils Vercel en lecture du hook` | Outils de lecture ajoutés à `VERCEL_LECTURE`, appliqués par le mainteneur | Aucun nouveau test ; couverts par `test_vercel_la_lecture_passe_sans_decision`, paramétré sur la liste | Fusionnée | [#46](https://github.com/leonardgst/Training-charge/pull/46) |
| 4b.6 | `docs:` (vérification, étapes du mainteneur, essai à blanc) | Fiche, journal et guide à jour après les essais du hook et du jeton ; essai à blanc | Aucun (test des liens existant) | Fusionnées | [#47](https://github.com/leonardgst/Training-charge/pull/47), [#48](https://github.com/leonardgst/Training-charge/pull/48), [#49](https://github.com/leonardgst/Training-charge/pull/49), [#50](https://github.com/leonardgst/Training-charge/pull/50) |

## Tes étapes

- [x] Clore la phase 4 : recette avec une séance de 25 joueurs chronométrée (2026-11-12, tag `v0.4.0` ; contrôle de `/connexion/` en production fait le 2026-11-12)
- [x] Mettre en place le poste ([guide, section 2](../outillage-claude-code.md#2-mise-en-place-du-poste))
- [x] Créer le jeton GitHub de Claude (Contents, Pull requests, Issues en écriture ; Actions et Commit statuses en lecture) et le connecter dans WSL ([guide, section 4](../outillage-claude-code.md#4-accès-github))
- [x] Exporter `NEON_PROJECT_ID` dans `~/.bashrc` ; ajouter l'identifiant de la branche `production` au fichier des branches protégées (fait, PR #41)
- [x] Première session : approuver les serveurs du projet, authentifier Neon et Vercel dans `/mcp`
- [x] Vercel : donner à `DJANGO_SECRET_KEY` une valeur Preview distincte de la valeur Production
- [x] Compléter la liste de lecture Vercel du hook (PR [#46](https://github.com/leonardgst/Training-charge/pull/46), appliquée par le mainteneur)
- [x] Activer les alertes et les mises à jour de sécurité Dependabot du dépôt (réglages, sécurité du code), prévues par l'architecture (section 2) et désactivées (activées par le mainteneur le 2026-11-12)

## Critères de fin (Definition of Done)

- [x] PR 4b.1 à 4b.3 fusionnées, CI verte
- [x] `claude mcp list` montre Neon et Vercel connectés, sans variable manquante
- [x] Hook essayé en session réelle : une lecture passe, `run_sql` sur `production` demande l'accord, `delete_branch` sur `production` est refusé
- [x] Déploiement de production vérifié après les fusions de Dependabot : CI de `main` verte sur `373c6fe` (run 43260112213, six jobs) ; déploiement de `5731cc3` (run 43274245639) vert : migrations, déploiement, test de fumée ; version `READY` côté Vercel, aucune erreur d'exécution sur 2 heures, `/connexion/` répond 200 avec sa politique de sécurité du contenu et `Referrer-Policy: same-origin` (serveur MCP de Vercel, 2026-11-12)
- [x] GitHub refuse au jeton de Claude la poussée d'un workflow et l'approbation d'un déploiement de production
- [x] Essai à blanc : la prochaine PR ordinaire (sans fichier réservé) menée par Claude sans intervention, de la branche à la demande de fusion (PR [#49](https://github.com/leonardgst/Training-charge/pull/49), acceptée par le mainteneur le 2026-11-12)
- [x] Documentation à jour : fiche, journal, `CLAUDE.md`, guide

## Décisions prises (liens vers les ADR)

- [ADR-0019](../adr/0019-autonomie-de-claude-code.md) — Autonomie de Claude Code et accès aux plateformes

## Écarts par rapport au plan

- Phase ajoutée hors du cadrage (section 8), à ta demande le 2026-11-12, après l'analyse de l'infrastructure.
- Le cadrage (section 9.1) interdit à Claude de fusionner une PR. L'ADR-0019 le permet après ton accord explicite dans la session.
- PR 4b.3 : titre en `chore:` au lieu de `ci:`, absent de la liste des types de `CLAUDE.md`.
- PR 4b.3 : pas de preview pour les PR de Dependabot. Elles n'ont pas accès aux secrets des Actions, et `deployer` aurait échoué sur chacune ; la CI, sans secret, les vérifie. Leurs commits (`chore: bump …`) et leurs branches (`dependabot/…`) sortent des conventions de `CLAUDE.md`.
- PR 4b.3 : alertes et correctifs de sécurité Dependabot désactivés sur le dépôt, alors que l'architecture (section 2) les prévoit ; leur activation est un réglage du dépôt, ajouté à tes étapes.
- Ranger `VERCEL_TOKEN` et `NEON_API_KEY` dans un environnement GitHub, proposé le 2026-11-12, est abandonné : le jeton de Claude ne peut pas modifier un workflow, et un environnement sans relecteur ne protégerait pas les previews (ADR-0019, conséquences).
- Vérification des critères de fin le 2026-11-12 : un premier `claude mcp list` signale `NEON_PROJECT_ID` manquante ; la session avait démarré avant l'export dans `~/.bashrc`, le serveur Neon a reçu le texte `${NEON_PROJECT_ID}` et refuse tout appel. Après relance de la session, `claude mcp list` donne `neon` et `vercel` connectés sans variable manquante, puis les essais du hook réussissent : `list_branches` passe sans invite ; `run_sql` sur `production` (`br-long-brook-b9cndbjm`) fait apparaître l'invite d'accord, y compris avec une règle `mcp__neon__run_sql` dans `settings.local.json` (le `ask` du hook l'emporte) ; `delete_branch` sur `production` est refusé par le hook. La règle ajoutée par « Yes, and don't ask again » a été retirée.
- Jeton GitHub de Claude, essayé le 2026-11-12 : `POST …/actions/runs/<run>/pending_deployments` refusé en 403 (« Resource not accessible by personal access token ») ; poussée d'un commit modifiant `.github/workflows/ci.yml` sur une branche jetable refusée (« without `workflow` scope »). La branche jetable n'a jamais existé sur GitHub ; son dossier de travail local est supprimé. Les droits sont ceux du guide, sans « Checks » : ce droit n'existe pas pour un jeton fine-grained.
- Essai à blanc : la PR 4b.3 n'a pas été menée sans intervention (le mainteneur a poussé les workflows et guidé Claude). Le critère a été reporté sur la prochaine PR ordinaire menée par Claude, de la branche à la demande de fusion, sans fichier réservé (les PR de Dependabot ne conviennent pas : Claude ne les crée pas, et elles modifient des workflows). La PR [#49](https://github.com/leonardgst/Training-charge/pull/49) a rempli ce rôle, acceptée par le mainteneur le 2026-11-12.
- Liste de lecture Vercel du hook : Claude a proposé le diff, le mainteneur l'a appliqué (`.claude/hooks/` lui est réservé), PR #46.
- Les quatre PR de Dependabot (#42 à #45) ont été fusionnées par le mainteneur en cinq minutes, contre la recommandation d'une fusion à la fois : les déploiements intermédiaires ont été annulés par la concurrence. `create-branch-action` 6.4.0 a été éprouvée par l'aperçu de la PR #49 (run 43272133731), `actions/checkout` 7 et `setup-uv` 10 par le déploiement de `8ddc430` (run 43273230010, approuvé par le mainteneur), puis par celui de `5731cc3`, sans incident. Le run de `373c6fe` (43260555840) a été annulé à l'arrivée de celui de `8ddc430`.
- PR #47 : titre hors du format Conventional Commits (« Docs/verifier fin phase 4b »), et la branche `docs/verifier-fin-phase-4b` a été réutilisée pour la PR #48 après la fusion de la #47 (écarts à la section 5 de `CLAUDE.md`).
- PR 4b.4 (#41) : l'identifiant `br-…` de `production` n'est pas testé ; le seul test du fichier vérifie le nom `production` (écart à la section 6 de `CLAUDE.md`).
- Vercel : le serveur MCP a d'abord refusé l'accès à l'équipe (403) ; `authorize_team_access` et l'approbation du mainteneur ont réglé le cas (ajouté au guide).

## Rétrospective : ce qui a marché, ce qui a coincé

**Ce qui a marché**
- Le hook `garde_plateformes.py` se comporte comme prévu en session réelle : lecture libre, SQL sur `production` soumis à l'accord (le `ask` du hook l'emporte même sur une règle `allow` locale), suppression de `production` refusée.
- Le jeton GitHub restreint : GitHub refuse l'approbation d'un déploiement (403) et la poussée d'un workflow, sans dépendre d'une règle de Claude.
- Le sous-agent `relecteur` a trouvé de vraies erreurs avant fusion : un lien de PR faux (#39 au lieu de #40), des coches contraires aux écarts, une recommandation de fusion des PR de Dependabot inexacte, un run « Déploiement » en file présenté comme en attente d'approbation.
- La PR #49, menée de la branche à la CI verte sans fichier réservé, a servi d'essai à blanc.

**Ce qui a coincé**
- Une session démarrée avant l'export de `NEON_PROJECT_ID` envoie `${NEON_PROJECT_ID}` au serveur Neon, qui refuse tout : le terminal doit être rouvert, et `echo $NEON_PROJECT_ID` vérifié (guide, section 5).
- La réponse « Yes, and don't ask again » à une invite d'un outil MCP ajoute une règle `allow` dans `settings.local.json` ; retirée, et déconseillée dans le guide.
- Les workflows ne peuvent pas être poussés par le jeton de Claude : la PR 4b.3 a donc exigé le mainteneur, et l'essai à blanc a dû être reporté.
- Quatre PR de Dependabot fusionnées d'un coup, alors que leurs aperçus sont sautés : les workflows modifiés n'ont été éprouvés qu'au premier aperçu et au déploiement suivants. Fusionner une à la fois quand une PR modifie un workflow.
- Le droit « Checks » n'existe pas pour un jeton fine-grained, et le serveur MCP de Vercel demande une autorisation d'équipe : une erreur du guide (« Checks ») et une omission (le cas 403 de Vercel), corrigées.
- Comme à la phase 4, la fiche et le journal modifiés par plusieurs PR en parallèle ont causé des conflits de fusion.
