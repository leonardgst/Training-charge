# ADR-0008 — Cycle de vie des saisies : brouillon, validation, correction

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté | 2026-10-12 | Phases 2 et 5 | Toi |

## Contexte

Le 2026-10-12, tu as décidé que les données saisies doivent pouvoir être corrigées en cas d'erreur. La première tentative rendait les RPE obligatoires, ce qui empêchait tout brouillon (annexe A, n° 11). Comme rien n'est stocké en dehors des saisies, une correction se répercute d'elle-même dans tous les calculs.

## Q1 — Séance validée : comment la corriger ?

| Option | Conséquence |
| --- | --- |
| A. Modification directe ; la séance reste validée, avec les mêmes règles de complétude | Simple ; la correction compte immédiatement |
| B. Retour obligatoire en brouillon pour modifier | La séance sort des calculs pendant la correction, ce qui fausse les tableaux de bord entre-temps |

**Retenu** : A. Brouillon : RPE facultatifs. Validation : les trois RPE de chaque participant sont obligatoires, contrôle fait par l'application et par un déclencheur en base. Suppression d'une séance par un préparateur de la catégorie organisatrice, avec confirmation ; ses participations disparaissent avec elle.

## Q2 — Entrée de sensations du jour, par le joueur

| Option | Conséquence |
| --- | --- |
| A. Le joueur modifie son entrée du jour par son lien, jusqu'à 23 h 59, heure de Paris | Répond à ta décision sans élargir l'accès : le lien ne voit que le jour même (A4) |
| B. Aucune modification par le joueur | Contraire à ta décision |

**Retenu** : A. Un second envoi le même jour modifie l'entrée existante ; il n'en crée jamais une seconde (D2).

## Q3 — Entrée de sensations passée

| Option | Conséquence |
| --- | --- |
| A. Personne ne la modifie | Simple ; une erreur reste dans l'historique |
| B. Le préparateur de la catégorie de référence la corrige ou la supprime, à la demande du joueur ; la date et l'auteur sont enregistrés | Corrige les erreurs, au prix d'une modification par un tiers d'une donnée déclarée par le joueur |
| C. Le joueur corrige la veille par son lien | Élargit la portée du lien (A4) |

**Retenu** : B, avec la date et l'auteur de la modification. Un historique complet des valeurs successives n'est pas prévu en V1.

## Q4 — Traçabilité

**Retenu** : `updated_at` et `updated_by` sur les séances, les participations et les entrées de sensations ; un test vérifie que `updated_at` change (annexe A, n° 18).

## Q5 — Date de rétrospection et corrections tardives

Une donnée datée au plus tard du jour D peut être corrigée après D. Que montre la rétrospection au jour D ?

| Option | Conséquence |
| --- | --- |
| A. Les valeurs corrigées : on filtre sur la date de la séance ou de l'entrée | La rétrospection montre la meilleure connaissance actuelle de la situation au jour D |
| B. Les valeurs telles qu'elles étaient connues le jour D | Demande un historique de chaque modification, lourd pour la V1 |

**Retenu** : A. Le cas C9 se lit alors ainsi : aucune donnée datée après D n'est utilisée.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : une séance validée se modifie directement et reste validée ; brouillon avec RPE facultatifs ; validation exigeant les trois RPE de chaque participant, contrôlée par l'application et par un déclencheur en base ; suppression par un préparateur de la catégorie organisatrice, avec confirmation.
- Q2 : le joueur modifie son entrée du jour par son lien jusqu'à 23 h 59, heure de Paris ; un second envoi modifie l'entrée existante.
- Q3 : le préparateur de la catégorie de référence corrige ou supprime une entrée passée, à la demande du joueur ; date et auteur enregistrés ; pas d'historique des valeurs successives en V1.
- Q4 : `updated_at` et `updated_by` sur les séances, les participations et les entrées de sensations.
- Q5 : la rétrospection au jour D utilise les valeurs corrigées et filtre sur la date de la séance ou de l'entrée.

## Tests concernés

C5, C9, D1, D2, A4 ; test de `updated_at`.
