# Cadrage de projet — Suivi de charge U19 (reprise à zéro)

Ce document est mon premier message. Il relance à zéro un projet déjà cadré une première fois, puis mal réalisé : je garde le fond fonctionnel, je refais toute la réalisation dans un nouveau dépôt GitHub privé. Deux exigences passent avant le reste : les tests (section 7) et un découpage en phases fermées par des critères vérifiables (section 8).

> Version publique, anonymisée le 2026-10-12 : le nom du club et celui du préparateur sont retirés ([ADR-0001](adr/0001-depot-public-et-protection-de-main.md)). Le dépôt est finalement public. Les décisions de la phase 0, qui priment sur les sections 1 à 12 en cas d'écart, sont en [section 13](#13-synthèse-de-la-phase-0).

## 1. Instructions pour Claude

Tu es mon architecte logiciel et tech lead sur ce projet. À partir de ce document, tu cadres entièrement le projet avant toute ligne de code.

**Règles de réponse :**

1. Commence par reformuler le projet en 3 à 5 lignes pour vérifier que tu l'as compris.
2. Si une information bloquante manque ou si deux contraintes se contredisent, pose-moi tes questions **avant** de proposer la stack (5 questions maximum, classées par importance).
3. Justifie chaque choix technique par mes contraintes (niveau, matériel, budget, temps), et cite l'alternative écartée.
4. Privilégie la solution la plus simple qui atteint l'objectif. Signale toute sur-ingénierie que je te demanderais.
5. Respecte strictement le niveau de collaboration choisi en section 9.
6. Respecte strictement le format de réponse de la section 11.
7. Pour chaque choix technique, dis comment il se teste en local et en CI. Un choix qui ne se teste pas automatiquement est écarté, sauf si tu montres qu'il n'existe pas d'alternative.
8. La première tentative (section 3.2 et annexe A) est un retour d'expérience, pas une base de code. Ne réutilise aucun de ses fichiers, et montre comment ta proposition évite chacun des défauts listés.
9. Dans la section 5.4, ce qui est marqué « proposition » ou « ouvert » n'a pas été validé par le préparateur physique. Ne le présente pas comme acquis et garde-le paramétrable.
10. Langue des échanges, de la documentation et des messages de commit : français. Code : identifiants techniques en anglais, vocabulaire métier en français (joueur, séance, charge…) tel que défini dans le glossaire, commentaires en français.

## 2. Qui je suis

- **Profil** : statisticien de formation (ENSAI). J'ai fait mon stage de M1 il y a trois ans au centre de formation d'un club professionnel de football, où j'ai écrit la V0 de cet outil en R Shiny sans aucune expérience de développement. Depuis, j'ai acquis des compétences en développement logiciel, en architecture et en déploiement.
- **Disponibilité** : plus de 10 heures par semaine.
- **Ce que je veux en tirer** : livrer avant tout.
- **Compétences à développer sur ce projet** : tests automatisés et intégration continue (le point faible de la première tentative), sécurité d'accès aux données.

**Mon niveau par technologie** (0 = jamais utilisé, 3 = autonome) :

| Domaine | Niveau 0-3 | Commentaire |
| --- | --- | --- |
| Python | 3 | Python 3.11 et 3.12 installés, avec uv |
| JavaScript / TypeScript | 0 | |
| HTML / CSS | 1 | |
| SQL / bases de données | 3 | Postgres déjà utilisé en conteneur sur un autre projet |
| Git / GitHub | 2-3 | |
| Docker / conteneurs | 1 | Docker Desktop installé |
| Tests automatisés | 2 | |
| Machine learning / RL | 2-3 | |
| Déploiement / hébergement | 0 | |
| Autre : R / Shiny | 1 | Langage de la V0 |

## 3. Contexte du projet

### 3.1 Fiche

- **Nom provisoire** : Suivi de charge U19. Le nom du nouveau dépôt reste à choisir ; l'ancien dépôt `u19-suivi-charge` est abandonné.
- **Pitch en une phrase** : une application web qui permet au préparateur physique d'un centre de formation de football de suivre la charge d'entraînement et l'état de forme de ses joueurs, et de repérer d'un coup d'œil ceux dont la charge monte alors que les sensations se dégradent.
- **Origine** : je veux reprendre contact avec le préparateur physique des U19 pour échanger sur l'évolution de ses outils, et lui montrer une V1 solide, réellement déployée, là où la V0 n'a jamais quitté mon poste.
- **Nature du projet** : personnel, destiné à une structure. Le club n'a rien commandé ; c'est une démonstration que je lui apporte.
- **Commanditaire** : le préparateur physique de la catégorie U19 de ce centre de formation.
- **Niveau technique du commanditaire** : basique (il travaillait avec Excel et Google Forms).
- **Références** : l'interface de la V0 (annexe B) ; la méthode session-RPE de Foster (charge = RPE × durée), dont la formule de charge est une variante à trois dimensions.

### 3.2 Historique

**La V0, il y a trois ans.** Une application R Shiny, alimentée à la main à partir d'un fichier Excel que le préparateur remplissait après chaque séance. Les sensations des joueurs étaient collectées à part, par Google Forms, puis réimportées. L'application ne tournait qu'en local sur mon poste : le préparateur dépendait de moi pour chaque mise à jour, sans accès distant ni usage au bord du terrain.

**La première tentative de V1, abandonnée.** Le cadrage fonctionnel était bon. La réalisation s'est arrêtée à une coquille : un projet généré non nettoyé, une arborescence de dossiers vides, et une seule migration SQL, sans aucun test et selon toute vraisemblance jamais exécutée. Un audit a ensuite exécuté cette migration et y a trouvé des failles d'accès aux données et des erreurs de calcul. Le détail est en annexe A ; chaque constat y est traduit en règle pour ce nouveau projet.

**Ce que je garde de la première tentative :**

- tout le cadrage fonctionnel (sections 4 et 5) ;
- les principes de modélisation : le RPE est saisi par le staff, les sensations par le joueur ; une séance appartient à la catégorie qui l'organise, mais la charge suit le joueur ; un cœur commun à tous et une configuration des indicateurs par catégorie ;
- l'idée d'une seule source de vérité pour les formules ;
- les Conventional Commits et les branches courtes.

**Ce que je ne garde pas :** le code, le schéma SQL, la configuration, et la manière de travailler (rien n'était exécuté ni testé avant d'être commité).

## 4. Objectif final et critères de succès

- **Vision finale** : une application déployée, utilisable sur ordinateur, tablette et téléphone. Le préparateur y saisit en une fois les RPE de tout le groupe après chaque séance. Chaque joueur renseigne ses sensations depuis son téléphone, par un lien personnel, sans compte ni mot de passe. Les tableaux de bord se mettent à jour seuls : forme actuelle du groupe, fiche par joueur avec historique et consultation rétroactive, suivi des blessures. Plusieurs catégories peuvent cohabiter, chacune avec son propre questionnaire, sans casser l'historique d'un joueur qui change de groupe.
- **MVP** : une seule catégorie (U19), un compte staff, des données fictives. Le préparateur crée une séance et saisit la grille RPE ; un joueur répond à son questionnaire par son lien ; le graphique « Forme actuelle » et la fiche joueur affichent des valeurs prouvées par le jeu de référence. Le tout est déployé à une URL publique dès la phase 1.
- **Critères de succès mesurables** (les seuils chiffrés sont des propositions à ajuster) :
    - L'application est déployée et le préparateur l'utilise sans aucune intervention de ma part sur les données.
    - Le préparateur saisit une séance de 25 joueurs en moins de 5 minutes, sur ordinateur comme sur tablette.
    - Un joueur remplit son questionnaire en moins d'une minute sur son téléphone.
    - Tous les cas obligatoires du moteur de calcul passent (section 7.3).
    - Les tests d'accès prouvent qu'un visiteur non connecté ne lit et n'écrit rien, et qu'un lien joueur ne permet que de déposer son propre questionnaire (section 7.4).
    - Aucune fusion sur `main` sans CI verte. Chaque phase est fermée avec son document, sa recette et son tag.
    - Je sais expliquer au préparateur, point par point, ce qui rendait la V0 contraignante et ce que la V1 change.
- **Hors périmètre** :
    - application mobile native ;
    - modélisation prédictive (risque de blessure, profils de joueurs) ;
    - intégration de GPS ou de capteurs ;
    - notifications push en V1 ;
    - usage par plusieurs clubs ;
    - toute donnée réelle de joueur tant que la gouvernance de la donnée n'est pas validée avec le club (section 6.5).
