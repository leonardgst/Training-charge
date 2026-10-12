# Stratégie de tests

| Version | Date | Statut |
| --- | --- | --- |
| 1.0 | 2026-10-12 | Validé |

Ce document décrit comment chaque exigence de la section 7 du cadrage est prouvée : niveaux de test, outils, base de données, jeu de référence, et le niveau qui couvre chaque cas.

## 1. Principes et garde-fous automatiques

Rien n'est fait tant qu'un test automatisé ne le prouve pas et que la CI ne l'a pas exécuté. Chaque règle de la section 7 du cadrage a, autant que possible, un garde-fou automatique plutôt qu'une simple consigne :

| Règle du cadrage | Garde-fou |
| --- | --- |
| Aucune fusion sans CI verte (7.2) | Ruleset sur `main` : les jobs de la section 4 sont obligatoires, sans contournement possible ([ADR-0001](adr/0001-depot-public-et-protection-de-main.md)) |
| Valeurs attendues jamais recopiées de la sortie du code (7.3, 7.7) | Les fichiers `attendu.csv` et `provenance.md` du jeu de référence sont en écriture interdite pour Claude Code dans `.claude/settings.json` ; toi seul les écris |
| Pas de simulacre de base pour l'accès et le calcul (7.7) | Les tests d'intégration et de bout en bout tournent sur un vrai Postgres ; aucune bibliothèque de simulacre n'est installée |
| Migrations rejouées depuis zéro (7.2, D3) | Job `migrations` sur une base vide à chaque PR ; `--reuse-db` et `--nomigrations` interdits en CI |
| « Testé » toujours accompagné de la commande et de sa sortie (7.7) | Rubrique obligatoire du modèle de PR |
| Une correction de bug commence par un test qui échoue (7.2) | Rubrique du modèle de PR ; le test est dans la même PR |
| Un document ne cite jamais un fichier inexistant (10.4) | Test unitaire qui vérifie tous les liens relatifs de `docs/`, `README.md` et `CLAUDE.md` |

**Tests écrits avant le code (phase 3).** Une PR dont un test échoue ne peut pas être fusionnée. Les tests du moteur sont donc introduits marqués `xfail(strict=True)` : ils doivent échouer tant que le calcul n'existe pas, et la CI échoue s'ils passent sans qu'on ait retiré le marqueur. Chaque PR d'implémentation retire le marqueur des cas qu'elle fait passer. C'est le seul usage autorisé de `xfail` ; tu l'as accepté le 2026-10-12.

## 2. Niveaux de test

| Niveau | Ce qui est testé | Outils | Base | Où |
| --- | --- | --- | --- | --- |
| Statique | Style, format, typage, migrations manquantes, réglages de sécurité | Ruff, mypy et `django-stubs`, `makemigrations --check`, `manage.py check --deploy` | Aucune | Local et CI |
| Unitaire | Fonctions pures du moteur, validation des formulaires, génération et hachage des jetons, construction des spécifications de graphiques, liens de la documentation, absence d'import Django dans `engine/` | pytest | Aucune | Local et CI |
| Intégration | Contraintes du schéma, règles d'accès par HTTP et par le catalogue de la base, moteur via l'adaptateur sur le jeu de référence, suppression d'un joueur, données de démonstration | pytest, `pytest-django`, client de test Django | Postgres 16 réel, migré depuis zéro | Local et CI |
| Bout en bout | Parcours E1 à E3 dans un vrai navigateur, sur ordinateur, tablette et téléphone émulés | Playwright pour Python (Chromium), serveur de test de `pytest-django` | Postgres 16 réel | Local et CI |
| Après déploiement | Test de fumée à chaque déploiement ; tests d'accès en boîte noire avant la mise en service | pytest et un client HTTP contre l'URL publique | Base déployée | CI |
| Recette manuelle | Liste de vérifications de fin de phase, sur ordinateur et téléphone | Toi | Environnement déployé | Toi |

## 3. Commandes locales

Commandes visées, à figer dans le README en phase 1 :

| Action | Commande |
| --- | --- |
| Installer | `uv sync` puis `uv run playwright install --with-deps chromium` |
| Démarrer la base locale | `docker compose up -d db` |
| Réinitialiser la base locale | `docker compose down -v && docker compose up -d db` |
| Migrer | `uv run --env-file .env python manage.py migrate` |
| Charger la démonstration | `uv run --env-file .env python manage.py generer_demo` |
| Lancer l'application | `uv run --env-file .env python manage.py runserver` |
| Lint et format | `uv run ruff check . && uv run ruff format --check .` |
| Typage | `uv run mypy .` |
| Tests unitaires | `uv run pytest tests/unit` |
| Tests d'intégration | `uv run --env-file .env pytest tests/integration` |
| Tests de bout en bout | `uv run --env-file .env pytest tests/e2e` |
| Couverture | `uv run --env-file .env pytest tests/unit tests/integration --cov=engine --cov=suivi --cov-branch` |

