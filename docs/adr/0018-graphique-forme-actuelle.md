# ADR-0018 — Graphique « Forme actuelle »

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 6 | Toi |

## Contexte

Le graphique place un point par joueur : intensité en abscisse, sensations en ordonnée, chacune en z-score par rapport au joueur lui-même. Il sert à repérer une intensité au-dessus de la moyenne combinée à de mauvaises sensations. Dans la V0, les mauvaises sensations étaient en haut et en rouge, les bonnes en bas et en jaune.

## Q1 — Sens de l'axe des sensations

| Option | Conséquence |
| --- | --- |
| A. Convention de la V0 : sensations dégradées en haut | La zone à surveiller (intensité haute, sensations dégradées) est en haut à droite, où l'œil va d'abord ; le préparateur a l'habitude de cette lecture |
| B. Convention usuelle : bonnes sensations en haut | Lecture plus classique, mais la zone à surveiller passe en bas à droite et le préparateur doit réapprendre |

**Retenu** : A, avec un libellé d'axe explicite (« sensations dégradées ↑ »).

## Q2 — Couleur des points

| Option | Conséquence |
| --- | --- |
| A. Selon l'ordonnée seule, du jaune au rouge (V0) | Fidèle à la V0, mais ignore l'intensité |
| B. Selon une combinaison des deux z-scores, par exemple (intensité − sensations) / 2, bornée entre −3 et 3, du jaune au rouge | Le rouge désigne exactement la zone à surveiller |

**Retenu** : B, avec une légende qui explique le calcul. Le calcul de la couleur vit dans le moteur ou dans la construction de la spécification Python, jamais dans le JavaScript.

## Q3 — Entrée de sensations retenue pour le jour D

| Option | Conséquence |
| --- | --- |
| A. L'entrée du jour D seulement | Rigoureux, mais le graphique est presque vide le matin, ou les jours sans questionnaire |
| B. L'entrée la plus récente datée de D − k à D, avec sa date affichée au survol | Graphique utile toute la journée ; une entrée un peu ancienne est signalée |

**Retenu** : B, avec `fraicheur_entree_jours = 3`, ou 4 si le questionnaire passe à deux jours par semaine.

## Q4 — Joueurs sans point

**Retenu** : liste à côté du graphique, avec l'état de chacun : historique insuffisant, non calculable, absent depuis N jours, pas d'entrée récente.

## Q5 — Repères

**Retenu** : axes en 0, quadrants nommés, lignes pointillées à ±2. Le seuil 2 est un repère visuel, pas un test statistique ([ADR-0012](0012-zscore-d-intensite.md)).

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : convention de la V0 : sensations dégradées en haut, avec un libellé d'axe explicite.
- Q2 : couleur selon (intensité − sensations) / 2, bornée entre −3 et 3, du jaune au rouge, calculée côté Python.
- Q3 : entrée la plus récente datée de D − 3 à D, avec sa date affichée (`fraicheur_entree_jours = 3`).
- Q4 : joueurs sans point listés à côté du graphique, avec leur état.
- Q5 : axes en 0, quadrants nommés, lignes pointillées à ±2.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`fraicheur_entree_jours` ; cas E3 et tests unitaires de la spécification du graphique.
