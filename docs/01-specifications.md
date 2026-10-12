# Spécifications fonctionnelles

| Version | Date | Statut |
| --- | --- | --- |
| 1.0 | 2026-10-12 | Validé |

Ce document traduit le cadrage ([00-cadrage.md](00-cadrage.md)) en fonctionnalités priorisées, user stories, parcours et règles métier. Le vocabulaire est défini dans le [glossaire](glossaire.md). Chaque règle porte un statut et renvoie, le cas échéant, à l'ADR qui la justifie.

## 1. Périmètre de la V1

Décisions du 2026-10-12 :

- La V1 est une **démonstration** sur données fictives. Elle sera présentée au préparateur telle quelle ; un usage réel éventuel est un chantier distinct, qui passera par la gouvernance de la donnée avec le club.
- Le dépôt est **public** et ne contiendra jamais de données personnelles réelles ([ADR-0001](adr/0001-depot-public-et-protection-de-main.md)).
- Les points ouverts du cadrage sont tranchés par toi, sans consultation préalable du préparateur : tu as accepté le 2026-10-12 les recommandations des ADR 0007 à 0018. Les valeurs retenues restent paramétrables et provisoires jusqu'à la validation du préparateur.
- Une seule catégorie est visible dans l'interface (U19). Le modèle de données gère déjà plusieurs catégories, parce que la charge suit le joueur (cas C10 et A3).

Statuts utilisés dans ce document :

| Statut | Sens |
| --- | --- |
| Décidé (cadrage) | Fixé dans le cadrage initial. |
| Décidé le 2026-10-12 | Fixé par tes réponses aux questions de la phase 0 ou par une ADR acceptée ce jour-là. |
| Provisoire | Proposition ou point ouvert du cadrage, tranché par toi le 2026-10-12 dans l'ADR indiquée ; paramétrable et à confirmer par le préparateur. |
| Reporté après la V1 | Hors V1 ; valeur par défaut indiquée pour la V1. |

## 2. Fonctionnalités priorisées (MoSCoW)

| ID | Fonctionnalité | Priorité | Phase | Commentaire |
| --- | --- | --- | --- | --- |
| F01 | Connexion du staff ; comptes créés par l'administrateur ; inscription publique fermée | Must | 2 et 4 | Modèle et règles en phase 2, écrans en phase 4 |
| F02 | Gestion des joueurs de sa catégorie par le préparateur : créer, modifier, archiver | Must | 4 | Décidé le 2026-10-12 : autonomie et droit d'écriture du préparateur (cadrage 6.7) ; l'administrateur peut aussi le faire par l'administration Django dès la phase 2 |
| F03 | Création d'une séance : en-tête, participants pré-remplis, ajout d'un joueur invité, retrait | Must | 4 | |
| F04 | Grille RPE au clavier, code couleur en direct, brouillon puis validation | Must | 4 | |
| F05 | Historique des séances : liste, correction, suppression | Must | 4 | |
| F06 | Moteur de calcul : charges, CE courte et longue, intensité, score et z-score de sensations | Must | 3 | |
| F07 | Liens joueurs : génération, révocation, régénération | Must | 5 | |
| F08 | Questionnaire mobile par lien, limité aux indicateurs de la catégorie de référence | Must | 5 | |
| F09 | Correction de son entrée du jour par le joueur | Must | 5 | Décidé le 2026-10-12 |
| F10 | Badge Reçu / Manquant dans la grille | Must | 5 | |
| F11 | Graphique « Forme actuelle » | Must | 6 | |
| F12 | Fiche joueur avec date de rétrospection | Must | 6 | |
| F13 | Données de démonstration générées par un script versionné | Must | 2 | Jamais copiées de données réelles |
| F14 | Suppression définitive d'un joueur (droit à l'effacement) | Must | 2 | Cas D4, [ADR-0009](adr/0009-suppression-et-archivage-d-un-joueur.md) |
| F15 | QR code du lien joueur | Should | 5 | |
| F16 | Données brutes depuis le début de la saison et export CSV | Should | 6 | |
| F17 | Correction par le staff d'une entrée de sensations passée | Should | 5 | Par le préparateur de la catégorie de référence, à la demande du joueur ([ADR-0008](adr/0008-cycle-de-vie-des-saisies.md)) |
| F18 | Configuration des indicateurs dans l'interface | Could | Après V1 | En V1, par l'administration Django |
| F19 | Plusieurs catégories dans l'interface, rôles par catégorie | Could | Après V1 | Modèle prêt dès la phase 2 |
| F20 | Blessures et carte corporelle | Could | Après V1 | |
| F21 | Régularité du sommeil | Could | Après V1 | Données collectées en V1 si [ADR-0010](adr/0010-indicateurs-et-echelles.md) le retient |
| F22 | Import de l'historique Excel de la V0 | Could | Après V1 | |
| F23 | Installation sur l'écran d'accueil (manifeste web) et rappels | Could | Après V1 | En V1, un raccourci d'écran d'accueil vers le lien suffit |
| W01 | Application native, modélisation prédictive, GPS et capteurs, notifications push, plusieurs clubs, données réelles | Won't | — | Hors périmètre du cadrage |

