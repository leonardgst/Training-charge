# ADR-0011 — Calendrier continu et charges glissantes

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 3 | Toi |

## Contexte

Propositions du cadrage : charge du jour = somme des charges des séances validées du jour, 0 les jours sans séance, sur un calendrier continu par joueur ; CE courte = somme sur 7 jours glissants, jour courant inclus ; CE longue = même somme sur 28 jours. La première tentative calculait une ligne par participation (annexe A, n° 8). Les cas C2, C3 et C4 imposent déjà le calendrier continu. Restent à fixer son point de départ, la longueur des fenêtres et le traitement des premiers jours.

## Q1 — Début du calendrier d'un joueur

| Option | Conséquence |
| --- | --- |
| A. Date de sa première participation validée | Aucun champ supplémentaire ; avant cette date, rien n'est connu du joueur |
| B. Date de début de suivi, saisie sur la fiche du joueur | Distingue un joueur arrivé blessé d'un joueur sans historique ; un champ de plus à tenir |
| C. Début de saison commun | Des semaines de zéros pour un joueur arrivé en cours de saison |

**Retenu** : A.

## Q2 — Longueur des fenêtres

**Retenu** : 7 jours et 28 jours, les fenêtres usuelles du suivi aigu et chronique, jour courant inclus. Paramètres `fenetre_courte_jours` et `fenetre_longue_jours`.

## Q3 — Premiers jours, quand la fenêtre dépasse le début du calendrier

| Option | Conséquence |
| --- | --- |
| A. CE calculée sur les jours disponibles, avec un drapeau « fenêtre incomplète » affiché | Valeur toujours définie et vraie (la somme connue) ; l'interface signale qu'elle est partielle |
| B. Aucune CE avant 7 jours (ou 28 pour la CE longue) | État « historique insuffisant » sur les barres de la fiche pendant les premières semaines |

**Retenu** : A. Le z-score d'intensité a sa propre exigence d'historique ([ADR-0012](0012-zscore-d-intensite.md)).

## Q4 — Fin du calendrier

Le calendrier s'arrête à la date de calcul D, aujourd'hui ou la date de rétrospection. Aucune donnée datée après D n'est lue (C9). Ce point découle du cadrage ; il est consigné ici pour mémoire.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : le calendrier d'un joueur commence à sa première participation validée.
- Q2 : fenêtres de 7 et 28 jours, jour courant inclus (`fenetre_courte_jours = 7`, `fenetre_longue_jours = 28`).
- Q3 : CE calculée sur les jours disponibles, avec un drapeau « fenêtre incomplète » affiché.
- Q4 : le calendrier s'arrête à la date de calcul D.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`fenetre_courte_jours`, `fenetre_longue_jours` ; cas C2, C3, C4, C9, C10.
