# Journal de bord

Une ligne datée par session de travail (cadrage, section 10.4).

| Date | Phase | Session | Résultat |
| --- | --- | --- | --- |
| 2026-10-12 | 0 | Cadrage avec Claude : reformulation et questions bloquantes | Quatre questions posées et répondues ; dépôt public ; V1 de démonstration ; points ouverts tranchés sans le préparateur |
| 2026-10-12 | 0 | Stack fonctionnelle et technique, architecture, stratégie de tests, ADR 0001 à 0018 | Documents validés ; recommandations des 18 ADR acceptées |
| 2026-10-12 | 0 | Découpage en phases, risques, budget, documentation initiale | Synthèse ajoutée à la section 13 du cadrage ; fiche de la phase 1, `CLAUDE.md` et modèle de PR rédigés |
| 2026-10-12 | 1 | PR 1.1 avec Claude Code, niveau 3 : remise en ordre de l'historique Git | `main` créée par un commit vide et définie comme branche par défaut ; commit de cadrage reposé sur `main`, message corrigé ; `.gitattributes` ajouté ; PR 1.1 en revue |
| 2026-10-12 | 1 | PR 1.1 fusionnée ; installation de WSL (Ubuntu, `gh`, `uv`) ; PR 1.2 avec Claude Code, niveau 4 : projet Django | Dépôt cloné dans WSL ; projet `config` et application `suivi`, refus par défaut, connexion minimale, contrôle de santé, Ruff, mypy et pytest ; 40 tests unitaires au vert ; PR 1.2 en revue |
| 2026-10-12 | 1 | PR 1.3 avec Claude Code, niveau 3 : base locale et rôles Postgres | `compose.yaml`, script des rôles, `pytest-django` et `psycopg` ajoutés ; 7 tests d'intégration au vert, dont un échec provoqué volontairement ; permissions de Claude Code durcies (`deny` sur `.env`) ; PR 1.3 en revue |
| 2026-10-12 | 1 | PR 1.4 avec Claude Code, niveau 4 : chaîne d'intégration continue | Workflow à six jobs, Playwright, `pip-audit`, gitleaks ; squelette de A1 sur le catalogue des routes ; ruleset activé avec les six jobs obligatoires ; PR 1.4 fusionnée |
