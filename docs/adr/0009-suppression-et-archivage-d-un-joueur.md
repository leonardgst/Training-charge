# ADR-0009 — Suppression et archivage d'un joueur

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté | 2026-10-12 | Phase 2 | Toi |

## Contexte

Le cadrage exige que supprimer ou anonymiser un joueur soit une opération définie et testée (D4), en traitant les données comme des données de santé au sens du RGPD. Deux situations sont différentes : un joueur qui quitte le groupe, et un joueur qui demande l'effacement de ses données.

## Q1 — Départ du groupe

**Retenu** : archivage (`actif = False`). Les données sont conservées ; le joueur disparaît des listes de saisie et de l'annuaire ; son lien est révoqué. L'opération est réversible.

## Q2 — Demande d'effacement

| Option | Conséquence |
| --- | --- |
| A. Suppression définitive en cascade : joueur, liens, participations, entrées et réponses | Effacement réel. Les autres participants de ses séances ne sont pas touchés. |
| B. Anonymisation : identité remplacée, charges conservées | Dans un groupe de 30 joueurs, les dates de séance et les charges permettent de retrouver la personne : c'est une pseudonymisation, et les données restent personnelles |
| C. A, avec un export de ses données remis avant suppression | Couvre aussi le droit d'accès |

**Retenu** : A en V1, l'export de C étant reporté après la V1.

## Q3 — Qui peut effacer ?

| Option | Conséquence |
| --- | --- |
| A. L'administrateur seul | Opération irréversible, gardée au niveau le plus haut |
| B. Le préparateur de la catégorie de référence | Plus autonome, mais une erreur ne se rattrape pas |

**Retenu** : A. Le préparateur peut archiver ; l'administrateur seul efface.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : départ du groupe = archivage (`actif = False`), réversible ; lien révoqué ; historique conservé.
- Q2 : effacement = suppression définitive en cascade (joueur, liens, participations, entrées, réponses) ; export préalable reporté après la V1.
- Q3 : seul l'administrateur efface ; le préparateur archive.

## Tests concernés

D4 : après effacement, aucune ligne ne référence le joueur, son lien est refusé, les participations des autres joueurs à ses séances sont intactes. Après archivage : absent des listes, lien refusé, historique consultable.
