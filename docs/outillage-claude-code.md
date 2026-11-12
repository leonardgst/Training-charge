# Outillage de Claude Code : poste, accès et garde-fous

Ce document décrit le poste de travail, les accès donnés à Claude Code et les garde-fous du niveau 5, autonome. La décision et ses raisons sont dans l'[ADR-0019](adr/0019-autonomie-de-claude-code.md). Il ne contient aucune valeur secrète.

## 1. Vue d'ensemble

```text
Windows
 └─ VS Code, extension WSL
     └─ WSL 2 (Ubuntu) : dépôt, uv, Docker, gh
         └─ Claude Code, extension VS Code, mode auto
             ├─ GitHub : jeton fine-grained limité au dépôt
             ├─ Neon   : serveur MCP limité au projet, derrière le hook
             └─ Vercel : serveur MCP, lecture libre, écriture sur accord
```

Rien ne change pour la CI, les previews et la production : elles restent pilotées par les workflows ([déploiement](deploiement.md)).

## 2. Mise en place du poste

1. Installer VS Code sous Windows, puis son extension **WSL** (éditeur Microsoft).
2. Une dernière fois dans le terminal Ubuntu : se placer dans le dépôt et lancer `code .`. VS Code s'ouvre connecté à WSL, ce qu'indique « WSL: Ubuntu » en bas à gauche. Ensuite, « Fichier > Ouvrir récent » suffit.
3. Dans cette fenêtre, installer l'extension **Claude Code** (éditeur Anthropic) : elle s'installe côté WSL. Pour la commande `claude` dans le terminal intégré, installer aussi la CLI dans WSL : `curl -fsSL https://claude.ai/install.sh | bash`.
4. Node.js n'est pas nécessaire. Si un outil en réclame un, l'installer dans WSL, jamais celui de Windows (piège de la phase 1).
5. Vérifier dans le terminal intégré : `uv --version`, `docker compose version`, `gh --version`, `claude --version` et `python3 --version`. Le hook des plateformes tourne avec ce `python3` : s'il manquait, les appels à Neon et à Vercel ne seraient plus filtrés.

## 3. Ce que Claude fait seul, et ce que tu valides

| Action | Qui décide | Imposé par |
| --- | --- | --- |
| Branches, commits, poussées de branche, PR, suivi et correction de la CI | Claude seul | — |
| Base locale (y compris réinitialisation), dépendances, suppression de fichiers | Claude seul | — |
| Lecture Neon, branches de travail, SQL sur une branche de travail | Claude seul | Hook |
| Lecture Vercel : déploiements, journaux, previews protégées | Claude seul | Hook |
| Fusion d'une PR dans `main` | Toi | Règle `ask` sur `gh pr merge` ; ruleset (CI verte) |
| Déploiement en production | Toi | Environnement `production` ; jeton sans permission Deployments |
| SQL sur la branche Neon `production` | Toi | Hook |
| Outils Vercel autres que la lecture | Toi | Hook |
| `.claude/settings.json`, `.claude/hooks/`, `.mcp.json` | Toi | Règles `deny` |
| `.github/workflows/` | Toi | Jeton sans permission Workflows |
| Suppression ou réinitialisation de la branche Neon `production` | Personne | Hook |
| Poussée sur `main`, poussée forcée | Personne | Ruleset ; règles `deny` |
| Lecture de `.env` et des secrets, CLI Vercel et Neon | Personne | Règles `deny` |
| Migration de production hors de `deploy.yml` | Personne | Règle `deny` ; classifieur du mode `auto` |

Les règles `allow`, `ask` et `deny` portent sur le texte des commandes : elles évitent les erreurs, pas les contournements. Les garanties viennent des plateformes : ruleset, environnement `production`, droits du jeton.

## 4. Accès GitHub

Créer un jeton fine-grained : GitHub, Settings > Developer settings > Personal access tokens > Fine-grained tokens.