## 4. Pipeline de CI

Déclenchée sur chaque PR et sur chaque fusion dans `main`. Les jobs tournent en parallèle ; tous sont obligatoires dans le ruleset.

| Job | Contenu | Durée visée |
| --- | --- | --- |
| `qualite` | Ruff (lint et format), mypy, `makemigrations --check`, `manage.py check --deploy` | 1 à 2 min |
| `tests` | Tests unitaires et d'intégration sur un conteneur de service `postgres:16`, avec les seuils de couverture de la section 7 | 2 à 4 min |
| `migrations` | Base vide : `migrate`, puis `generer_demo`, puis contrôle des effectifs chargés (D3) | 1 à 2 min |
| `e2e` | Tests Playwright sur un conteneur de service `postgres:16` | 3 à 5 min |
| `audit` | `pip-audit` sur les dépendances verrouillées ; gitleaks sur l'historique | 1 min |
| `build` | `collectstatic` et import de l'application avec les réglages de production | 1 min |

Le dépôt étant public, les minutes de CI ne sont pas comptées ([ADR-0001](adr/0001-depot-public-et-protection-de-main.md)).

## 5. Base de données en local et en CI

- **Local** : `compose.yaml` démarre `postgres:16` avec un volume nommé et un script d'initialisation qui crée le rôle de migration et le rôle d'exécution. `pytest-django` crée une base de test, la migre depuis zéro et isole chaque test dans une transaction.
- **CI** : conteneur de service `postgres:16` avec contrôle de santé ; une étape crée les deux rôles ; aucune base n'est réutilisée d'une exécution à l'autre.
- **Previews** : une branche Neon par PR, supprimée à la fermeture de la PR ([ADR-0003](adr/0003-hebergement-vercel-et-neon.md)).
- **Date du jour** : le code obtient la date du jour à l'heure de Paris par une fonction unique, que les tests remplacent par une date fixe. Aucun appel direct à `date.today()` ; un test le vérifie.

## 6. Jeu de référence

### Format

Un dossier par cas, au format CSV pour être produit dans un tableur, plus un fichier TOML pour les paramètres (lu par `tomllib`, sans dépendance).

```
tests/reference/
  README.md                  règles de format, de provenance et de tolérance
  C01-seance-simple/
    cas.toml                 description, dates de calcul, paramètres surchargés
    seances.csv              id, date, categorie, type, duree_min, statut
    participations.csv       seance_id, joueur, rpe_cardio, rpe_musculaire, rpe_teta
    indicateurs.csv          categorie, code, type, borne_min, borne_max, sens, poids, inclus_score
    reponses.csv             joueur, date, indicateur, valeur
    attendu.csv              joueur, date, grandeur, valeur, etat
    provenance.md            outil, auteur, date et méthode du calcul indépendant
  …
  E3-fiche-joueur/           jeu du parcours E3, même format
```

- `grandeur` prend les valeurs `charge_jour`, `ce_courte`, `ce_longue`, `intensite`, `score_sensations`, `sensations_z`.
- `etat` vaut `ok`, `historique_insuffisant`, `non_calculable` ou `reponses_insuffisantes` ; `valeur` est vide quand `etat` n'est pas `ok`.
- Les fichiers absents d'un cas (par exemple `reponses.csv` pour un cas de charge) sont simplement omis.

### Provenance

- Toi seul produis `attendu.csv`, dans un tableur ou par un script séparé. Si c'est un script, il vit dans `tests/reference/outils/` et un test vérifie qu'il n'importe ni `engine` ni `suivi`.
- `provenance.md` dit comment chaque valeur a été obtenue. Une valeur sans provenance n'est pas une valeur attendue.
- Les valeurs sont exportées avec au moins dix chiffres significatifs, jamais arrondies à l'affichage du tableur.
- Exception unique : C14 rejoue le jeu `C06` avec un facteur d'échelle multiplié par une constante. Ses valeurs attendues sont dérivées de `attendu.csv` de `C06` (charges multipliées, z-scores identiques), jamais d'une sortie du code.

### Tolérances