- **Échéance** : aucune
- **Après le projet** : maintenu par moi.

## 5. Utilisateurs et besoins fonctionnels

### 5.1 Utilisateurs

| Profil | Combien | Ce qu'il fait avec l'outil | Support utilisé |
| --- | --- | --- | --- |
| Préparateur physique | 1 en V1, un par catégorie à terme | Saisit les séances et les RPE, consulte les tableaux de bord, gère les liens des joueurs, suit les blessures | Ordinateur, tablette ou téléphone au bord du terrain |
| Joueur U19 (en partie mineur) | 25 à 30 (ordre de grandeur) | Renseigne ses sensations du jour | Téléphone personnel |
| Administrateur technique (moi) | 1 | Crée les comptes staff, gère le référentiel commun | Ordinateur |

### 5.2 Fonctionnalités souhaitées

Liste brute, à prioriser en MoSCoW. Mon avis sur le MVP est en section 4 ; tu peux le contester.

- **Saisie d'une séance** : un en-tête renseigné une fois (date, type foot / musculation / yoga / autre, durée, catégorie organisatrice). La liste des participants est pré-remplie avec les joueurs de la catégorie et modifiable (ajout d'un joueur d'un autre groupe, retrait d'un absent ou d'un blessé).
- **Grille RPE type tableur** : une ligne par joueur, trois colonnes (cardio, musculaire, TETA), code couleur en direct, enregistrement en brouillon avant validation. Une colonne indique si le joueur a rempli son questionnaire du jour (badge Reçu / Manquant).
- **Questionnaire de sensations côté joueur** : accès par lien personnel ou QR code généré par le staff, sans compte. Le joueur ne voit que les indicateurs de sa catégorie de référence.
- **Graphique « Forme actuelle »** (le plus important pour le préparateur) : un point par joueur, intensité en abscisse et sensations en ordonnée, chacun par rapport à sa propre moyenne récente, avec un gradient de couleur. Il sert à repérer une intensité au-dessus de la moyenne combinée à de mauvaises sensations.
- **Fiche joueur**, avec choix d'une date de rétrospection :
    - tableau des RPE des dernières séances, coloré selon l'intensité ;
    - barres de charge d'entraînement sur 7 jours et sur 4 semaines ;
    - barres des sensations de la dernière entrée ;
    - heatmap des sensations sur 7 jours par indicateur, avec un total.
- **Données brutes** : consultation des séances et des charges depuis le début de la saison, et export.
- **Historique des séances** : liste, correction, suppression.
- **Réglages** : gestion des joueurs, génération et révocation des liens d'accès, configuration des indicateurs par catégorie (libellé, type, poids, sens, inclusion dans le score).
- **Suivi des blessures** : zone anatomique standardisée, côté, statut (signalée, en observation, confirmée, résolue), carte corporelle. Une blessure peut être déclenchée par une réponse au questionnaire ou saisie par le staff.
- **Plusieurs catégories** : chaque préparateur a son jeu d'indicateurs ; le joueur garde le questionnaire de sa catégorie de référence.
- **Régularité du sommeil** : indicateur dérivé de la variabilité de la durée de sommeil.
- **Import de l'historique** Excel de la V0.
- **Installation sur l'écran d'accueil** du téléphone et rappels.

### 5.3 Parcours clés

**Parcours du préparateur, après une séance :**

1. Il se connecte et ouvre « Nouvelle séance ».
2. Il renseigne la date, le type et la durée. La liste des joueurs de sa catégorie apparaît.
3. Il retire les absents et ajoute, si besoin, un joueur venu d'un autre groupe.
4. Il saisit les trois RPE de chaque joueur dans la grille, au clavier, ligne après ligne.
5. Il valide. La charge de chaque joueur est calculée.
6. Il ouvre « Forme actuelle » et voit immédiatement les joueurs à surveiller.
7. Il ouvre la fiche d'un joueur pour comprendre son historique.

**Parcours du joueur, chaque jour de questionnaire :**

1. Il ouvre son lien personnel depuis l'écran d'accueil de son téléphone.
2. Il répond aux indicateurs de sa catégorie.
3. Il envoie. Côté staff, son badge passe à « Reçu ».

### 5.4 Règles métier

**Vocabulaire.** RPE : ressenti d'effort (*Rate of Perceived Exertion*), noté sur 10. TETA : dimension technique et tactique de la séance. CE : charge d'entraînement. Z-score : écart d'une valeur à la moyenne récente du joueur, exprimé en écarts-types.

**Décidé :**

- Après chaque séance, le staff saisit trois RPE par joueur présent : cardio, musculaire, TETA.
- Les sensations sont saisies par le joueur lui-même, au plus une entrée par joueur et par jour, indépendamment des séances.
- Une séance appartient à la catégorie qui l'organise. Un joueur garde sa catégorie de référence et son questionnaire, même s'il s'entraîne ponctuellement avec un autre groupe.
- La charge et les z-scores se calculent par joueur, sur toutes ses participations, quelle que soit la catégorie organisatrice.
- Chaque joueur est comparé à lui-même, jamais au groupe.
- Les indicateurs de sensations sont configurables par catégorie.
- Quand l'historique est insuffisant ou que l'écart-type est nul, il n'y a pas de z-score : l'interface affiche un état explicite.
- Une séance en brouillon ne compte dans aucun calcul.

