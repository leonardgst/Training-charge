# Décisions d'architecture et de métier

Une décision par fichier. Format : contexte, options, décision, conséquences. Une décision n'existe que si elle est écrite ici (cadrage, section 10.4). Quand une décision change, la même PR met à jour l'ADR, les [spécifications](../01-specifications.md) et les tests concernés.

## ADR techniques

| ADR | Sujet | Statut |
| --- | --- | --- |
| [0001](0001-depot-public-et-protection-de-main.md) | Dépôt public et protection de `main` | Accepté le 2026-10-12 |
| [0002](0002-django-et-rendu-serveur.md) | Django et rendu côté serveur | Accepté le 2026-10-12 |
| [0003](0003-hebergement-vercel-et-neon.md) | Hébergement sur Vercel et Neon | Accepté le 2026-10-12 |
| [0004](0004-moteur-de-calcul-en-python.md) | Moteur de calcul en Python pur | Accepté le 2026-10-12 |
| [0005](0005-controle-d-acces-applicatif.md) | Contrôle d'accès applicatif et refus par défaut | Accepté le 2026-10-12 |
| [0006](0006-lien-joueur-a-jeton-hache.md) | Lien joueur à jeton haché | Accepté le 2026-10-12 |

## ADR métier et statistiques

Décidées par toi le 2026-10-12, sans consultation du préparateur. Celles marquées « provisoire » sont paramétrables et restent à confirmer par le préparateur (cadrage, règle 9).

| ADR | Sujet | Statut | Phase concernée |
| --- | --- | --- | --- |
| [0007](0007-echelle-rpe-et-formule-de-charge.md) | Échelle RPE et formule de charge | Accepté, provisoire | 2 |
| [0008](0008-cycle-de-vie-des-saisies.md) | Cycle de vie des saisies : brouillon, validation, correction | Accepté | 2 et 5 |
| [0009](0009-suppression-et-archivage-d-un-joueur.md) | Suppression et archivage d'un joueur | Accepté | 2 |
| [0010](0010-indicateurs-et-echelles.md) | Indicateurs et échelles de la démonstration U19 | Accepté, provisoire | 2 |
| [0011](0011-calendrier-et-charges-glissantes.md) | Calendrier continu et charges glissantes | Accepté, provisoire | 3 |
| [0012](0012-zscore-d-intensite.md) | Z-score d'intensité | Accepté, provisoire | 3 |
| [0013](0013-absences-longues.md) | Absences longues | Accepté, provisoire | 3 |
| [0014](0014-score-de-sensations.md) | Score de sensations | Accepté, provisoire | 3 |
| [0015](0015-zscore-de-sensations.md) | Z-score de sensations | Accepté, provisoire | 3 |
| [0016](0016-evolution-de-la-configuration.md) | Évolution de la configuration en cours de saison | Accepté, provisoire | 3 |
| [0017](0017-frequence-du-questionnaire.md) | Fréquence du questionnaire et badge | Accepté, provisoire | 5 |
| [0018](0018-graphique-forme-actuelle.md) | Graphique « Forme actuelle » | Accepté, provisoire | 6 |

## Points reportés après la V1, sans ADR pour l'instant

Joueur sans smartphone, droit de modifier le référentiel, consultation de ses propres données par le joueur, blessures, régularité du sommeil. Le comportement retenu en V1 figure dans les [spécifications](../01-specifications.md), section 5. Leur ADR sera écrite au moment de les traiter, pas avant.
