# Glossaire

Termes métier et techniques du projet. La colonne « Code » donne l'identifiant utilisé dans le code : vocabulaire métier en français sans accent, termes techniques en anglais.

## Termes métier

| Terme | Définition | Code |
| --- | --- | --- |
| Catégorie | Groupe d'âge d'un centre de formation (U17, U19…). Elle organise des séances et définit son questionnaire. | `Categorie` |
| Catégorie de référence | Catégorie à laquelle un joueur est rattaché. Elle détermine son questionnaire et le staff qui le suit. | `categorie_reference` |
| Catégorie organisatrice | Catégorie qui organise une séance. Elle détermine qui peut créer et modifier la séance, pas à qui la charge est imputée. | `categorie_organisatrice` |
| Préparateur | Membre du staff d'une catégorie : il saisit les séances, consulte les tableaux de bord et gère les liens de ses joueurs. Désigné « staff » dans le cadrage. | `Preparateur` |
| Administrateur | Personne qui crée les comptes staff, gère le référentiel et les paramètres. Un seul en V1. | `is_superuser` |
| Joueur | Personne suivie. En V1, toujours fictive. | `Joueur` |
| Joueur invité | Joueur qui participe à une séance organisée par une autre catégorie que sa catégorie de référence. | — |
| Annuaire | Liste minimale des joueurs actifs (nom, prénom, catégorie de référence) lisible par tout préparateur, pour ajouter un joueur invité à une séance. | `annuaire` |
| Joueur archivé | Joueur qui ne fait plus partie du groupe : ses données sont conservées, il n'apparaît plus dans les listes de saisie et son lien est révoqué. | `actif = False` |
| Séance | Entraînement daté, d'un type (foot, musculation, yoga, autre) et d'une durée en minutes, organisé par une catégorie. | `Seance` |
| Brouillon | État d'une séance en cours de saisie. Une séance en brouillon n'entre dans aucun calcul. | `statut = "brouillon"` |
| Séance validée | État d'une séance dont la grille RPE est complète. Seules les séances validées entrent dans les calculs. | `statut = "validee"` |
| Participation | Présence d'un joueur à une séance, avec ses trois RPE. | `Participation` |
| RPE | *Rate of Perceived Exertion* : ressenti d'effort noté sur 10, saisi par le staff. Trois dimensions : cardio, musculaire, TETA. | `rpe_cardio`, `rpe_musculaire`, `rpe_teta` |
| TETA | Dimension technique et tactique d'une séance. | `teta` |
| Charge de séance | Charge d'une participation : moyenne des trois RPE × durée en minutes × 10 ([ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md)). | `charge_seance` |
| Charge du jour | Somme des charges des séances validées d'un joueur un jour donné ; 0 les jours sans séance. | `charge_jour` |
| Calendrier continu | Suite de tous les jours d'un joueur, avec ou sans séance, sur laquelle se font les calculs glissants. | `calendrier` |
| CE | Charge d'entraînement cumulée sur une fenêtre glissante. | — |
| CE 7 jours (CE courte) | Somme des charges du jour sur la fenêtre courte (7 jours par défaut), jour courant inclus. | `ce_courte` |
| CE 4 semaines (CE longue) | Somme des charges du jour sur la fenêtre longue (28 jours par défaut), jour courant inclus. | `ce_longue` |
| Intensité | Z-score de la CE courte du jour par rapport à la CE courte des jours précédents du joueur. Abscisse du graphique « Forme actuelle ». | `intensite` |
| Indicateur | Question du questionnaire de sensations, configurée par catégorie : libellé, type, échelle, sens, poids, inclusion dans le score. | `Indicateur` |
| Sens d'un indicateur | « Haut = bon » (énergie, plaisir…) ou « bas = bon » (fatigue, douleurs…). | `sens` |
| Entrée de sensations | Ensemble des réponses d'un joueur pour un jour donné. Au plus une par joueur et par jour. | `EntreeSensations` |
| Réponse | Valeur donnée par un joueur à un indicateur dans une entrée. | `Reponse` |
| Score de sensations | Moyenne pondérée des réponses d'une entrée, ramenées sur une échelle commune et orientées dans le même sens. | `score_sensations` |
| Sensations (z) | Z-score du score de sensations par rapport aux entrées précédentes du joueur. Ordonnée du graphique « Forme actuelle ». | `sensations_z` |
| Z-score | Écart d'une valeur à la moyenne de référence du joueur, exprimé en écarts-types de référence. | `zscore` |
| Référence | Ensemble des valeurs passées d'un joueur (jour courant exclu) qui servent à calculer un z-score. | `reference` |
| Historique insuffisant | État affiché quand la référence ne contient pas assez de valeurs pour calculer un z-score. | `HISTORIQUE_INSUFFISANT` |
| Non calculable | État affiché quand l'écart-type de référence est nul : aucune division par zéro n'est faite. | `NON_CALCULABLE` |
| Date de rétrospection | Date D choisie pour consulter un tableau de bord tel qu'il se présentait le jour D, sans aucune donnée datée après D. | `date_calcul` |
| Lien joueur | Adresse personnelle qui permet à un joueur de déposer son entrée du jour sans compte. | `LienJoueur` |
| Jeton | Partie secrète et aléatoire du lien joueur. Seule son empreinte (hachage) est stockée. | `token`, `token_hash` |
| Révocation | Désactivation d'un lien joueur. Un lien révoqué est refusé. | `revoked_at` |
| Régénération | Création d'un nouveau lien pour un joueur, qui révoque le précédent. | — |
| Badge Reçu / Manquant | Indication, dans la grille RPE, que le joueur a ou n'a pas déposé son entrée du jour. | — |

## Termes du projet et techniques

| Terme | Définition |
| --- | --- |
| ADR | *Architecture Decision Record* : une décision, son contexte, les options et ses conséquences, dans un fichier de `docs/adr/`. |
| Jeu de référence | Petit jeu de données versionné dans `tests/reference/`, accompagné de résultats attendus calculés indépendamment du code. |
| Recette | Liste de vérifications manuelles déroulée à chaque fin de phase sur l'environnement déployé. |
| CI | Intégration continue : GitHub Actions exécute lint, typage, tests, migrations, build et audit à chaque PR. |
| Ruleset | Règle GitHub qui protège la branche `main` : pas de poussée directe, PR et CI verte obligatoires. |
| Preview | Déploiement temporaire d'une PR, sur sa propre branche de base de données. |
| Rôle d'exécution | Rôle Postgres utilisé par l'application déployée : lecture et écriture des données, aucune modification du schéma. |
| Rôle de migration | Rôle Postgres propriétaire du schéma, utilisé uniquement par la CI pour appliquer les migrations. |
| E2E | Test de bout en bout : un vrai navigateur pilote l'application complète. |

Attention : le drapeau Django `is_staff` signifie « peut ouvrir l'administration Django ». Il n'a rien à voir avec le staff du cadrage : un préparateur a `is_staff = False`.