Le MVP du cadrage (section 4) est retenu tel quel : il correspond à la fin de la phase 6, avec une application déployée dès la phase 1.

## 3. User stories et critères d'acceptation

Les identifiants entre crochets renvoient aux cas de test de la section 7 du cadrage, détaillés dans [03-strategie-tests.md](03-strategie-tests.md).

**US-01 — Créer un compte préparateur.** En tant qu'administrateur, je crée le compte d'un préparateur et le rattache à une catégorie, pour qu'il travaille sans me solliciter.
- Le compte se crée depuis l'administration, avec une catégorie obligatoire.
- Aucune page publique ne permet de créer un compte. [A6]
- Le préparateur ne peut pas ouvrir l'administration.

**US-02 — Se connecter.** En tant que préparateur, je me connecte avec mon identifiant et mon mot de passe.
- Des identifiants invalides donnent un message générique, qui ne dit pas lequel est faux.
- Toute page demandée sans session redirige vers la connexion, sans aucune donnée dans la réponse. [A1]

**US-03 — Créer une séance.** En tant que préparateur, je crée une séance en renseignant une seule fois la date, le type et la durée.
- La catégorie organisatrice est la mienne.
- La liste des participants est pré-remplie avec les joueurs actifs de ma catégorie.
- Je retire un absent ; j'ajoute un joueur invité en le cherchant dans l'annuaire, qui ne montre que son nom, son prénom et sa catégorie.
- Une durée nulle, négative ou hors plage est refusée, à la saisie comme en base. [D1]

**US-04 — Saisir la grille RPE.** En tant que préparateur, je saisis les trois RPE de chaque participant au clavier, ligne après ligne.
- Une ligne par participant, trois colonnes : cardio, musculaire, TETA.
- La touche Tab passe à la cellule suivante dans l'ordre de lecture ; le clavier numérique s'ouvre sur tablette.
- La couleur de la cellule change pendant la frappe selon la valeur.
- Une valeur hors échelle est refusée, à la saisie comme en base. [D1]

**US-05 — Brouillon puis validation.** En tant que préparateur, j'enregistre une grille incomplète en brouillon et je la valide plus tard.
- Un brouillon s'enregistre même avec des RPE manquants.
- Un brouillon n'entre dans aucun calcul. [C5]
- La validation exige les trois RPE de chaque participant.
- Après validation, les charges apparaissent dans les tableaux de bord. [E1]

**US-06 — Corriger ou supprimer une séance.** En tant que préparateur, je corrige une erreur de saisie ou supprime une séance de ma catégorie.
- Les modalités sont fixées par [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md).
- Les tableaux de bord reflètent la correction sans action supplémentaire : les calculs ne sont pas stockés.
- La date et l'auteur de la dernière modification sont enregistrés.

**US-07 — Gérer les liens joueurs.** En tant que préparateur, je génère, révoque ou régénère le lien personnel d'un joueur de ma catégorie.
- Le lien est affiché une seule fois à la génération, avec son QR code (F15).
- Un lien révoqué ou remplacé par une régénération est refusé. [A5]
- Le jeton n'est jamais stocké en clair, et personne ne peut le relire en base. [A5]

**US-08 — Remplir le questionnaire.** En tant que joueur, j'ouvre mon lien sur mon téléphone, je réponds et j'envoie.
- Je ne vois que les indicateurs de ma catégorie de référence.
- Une seule entrée par jour ; un second envoi le même jour modifie l'entrée existante sans en créer une autre. [D2]
- Une valeur hors échelle est refusée. [D1]
- Côté staff, mon badge passe à « Reçu ». [E2]
- Je remplis le questionnaire en moins d'une minute (recette sur un vrai téléphone).