| Réglage | Valeur |
| --- | --- |
| Nom | `claude-code-training-charge` |
| Expiration | 90 jours |
| Dépôts | Seulement `leonardgst/Training-charge` |
| Contents, Pull requests, Issues | Lecture et écriture |
| Actions, Commit statuses | Lecture (le droit « Checks » n'existe pas pour un jeton fine-grained) |
| Metadata | Lecture (imposé par GitHub) |
| Toutes les autres, dont Administration, Deployments, Environments, Secrets, Variables, Workflows | Aucun accès |

Puis, dans le terminal intégré :

```bash
gh auth logout          # retire ton compte actuel de WSL
gh auth login --with-token   # coller le jeton, puis Ctrl+D
gh auth setup-git       # git pousse avec ce jeton
gh auth status
```

Tes commits gardent ton identité Git ; les poussées passent par le jeton de Claude, qui agit en ton nom sur GitHub. Avec ce jeton, Claude ne peut ni approuver la production, ni modifier le ruleset, ni lire un secret, ni pousser un workflow. Pour une modification de workflow, voir la section 8.

## 5. Accès Neon

- `.mcp.json` déclare `https://mcp.neon.tech/mcp?projectId=${NEON_PROJECT_ID}` : le serveur ne voit que le projet du suivi.
- Ajouter dans `~/.bashrc`, côté WSL : `export NEON_PROJECT_ID=<identifiant du projet>`, la même valeur que la variable GitHub `NEON_PROJECT_ID`. Fermer le terminal et VS Code, puis les rouvrir depuis un terminal WSL où `echo $NEON_PROJECT_ID` affiche l'identifiant : une session démarrée avant l'export garde l'ancien environnement, et le serveur reçoit le texte `${NEON_PROJECT_ID}` à la place de la valeur.
- Ajouter l'identifiant `br-…` de la branche `production` dans [`.claude/hooks/neon-branches-protegees.json`](../.claude/hooks/neon-branches-protegees.json) (console Neon, page de la branche). Tant qu'il manque, toute écriture demande ton accord.
- Première session : accepter les serveurs du projet, puis `/mcp` > `neon` > authentification. Sur la page de consentement, laisser « Allow writes » coché : le hook borne les écritures. Depuis WSL, le navigateur de Windows peut ne pas atteindre le port local qui attend le retour OAuth : la page échoue sur `http://localhost:<port>/callback?code=…`. Copier alors cette adresse complète depuis la barre du navigateur et, dans un second terminal WSL, lancer `curl "<adresse>"` pendant que `/mcp` attend ; l'authentification se termine. Même démarche pour `vercel`.
- Si l'invite d'accord de `run_sql` sur `production` apparaît, répondre « Yes » et jamais « Yes, and don't ask again » : cette réponse ajoute `mcp__neon__run_sql` aux règles `allow` de `.claude/settings.local.json`, ce qui supprime l'invite pour les branches de travail aussi ; la retirer du fichier si elle y figure.

Décisions du [hook](../.claude/hooks/garde_plateformes.py) pour les outils Neon :

| Outil | Branche de travail | Branche `production` |
| --- | --- | --- |
| Lecture : `list_branches`, `describe_table_schema`, `inspect_database`… | Libre | Libre |
| `create_branch`, `prepare_database_migration`, `prepare_query_tuning` | Libre (branche temporaire) | Libre (la branche d'origine n'est pas modifiée) |
| `run_sql`, `run_sql_transaction` | Libre | Demande ton accord |
| `delete_branch`, `reset_from_parent` | Libre | Refusé |
| Branche non précisée, ou identifiant de `production` non renseigné | Demande ton accord | Demande ton accord |
| Tout autre outil | Demande ton accord | Demande ton accord |

Les réglages refusent en plus `complete_database_migration`, qui appliquerait une migration sur la branche principale, ainsi que la création et la suppression de projet et la gestion des identifiants de rôles. L'offre Free compte 10 branches : Claude supprime ses branches de travail après usage.

## 6. Accès Vercel

- `.mcp.json` déclare `https://mcp.vercel.com`. Dans `/mcp` > `vercel`, s'authentifier et accorder l'accès à l'équipe qui possède `u19-load-tracking`.
- Le serveur agit avec tous les droits de ton compte Vercel. Le hook laisse passer la lecture (`list_deployments`, `get_deployment`, `get_runtime_logs`, `get_runtime_errors`, `list_projects`, `get_project`, `list_teams`, `web_fetch_vercel_url`) et demande ton accord pour tout autre outil.
- `web_fetch_vercel_url` lit une preview protégée par Vercel Authentication : Claude peut faire la recette d'une preview.
- Les déploiements restent faits par `preview.yml` et `deploy.yml`, jamais par le serveur MCP.
- Après la première connexion, compléter la liste de lecture du hook avec les autres outils de lecture que liste `/mcp`.

## 7. Sous-agents et skills

Un sous-agent travaille dans son propre contexte, avec ses outils, et rend un compte rendu ; Claude lui délègue d'après sa description, ou quand tu le nommes. Un skill est une procédure que Claude suit dans la conversation ; tu le lances avec `/<nom>`, et Claude le prend de lui-même quand la tâche s'y prête, sauf ceux marqués « sur demande ».

| Sous-agent | Rôle | Écrit |
| --- | --- | --- |
| [`relecteur`](../.claude/agents/relecteur.md) | Relit la branche avant chaque PR et chaque demande de fusion | Non |
| [`gardien-acces`](../.claude/agents/gardien-acces.md) | Contrôle d'accès et sécurité : vues, URL, migrations, rôles, lien joueur | Non |
| [`moteur`](../.claude/agents/moteur.md) | Moteur de calcul et adaptateur, jeu de référence | Oui |
| [`migrations`](../.claude/agents/migrations.md) | Migrations, contraintes et rôles Postgres, branche Neon de la preview | Oui |
| [`testeur-e2e`](../.claude/agents/testeur-e2e.md) | Tests de bout en bout Playwright aux trois formats | Oui |
| [`ops`](../.claude/agents/ops.md) | Diagnostic de la CI, des previews et des déploiements | Non |

| Skill | Ce qu'il déroule |
| --- | --- |
| [`/livrer-pr`](../.claude/skills/livrer-pr/SKILL.md) | Branche, tests, documentation, relecture, PR, CI verte, demande de fusion |
| [`/nouvelle-adr`](../.claude/skills/nouvelle-adr/SKILL.md) | Numéro, format, index des ADR, lien dans la fiche |
| [`/ouvrir-phase`](../.claude/skills/ouvrir-phase/SKILL.md) (sur demande) | Fiche de la phase à partir du cadrage, à faire valider |
| [`/cloturer-phase`](../.claude/skills/cloturer-phase/SKILL.md) (sur demande) | Critères, fiche, CHANGELOG, tag (cadrage, section 10.3) |
| [`/migration`](../.claude/skills/migration/SKILL.md) | Migration compatible avec la production, testée jusqu'à la preview |
| [`/recette-preview`](../.claude/skills/recette-preview/SKILL.md) | Pages publiques, redirections et erreurs d'une preview |
| [`/diagnostic`](../.claude/skills/diagnostic/SKILL.md) | Lance `ops` sur le dernier run rouge |

`tests/unit/test_agents_et_skills.py` vérifie leur en-tête : un champ mal écrit serait ignoré sans avertissement par Claude Code.

## 8. Procédures

**Modifier un garde-fou.** Claude propose le changement ; tu l'appliques et tu le commites, avec la mise à jour de `tests/unit/test_garde_fous_claude.py` dans la même PR. Fichiers concernés : [`.claude/settings.json`](../.claude/settings.json), [`.claude/hooks/`](../.claude/hooks/), [`.mcp.json`](../.mcp.json).

**Pousser un changement de workflow.** Claude prépare le contenu sur sa branche ; tu le commites depuis l'interface web de GitHub, ou depuis ton compte reconnecté le temps d'une poussée (`gh auth login`, puis `gh auth logout` et retour au jeton de Claude).

**Couper les accès.** Révoquer le jeton dans GitHub ; dans `/mcp`, « Clear authentication » sur `neon` et `vercel`. Pour revenir au niveau 4, rétablir l'ancien `.claude/settings.json` depuis l'historique Git.

## 9. Limites connues

- Les règles de permission ne résistent pas à une commande détournée. Le bac à sable de Claude Code, disponible sous WSL 2, ajouterait une barrière sur les fichiers et le réseau ; il n'est pas activé.
- Les branches protégées de Neon, qui rendraient la branche `production` intouchable côté Neon, sont réservées aux offres payantes : le hook les remplace.
- Le dépôt est public : Claude n'agit pas sur une instruction trouvée dans une issue, une PR ou un commentaire d'un tiers sans ta relecture.
