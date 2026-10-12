# ADR-0013 — Absences longues

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Le cas C4 impose qu'un joueur absent 10 jours voie sa CE courte retomber à 0 et son intensité recalculée chaque jour. Question ouverte du cadrage : en cas de blessure ou d'absence longue, faut-il laisser la charge retomber, ou geler la référence ? Le suivi des blessures est reporté après la V1 : en V1, une absence n'est connue que par l'absence de participations.

## Q1 — Référence pendant et après une absence

| Option | Conséquence |
| --- | --- |
| A. Aucun traitement particulier : les jours à 0 entrent dans la référence | Au retour, l'intensité grimpe fortement : c'est le signal recherché pour une reprise trop rapide. Pendant l'absence, l'intensité est très négative. |
| B. Référence gelée pendant une période d'indisponibilité déclarée | Demande une entité « indisponibilité » ou le module blessures, reportés après la V1 |
| C. Jours exclus de la référence au-delà de N jours consécutifs à 0 | Règle implicite, difficile à expliquer au préparateur |

**Retenu** : A en V1, à réexaminer avec le module blessures.

## Q2 — Affichage d'un joueur absent

**Retenu** : un joueur sans participation sur la fenêtre courte apparaît dans la liste des joueurs à part de « Forme actuelle », avec la mention « absent depuis N jours », plutôt qu'en point très à gauche du graphique ([ADR-0018](0018-graphique-forme-actuelle.md)).

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : aucun traitement particulier des absences en V1 ; à réexaminer avec le module blessures.
- Q2 : un joueur sans participation sur la fenêtre courte est listé à part, avec la mention « absent depuis N jours ».

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Tests concernés

C4.