**US-09 — Corriger son entrée du jour.** En tant que joueur, je rouvre mon lien le même jour pour corriger une réponse.
- Je retrouve mes réponses du jour pré-remplies et je les modifie.
- Je ne vois jamais une entrée d'un autre jour, ni les données d'un autre joueur. [A4]

**US-10 — Voir la forme actuelle du groupe.** En tant que préparateur, j'ouvre « Forme actuelle » et je repère les joueurs dont l'intensité est au-dessus de leur moyenne alors que leurs sensations se dégradent.
- Un point par joueur dont l'intensité et les sensations sont calculables.
- Les joueurs sans valeur sont listés à part avec leur état : historique insuffisant, non calculable, pas d'entrée récente.
- L'orientation, les couleurs et le choix de l'entrée de sensations suivent [ADR-0018](adr/0018-graphique-forme-actuelle.md).
- Les valeurs affichées sont celles du moteur : aucune formule n'est réécrite dans l'interface.

**US-11 — Consulter la fiche d'un joueur.** En tant que préparateur, j'ouvre la fiche d'un de mes joueurs pour comprendre son historique.
- Tableau des RPE des dernières séances, coloré selon l'intensité.
- Barres de CE courte et de CE longue.
- Barres des sensations de la dernière entrée.
- Heatmap des sensations sur 7 jours, par indicateur, avec un total.
- Pour le joueur du jeu de référence, les valeurs affichées sont les valeurs attendues. [E3]

**US-12 — Revenir à une date passée.** En tant que préparateur, je choisis une date D pour voir la fiche ou la forme du groupe telles qu'au jour D.
- Le résultat est identique à celui calculé le jour D : aucune donnée datée après D n'est utilisée. [C9]

**US-13 — Consulter et exporter les données brutes.** En tant que préparateur, je consulte les séances et les charges de mes joueurs depuis le début de la saison et je les exporte en CSV.
- L'export ne contient que les joueurs de ma catégorie de référence. [A3]

**US-14 — Supprimer un joueur.** En tant qu'administrateur, je supprime définitivement un joueur à sa demande.
- Le comportement suit [ADR-0009](adr/0009-suppression-et-archivage-d-un-joueur.md) et il est testé. [D4]

**US-15 — Gérer ses joueurs.** En tant que préparateur, je crée, modifie et archive les joueurs de ma catégorie sans solliciter l'administrateur.
- Un joueur créé a pour catégorie de référence celle du préparateur.
- Un joueur archivé disparaît des listes de saisie et de l'annuaire ; son lien est révoqué ; son historique reste consultable. [D4]
- Je ne peux ni voir ni modifier un joueur d'une autre catégorie. [A3]

## 4. Parcours clés

**Mise en place (administrateur, une fois)**

1. Il crée la catégorie U19 et ses indicateurs dans l'administration.
2. Il crée le compte du préparateur et le rattache à la catégorie.
3. Il crée les joueurs, ou lance le script de démonstration.

**Préparateur, après une séance**

1. Il se connecte et ouvre « Nouvelle séance ».
2. Il renseigne la date, le type et la durée. Les joueurs actifs de sa catégorie apparaissent.
3. Il retire les absents et ajoute, si besoin, un joueur invité depuis l'annuaire.
4. Il saisit les trois RPE de chaque joueur au clavier, ligne après ligne. La colonne de badge montre qui a déjà rempli son questionnaire.
5. Il enregistre en brouillon s'il est interrompu, puis valide quand la grille est complète.
6. Il ouvre « Forme actuelle » et voit les joueurs à surveiller.
7. Il ouvre la fiche d'un joueur, et choisit au besoin une date de rétrospection.

**Préparateur, gestion des liens**

1. Il ouvre la liste de ses joueurs et génère le lien d'un joueur.
2. Il montre le QR code au joueur, ou lui transmet le lien.
3. Si le lien a circulé, il le régénère : l'ancien est aussitôt refusé.

**Joueur, chaque jour de questionnaire**

1. Il ouvre son lien depuis le raccourci de l'écran d'accueil de son téléphone.
2. Il répond aux indicateurs de sa catégorie de référence.
3. Il envoie. Côté staff, son badge passe à « Reçu ».
4. S'il s'est trompé, il rouvre le lien le même jour, corrige et renvoie.

