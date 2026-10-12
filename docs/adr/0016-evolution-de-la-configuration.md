# ADR-0016 — Évolution de la configuration en cours de saison

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Le cas C15 demande un comportement décidé, puis testé, quand on ajoute un indicateur ou qu'on change un poids en cours de saison, pour éviter un saut artificiel du score. En V1, seul l'administrateur modifie la configuration.

## Q1 — Changement de poids ou retrait d'un indicateur

| Option | Conséquence |
| --- | --- |
| A. Rétroactif : tous les scores, passés compris, sont recalculés avec la configuration actuelle | Aucun saut : l'entrée courante et sa référence utilisent les mêmes poids. Un score affiché pour une date passée peut changer après la modification. |
| B. Versionné : chaque entrée garde la configuration en vigueur à sa date | Le passé est figé, mais un saut apparaît au changement ; il faudrait remettre la référence à zéro (28 jours d'historique insuffisant) |

**Retenu** : A. C'est la conséquence naturelle de « rien n'est stocké qui puisse se recalculer ».

## Q2 — Ajout d'un indicateur

Avec l'option A, les entrées antérieures à l'ajout n'ont pas de réponse pour le nouvel indicateur : leur score est calculé sans lui, sur les réponses présentes. Un décalage reste possible si le nouvel indicateur a un niveau moyen différent des autres.

| Option | Conséquence |
| --- | --- |
| A. Accepter ce décalage et le documenter | Simple ; effet limité si le nouvel indicateur pèse peu face aux autres |
| B. N'inclure le nouvel indicateur dans le score qu'après une période de rodage (28 jours de collecte) | Évite le décalage, au prix d'un paramètre de plus par indicateur |

**Retenu** : A en V1.

## Q3 — Changement d'échelle d'un indicateur existant

**Retenu** : interdit dès qu'une réponse existe. On crée un nouvel indicateur et on désactive l'ancien. Les réponses ne sont jamais supprimées quand un indicateur est désactivé.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : configuration rétroactive : tous les scores sont recalculés avec la configuration actuelle.
- Q2 : un indicateur ajouté n'entre que dans les entrées qui y répondent ; le décalage possible est documenté.
- Q3 : l'échelle d'un indicateur ne change plus dès qu'une réponse existe ; on crée un nouvel indicateur. Aucune réponse n'est supprimée à la désactivation d'un indicateur.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Tests concernés

C15 : avec l'option A, un changement de poids donne des z-scores identiques à ceux d'un jeu où le nouveau poids aurait toujours été en vigueur ; un indicateur ajouté n'entre que dans les entrées qui y répondent ; une modification d'échelle d'un indicateur déjà utilisé est refusée.