| Grandeur | Comparaison |
| --- | --- |
| Charges et CE | Écart relatif inférieur à 1e-9 |
| Z-scores et score de sensations | Écart absolu inférieur à 1e-6 |
| États | Égalité exacte |

### Exécution

Un même test paramétré parcourt tous les dossiers de cas. Il charge le jeu dans un Postgres réel par l'ORM, appelle l'adaptateur puis le moteur pour chaque date listée, et compare à `attendu.csv`. Une variante sans base appelle directement le moteur pour un retour rapide en local ; la version sur base fait foi.

## 7. Seuils de couverture

Seuils validés le 2026-10-12, imposés en CI sur ces modules seulement (cadrage 7.3) :

| Module | Seuil |
| --- | --- |
| `engine/` | 95 % des branches |
| Validation des saisies (`suivi/forms.py` et les validateurs du modèle) | 90 % des branches |

## 8. Couverture des cas de la section 7

| Id | Situation | Niveau | Comment | Phase | Dépend de |
| --- | --- | --- | --- | --- | --- |
| C1 | Une séance simple | Intégration et unitaire | Jeu `C01` | 3 | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) |
| C2 | Deux séances le même jour | Intégration et unitaire | Jeu `C02` : une seule ligne pour le jour, charges additionnées | 3 | [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) |
| C3 | Jours sans séance | Intégration et unitaire | Jeu `C03` : jours présents à 0, CE courte décroissante | 3 | [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md) |
| C4 | Joueur absent 10 jours | Intégration et unitaire | Jeu `C04` : CE courte à 0, intensité recalculée chaque jour | 3 | [ADR-0011](adr/0011-calendrier-et-charges-glissantes.md), [ADR-0013](adr/0013-absences-longues.md) |
| C5 | Séance en brouillon | Intégration | Jeu `C05` : un brouillon en base, ignoré par l'adaptateur | 3 | [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) |
| C6 | Charge extrême après un historique régulier non constant | Intégration et unitaire | Jeu `C06` : z-score très supérieur à 2 | 3 | [ADR-0012](adr/0012-zscore-d-intensite.md) |
| C7 | Historique constant | Intégration et unitaire | Jeu `C07` : état `non_calculable` pour l'intensité et pour les sensations | 3 | [ADR-0012](adr/0012-zscore-d-intensite.md), [ADR-0015](adr/0015-zscore-de-sensations.md) |
| C8 | Historique trop court | Intégration et unitaire | Jeu `C08` : état `historique_insuffisant` | 3 | [ADR-0012](adr/0012-zscore-d-intensite.md), [ADR-0015](adr/0015-zscore-de-sensations.md) |
| C9 | Date de rétrospection D | Intégration | Jeu `C09` : des données datées après D sont en base ; le résultat à D égale `attendu.csv` à D | 3 | [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) |
| C10 | Séance faite avec une autre catégorie | Intégration | Jeu `C10` : deux catégories en base, charge comptée pour le joueur | 3 | — |
| C11 | Indicateurs d'échelles différentes | Intégration et unitaire | Jeu `C11` : deux échelles dans la même entrée | 3 | [ADR-0014](adr/0014-score-de-sensations.md) |
| C12 | Indicateur inversé | Intégration et unitaire | Jeu `C12` | 3 | [ADR-0014](adr/0014-score-de-sensations.md) |
| C13 | Réponse manquante | Intégration et unitaire | Jeu `C13` : score sur les réponses présentes ; sous le minimum, état `reponses_insuffisantes` | 3 | [ADR-0014](adr/0014-score-de-sensations.md) |
| C14 | Charges multipliées par une constante | Intégration et unitaire | Jeu `C06` rejoué avec `facteur_echelle_charge` multiplié par 7 : z-scores identiques, charges multipliées par 7 | 3 | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md) |
| C15 | Ajout d'un indicateur ou changement de poids en cours de saison | Intégration | Jeu `C15`, selon le comportement retenu | 3 | [ADR-0016](adr/0016-evolution-de-la-configuration.md) |
| A1 | Visiteur non connecté | Intégration | Toutes les routes du résolveur d'URL, en GET et en POST, sans session : redirection vers la connexion ou refus, jamais de donnée, hors liste blanche. Catalogue de la base : aucun droit à `PUBLIC`, aucune fonction `SECURITY DEFINER`, aucune vue sans `security_invoker`, aucun droit de schéma pour le rôle d'exécution | 1 (squelette), 2 | [ADR-0005](adr/0005-controle-d-acces-applicatif.md) |
| A2 | Nouvel objet sans règle d'accès | Intégration | Méta-test : une route ajoutée sans protection, puis une table accordée à `PUBLIC` dans une transaction, sont détectées par les vérifications de A1 | 2 | [ADR-0005](adr/0005-controle-d-acces-applicatif.md) |
| A3 | Staff d'une catégorie | Intégration | Deux catégories, deux préparateurs, un joueur invité : listes, fiches, participations, export | 2, puis 4 à 6 pour chaque écran | [ADR-0005](adr/0005-controle-d-acces-applicatif.md) |
| A4 | Lien joueur valide (formulation validée le 2026-10-12 : dépose et modifie son entrée du jour ; ne lit ni ses entrées des autres jours ni les autres joueurs) | Intégration et bout en bout | Dépose et modifie l'entrée du jour ; ne lit ni l'entrée d'un autre jour ni un autre joueur ; aucune autre route n'accepte le jeton | 5 | [ADR-0006](adr/0006-lien-joueur-a-jeton-hache.md), [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) |
| A5 | Lien invalide, révoqué ou régénéré | Intégration | Même réponse 404 dans les trois cas ; le jeton en clair ne figure dans aucune colonne de la base | 5 | [ADR-0006](adr/0006-lien-joueur-a-jeton-hache.md) |
| A6 | Tentative d'inscription publique | Intégration | Aucune route d'inscription ; création de compte refusée sans superutilisateur ; administration fermée aux préparateurs | 2 | [ADR-0005](adr/0005-controle-d-acces-applicatif.md) |
| D1 | Valeur hors plage | Unitaire et intégration | Formulaires ; puis insertion SQL directe, sans passer par Django, rejetée par la base (RPE, durée nulle ou négative, valeur hors bornes d'un indicateur) | 2, puis 4 et 5 | [ADR-0007](adr/0007-echelle-rpe-et-formule-de-charge.md), [ADR-0010](adr/0010-indicateurs-et-echelles.md) |
| D2 | Doublons | Intégration | Participation en double et seconde entrée le même jour rejetées par la base ; un second envoi par le lien modifie l'entrée existante | 2, puis 5 | [ADR-0008](adr/0008-cycle-de-vie-des-saisies.md) |
| D3 | Base vide | CI | Job `migrations` ; test d'intégration de `generer_demo` ; `makemigrations --check` | 1 (migration vide), 2 | — |
| D4 | Suppression ou archivage d'un joueur | Intégration | Comportement de l'ADR, y compris l'absence de toute donnée résiduelle | 2 | [ADR-0009](adr/0009-suppression-et-archivage-d-un-joueur.md) |
| E1 | Séance de 25 joueurs | Bout en bout | Format ordinateur, puis format tablette ; les charges apparaissent sur le tableau de bord | 4 | — |
| E2 | Questionnaire sur téléphone | Bout en bout | Format téléphone ; le badge passe à « Reçu » côté staff | 5 | [ADR-0017](adr/0017-frequence-du-questionnaire.md) |
| E3 | Fiche du joueur de référence | Bout en bout | Jeu `E3-fiche-joueur` ; valeurs lues dans les tableaux qui accompagnent les graphiques | 6 | [ADR-0018](adr/0018-graphique-forme-actuelle.md) |

Tests complémentaires, hors liste du cadrage : `engine/` n'importe pas Django ; `updated_at` change à chaque modification ; aucun index en double ; `.env.example` déclare toutes les variables lues par les réglages ; liens internes de la documentation.

## 9. Tests contre l'environnement déployé

- **À chaque déploiement** : test de fumée. La racine redirige vers la connexion ; la page de connexion répond ; les en-têtes de sécurité sont présents.
- **Avant la mise en service (phase 7)** : A1, A4, A5 et A6 en boîte noire par HTTP contre l'URL publique, et les vérifications de catalogue de A1 exécutées par la CI contre la base Neon de production.

## 10. Pièges connus

- Playwright en mode synchrone et l'ORM Django dans le même processus : Django refuse l'accès à la base depuis une boucle asynchrone. La variable `DJANGO_ALLOW_ASYNC_UNSAFE` n'est activée que pour les tests de bout en bout.
- Le pooler de connexions de Neon fonctionne par transaction : en production, curseurs côté serveur désactivés et connexions non persistantes. Les previews détectent ce type d'écart, que la CI sur Postgres direct ne voit pas.
- Les nombres à virgule se comparent avec la tolérance de la section 6, jamais après arrondi.
- Les dates se calculent toujours à l'heure de Paris, par la fonction unique de la section 5.
