# ADR-0015 — Z-score de sensations

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Proposition du cadrage : sensations = z-score du score de l'entrée par rapport aux entrées précédentes du joueur sur 28 jours, entrée courante exclue. Le nombre d'entrées disponibles dépend de la fréquence du questionnaire ([ADR-0017](0017-frequence-du-questionnaire.md)) : jusqu'à 28 par mois en quotidien, environ 8 à deux jours fixes par semaine.

## Q1 — Référence

**Retenu** : les scores des entrées datées de D − 28 à D − 1, pour une entrée datée D, en excluant les entrées sans score. Paramètre `sensations_reference_jours = 28`.

## Q2 — Nombre minimal d'entrées de référence

| Option | Conséquence |
| --- | --- |
| A. 6 entrées | Compatible avec deux questionnaires par semaine malgré quelques oublis ; peu de données en rythme quotidien |
| B. 10 entrées | Plus stable ; impossible à atteindre à deux questionnaires par semaine |
| C. Valeur dérivée de la fréquence, par exemple 75 % des entrées attendues | S'adapte, mais la règle est plus difficile à expliquer |

**Retenu** : A, `sensations_reference_min_entrees = 6`. En dessous : état `HISTORIQUE_INSUFFISANT` (C8).

## Q3 — Estimateur et écart-type nul

**Retenu** : même estimateur et même règle que pour l'intensité ([ADR-0012](0012-zscore-d-intensite.md)).

Point d'attention : un joueur qui répond toujours la même chose a un écart-type nul. C'est un cas réaliste, et il est utile de l'afficher comme tel (« non calculable ») plutôt que de le masquer.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : référence = les scores des entrées datées de D − 28 à D − 1 (`sensations_reference_jours = 28`).
- Q2 : au moins 6 entrées de référence (`sensations_reference_min_entrees = 6`), sinon `HISTORIQUE_INSUFFISANT`.
- Q3 : même estimateur et même règle d'écart-type nul que l'intensité.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`sensations_reference_jours`, `sensations_reference_min_entrees` ; cas C7, C8, C13.
