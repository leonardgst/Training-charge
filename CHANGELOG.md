# Journal des modifications

Toutes les modifications notables du projet sont consignées ici, au format [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Les versions suivent la convention du cadrage : `v0.<phase>.0`, puis `v1.0.0` à la mise en service.

## [Non publié]

## [0.4.0] - 2026-10-15

Phase 4 : saisie des séances.

### Ajouté

- Connexion et déconnexion du staff, avec un message d'erreur qui ne dit pas quel identifiant est faux ; gabarit de base avec Pico CSS 2.1.1 copié dans le dépôt (accord du mainteneur), navigation, pages 403, 404 et 500 en français, mise en page sur ordinateur, tablette et téléphone.
- Politique de sécurité du contenu limitée à l'origine du site sur toute réponse ; `Referrer-Policy: same-origin` rendu explicite ; test de fumée étendu à ces en-têtes.
- Gestion des joueurs de sa catégorie par le préparateur : liste, création, modification, archivage et réactivation (US-15).
- Création d'une séance en brouillon : en-tête saisi une fois, joueurs actifs de la catégorie cochés, recherche dans l'annuaire pour ajouter un joueur invité, retrait d'un absent (US-03).
- Grille RPE au clavier (Tab dans l'ordre de lecture, clavier numérique sur tablette), code couleur pendant la frappe, brouillon puis validation, charge de séance de chaque participant calculée par le moteur (US-04, US-05).
- Historique des séances, correction directe d'une séance validée (grille, en-tête, participants), suppression confirmée, date et auteur de la dernière modification affichés (US-06).
- Seuil de couverture de 90 % des branches de `suivi/forms.py` imposé en CI (accord du mainteneur).
- Tests : parcours E1 sur ordinateur et tablette (25 joueurs), A1 et A3 étendus à chaque écran, D1 à la saisie, un test qui interdit deux fichiers de test du même nom.
- Fiche de la phase 5 (questionnaire joueur), à valider par le mainteneur.

### Modifié

- Phase 4 en niveau 4 de collaboration pour toute la phase, accès et migrations compris (décision du mainteneur).
- Le middleware du profil préparateur pose le profil sur `request.preparateur`.
- Architecture (section 5) : `Referrer-Policy: same-origin` au lieu de `no-referrer`, incompatible avec le contrôle CSRF de Django (décision du mainteneur) ; ADR-0005 et ADR-0008 complétées par leur mise en œuvre.
- README remis à jour (état du projet, fiche de la phase en cours, comptes de démonstration).
- `CLAUDE.md` pointe vers la phase 5.

### Corrigé

- La politique de sécurité du contenu, prévue par l'architecture, n'était pas posée depuis la phase 1.
- `uv run pytest` à la racine échouait à collecter deux fichiers de test du même nom ; la CI, qui lance les niveaux séparément, ne le voyait pas.

## [0.3.0] - 2026-10-15

Phase 3 : moteur de calcul.

### Ajouté

- Moteur pur `engine/` (sans Django, typage strict, 100 % des branches couvertes, seuil de 95 % imposé en CI) : charge de séance et charge du jour sur un calendrier continu ; CE courte (7 jours) et CE longue (28 jours) avec drapeau de fenêtre incomplète ; z-score d'intensité (référence à la veille, fenêtres complètes, au moins 21 jours, écart-type d'échantillon, états `historique_insuffisant` et `non_calculable`) ; score de sensations normalisé par les bornes, orienté et pondéré (au moins 50 % du poids répondu, état `reponses_insuffisantes`) ; z-score de sensations (au moins 6 entrées dans les 28 jours précédents).
- Adaptateur `suivi/calculs.py` : séances validées seulement, données datées au plus tard de la date de calcul, configuration des indicateurs rétroactive.
- `config/calcul.toml` : paramètres de calcul validés au démarrage.
- Jeu de référence `tests/reference/` : format, harnais sur base et sans base, cas C01 à C15 avec leurs entrées, leurs valeurs attendues et leur provenance, script de calcul indépendant du moteur en arithmétique exacte.
- Fiche de la phase 4 (saisie des séances).

### Modifié

- Phase 3 en niveau 4 de collaboration (décision du mainteneur).
- Écriture des `attendu.csv` et `provenance.md` confiée à Claude Code, et contrôle indépendant du mainteneur levé, par décision du mainteneur ; consigné dans chaque `provenance.md`.
- `CLAUDE.md` pointe vers la phase 4.

## [0.2.0] - 2026-10-13

Phase 2 : modèle de données et accès.

### Ajouté

- Modèles `Categorie`, `Preparateur` et `Joueur` avec leur migration : contraintes en base (code unique, jours de questionnaire dans la semaine, nom et prénom non vides), archivage par `actif`, `updated_at` et `updated_by`, administration Django réservée au superutilisateur.
- Modèles `Seance` et `Participation` : durée de 1 à 300, RPE de 0 à 10 (ou absents en brouillon), type et statut dans une liste fermée, `validated_at` cohérent avec le statut, une participation par joueur et par séance ; déclencheurs Postgres interdisant une participation incomplète dans une séance validée.
- Modèles `Indicateur`, `EntreeSensations` et `Reponse` : bornes ordonnées, poids positif, types et sens en liste fermée, un indicateur sans sens ni de type note hors du score, une entrée par joueur et par jour, une réponse par indicateur et par entrée ; déclencheurs Postgres pour la valeur dans les bornes et pour l'échelle figée dès qu'une réponse existe ; indicateurs configurables dans l'administration.
- Accès du staff : profil préparateur exigé sur toute URL hors liste blanche (403 sinon), administration réservée au superutilisateur, `suivi/acces.py` (joueurs suivis, annuaire, séances, participations et entrées visibles) ; tests A1 (routes connecté ou non, catalogue Postgres), A2 (méta-tests), A3 (deux catégories et joueur invité), A6 (aucune inscription), index en double.
- Démonstration : commande `generer_demo` à graine fixe (U19 et U17, 33 joueurs fictifs dont un archivé et trois invités, huit semaines de séances, sensations quotidiennes, un joueur à surveiller, une séance en brouillon, trois comptes ; refuse une base non vide) ; fonction unique de la date du jour (`suivi/horloge.py`) ; job `migrations` de la CI qui charge la démonstration et contrôle les effectifs ; tests D3 et D4 (archivage, effacement en cascade par l'administrateur).
- Fiche de la phase 3 (moteur de calcul).

### Modifié

- Phase 2 en niveau 4 de collaboration (décision du mainteneur) : permissions de Claude Code et règles de `CLAUDE.md` alignées.
- `CLAUDE.md` pointe vers la phase 3, en niveau 3.

## [0.1.0] - 2026-10-13

Phase 1 : socle et chaîne de qualité.

### Ajouté

- Documentation de cadrage : cadrage anonymisé et synthèse de la phase 0, spécifications, architecture, stratégie de tests, ADR 0001 à 0018, glossaire, journal, fiche de la phase 1.
- `CLAUDE.md`, modèle de PR et permissions de Claude Code.
- `.gitattributes` : fins de ligne normalisées en LF.
- Projet Django 5.2 : projet `config` et application `suivi`, réglages par variables d'environnement (`.env.example`), français et Europe/Paris, refus par défaut des vues (`LoginRequiredMiddleware`), page de connexion minimale, contrôle de santé (`/sante/`).
- Chaîne locale de qualité : uv (Python 3.12), Ruff, mypy avec `django-stubs`, pytest ; tests unitaires des liens de la documentation, des réglages et de l'accès d'un visiteur sans session.
- Base locale : `compose.yaml` (Postgres 16), script d'initialisation des rôles de migration et d'exécution sans droit à `PUBLIC`, réglages `DATABASES` par variables d'environnement ; `pytest-django` et `psycopg` ; tests d'intégration des migrations depuis zéro et des droits des rôles.
- Chaîne d'intégration continue : workflow GitHub Actions à six jobs (`qualite`, `tests`, `migrations`, `e2e`, `audit`, `build`), tests de bout en bout Playwright de la connexion sur ordinateur et téléphone, test d'intégration du catalogue des routes pour un visiteur (A1, squelette), `pip-audit` et gitleaks ; ruleset de `main` actif, six jobs obligatoires.
- Déploiement : réglages HTTPS (`DJANGO_HTTPS`, `DB_SSLMODE`), `vercel.json` (région `fra1`), workflows de preview (branche Neon par PR) et de production (environnement `production`, migrations par le rôle de migration), test de fumée, `check --deploy` dans `qualite`, `docs/deploiement.md`.
- `README.md` : présentation, prérequis, installation, base locale, lancement, tests et intégration continue.

### Modifié

- Permissions de Claude Code : lecture de `.env` refusée aussi par le shell ; auto-mode autorisé et mode par défaut.