## 5. Règles métier

| ID | Règle | Statut | Paramètre | Tests |
| --- | --- | --- | --- | --- |
| R01 | Après chaque séance, le staff saisit trois RPE par joueur présent : cardio, musculaire, TETA. | Décidé (cadrage) | — | D1 |
| R02 | RPE entiers de 0 à 10 ; durée entière de 1 à 300 minutes. | Provisoire → [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) | `rpe_min = 0`, `rpe_max = 10`, `duree_max_min = 300` | D1 |
| R03 | Charge de séance = (cardio + musculaire + TETA) / 3 × durée en minutes × 10. Le facteur 10 ne change aucun z-score. | Provisoire → [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) | `facteur_echelle_charge = 10` | C1, C14 |
| R04 | Une séance appartient à la catégorie qui l'organise. Un joueur garde sa catégorie de référence et son questionnaire, même s'il s'entraîne avec un autre groupe. | Décidé (cadrage) | — | A3, C10 |
| R05 | La charge et les z-scores se calculent par joueur, sur toutes ses participations, quelle que soit la catégorie organisatrice. | Décidé (cadrage) | — | C10 |
| R06 | Chaque joueur est comparé à lui-même, jamais au groupe. | Décidé (cadrage) | — | C6 |
| R07 | Une séance en brouillon n'entre dans aucun calcul. | Décidé (cadrage) | — | C5 |
| R08 | Une séance se crée en brouillon, RPE facultatifs, et se valide quand les trois RPE de chaque participant sont saisis. Une séance validée se corrige directement et reste validée. Sa suppression par un préparateur de la catégorie organisatrice demande une confirmation. La date et l'auteur de la dernière modification sont enregistrés. | Décidé le 2026-10-12 → [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) | — | C5, D1 |
| R09 | « Jour » désigne le jour calendaire à l'heure de Paris : pour la charge du jour, l'entrée unique de sensations et le badge. | Décidé le 2026-10-12 | `fuseau = Europe/Paris` | C2, D2 |
| R10 | Charge du jour = somme des charges des séances validées du jour, et 0 les jours sans séance, sur un calendrier continu qui commence à la première participation validée du joueur et s'arrête à la date de calcul. | Provisoire → [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) | — | C2, C3, C4, C9 |
| R11 | CE courte = somme sur 7 jours, CE longue = somme sur 28 jours, jour courant inclus. Au début du calendrier, la CE est calculée sur les jours disponibles et signalée « fenêtre incomplète ». | Provisoire → [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) | `fenetre_courte_jours = 7`, `fenetre_longue_jours = 28` | C3, C4 |
| R12 | Intensité = (CE courte du jour − m) / s, où m et s sont la moyenne et l'écart-type d'échantillon (n − 1) des CE courtes des 28 jours précédents, jour courant exclu. Au moins 21 jours de référence à fenêtre complète sont exigés. | Provisoire → [ADR-0012](adr/0012-zscore-d-intensite.md) | `reference_jours = 28`, `reference_min_jours = 21` | C6, C8, C14 |
| R13 | Quand l'historique est insuffisant ou que l'écart-type est nul, il n'y a pas de z-score : l'interface affiche un état explicite. L'écart-type est tenu pour nul si s ≤ 1e-9 × max(1, \|m\|). | Décidé (cadrage) ; seuil provisoire → [ADR-0012](adr/0012-zscore-d-intensite.md) | — | C7, C8 |
| R14 | Absence longue : aucun traitement particulier en V1. Un joueur sans participation sur la fenêtre courte est listé « absent depuis N jours ». | Provisoire → [ADR-0013](adr/0013-absences-longues.md) | — | C4 |
| R15 | Les sensations sont saisies par le joueur, au plus une entrée par joueur et par jour, indépendamment des séances. | Décidé (cadrage) | — | D2 |
| R16 | Le joueur modifie son entrée du jour par son lien jusqu'à 23 h 59. Une entrée passée est corrigée ou supprimée par le préparateur de la catégorie de référence, à la demande du joueur. La rétrospection utilise les valeurs corrigées. | Décidé le 2026-10-12 → [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) | — | A4, C9 |
| R17 | Les indicateurs de sensations sont configurables par catégorie. | Décidé (cadrage) | — | C11, C12 |
| R18 | Démonstration U19 : sept indicateurs notés de 0 à 10 (concentration, plaisir, fatigue, énergie, qualité du sommeil, douleurs musculaires, compréhension des consignes) et deux heures (coucher, lever) hors du score. Fatigue et douleurs sont « bas = bon ». | Provisoire → [ADR-0010](adr/0010-indicateurs-et-echelles.md) | — | D1 |
| R19 | Score = Σ(poids × u) / Σ(poids) sur les indicateurs inclus et répondus, où u est la réponse ramenée dans [0, 1] par les bornes de l'indicateur et inversée pour « bas = bon ». Au moins 50 % du poids total doit être répondu. Affichage sur 10. | Provisoire → [ADR-0014](adr/0014-score-de-sensations.md) | `score_poids_min = 0.5` | C11, C12, C13 |
| R20 | Sensations (z) = z-score du score par rapport aux scores des entrées des 28 jours précédents, entrée courante exclue, avec au moins 6 entrées de référence et le même estimateur que l'intensité. | Provisoire → [ADR-0015](adr/0015-zscore-de-sensations.md) | `sensations_reference_jours = 28`, `sensations_reference_min_entrees = 6` | C7, C8 |
| R21 | Configuration rétroactive : tous les scores sont recalculés avec la configuration actuelle ; un indicateur ajouté ne compte que dans les entrées qui y répondent ; l'échelle d'un indicateur déjà utilisé ne change pas. | Provisoire → [ADR-0016](adr/0016-evolution-de-la-configuration.md) | — | C15 |
| R22 | Jours de questionnaire paramétrés par catégorie : tous les jours pour la démonstration U19. « Manquant » ne s'affiche que ces jours-là. | Provisoire → [ADR-0017](adr/0017-frequence-du-questionnaire.md) | `jours_questionnaire` | E2 |
| R23 | « Forme actuelle » : sensations dégradées en haut ; couleur selon (intensité − sensations) / 2, bornée à ±3 ; entrée de sensations la plus récente des 3 derniers jours ; joueurs sans point listés à part avec leur état. | Provisoire → [ADR-0018](adr/0018-graphique-forme-actuelle.md) | `fraicheur_entree_jours = 3` | E3 |
| R24 | Joueur invité : tout préparateur lit l'annuaire minimal ; le préparateur organisateur lit et écrit les participations à ses propres séances, sans voir le reste des données de l'invité. | Décidé le 2026-10-12 | — | A3 |
| R25 | Départ du groupe : archivage réversible, par le préparateur. Effacement : suppression définitive en cascade, par l'administrateur seul. | Décidé le 2026-10-12 → [ADR-0009](adr/0009-suppression-et-archivage-d-un-joueur.md) | — | D4 |
| R26 | Régularité du sommeil = écart-type de la durée de sommeil sur les 8 dernières réponses. | Reporté après la V1 | — | — |

