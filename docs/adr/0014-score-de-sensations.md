# ADR-0014 — Score de sensations

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Proposition du cadrage : score d'une entrée = moyenne pondérée des indicateurs inclus dans le score, chacun ramené à une échelle commune et orienté dans le même sens, calculée sur les réponses présentes avec un nombre minimal de réponses. La première tentative additionnait une note et une durée en minutes (annexe A, n° 10).

## Q1 — Échelle commune

| Option | Conséquence |
| --- | --- |
| A. Ramener chaque réponse dans [0, 1] par ses bornes déclarées : u = (v − min) / (max − min) | Simple, indépendant du joueur, exact pour des échelles bornées |
| B. Standardiser chaque indicateur par joueur (z-score par indicateur) | Corrige les habitudes de réponse de chacun, mais double les z-scores et dépend de l'historique de chaque indicateur |

**Retenu** : A. Les indicateurs de type heure sont exclus du score ([ADR-0010](0010-indicateurs-et-echelles.md)).

## Q2 — Orientation

**Retenu** : pour un indicateur « bas = bon », u devient 1 − u. Le score final vaut 1 pour le meilleur état et 0 pour le pire.

## Q3 — Pondération

**Retenu** : score = Σ(poids × u) / Σ(poids), sur les seuls indicateurs inclus et répondus. Poids par défaut : 1.

## Q4 — Minimum de réponses

| Option | Conséquence |
| --- | --- |
| A. Part minimale du poids total des indicateurs inclus, par exemple 50 % | Tient compte des poids ; reste valable si la liste change |
| B. Nombre minimal de réponses, par exemple 4 | Plus lisible, mais insensible aux poids |

**Retenu** : A, avec `score_poids_min = 0.5`. En dessous : état `REPONSES_INSUFFISANTES` (C13).

## Q5 — Affichage du score

**Retenu** : sur 10 (score × 10), pour rester dans l'échelle que le préparateur connaît. Le z-score n'en dépend pas.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : chaque réponse est ramenée dans [0, 1] par les bornes de son indicateur.
- Q2 : u devient 1 − u pour un indicateur « bas = bon » ; 1 = meilleur état.
- Q3 : score = Σ(poids × u) / Σ(poids), sur les indicateurs inclus et répondus ; poids par défaut 1.
- Q4 : au moins 50 % du poids total des indicateurs inclus (`score_poids_min = 0.5`), sinon `REPONSES_INSUFFISANTES`.
- Q5 : score affiché sur 10.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`score_poids_min` ; cas C11, C12, C13.

## Précisions de la phase 6 (PR 6.3, fiche joueur)

La fiche joueur détaille le score ; ces choix sont paramétrables et restent provisoires comme le reste de l'ADR.

- **Niveau par indicateur** : la réponse normalisée u (Q1), inversée pour « bas = bon » (Q2), est affichée sur 10 (u × 10), comme le total (Q5). Un niveau de 10 est donc toujours le meilleur état : une barre « Fatigue » à 8 signifie peu de fatigue. La réponse brute est donnée dans l'infobulle et dans le tableau de valeurs.
- **Indicateurs détaillés** : ceux du score seulement (actifs, notés, inclus dans le score de la catégorie de référence). Un indicateur d'heure ou exclu du score n'a pas de niveau sur 10 et n'est pas affiché.
- **Dernière entrée** : la plus récente datée au plus tard du jour affiché, sans seuil de fraîcheur (le seuil `fraicheur_entree_jours` ne concerne que « Forme actuelle », ADR-0018).
- **Heatmap** : les 7 jours de D − 6 à D ; un jour sans entrée reste vide ; une ligne de total, égale au score du moteur × 10 ; sous le poids minimal (Q4), le total est absent et le tableau de valeurs écrit « Réponses insuffisantes ».
- **Ordre des indicateurs** : celui du champ `ordre` de l'indicateur.