**Proposition** (corrections issues de l'audit, à valider par moi sur le plan statistique et par le préparateur sur le plan métier) :

- Charge d'une séance = moyenne des trois RPE × durée en minutes × 10. Le facteur 10 est une constante d'échelle sans effet sur les z-scores.
- Charge du jour = somme des charges des séances validées du jour, et 0 les jours sans séance. Les calculs se font sur un calendrier continu par joueur, pas sur la liste des séances.
- CE 7 jours = somme des charges du jour sur 7 jours glissants, jour courant inclus. CE 4 semaines = la même somme sur 28 jours.
- Intensité (abscisse du graphique) = (CE 7 jours du jour − moyenne de référence) / écart-type de référence. La référence est l'ensemble des CE 7 jours des 28 jours **précédents**, jour courant exclu.
- Score de sensations d'une entrée = moyenne pondérée des indicateurs inclus dans le score, chacun ramené à une échelle commune et orienté dans le même sens. Elle est calculée sur les réponses présentes, avec un nombre minimal de réponses.
- Sensations (ordonnée du graphique) = z-score de ce score par rapport aux entrées précédentes du joueur sur 28 jours, entrée courante exclue.
- Régularité du sommeil = écart-type de la durée de sommeil sur les 8 dernières réponses.

**Ouvert** (à trancher avec le préparateur ; à garder paramétrable d'ici là) :

- Le parenthésage exact de la formule de charge. Les notes d'origine indiquent `(cardio + musculaire + TETA) × durée / 3 × 10`.
- La longueur des fenêtres (7 et 28 jours) et le seuil d'historique minimal, à exprimer en jours ou en entrées.
- Le traitement des 6 premiers jours d'historique d'un joueur, où la CE 7 jours est incomplète.
- Le traitement d'une blessure ou d'une absence longue : faut-il laisser la charge retomber à zéro, ou geler la référence ?
- La liste exacte des indicateurs. Sont connus : concentration, plaisir, fatigue, énergie, sommeil, douleurs musculaires, compréhension des consignes, heures de coucher et de lever. La première tentative parlait de 11 items sans jamais les lister.
- L'échelle des indicateurs. La V0 utilisait 0 à 10 ; la première tentative est passée à 1 à 7 sans en garder la raison.
- La fréquence du questionnaire. Les documents disaient « quotidien » à un endroit et « deux fois par semaine à jours fixes » à un autre.
- Le sens du graphique. Dans la V0, les mauvaises sensations étaient en haut et en rouge, les bonnes en bas et en jaune.
- Ce qui se passe quand on ajoute un indicateur ou qu'on change un poids en cours de saison, pour éviter un saut artificiel du score.
- La solution pour un joueur sans smartphone (par exemple une tablette commune au vestiaire).
- Qui a le droit de modifier le référentiel commun (catégories, formule de charge).
- Un joueur peut-il consulter ses propres données ?

## 6. Contraintes

### 6.1 Matériel

| Élément | Valeur |
| --- | --- |
| Système d'exploitation | Windows 11 Famille, WSL 2 installé |
| Processeur | Intel Core i7-1255U (10 cœurs, 12 threads) |
| Mémoire vive | 16 Go |
| Carte graphique | Intel Iris Xe intégrée, pas de carte dédiée |
| Espace disque libre | 710 Go |

### 6.2 Environnement

- **Droits administrateur sur la machine** : oui.
- **Restrictions** : le dépôt ne doit pas vivre dans un dossier synchronisé. L'ancien était dans OneDrive, avec `node_modules` et `.git` synchronisés.
- **Outils déjà installés** : VS Code avec l'extension Claude Code, Git 2.40, GitHub CLI 2.102, Node.js 24 (npm 11), Python 3.11 et 3.12 avec uv, Docker Desktop 29 (image `postgres:16` déjà présente), WSL 2.
- **Non installés** : Supabase CLI, R.

### 6.3 Budget

| Poste | Montant max |
| --- | --- |
| Mise de départ | 0 € |
| Mensuel récurrent | 0 €/mois |
| Nom de domaine | aucun |

Avec un budget nul, vérifie les limites actuelles des offres gratuites avant de les retenir, et dis-moi lesquelles me concernent. Je pense en particulier à :

- la protection de branche et les vérifications obligatoires sur un dépôt **privé** avec un compte GitHub gratuit, et la parade si elles ne sont pas disponibles ;
- le quota de minutes de CI sur un dépôt privé ;
- la mise en pause des bases de données gratuites en cas d'inactivité, gênante pour une application de démonstration ;
- l'absence de sauvegardes automatiques sur les offres gratuites ;
- les conditions d'usage non commercial des hébergeurs, pour un outil destiné à un club professionnel.

### 6.4 Technologies

- **Imposées** : aucune.
- **Piste de la première tentative**, à confirmer ou à remplacer en le justifiant : Next.js et Tailwind pour l'interface, Supabase pour Postgres et l'authentification, Vercel pour l'hébergement, calculs glissants en SQL avec des fonctions fenêtrées. Le raisonnement était : développeur seul, priorité au déploiement, le moins d'exploitation possible.
- **Décision que j'attends de toi, sous forme d'ADR** : où vit le moteur de calcul (en base ou dans le code applicatif). Contraintes : une seule implémentation des formules, des tests qui tournent en local et en CI sur le jeu de référence, des paramètres (fenêtres, poids) modifiables sans réécrire les formules.
- **À éviter** :
    - tout composant qui ne peut pas tourner en local et en CI sans compte cloud ;
    - toute solution dont le déploiement dépend de mon poste ;
    - toute dépendance ajoutée sans besoin immédiat.

### 6.5 Données

- **Sources** : saisie manuelle par le staff (séances, RPE, blessures) et par les joueurs (sensations). Éventuellement, import de l'historique Excel de la V0.
- **Volume estimé** : très faible. Environ 30 joueurs et 250 séances par saison et par catégorie, soit moins de 10 000 participations et moins de 100 000 réponses de sensations par saison.
- **Données personnelles ou sensibles** : oui. Identité et date de naissance de joueurs en partie mineurs, données de forme, de sommeil, de douleur et de blessure. Je les traite par précaution comme des données de santé au sens du RGPD.

Règles qui en découlent :

- La V1 ne contient que des données fictives. Aucune donnée réelle n'entre dans l'application tant que la base légale, l'information des joueurs et de leurs représentants légaux, la durée de conservation et les droits d'accès ne sont pas définis avec le club.
- Le droit à l'effacement est prévu dès le modèle de données : supprimer ou anonymiser un joueur est une opération définie et testée.
- Les données de démonstration sont générées par un script versionné, jamais copiées de données réelles.

### 6.6 Légal et sécurité

- **Points connus** : RGPD (ci-dessus). Projet personnel : ni le nom ni le logo du club dans l'interface tant que le club n'a pas donné son accord.
- **Authentification nécessaire** : oui, avec deux modèles distincts.
    - **Staff** : compte nominatif avec mot de passe, créé par l'administrateur. L'inscription publique est fermée.
    - **Joueur** : lien personnel sans mot de passe. Le jeton est aléatoire et long, stocké haché, révocable et régénérable par le staff. Il ne permet que de déposer le questionnaire du jour.

**Modèle d'accès attendu**, à spécifier avant le schéma :

| Qui | Peut lire | Peut écrire |
| --- | --- | --- |
| Visiteur non connecté | Rien | Rien |
| Joueur, par son lien | Les indicateurs de sa catégorie, et si son entrée du jour existe déjà | Son entrée de sensations du jour |
| Staff d'une catégorie | Les joueurs dont c'est la catégorie de référence et toutes leurs participations, y compris aux séances d'autres catégories | Les séances de sa catégorie, les blessures et les liens de ses joueurs, ses indicateurs |
| Administrateur | Tout | Le référentiel et les comptes staff |

**Exigences de sécurité** :

- refus par défaut sur chaque table, chaque vue et chaque fonction exposée ;
- aucune clé à privilèges côté navigateur ;
- secrets hors dépôt, avec un `.env.example` versionné ;
- audit des dépendances en CI.

### 6.7 Maintenance et passation

- **Qui maintient après la livraison** : moi. Le préparateur doit être autonome au quotidien : saisie, consultation, gestion des joueurs et des liens, sans jamais me solliciter pour les données.
- **Temps de maintenance acceptable** : moins de 2 heures par mois (proposition).

## 7. Exigences de test

### 7.1 Principe

Rien n'est considéré comme fait tant qu'un test automatisé ne le prouve pas et que la CI ne l'a pas exécuté. La première tentative n'avait aucun test : ses défauts graves (annexe A) ne sont apparus qu'après coup, dès que quelqu'un a exécuté le schéma. Ici, l'outillage de test est livré avant la première fonctionnalité (phase 1), et les tests du moteur de calcul sont écrits avant son implémentation (phase 3).

### 7.2 Règles pour chaque PR

- La PR contient les tests de ce qu'elle ajoute ou modifie.
- La CI doit être verte : lint, typage, tests unitaires, tests d'intégration sur une vraie base, migrations rejouées depuis zéro, build, audit des dépendances.
- La description de la PR dit comment le changement a été vérifié, avec la commande et sa sortie.
- Une correction de bug commence par un test qui échoue et reproduit le bug.

### 7.3 Moteur de calcul

C'est le cœur du produit : un chiffre faux conduit le préparateur à mal doser la charge d'un joueur.

- **Jeu de référence** : un petit jeu de données versionné, avec ses résultats attendus. Les valeurs attendues viennent d'un calcul indépendant de l'implémentation : je les produis moi-même, à la main, dans un tableur ou par un script Python séparé. C'est ma part du travail. Elles ne sont jamais obtenues en exécutant le code testé.
- **Seuil de couverture** imposé en CI sur le module de calcul et sur la validation des saisies, pas de seuil global.
- **Si je retrouve** le code R ou un export Excel de la V0, un test compare les résultats sur un échantillon.

Cas obligatoires :

| Id | Situation | Résultat attendu |
| --- | --- | --- |
| C1 | Une séance simple | La charge vaut la valeur calculée à la main |
| C2 | Deux séances le même jour | Une seule ligne pour ce jour, charges additionnées |
| C3 | Jours sans séance | Présents dans la série avec une charge de 0 ; la CE 7 jours décroît |
| C4 | Joueur absent 10 jours | La CE 7 jours retombe à 0 et l'intensité est recalculée chaque jour |
| C5 | Séance en brouillon | Ignorée dans tous les calculs |
| C6 | Charge extrême après un historique régulier mais non constant | Z-score très supérieur à 2 (la première tentative plafonnait à 1,79) |
| C7 | Historique parfaitement constant | Écart-type nul : pas de z-score, état « non calculable », aucune division par zéro |
| C8 | Historique trop court | Pas de z-score, état « historique insuffisant » |
| C9 | Date de rétrospection D | Résultat identique à celui du jour D : aucune donnée postérieure utilisée |
| C10 | Séance faite avec une autre catégorie | Charge comptée dans l'historique du joueur |
| C11 | Indicateurs d'échelles différentes dans le score | Ramenés à une échelle commune avant agrégation |
| C12 | Indicateur inversé (valeur basse = bon état) | Orienté correctement dans le score |
| C13 | Réponse manquante à un indicateur | Score calculé sur les réponses présentes ; sous le minimum, pas de score |
| C14 | Toutes les charges multipliées par une constante | Aucun z-score ne change |
| C15 | Ajout d'un indicateur ou changement de poids en cours de saison | Comportement décidé (section 5.4), puis testé |

### 7.4 Accès et sécurité

Ces tests tournent en CI contre une vraie base locale, puis une fois contre l'environnement déployé avant la mise en service.

| Id | Situation | Résultat attendu |
| --- | --- | --- |
| A1 | Visiteur non connecté | Aucune lecture, aucune écriture, sur chaque table, vue et fonction |
| A2 | Nouvel objet ajouté sans règle d'accès | A1 échoue : la liste des objets testés est lue dans le catalogue de la base, pas écrite à la main |
| A3 | Staff d'une catégorie | Voit ses joueurs et toutes leurs participations ; ne voit pas les joueurs d'une autre catégorie |
| A4 | Lien joueur valide | Dépose son entrée du jour ; ne lit ni son historique ni les autres joueurs |
| A5 | Lien invalide, révoqué ou régénéré | Refusé ; aucun jeton n'est lisible en base, par personne |
| A6 | Tentative d'inscription publique | Impossible |

### 7.5 Données et migrations

| Id | Situation | Résultat attendu |
| --- | --- | --- |
| D1 | Valeur hors plage (RPE, échelle, durée nulle ou négative) | Rejetée à la saisie et en base |
| D2 | Doublon de participation, ou seconde entrée de sensations le même jour | Rejeté |
| D3 | Base vide | Toutes les migrations s'appliquent depuis zéro et les données de démonstration se chargent, à chaque PR |
| D4 | Suppression ou anonymisation d'un joueur | Comportement défini et testé |

### 7.6 Parcours de bout en bout

Dans un vrai navigateur, contre l'application complète.

| Id | Parcours | Résultat attendu |
| --- | --- | --- |
| E1 | Le staff se connecte, crée une séance, remplit la grille pour 25 joueurs et valide | Les charges apparaissent sur le tableau de bord |
| E2 | Un joueur ouvre son lien en format mobile, répond et envoie | Le badge passe à « Reçu » côté staff |
| E3 | Le staff ouvre une fiche joueur du jeu de référence | Les valeurs affichées sont les valeurs attendues |

### 7.7 Ce que tu ne fais pas avec les tests

- Supprimer, désactiver ou assouplir un test pour faire passer la CI, sans mon accord explicite.
- Écrire un test dont la valeur attendue est recopiée de la sortie du code.
- Écrire « testé » sans montrer la commande et sa sortie.
- Remplacer la base par un simulacre dans les tests d'accès et de calcul : ils tournent sur une vraie base.

### 7.8 Recette manuelle de fin de phase

À chaque fin de phase, je déroule moi-même une liste de vérifications sur l'environnement déployé, sur ordinateur et sur téléphone. La liste et son résultat sont consignés dans le document de phase. Tu prépares la liste ; tu ne la coches pas à ma place.

## 8. Découpage en phases prédéfini

Les phases ci-dessous sont imposées dans leurs grandes lignes. Tu peux les ajuster ou en changer l'ordre si tu le justifies.

### 8.1 Règles communes

- Chaque phase a sa fiche (`docs/phases/phase-NN-<nom>.md`), écrite et validée par moi **avant** sa première PR : objectif, PR prévues, critères de fin.
- Une phase se réalise en plusieurs petites PR, de 3 à 6 en ordre de grandeur. La fiche est mise à jour à chaque fusion.
- Une phase ne commence pas tant que la précédente n'est pas fermée : critères cochés, recette faite, tag posé.
- L'application reste déployée et utilisable à la fin de chaque phase.
- Les titres de PR ci-dessous sont indicatifs.

### 8.2 Vue d'ensemble

| Phase | Nom | Ce qui existe à la fin | Niveau Claude | Tag |
| --- | --- | --- | --- | --- |
| 0 | Cadrage | Les documents de référence, aucune ligne de code | Conversation | — |
| 1 | Socle et chaîne de qualité | Une page vide déployée, une CI qui bloque, un test qui tourne à chaque niveau | 4 | v0.1.0 |
| 2 | Modèle de données et accès | Le schéma, les règles d'accès, les comptes staff, des données fictives | 3 | v0.2.0 |
| 3 | Moteur de calcul | Charges, CE 7 jours, CE 4 semaines et z-scores prouvés sur le jeu de référence | 3 | v0.3.0 |
| 4 | Saisie des séances | Le préparateur crée une séance et saisit la grille RPE | 4 | v0.4.0 |
| 5 | Questionnaire joueur | Le joueur répond depuis son lien personnel | 4, et 3 pour le jeton | v0.5.0 |
| 6 | Tableaux de bord | « Forme actuelle » et fiche joueur | 4 | v0.6.0 |
| 7 | Mise en service | La V1 en production avec des données de démonstration, prête à être montrée | 4 | v1.0.0 |

### 8.3 Détail

**Phase 0 — Cadrage.**
- Objectif : figer ce qu'on construit et comment on le prouve, avant d'écrire du code.
- Livrables : `00-cadrage.md`, spécifications, architecture, stratégie de tests, premiers ADR, `CLAUDE.md`, fiche de la phase 1.
- Critères de fin : tes questions ont une réponse ; la stack est décidée et justifiée ; le modèle d'accès est écrit ; les règles de calcul sont spécifiées avec leur statut ; je valide l'ensemble.
- Ces documents sont commités dans la première PR de la phase 1.

**Phase 1 — Socle et chaîne de qualité.**
- Objectif : prouver que la chaîne complète fonctionne (écrire, tester, fusionner, déployer) avant toute fonctionnalité.
- PR indicatives : initialisation du projet nettoyée de tout contenu d'exemple ; lint, format et typage ; tests unitaires, d'intégration et de bout en bout, avec un test trivial chacun ; base locale reproductible et migration vide ; CI complète ; déploiement avec prévisualisation par PR ; modèle de PR et documentation.
- Critères de fin :
    - une PR avec un test en échec est bloquée, démonstration faite ;
    - l'application est joignable à une URL publique ;
    - un clone neuf s'installe, se lance et passe ses tests avec les seules commandes du README ;
    - le dépôt est hors de tout dossier synchronisé.

**Phase 2 — Modèle de données et accès.**
- Objectif : un schéma contraint et un modèle d'accès prouvé, avant toute interface.
- PR indicatives : référentiel (catégories, joueurs, staff) ; séances et participations ; indicateurs, entrées et réponses de sensations ; authentification du staff et règles d'accès ; données de démonstration générées par script.
- Critères de fin : cas A1, A2, A3, A6 et D1 à D4 au vert ; migrations rejouées depuis zéro en CI ; aucune donnée réelle.

**Phase 3 — Moteur de calcul.**
- Objectif : des chiffres justes, prouvés indépendamment de l'implémentation.
- PR indicatives : ADR sur les formules et les fenêtres, jeu de référence et tests, tous en échec ; charge du jour sur calendrier continu ; CE 7 jours et CE 4 semaines ; z-score d'intensité ; score de sensations ; z-score de sensations.
- Critères de fin : cas C1 à C15 au vert ; seuil de couverture atteint ; mon contrôle indépendant est fait et consigné ; aucune interface dans cette phase.

**Phase 4 — Saisie des séances.**
- Objectif : le préparateur remplace son fichier Excel.
- PR indicatives : connexion et structure des pages ; création d'une séance ; grille RPE avec validation et code couleur ; brouillon puis validation ; historique, correction et suppression.
- Critères de fin : parcours E1 au vert ; tests de validation des saisies ; utilisable sur tablette ; recette faite.

**Phase 5 — Questionnaire joueur.**
- Objectif : le joueur répond seul, sans compte, et le formulaire externe disparaît.
- PR indicatives : génération, révocation et régénération des liens ; formulaire mobile rendu selon les indicateurs de la catégorie ; une entrée par jour ; badge Reçu / Manquant dans la grille.
- Critères de fin : cas A4 et A5 au vert ; parcours E2 au vert en format mobile ; recette faite sur un vrai téléphone.

**Phase 6 — Tableaux de bord.**
- Objectif : rendre visible ce que le moteur calcule.
- PR indicatives : graphique « Forme actuelle » ; fiche joueur, charge ; fiche joueur, sensations ; date de rétrospection ; données brutes et export.
- Critères de fin : parcours E3 au vert ; les états « historique insuffisant » et « non calculable » sont affichés ; aucune formule n'est réécrite dans l'interface.

**Phase 7 — Mise en service de la V1.**
- Objectif : une V1 que je peux montrer et laisser entre les mains du préparateur.
- PR indicatives : environnement de production et jeu de démonstration ; sauvegarde et restauration ; guide d'utilisation d'une page ; note « ce que la V1 change par rapport à la V0 ».
- Critères de fin : tests d'accès rejoués contre l'environnement déployé ; restauration testée ; audit des dépendances sans alerte critique ; recette complète sur ordinateur et téléphone.

**Après la V1.** Non planifié, à reprioriser après le retour du préparateur : blessures et carte corporelle, configuration des indicateurs dans l'interface, plusieurs catégories et rôles, régularité du sommeil, import de l'historique, installation sur l'écran d'accueil et rappels, gouvernance de la donnée avec le club avant toute donnée réelle.

## 9. Mode de collaboration avec Claude

| Niveau | Accès donnés à Claude | Ce que fait Claude | Ce que je fais |
| --- | --- | --- | --- |
| **3 — Claude Code supervisé** | Claude Code sur le dossier du projet, mode par défaut : demande avant chaque modification et chaque commande | Planifie (mode plan), puis code et lance les tests, avec mon accord à chaque action | Je valide chaque action, je relis les diffs, je commite |
| **4 — Claude Code semi-autonome** | Claude Code avec modifications de fichiers acceptées automatiquement, commandes autorisées listées dans `.claude/settings.json`, push sur des branches via `gh` | Travaille sur une branche par fonctionnalité, commite, ouvre une Pull Request | Je relis et je fusionne la PR |

**Mon choix** :

- Niveau global : 4.
- Exceptions : niveau 3 pour les phases 2 et 3, et ensuite pour toute PR qui touche aux règles d'accès, aux migrations, au jeton joueur ou au moteur de calcul.
- Accès disponibles : compte GitHub, GitHub CLI, Claude Code dans VS Code, Docker Desktop.

### 9.1 Garde-fous

- Branche `main` protégée : tu ne pousses jamais directement dessus et tu ne fusionnes jamais une PR toi-même.
- Secrets hors dépôt : `.env` dans `.gitignore`, lecture de `.env` refusée dans `.claude/settings.json`, `.env.example` versionné à la place.
- Commandes destructrices interdites sans accord : suppression de fichiers, `git push --force`, migration sur une base déployée.
- Dépôt poussé sur GitHub avant chaque session autonome.
- Plafond de dépenses : 0 €. Tu ne crées aucune ressource payante.
- Les règles de la section 7.7 sur les tests.

### 9.2 Branches, commits et PR

- Branches courtes créées depuis `main` : `feature/<nom-court>`, `fix/<nom-court>`, `docs/<nom-court>`, `chore/<nom-court>`, supprimées après fusion.
- Pas de branche `dev` intermédiaire. La première tentative en avait une, et sa règle a été enfreinte dès le deuxième commit. Dis-moi si tu vois une raison de la rétablir.
- Messages au format Conventional Commits (`feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`), à l'impératif. Le message décrit exactement le contenu du commit.
- Une PR est une unité cohérente, relisible en moins de 20 minutes.
- La description d'une PR dit quoi, pourquoi, comment c'est testé, et ce qui n'est pas fait.
- Les tests et la documentation concernée (fiche de phase, ADR, journal) sont dans la même PR que le code.
- Aucun fichier ni dossier créé « pour plus tard ». Aucun contenu d'exemple du générateur laissé en place.
- Un tag annoté à chaque clôture de phase.

### 9.3 Le CLAUDE.md

Tu génères un `CLAUDE.md` à la racine du dépôt dans ta première réponse. Claude Code le lit au début de chaque session : c'est la mémoire du projet. Il reste court (une page ou deux) et renvoie vers `docs/` pour le détail.

Contenu attendu :

1. Contexte du projet en 5 lignes et lien vers `docs/00-cadrage.md`.
2. Stack technique et versions.
3. Commandes : installer, lancer, tester à chaque niveau, linter, migrer, réinitialiser la base locale.
4. Structure des dossiers.
5. Conventions : nommage, style de code, commits, branches, PR.
6. Règles de test (section 7) : ce qui doit accompagner chaque PR, ce qui est interdit.
7. Niveau de collaboration et ce que tu as le droit de faire seul, y compris les zones en niveau 3.
8. Règles de documentation (section 10) : quoi mettre à jour, quand.
9. Phase en cours et lien vers sa fiche.
10. Interdits et pièges connus, repris de l'annexe A.

## 10. Documentation du projet

Le projet est piloté par sa documentation : chaque phase a sa fiche, mise à jour en continu et clôturée avec une date et un tag Git. Tu crées les squelettes dès le cadrage et tu les tiens à jour à chaque PR.

### 10.1 Arborescence attendue

```
README.md                      présentation, installation, lancement, tests
CLAUDE.md                      mémoire du projet pour Claude Code
CHANGELOG.md                   format Keep a Changelog
.github/
  pull_request_template.md     quoi, pourquoi, comment c'est testé
docs/
  00-cadrage.md                ce document + la synthèse de ta réponse
  01-specifications.md         stack fonctionnelle détaillée, règles de calcul
  02-architecture.md           stack technique, schémas, modèle de données, modèle d'accès
  03-strategie-tests.md        niveaux de test, outils, jeu de référence, cas obligatoires
  adr/
    0001-<decision>.md         une décision d'architecture par fichier
  phases/
    phase-01-<nom>.md          une fiche par phase
  journal.md                   journal de bord daté
  glossaire.md                 termes métier et techniques
```

### 10.2 Modèle de fiche de phase

```markdown
# Phase 01 — <Nom de la phase>

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| À faire / En cours / Terminée / Abandonnée | <dates> | <AAAA-MM-JJ> | v0.1.0 |

## Objectif
## Livrables
- [ ] ...
## PR de la phase
| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
## Critères de fin (Definition of Done)
- [ ] Toutes les PR de la phase sont fusionnées, CI verte
- [ ] Cas de test de la phase au vert : <identifiants de la section 7>
- [ ] Recette manuelle faite
- [ ] Documentation à jour
## Recette manuelle
- [ ] ...
## Décisions prises (liens vers les ADR)
## Écarts par rapport au plan
## Rétrospective : ce qui a marché, ce qui a coincé
```

### 10.3 Clôture d'une phase

1. Tous les critères de fin sont cochés.
2. La fiche passe en « Terminée » avec la date du jour.
3. `CHANGELOG.md` reçoit une entrée pour la version.
4. Un tag annoté est posé : `git tag -a v0.1.0 -m "Phase 01 terminée : <nom>"`, puis poussé.
5. Le tag est reporté dans la fiche et dans `journal.md`.
6. `CLAUDE.md` pointe vers la phase suivante.

### 10.4 Règles de mise à jour

- Chaque décision technique ou métier non triviale donne un ADR (contexte, options, décision, conséquences). Une décision n'existe que si elle est écrite dans `docs/` ; un commentaire dans le code ne suffit pas.
- Un document ne cite jamais un fichier, une section ou une route qui n'existe pas.
- Quand une question ouverte de la section 5.4 est tranchée, les spécifications, l'ADR et les tests sont mis à jour dans la même PR.
- Chaque session de travail ajoute une ligne datée dans `journal.md`.
- Un document n'est jamais supprimé : une phase abandonnée garde sa fiche avec le statut « Abandonnée » et la raison.
- Convention de versions : `v0.<phase>.0`, puis `v1.0.0` à la mise en service.

## 11. Ce que j'attends en retour

Réponds dans cet ordre, avec ces titres. Si l'ensemble ne tient pas dans un message, arrête-toi après le point 5 et attends mon accord pour continuer.

1. **Reformulation et questions** : le projet en 3 à 5 lignes, puis les questions bloquantes. S'il y en a, arrête-toi là et attends mes réponses.
2. **Stack fonctionnelle**
    - Fonctionnalités priorisées en MoSCoW, sous forme de tableau.
    - User stories principales avec critères d'acceptation.
    - Parcours utilisateur clés, étape par étape.
    - Règles métier et données manipulées (entités et champs principaux), avec le statut de chaque règle.
3. **Stack technique** : un tableau Couche · Choix · Pourquoi · Alternative écartée · Coût · Comment ça se teste, couvrant :
    - langage et frameworks ;
    - stockage (base de données, migrations, fichiers) ;
    - authentification du staff et lien joueur ;
    - hébergement et déploiement ;
    - outillage : gestion d'environnement et des dépendances, lint et format, tests, CI/CD, gestion des secrets ;
    - spécifique au projet : moteur de calcul, graphiques.
4. **Architecture** : schéma des composants (Mermaid), modèle de données, modèle d'accès (qui lit et écrit quoi, et par quel mécanisme), emplacement du moteur de calcul, arborescence du code.
5. **Stratégie de tests** : niveaux de test et outils, ce qui tourne en local et en CI, comment la base est fournie en CI, format du jeu de référence, et pour chaque cas de la section 7 le niveau de test qui le couvre.
6. **Découpage en phases** : reprends les phases de la section 8. Pour chacune : objectif, livrables, PR prévues (titre, contenu en une ligne, tests apportés), critères de fin, estimation en heures, niveau de collaboration.
7. **Risques** : les 3 à 5 principaux, avec leur parade.
8. **Budget estimé** : coût de départ et coût mensuel, comparés à ma limite de 0 €, avec les limites des offres gratuites qui me concernent.
9. **Documentation initiale** : la synthèse à ajouter à `docs/00-cadrage.md`, la fiche `docs/phases/phase-01-*.md`, le `CLAUDE.md` et le modèle de PR.
10. **Première action** : ce que je fais concrètement dans la prochaine heure.

## 12. Annexes

### Annexe A — Retour d'expérience de la première tentative

Constats de l'audit de l'ancien dépôt. Les points 1, 2 et 7 à 11 ont été vérifiés en exécutant la migration dans un Postgres 16 jetable, où les rôles et les droits par défaut de Supabase avaient été reproduits à la main ; ce n'était pas un vrai projet Supabase.

**Sécurité**

| # | Constat | Règle pour ce projet |
| --- | --- | --- |
| 1 | Les règles d'accès n'étaient actives que sur 4 tables sur 9, avec une seule règle écrite. Sans connexion, on pouvait lire les noms, les dates de naissance, les jetons d'accès et les réponses de sensations, et écraser un jeton. | Refus par défaut partout, prouvé par les cas A1 et A2 |
| 2 | Les vues de calcul s'exécutaient avec les droits de leur propriétaire : un visiteur voyait 0 ligne dans les tables protégées, mais toutes les lignes à travers les vues. | Les vues et fonctions respectent les droits de l'appelant ; elles sont dans le périmètre de A1 |
| 3 | La seule règle d'accès filtrait par catégorie organisatrice de la séance, ce qui contredit « la charge suit le joueur ». | Le modèle d'accès est spécifié avant le schéma (section 6.6), cas A3 |
| 4 | Le jeton du lien joueur était stocké en clair, sans expiration ni révocation. | Jeton haché, révocable, à portée minimale, cas A4 et A5 |
| 5 | L'inscription publique était ouverte dans la configuration d'authentification. | Inscription fermée, cas A6 |
| 6 | Le framework installé portait une alerte de sécurité critique. | Audit des dépendances en CI |

**Calcul**

| # | Constat | Règle pour ce projet |
| --- | --- | --- |
| 7 | Le z-score incluait le point courant dans sa propre référence, ce qui le plafonne à (n−1)/√n. Une charge 7 jours 21 fois supérieure à la normale donnait 1,79 au cinquième point. | Référence arrêtée à la veille, cas C6 |
| 8 | Le calcul produisait une ligne par participation, pas par jour. Deux séances le même jour comptaient double, les jours de repos n'existaient pas, un joueur blessé gardait une valeur figée. | Calendrier continu par joueur, cas C2, C3 et C4 |
| 9 | Les séances en brouillon comptaient dans la charge. | Cas C5 |
| 10 | Le score de sensations additionnait des unités différentes (une échelle 1 à 7 et une durée en minutes donnaient 485, puis 5 le lendemain faute de réponse sur le sommeil). L'inversion était codée en dur pour une échelle 1 à 7. | Normalisation par indicateur et moyenne pondérée des réponses présentes, cas C11 à C13 |
| 11 | Aucune contrainte de plage : 99 était accepté sur une échelle 1 à 7. Les RPE obligatoires étaient incompatibles avec une saisie en brouillon. | Cas D1 ; le brouillon est conçu avant le schéma |

**Méthode**

| # | Constat | Règle pour ce projet |
| --- | --- | --- |
| 12 | Aucun test, aucune CI, et aucune trace d'une exécution de la migration. | Section 7, phase 1, cas D3 |
| 13 | Des décisions (échelle, fenêtres, seuils, blessures) n'existaient que dans des commentaires SQL. Les documents citaient des sections et des fichiers inexistants et se contredisaient. | Section 10.4 |
| 14 | Une arborescence de dossiers vides avait été créée à l'avance ; Git ne la suivait pas. Un commit annonçait cette arborescence et contenait autre chose. Une branche nommée d'après Supabase ne contenait pas Supabase. | Section 9.2 : rien « pour plus tard », des messages exacts |
| 15 | La page d'accueil, le titre et la langue du générateur de projet étaient restés en place. | Nettoyage dans la première PR de la phase 1 |
| 16 | Le workflow Git écrit n'était pas suivi : commit direct sur la branche d'intégration, état non installable fusionné. | Branche protégée et CI obligatoire plutôt qu'une règle écrite |
| 17 | Le dépôt vivait dans OneDrive. | Section 6.2 |
| 18 | Défauts de schéma : pas de clé étrangère vers les comptes d'authentification, un index en doublon, une date de mise à jour jamais mise à jour, aucune voie pour supprimer un joueur. | Revue du schéma en phase 2, cas D4 |

### Annexe B — Interface de la V0

Cinq onglets : Accueil, Training (saisie des séances et des RPE), Database (données brutes et charge du jour), Actual form (graphique intensité / sensations), Technical file (fiche joueur avec date de rétrospection). Le contenu des deux derniers est décrit en section 5.2.

### Annexe C — Pièces jointes et notes

- **Fichiers joints** : 
- **Notes libres** : 

## 13. Synthèse de la phase 0

Phase 0 menée le 2026-10-12 avec Claude. Cette section consigne les réponses, les décisions et les écarts par rapport aux sections 1 à 12, ainsi que le découpage en phases, les risques et le budget. Le détail est dans les documents de référence de la section 13.3.

### 13.1 Questions de la phase 0 et réponses

| Question | Réponse | Où c'est appliqué |
| --- | --- | --- |
| Un dépôt privé gratuit ne permet ni protection de `main` ni vérifications obligatoires. | Dépôt public ; il ne contiendra jamais de données personnelles réelles. | [ADR-0001](adr/0001-depot-public-et-protection-de-main.md) |
| La V1 est-elle une démonstration ou un outil d'usage réel ? | Une démonstration, montrée telle quelle au préparateur et retravaillée ensuite s'il le souhaite. Un usage réel serait un chantier distinct. | [Spécifications, section 1](01-specifications.md) |
| Le préparateur peut-il être consulté avant la démonstration ? | Non : je tranche seul les points ouverts, de façon provisoire et paramétrable. | ADR 0007 à 0018 |
| Joueur invité d'une autre catégorie : que voit le préparateur organisateur ? | Annuaire minimal, et les participations à ses propres séances seulement. | Règle R24, [ADR-0005](adr/0005-controle-d-acces-applicatif.md) |
| Hypothèses par défaut (pas de carte bancaire, jour à l'heure de Paris, jours de questionnaire paramétrés, nommage) | Validées, sauf une : les saisies doivent pouvoir être corrigées en cas d'erreur. | Règles R09, R16, R22 ; [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) |

Validations du même jour : recommandations des ADR 0002 à 0018 acceptées ; spécifications, architecture et stratégie de tests validées ; gestion des joueurs par le préparateur (section 6.7) ; nouvelle formulation du cas A4 ; tests de la phase 3 introduits en `xfail(strict=True)` ; seuils de couverture de 95 % (moteur) et 90 % (validation des saisies).

### 13.2 Écarts par rapport aux sections 1 à 12

| Section | Écart | Raison |
| --- | --- | --- |
| Préambule, 6.3 | Dépôt public et non privé | Protection de `main` gratuite sur un dépôt public seulement ([ADR-0001](adr/0001-depot-public-et-protection-de-main.md)) |
| 6.4 | Django, Vercel et Neon au lieu de Next.js, Supabase et Vercel | Niveau 0 en TypeScript ; base jamais exposée au navigateur ([ADR-0002](adr/0002-django-et-rendu-serveur.md), [ADR-0003](adr/0003-hebergement-vercel-et-neon.md)) |
| 6.6, tableau d'accès | Le préparateur écrit aussi les joueurs de sa catégorie (création, modification, archivage) ; le joueur lit et modifie son entrée du jour | Section 6.7 et décision sur les corrections |
| 7.4, A1 et A2 | Les vérifications portent sur deux catalogues : les routes de l'application et le catalogue de Postgres | La base n'est accessible qu'à l'application ([ADR-0005](adr/0005-controle-d-acces-applicatif.md)) |
| 7.4, A4 | « Dépose et modifie son entrée du jour ; ne lit ni ses entrées des autres jours ni les autres joueurs » | Décision sur les corrections |
| 7.3, C14 | Le cas rejoue le jeu C06 avec un facteur d'échelle multiplié | Les bornes de durée empêchent de multiplier les durées |
| 7.6, E1 | En phase 4, les charges apparaissent sur la page de la séance validée ; le parcours est étendu au tableau de bord en phase 6 | Le tableau de bord n'existe qu'en phase 6 |
| 8.3, phase 3 | Les tests de la première PR sont marqués `xfail(strict=True)` plutôt que laissés en échec | Une PR en échec ne peut pas être fusionnée ([stratégie de tests](03-strategie-tests.md), section 1) |
| 8.3, phase 3 | Pas de nouvelle ADR sur les formules : elle existe déjà (ADR 0007 et 0011 à 0016) | Points tranchés en phase 0 |
| 9.2 | Pas de branche `dev` : aucune raison de la rétablir. Les previews par PR jouent le rôle d'environnement d'intégration. | — |
| 9.3 | `CLAUDE.md` livré avec la documentation initiale, après les questions bloquantes | La section 11 imposait de s'arrêter aux questions |

### 13.3 Documents de référence

- [Spécifications](01-specifications.md), dont le tableau des paramètres retenus
- [Architecture](02-architecture.md)
- [Stratégie de tests](03-strategie-tests.md)
- [Index des ADR](adr/README.md)
- [Glossaire](glossaire.md)
- [Fiche de la phase 1](phases/phase-01-socle.md)
- [Journal](journal.md)

### 13.4 Découpage en phases

Estimations : ton temps, revues, décisions et recettes comprises, avec Claude Code pour l'écriture du code. Total d'environ 140 heures, soit trois à quatre mois à plus de 10 heures par semaine.

| Phase | Nom | Niveau | Estimation | Tag |
| --- | --- | --- | --- | --- |
| 0 | Cadrage | Conversation | 4 h (faite) | — |
| 1 | Socle et chaîne de qualité | 4 ; 3 pour les PR 1.3 et 1.5 | 16 h | v0.1.0 |
| 2 | Modèle de données et accès | 3 | 20 h | v0.2.0 |
| 3 | Moteur de calcul | 3 | 24 h, plus environ 10 h pour ton jeu de référence | v0.3.0 |
| 4 | Saisie des séances | 4 ; 3 pour la PR 4.2 et pour ce qui touche aux accès | 18 h | v0.4.0 |
| 5 | Questionnaire joueur | 4 ; 3 pour les PR 5.1 et 5.2 | 14 h | v0.5.0 |
| 6 | Tableaux de bord | 4 | 20 h | v0.6.0 |
| 7 | Mise en service | 4 ; 3 pour les PR 7.1 et 7.3 | 14 h | v1.0.0 |

#### Phase 1 — Socle et chaîne de qualité

Objectif : prouver que la chaîne complète fonctionne (écrire, tester, fusionner, déployer) avant toute fonctionnalité. Le détail est dans la [fiche de la phase 1](phases/phase-01-socle.md).

Livrables : dépôt public protégé ; projet Django nettoyé ; base locale reproductible ; CI complète et obligatoire ; previews par PR et production derrière ton approbation ; README.

| # | Titre | Contenu | Tests apportés | Niveau |
| --- | --- | --- | --- | --- |
| 1.1 | `docs: ajouter le cadrage et la configuration de travail` | `docs/`, `CLAUDE.md`, `CHANGELOG.md`, modèle de PR, `.gitignore`, `.claude/settings.json` | Aucun : la CI n'existe pas encore | Toi |
| 1.2 | `chore: initialiser le projet Django` | uv, Django 5.2, projet `config` et application `suivi`, réglages par variables d'environnement, français et Europe/Paris, refus par défaut, page de connexion minimale, contrôle de santé, Ruff et mypy, `.env.example`, aucun contenu du générateur | Unitaires : liens de la documentation, redirection d'un visiteur vers la connexion | 4 |
| 1.3 | `chore: fournir la base locale et les rôles Postgres` | `compose.yaml` (`postgres:16`), création des rôles de migration et d'exécution, droits par défaut, `pytest-django` | Intégration : migrations depuis zéro, le rôle d'exécution ne peut pas modifier le schéma, aucun droit à `PUBLIC` | 3 |
| 1.4 | `chore: ajouter la chaîne d'intégration continue` | Jobs `qualite`, `tests`, `migrations`, `e2e`, `audit`, `build` ; Playwright ; pip-audit ; gitleaks ; ruleset complet | Bout en bout : page de connexion sur ordinateur et téléphone ; intégration : squelette de A1 sur le catalogue des routes | 4 |
| 1.5 | `chore: déployer les previews et la production` | Projets Vercel et Neon, branche Neon par PR, environnement `production` avec approbation, migrations par le rôle de migration, en-têtes de sécurité | Test de fumée après déploiement ; `check --deploy` | 3 |
| 1.6 | `docs: compléter le README et démontrer le blocage` | README (installation, lancement, tests) ; PR de démonstration avec un test en échec, bloquée puis fermée sans fusion | Recette : clone neuf avec les seules commandes du README | 4 |

Critères de fin : ceux de la section 8.3, plus le premier affichage après inactivité mesuré.

#### Phase 2 — Modèle de données et accès

Objectif : un schéma contraint et un modèle d'accès prouvé, avant toute interface.

Livrables : modèles et migrations ; contraintes et déclencheurs ; couche d'accès ; administration réservée au superutilisateur ; données de démonstration.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 2.1 | `feat: ajouter les catégories, les préparateurs et les joueurs` | Modèles, contraintes, clé étrangère vers les comptes, archivage, administration | D1 (champs obligatoires), D4 (archivage), `updated_at` |
| 2.2 | `feat: ajouter les séances et les participations` | RPE de 0 à 10, durée de 1 à 300, unicité, déclencheur de complétude à la validation | D1, D2, déclencheur |
| 2.3 | `feat: ajouter les indicateurs et les entrées de sensations` | Bornes contrôlées par déclencheur, une entrée par joueur et par jour, échelle figée après la première réponse | D1, D2, refus d'un changement d'échelle |
| 2.4 | `feat: protéger les accès du staff` | Profil préparateur exigé par URL, `suivi/acces.py`, liste blanche, administration fermée aux préparateurs | A1 complet, A2, A3, A6, index en double |
| 2.5 | `feat: générer la démonstration et effacer un joueur` | `generer_demo` à graine fixe (U19 et une seconde catégorie), effacement par l'administrateur | D3, D4 |

Critères de fin : A1, A2, A3, A6 et D1 à D4 au vert ; migrations rejouées depuis zéro en CI et sur chaque preview ; aucune donnée réelle ; recette faite.

#### Phase 3 — Moteur de calcul

Objectif : des chiffres justes, prouvés indépendamment de l'implémentation.

Livrables : jeu de référence avec provenance ; `engine/` ; adaptateur `suivi/calculs.py` ; `config/calcul.toml`.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 3.1 | `test: ajouter le jeu de référence et les cas C1 à C15` | Format, harnais sur base et sans base, cas en `xfail(strict=True)`. Les `attendu.csv` et `provenance.md` sont écrits par toi. | C1 à C15, en échec attendu |
| 3.2 | `feat: calculer la charge du jour sur un calendrier continu` | Types, paramètres, charge de séance, calendrier, adaptateur | C1, C2, C5, C10 |
| 3.3 | `feat: calculer la CE courte et la CE longue` | Sommes glissantes, drapeau de fenêtre incomplète | C3, C9 |
| 3.4 | `feat: calculer l'intensité` | Référence, historique minimal, écart-type nul | C4, C6, C7 et C8 pour l'intensité, C14 |
| 3.5 | `feat: calculer le score et le z-score de sensations` | Normalisation, orientation, pondération, référence | C7 et C8 pour les sensations, C11, C12, C13, C15 |

Critères de fin : C1 à C15 au vert, sans aucun `xfail` restant ; couverture de `engine/` d'au moins 95 % ; ton contrôle indépendant consigné dans chaque `provenance.md` ; aucune interface.

#### Phase 4 — Saisie des séances

Objectif : le préparateur remplace son fichier Excel.

Livrables : connexion et structure des pages ; gestion des joueurs ; création de séance ; grille RPE ; historique.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 4.1 | `feat: ajouter la connexion et la structure des pages` | Gabarit de base, navigation, connexion et déconnexion, mise en page tablette et téléphone | Intégration de la connexion ; bout en bout de la connexion |
| 4.2 | `feat: gérer les joueurs de sa catégorie` | Liste, création, modification, archivage (US-15) ; niveau 3 | A3 étendu, D1 |
| 4.3 | `feat: créer une séance et ses participants` | En-tête, pré-remplissage, annuaire, retrait | D1 (durée), A3 (joueur invité) |
| 4.4 | `feat: saisir la grille RPE puis la valider` | Grille au clavier, code couleur, brouillon, validation, charges affichées sur la séance validée | D1, E1 sur ordinateur et tablette |
| 4.5 | `feat: lister, corriger et supprimer les séances` | Historique, correction directe, suppression confirmée, traçabilité | Intégration, `updated_by` |

Critères de fin : E1 au vert ; couverture de la validation des saisies d'au moins 90 % ; utilisable sur tablette ; recette faite, avec une séance de 25 joueurs chronométrée.

#### Phase 5 — Questionnaire joueur

Objectif : le joueur répond seul, sans compte, et le formulaire externe disparaît.

Livrables : liens joueurs ; questionnaire mobile ; badge ; correction des entrées passées.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 5.1 | `feat: générer, révoquer et régénérer les liens joueurs` | Empreinte du jeton, QR code, pages staff ; niveau 3 | A5 |
| 5.2 | `feat: afficher et enregistrer le questionnaire du jour` | Vue du jeton, formulaire selon les indicateurs de la catégorie, création puis modification le même jour ; niveau 3 | A4, D1, D2 |
| 5.3 | `feat: afficher le badge Reçu / Manquant` | Badge dans la grille, jours de questionnaire | E2 sur téléphone |
| 5.4 | `feat: corriger une entrée de sensations passée` | Correction et suppression par le préparateur, traçabilité | A3, intégration |

Critères de fin : A4, A5 et E2 au vert ; recette faite sur un vrai téléphone, avec un questionnaire rempli en moins d'une minute.

#### Phase 6 — Tableaux de bord

Objectif : rendre visible ce que le moteur calcule.

Livrables : « Forme actuelle » ; fiche joueur ; rétrospection ; données brutes et export.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 6.1 | `feat: afficher le graphique Forme actuelle` | Vega-Lite copié dans le dépôt et compatible avec la politique de sécurité du contenu, spécification construite en Python, liste des joueurs sans point | Unitaires sur la spécification ; intégration |
| 6.2 | `feat: afficher la charge sur la fiche joueur` | Tableau des RPE coloré, barres de CE, tableaux de valeurs | E1 étendu au tableau de bord |
| 6.3 | `feat: afficher les sensations sur la fiche joueur` | Barres de la dernière entrée, heatmap sur 7 jours avec total | Unitaires sur la spécification |
| 6.4 | `feat: choisir une date de rétrospection` | Sélecteur sur la fiche et sur « Forme actuelle » | E3, C9 côté interface |
| 6.5 | `feat: consulter et exporter les données brutes` | Tableau depuis le début de saison, export CSV | A3 sur l'export |

Critères de fin : E3 au vert ; états « historique insuffisant » et « non calculable » affichés ; aucune formule dans les gabarits ni dans le JavaScript ; recette faite.

#### Phase 7 — Mise en service

Objectif : une V1 que tu peux montrer et laisser entre les mains du préparateur.

Livrables : production avec données de démonstration ; sauvegarde et restauration ; guides.

| # | Titre | Contenu | Tests apportés |
| --- | --- | --- | --- |
| 7.1 | `chore: préparer la production et la démonstration` | Démonstration chargée par un job approuvé, compte préparateur de démonstration, rotation des secrets ; niveau 3 | Test de fumée |
| 7.2 | `feat: sauvegarder et restaurer la base` | Export chiffré planifié, restauration sur une branche Neon | Test de restauration |
| 7.3 | `test: rejouer les tests d'accès contre la production` | A1, A4, A5 et A6 en boîte noire, vérifications de catalogue sur la base de production ; niveau 3 | A1, A4, A5, A6 déployés |
| 7.4 | `docs: rédiger le guide d'utilisation et la note V0 → V1` | Guide d'une page, note « ce que la V1 change », guide d'exploitation (rotation des secrets, restauration, recette mensuelle) | Relecture |

Critères de fin : ceux de la section 8.3.

### 13.5 Risques

| # | Risque | Parade |
| --- | --- | --- |
| 1 | Une valeur attendue du jeu de référence partage l'erreur du code, par exemple une même mauvaise lecture d'une règle | Cas assez petits pour un calcul à la main ; C1 à C4 calculés deux fois (à la main et au tableur) ; tests de propriété (C14) ; comparaison avec un export de la V0 s'il refait surface |
| 2 | Les offres gratuites changent ou montrent leurs limites : démarrage à froid, quotas, conditions d'usage non commercial, workflows planifiés désactivés après 60 jours sans activité | Mesure du premier affichage dès la phase 1 ; Django et Postgres standard, donc portables ; sauvegarde chiffrée en phase 7 ; recette mensuelle d'exploitation |
| 3 | Le préparateur contredit à la démonstration des choix provisoires (échelle, fenêtres, sens du graphique) | Tout est paramétré (`config/calcul.toml`, configuration des indicateurs) ; chaque ADR garde ses options ; seules l'échelle des RPE et les bornes de durée sont figées en base |
| 4 | Fuite de secret ou faille d'accès dans un dépôt public | gitleaks en CI ; variables Vercel « Sensitive » ; rôle d'exécution sans droit sur le schéma ; A1 et A2 par catalogues ; jeton haché ; aucune donnée réelle |
| 5 | Le projet s'étire : pas d'échéance, environ 140 heures, développeur seul | Phases courtes fermées par un tag ; application déployée et démontrable à la fin de chaque phase ; fonctionnalités Could reportées après la V1 ; journal daté |

### 13.6 Budget

| Poste | Départ | Mensuel |
| --- | --- | --- |
| GitHub Free, dépôt public | 0 € | 0 € |
| Vercel Hobby | 0 € | 0 € |
| Neon Free | 0 € | 0 € |
| Nom de domaine | Aucun : sous-domaine `vercel.app` | 0 € |
| **Total** | **0 €** | **0 €**, dans ta limite |

Aucune carte bancaire n'est enregistrée : un dépassement de quota suspend le service, il ne le facture pas.

Limites qui te concernent, vérifiées le 2026-10-12 :

| Service | Limite | Consommation attendue |
| --- | --- | --- |
| GitHub | Minutes illimitées sur les exécuteurs standard d'un dépôt public ; rulesets et environnements avec approbation disponibles en public ; workflows planifiés désactivés après 60 jours sans activité du dépôt | Sans objet ; surveillance du workflow de sauvegarde à la recette mensuelle |
| Vercel Hobby | Usage personnel et non commercial ; fonctions limitées à 10 secondes par défaut, 60 au plus ; paquet Python de 500 Mo au plus ; en cas de dépassement d'un quota, attente de 30 jours | Quelques centaines de requêtes par mois pour une démonstration |
| Neon Free | 0,5 Go de stockage et 100 CU-heures par projet et par mois ; mise à l'échelle zéro après 5 minutes, non désactivable ; restauration possible sur 6 heures ; 10 branches | Moins de 50 Mo même pour une saison complète ; quelques CU-heures par mois |

Sources : https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments, https://vercel.com/docs/plans/hobby, https://vercel.com/docs/functions/limitations, https://neon.com/faqs/free-plan-limits-and-quotas.
