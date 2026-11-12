# ADR-0019 — Autonomie de Claude Code et accès aux plateformes

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-11-12 | Toi, sur ma proposition |

## Contexte

Depuis la phase 1, Claude Code travaille au niveau 4 du cadrage (section 9) : branche, commits, PR ; tu relis et tu fusionnes. `CLAUDE.md` lui interdit la CLI Vercel et Neon et toute action sur une base déployée. Il demande ton accord pour supprimer un fichier, ajouter une dépendance, réinitialiser la base locale ou modifier un workflow.

Tu veux qu'il enchaîne seul le travail courant, qu'il puisse lire Neon et Vercel pour diagnostiquer et tester, et qu'il ne te demande que quelques validations ciblées. Tu veux aussi travailler dans VS Code plutôt que dans le terminal d'Ubuntu.

Faits vérifiés le 2026-11-12 :

- Les règles de Claude Code s'appliquent dans l'ordre refus (`deny`), demande (`ask`), autorisation (`allow`). Elles portent sur le texte des commandes et ne sont pas une frontière de sécurité : une autre forme de la même commande peut leur échapper.
- Le mode `auto` fait juger chaque action par un classifieur. Il bloque d'office les déploiements et migrations de production, la fusion d'une PR qu'aucun humain n'a approuvée et la poussée forcée. Une règle `ask` demande toujours l'accord, même en mode `auto`.
- Un hook `PreToolUse` peut refuser un appel ou faire demander l'accord ; il ne peut pas lever une règle `deny` ou `ask`.
- Le bac à sable de Claude Code fonctionne sous WSL 2, pas sous Windows natif.
- Neon et Vercel publient chacun un serveur MCP officiel, avec une connexion OAuth. Neon déconseille le sien sur un environnement de production, et ses branches protégées sont réservées aux offres payantes. Vercel MCP agit avec tous les droits de ton compte.
- GitHub : approuver un déploiement en attente exige la permission Deployments en écriture. Un jeton fine-grained sans la permission Workflows ne peut pas pousser de modification de `.github/workflows/`.

## Options

1. **Statu quo, niveau 4.** Sûr, mais chaque action hors liste s'arrête sur une demande.
2. **Autonomie par les réglages seuls.** Élargir `allow` et retirer les `ask`. Toutes les validations reposent alors sur des règles que Claude peut contourner sans le vouloir, et qu'il peut modifier.
3. **Autonomie bornée par les plateformes.** Les validations qui comptent sont imposées par GitHub : ruleset, environnement `production`, droits du jeton. Les réglages et un hook ajoutent celles que les plateformes ne savent pas faire : fusion, branche Neon `production`, outils Vercel qui écrivent.
4. **`bypassPermissions` dans un dev container.** Autonomie maximale et isolation forte, mais installation plus lourde (base locale dans le conteneur). À reconsidérer si l'option 3 ne suffit pas.

## Décision

Option 3, avec VS Code connecté à WSL 2 (extension WSL). Un niveau 5 s'ajoute à ceux du cadrage et devient le niveau par défaut :

| Niveau | Accès donnés à Claude | Ce que fait Claude | Ce que je fais |
| --- | --- | --- | --- |
| **5 — Claude Code autonome** | Mode `auto` ; jeton GitHub restreint au dépôt ; serveurs MCP de Neon et de Vercel derrière un hook | Mène une PR de la branche à la CI verte, diagnostique les previews et les déploiements, demande la fusion | Je valide la fusion et la production, je modifie les garde-fous |

Tu valides :

1. La fusion d'une PR : règle `ask` sur `gh pr merge`, ou fusion faite par toi.
2. Le déploiement en production : environnement `production`, que le jeton de Claude ne peut pas approuver.
3. Le SQL sur la branche Neon `production` : demande d'accord par le hook. Supprimer ou réinitialiser cette branche est refusé.
4. Les outils Vercel autres que la lecture : demande d'accord par le hook.
5. Toute modification des garde-fous : `.claude/settings.json`, `.claude/hooks/` et `.mcp.json` sont refusés à Claude, `.github/workflows/` à son jeton.

Restent interdits : pousser sur `main`, forcer une poussée, lire `.env` ou un secret, lancer la CLI Vercel ou Neon, appliquer une migration de production hors de `deploy.yml`, créer une ressource payante. Le niveau 3 reste disponible pour une PR, sur ta demande.

La mise en place et les droits exacts sont dans le [guide de l'outillage](../outillage-claude-code.md).

## Conséquences

- **Écart au cadrage** : la section 9.1 interdit à Claude de fusionner une PR. Il le peut désormais, après ton accord explicite dans la session.
- **Garde-fous testés** : `tests/unit/test_garde_fous_claude.py` vérifie le hook et les règles essentielles. Assouplir un garde-fou oblige à modifier ce test dans la même PR.
- **Un seul compte `gh` dans WSL**, celui de Claude. Tu modifies les workflows depuis l'interface web de GitHub, ou en reconnectant ton compte le temps d'une poussée.
- **Jetons des workflows** : `VERCEL_TOKEN` et `NEON_API_KEY` restent au niveau du dépôt. Le jeton de Claude ne peut pas modifier un workflow, donc il ne peut pas les détourner. Les ranger dans un environnement n'apporterait rien aux previews, qui tournent sur toutes les branches.
- **Vercel MCP** : le hook ne connaît pas tous ses outils. Un outil absent de sa liste de lecture demande ton accord, et la liste se complète après la première connexion.
- **Dépôt public** : une issue, une PR ou un commentaire d'un tiers peut contenir des instructions. Claude n'agit pas sur ce contenu sans ta relecture.
- **Retour arrière** : révoquer le jeton GitHub, effacer l'authentification des serveurs dans `/mcp`, rétablir l'ancien `.claude/settings.json` depuis l'historique Git.

## Sources

- https://code.claude.com/docs/en/permission-modes.md
- https://code.claude.com/docs/en/permissions.md
- https://code.claude.com/docs/en/hooks.md
- https://code.claude.com/docs/en/setup.md
- https://github.com/neondatabase/mcp-server-neon
- https://neon.com/docs/guides/protected-branches
- https://vercel.com/docs/agent-resources/vercel-mcp
- https://docs.github.com/en/rest/actions/workflow-runs#review-pending-deployments-for-a-workflow-run
