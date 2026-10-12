# ADR-0001 — Dépôt public et protection de `main`

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi |

## Contexte

Le cadrage demande un dépôt privé, un budget de 0 € et une branche `main` protégée par une CI obligatoire (section 9.1 ; annexe A, n° 16). Avec un compte GitHub gratuit, la protection de branche et les rulesets ne sont disponibles que sur les dépôts publics, et les dépôts privés n'ont que 2 000 minutes de CI par mois. Dans un dépôt privé gratuit, une PR dont la CI est rouge resterait fusionnable, et le critère de fin de phase 1 serait impossible à démontrer.

## Options

1. **Dépôt public.** Protection de `main`, vérifications obligatoires, environnements avec approbation et minutes de CI illimitées, gratuitement.
2. **Dépôt privé avec GitHub Pro.** Hors budget.
3. **Dépôt privé gratuit avec garde-fous déclaratifs.** Une PR rouge reste fusionnable.

## Décision

Option 1. Le dépôt est public et ne contiendra jamais de données personnelles réelles.

## Conséquences

- Un ruleset protège `main` : PR obligatoire ; jobs de CI obligatoires (`qualite`, `tests`, `migrations`, `e2e`, `audit`, `build`) ; branche à jour avant fusion ; poussée forcée et suppression interdites ; aucun contournement, y compris pour l'administrateur.
- Aucune approbation de relecture n'est exigée : tu es seul et ne peux pas approuver ta propre PR. Claude Code n'a pas le droit de fusionner (`.claude/settings.json`).
- L'environnement GitHub `production` exige ton approbation avant chaque déploiement en production ([ADR-0003](0003-hebergement-vercel-et-neon.md)).
- Tout ce qui est versionné est public : code, documentation, historique Git. La CI exécute gitleaks pour détecter un secret commis par erreur.
- La documentation publique ne nomme ni le club ni le préparateur. `docs/00-cadrage.md` sera anonymisé avant son premier commit.
- La sécurité ne repose jamais sur le secret du code : le modèle d'accès est publié et doit tenir quand même.