Points reportés après la V1, avec le comportement retenu d'ici là :

| Point du cadrage | Comportement en V1 |
| --- | --- |
| Joueur sans smartphone | Non traité. Piste : saisie sur une tablette commune par le lien du joueur. |
| Droit de modifier le référentiel commun | L'administrateur seul. |
| Consultation de ses propres données par le joueur | Non : le lien ne donne accès qu'à l'entrée du jour. |
| Blessures | Hors V1 ; aucune table créée d'avance. |
| Régularité du sommeil | Hors V1 (R26). |

### Paramètres retenus

| Paramètre | Valeur | Emplacement | Source |
| --- | --- | --- | --- |
| `fuseau` | Europe/Paris | `config/calcul.toml` | R09 |
| `facteur_echelle_charge` | 10 | `config/calcul.toml` | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) |
| `fenetre_courte_jours` | 7 | `config/calcul.toml` | [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) |
| `fenetre_longue_jours` | 28 | `config/calcul.toml` | [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) |
| `reference_jours` | 28 | `config/calcul.toml` | [ADR-0012](adr/0012-zscore-d-intensite.md) |
| `reference_min_jours` | 21 | `config/calcul.toml` | [ADR-0012](adr/0012-zscore-d-intensite.md) |
| `tolerance_ecart_type_nul` | 1e-9, relative | `config/calcul.toml` | [ADR-0012](adr/0012-zscore-d-intensite.md) |
| `score_poids_min` | 0,5 | `config/calcul.toml` | [ADR-0014](adr/0014-score-de-sensations.md) |
| `sensations_reference_jours` | 28 | `config/calcul.toml` | [ADR-0015](adr/0015-zscore-de-sensations.md) |
| `sensations_reference_min_entrees` | 6 | `config/calcul.toml` | [ADR-0015](adr/0015-zscore-de-sensations.md) |
| `fraicheur_entree_jours` | 3 | `config/calcul.toml` | [ADR-0018](adr/0018-graphique-forme-actuelle.md) |
| `couleur_borne` | 3 | `config/calcul.toml` | [ADR-0018](adr/0018-graphique-forme-actuelle.md) |
| `jours_questionnaire` | Les sept jours pour U19 | Colonne de la catégorie, en base | [ADR-0017](adr/0017-frequence-du-questionnaire.md) |
| Bornes, sens, poids et inclusion des indicateurs | Tableau de l'ADR | Table `indicateur`, en base | [ADR-0010](adr/0010-indicateurs-et-echelles.md) |
| Échelle des RPE | Entiers de 0 à 10 | Contrainte en base ; un changement passe par une migration | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) |
| Bornes de la durée | Entiers de 1 à 300 minutes | Contrainte en base ; un changement passe par une migration | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) |
| `debut_saison` | 1er juillet | `config/calcul.toml` | Proposé, à valider avant la phase 6 (données brutes et export) |

