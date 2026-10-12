# ADR-0010 — Indicateurs et échelles de la démonstration U19

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 2 | Toi |

## Contexte

Indicateurs connus : concentration, plaisir, fatigue, énergie, sommeil, douleurs musculaires, compréhension des consignes, heures de coucher et de lever. La première tentative parlait de 11 items sans les lister. La V0 utilisait une échelle de 0 à 10 ; la première tentative est passée de 1 à 7 sans en garder la raison. Les indicateurs sont de la configuration par catégorie : ce choix ne fige pas le schéma, mais il fixe la démonstration et le questionnaire.

## Q1 — Échelle des indicateurs notés

| Option | Conséquence |
| --- | --- |
| A. 0 à 10 | Continuité avec la V0 et avec les RPE ; 11 boutons sur une ligne de téléphone, étroits mais utilisables |
| B. 1 à 7 | Boutons plus larges, réponse plus rapide ; résolution plus faible ; rupture avec la V0 |
| C. 1 à 5 | Encore plus rapide ; résolution faible pour un z-score |

**Retenu** : A, pour la continuité avec la V0 que le préparateur connaît. Le score ramène de toute façon chaque indicateur sur une échelle commune ([ADR-0014](0014-score-de-sensations.md)) : changer d'échelle plus tard reste possible.

## Q2 — Liste et sens

Proposition pour la démonstration :

| Code | Libellé | Type | Échelle | Sens | Poids | Dans le score |
| --- | --- | --- | --- | --- | --- | --- |
| `concentration` | Concentration | Note | 0–10 | Haut = bon | 1 | Oui |
| `plaisir` | Plaisir | Note | 0–10 | Haut = bon | 1 | Oui |
| `fatigue` | Fatigue | Note | 0–10 | Bas = bon | 1 | Oui |
| `energie` | Énergie | Note | 0–10 | Haut = bon | 1 | Oui |
| `sommeil` | Qualité du sommeil | Note | 0–10 | Haut = bon | 1 | Oui |
| `douleurs` | Douleurs musculaires | Note | 0–10 | Bas = bon | 1 | Oui |
| `comprehension` | Compréhension des consignes | Note | 0–10 | Haut = bon | 1 | Oui |
| `heure_coucher` | Heure de coucher | Heure | — | — | — | Non |
| `heure_lever` | Heure de lever | Heure | — | — | — | Non |

**Retenu** : cette liste. « Compréhension des consignes » porte sur une séance : elle est facultative, puisque le questionnaire ne dépend pas des séances.

## Q3 — Heures de coucher et de lever

| Option | Conséquence |
| --- | --- |
| A. Collectées dès la V1, hors du score | Prépare la régularité du sommeil (reportée après la V1) sans risque pour le score |
| B. Durée de sommeil dérivée et incluse dans le score | Exige des bornes de normalisation (par exemple 5 h → 0, 9 h → 1), et « plus » n'est pas toujours « mieux » |
| C. Non collectées en V1 | Questionnaire plus court |

**Retenu** : A.

## Q4 — Réponses obligatoires

**Retenu** : toutes les notes sont obligatoires dans le formulaire, sauf « compréhension des consignes » et les heures. Le moteur reste robuste aux réponses manquantes (C13), pour les données importées ou les changements de configuration.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : échelle de 0 à 10 pour tous les indicateurs notés.
- Q2 : la liste de neuf indicateurs du tableau, avec leurs sens et un poids de 1.
- Q3 : heures de coucher et de lever collectées dès la V1, hors du score.
- Q4 : notes obligatoires dans le formulaire, sauf « compréhension des consignes » et les heures.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Tests concernés

D1 (valeur hors bornes refusée par un déclencheur en base) ; C11 et C12 utilisent leur propre configuration de test, quelle que soit la démonstration.
