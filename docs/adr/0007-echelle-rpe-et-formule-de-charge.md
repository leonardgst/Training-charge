# ADR-0007 — Échelle RPE et formule de charge

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 2 | Toi |

## Contexte

Le cadrage propose : charge de séance = moyenne des trois RPE × durée en minutes × 10. Les notes d'origine écrivent `(cardio + musculaire + TETA) × durée / 3 × 10`. Lue de gauche à droite, cette écriture donne exactement la même formule (hypothèse validée le 2026-10-12). La seule autre lecture, `/ (3 × 10)`, divise toutes les charges par 100, ce qui ne change aucun z-score (C14). Il reste à fixer l'échelle des RPE, le facteur d'échelle et les bornes de la durée.

## Q1 — Échelle et pas des RPE

| Option | Conséquence |
| --- | --- |
| A. Entiers de 0 à 10 | Saisie la plus rapide au clavier ; cohérente avec « noté sur 10 » et avec la V0 |
| B. De 0 à 10 au demi-point | Plus fin, mais saisie plus lente et virgule à taper sur tablette |
| C. Entiers de 1 à 10 | Exclut 0, qui peut avoir un sens pour une dimension non sollicitée (TETA en musculation) |

**Retenu** : A. Contrainte en base : `0 ≤ RPE ≤ 10`, entier.

## Q2 — Facteur d'échelle

| Option | Conséquence |
| --- | --- |
| A. 10 (proposition du cadrage) | Une séance de 90 minutes à RPE 6 vaut 5 400 |
| B. 1 (session-RPE de Foster) | Une séance de 90 minutes à RPE 6 vaut 540 ; ordre de grandeur de la littérature |

Aucun z-score n'en dépend. Le critère est l'ordre de grandeur que le préparateur a l'habitude de lire.

**Retenu** : A, 10. Les notes d'origine de la V0 portent ce facteur, donc l'ordre de grandeur que le préparateur connaît. Si un export de la V0 refait surface, le test de comparaison prévu au cadrage (7.3) le confirmera. Paramètre `facteur_echelle_charge = 10`.

## Q3 — Bornes de la durée

**Retenu** : entier, de 1 à 300 minutes. Une durée nulle ou négative est rejetée (D1) ; la borne haute détecte une faute de frappe (900 au lieu de 90). Paramètre `duree_max_min`.

## Q4 — Pondération des trois RPE

| Option | Conséquence |
| --- | --- |
| A. Moyenne simple (proposition du cadrage) | Les trois dimensions pèsent autant |
| B. Moyenne pondérée paramétrable | Plus souple, mais des poids à justifier sans le préparateur |

**Retenu** : A. Le type de séance ne modifie pas la formule.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : RPE entiers de 0 à 10 ; contrainte en base `0 ≤ RPE ≤ 10`.
- Q2 : facteur d'échelle 10, conforme aux notes d'origine de la V0 (`facteur_echelle_charge = 10`).
- Q3 : durée entière de 1 à 300 minutes (`duree_max_min = 300`).
- Q4 : moyenne simple des trois RPE ; le type de séance ne modifie pas la formule.
- Formule retenue : charge de séance = (cardio + musculaire + TETA) / 3 × durée × 10.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`rpe_min`, `rpe_max`, `facteur_echelle_charge`, `duree_max_min` ; cas C1, C14, D1.