## 6. Données manipulées

Entités et champs principaux. Le détail des types, des contraintes et des index est dans [02-architecture.md](02-architecture.md).

| Entité | Champs principaux | Règles |
| --- | --- | --- |
| Catégorie | code (U19), libellé, jours de questionnaire, active | Code unique |
| Préparateur | compte (lien vers le compte de connexion), catégorie | Un compte de connexion = au plus un profil préparateur |
| Joueur | nom, prénom, date de naissance, catégorie de référence, actif | Données toujours fictives en V1 |
| Lien joueur | joueur, empreinte du jeton, créé le, créé par, révoqué le | Au plus un lien actif par joueur ; empreinte unique |
| Séance | catégorie organisatrice, date, type, durée en minutes, statut, créée par, validée le | Durée dans la plage autorisée ; type et statut dans une liste fermée |
| Participation | séance, joueur, RPE cardio, RPE musculaire, RPE TETA | Une participation par joueur et par séance ; RPE dans l'échelle ; RPE obligatoires une fois la séance validée |
| Indicateur | catégorie, code, libellé, type, borne basse, borne haute, sens, poids, inclus dans le score, ordre, actif | Code unique par catégorie ; borne basse < borne haute ; poids ≥ 0 |
| Entrée de sensations | joueur, date | Une entrée par joueur et par jour |
| Réponse | entrée, indicateur, valeur | Une réponse par indicateur et par entrée ; valeur dans les bornes de l'indicateur |

Toutes les entités modifiables portent une date de création, une date de dernière modification et l'auteur de cette modification.

Les résultats du moteur ne sont pas stockés : ils sont recalculés à chaque consultation, pour une date donnée.

| Résultat | Granularité | Valeur ou état |
| --- | --- | --- |
| Charge du jour | joueur × jour | valeur |
| CE courte, CE longue | joueur × jour | valeur, avec un indicateur de fenêtre incomplète |
| Intensité | joueur × jour | valeur, « historique insuffisant » ou « non calculable » |
| Score de sensations | joueur × entrée | valeur, ou « réponses insuffisantes » |
| Sensations (z) | joueur × entrée | valeur, « historique insuffisant » ou « non calculable » |

## 7. Exigences non fonctionnelles

| Exigence | Cible | Statut |
| --- | --- | --- |
| Supports | Ordinateur, tablette, téléphone ; mise en page adaptée à chaque largeur | Décidé (cadrage) |
| Langue et fuseau | Interface en français ; fuseau Europe/Paris | Décidé le 2026-10-12 |
| Saisie d'une séance de 25 joueurs | Moins de 5 minutes sur ordinateur et sur tablette | Proposition du cadrage, mesurée en recette |
| Questionnaire joueur | Moins d'une minute sur téléphone | Proposition du cadrage, mesurée en recette |
| Accessibilité des graphiques | Chaque graphique est accompagné d'un tableau de ses valeurs | Proposé ; sert aussi au cas E3 |
| Premier affichage après inactivité | Moins de 10 secondes, base et fonction comprises | Proposé ; mesuré en phase 1 |
| Maintenance | Moins de 2 heures par mois | Proposition du cadrage |
