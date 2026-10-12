# ADR-0012 — Z-score d'intensité

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Proposition du cadrage : intensité(D) = (CE courte(D) − m) / s, où m et s sont la moyenne et l'écart-type des CE courtes des 28 jours précédents, de D − 28 à D − 1, jour courant exclu. Inclure le point courant plafonnait le z-score à (n − 1)/√n (annexe A, n° 7). Restent à fixer l'historique minimal, l'estimateur de l'écart-type et le traitement d'un écart-type nul.

Remarque statistique : deux CE courtes consécutives partagent 6 jours sur 7. Les 28 valeurs de référence sont donc fortement autocorrélées, et s sous-estime la variabilité d'une semaine à l'autre. Les z-scores en sortent plus grands qu'avec des valeurs indépendantes. Ce n'est pas gênant pour comparer un joueur à lui-même, mais un seuil comme « 2 » n'a pas de sens probabiliste : c'est un repère visuel, pas un test.

## Q1 — Fenêtre de référence

| Option | Conséquence |
| --- | --- |
| A. Les 28 CE courtes quotidiennes précédentes (proposition) | Référence réactive, valeurs autocorrélées |
| B. Les 4 CE courtes hebdomadaires précédentes, sans chevauchement | Valeurs presque indépendantes, mais 4 points seulement : écart-type très instable |

**Retenu** : A. Paramètre `reference_jours = 28`.

## Q2 — Historique minimal

On compte les jours de référence dont la CE courte repose sur une fenêtre complète ([ADR-0011](0011-calendrier-et-charges-glissantes.md)).

| Option | Premier jour avec un z-score, avec un calendrier qui commence au jour 1 |
| --- | --- |
| A. 28 jours de référence complets | Jour 35 |
| B. 21 jours de référence complets | Jour 28 |
| C. 14 jours de référence complets | Jour 21 |

**Retenu** : B, compromis entre stabilité et délai d'attente pour un nouveau joueur. Paramètre `reference_min_jours = 21`. En dessous : état `HISTORIQUE_INSUFFISANT` (C8).

## Q3 — Estimateur de l'écart-type

| Option | Conséquence |
| --- | --- |
| A. Écart-type d'échantillon, dénominateur n − 1 (`statistics.stdev`) | Estimateur usuel de la variabilité ; écart de 2 % avec B pour n = 28 |
| B. Écart-type de population, dénominateur n (`statistics.pstdev`) | Légèrement plus petit, donc z légèrement plus grands |

**Retenu** : A, à utiliser aussi pour les sensations ([ADR-0015](0015-zscore-de-sensations.md)). Les valeurs attendues du jeu de référence doivent utiliser le même estimateur : pense à `ECARTYPE` contre `ECARTYPEP` dans ton tableur.

## Q4 — Écart-type nul ou quasi nul

| Option | Conséquence |
| --- | --- |
| A. `NON_CALCULABLE` si s ≤ 1e-9 × max(1, \|m\|) | Évite la division par zéro et les artefacts d'arrondi (C7) ; aucun plancher sinon |
| B. A, plus un plancher : s ≥ 5 % de m | Évite des z énormes après un historique presque constant, mais modifie la définition du z-score |

**Retenu** : A en V1, transparent et conforme au cas C6 ; le plancher sera réexaminé après la démonstration.

## Q5 — Affichage

**Retenu** : deux décimales à l'affichage ; aucun arrondi dans les calculs ni dans les comparaisons de test.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : référence = les 28 CE courtes quotidiennes précédentes (`reference_jours = 28`).
- Q2 : au moins 21 jours de référence à fenêtre complète (`reference_min_jours = 21`), sinon `HISTORIQUE_INSUFFISANT`.
- Q3 : écart-type d'échantillon, dénominateur n − 1 (`statistics.stdev`, `ECARTYPE` dans le tableur).
- Q4 : `NON_CALCULABLE` si s ≤ 1e-9 × max(1, \|m\|) ; aucun plancher.
- Q5 : deux décimales à l'affichage ; aucun arrondi dans les calculs ni dans les tests.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`reference_jours`, `reference_min_jours` ; cas C6, C7, C8, C14.
