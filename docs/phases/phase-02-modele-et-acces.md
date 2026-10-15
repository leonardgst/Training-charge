# Phase 02 — Modèle de données et accès

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| Terminée | 2026-10-13 → 2026-10-15 | 2026-10-15 | v0.2.0 (à poser après la fusion de cette PR) |

## Objectif

Un schéma contraint et un modèle d'accès prouvé, avant toute interface.

Niveau de collaboration : 4 pour la phase entière (relevé de 3 à 4 par le mainteneur le 2026-10-13). Claude Code travaille sur une branche et ouvre les PR ; le mainteneur relit et fusionne. Estimation : 20 heures (cadrage, section 9).

## Livrables

- [x] Modèles et migrations
- [x] Contraintes et déclencheurs
- [x] Couche d'accès (`suivi/acces.py`) et refus par défaut vérifié par le catalogue des URL
- [x] Administration réservée au superutilisateur
- [x] Données de démonstration générées par script, sans aucune donnée réelle

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 2.1 | `feat: ajouter les catégories, les préparateurs et les joueurs` | Modèles, contraintes, clé étrangère vers les comptes, archivage, administration | D1 (champs obligatoires), D4 (archivage), `updated_at` | Fusionnée | [#12](https://github.com/leonardgst/Training-charge/pull/12) |
| 2.2 | `feat: ajouter les séances et les participations` | RPE de 0 à 10, durée de 1 à 300, unicité, déclencheur de complétude à la validation | D1, D2, déclencheur | Fusionnée | [#13](https://github.com/leonardgst/Training-charge/pull/13) |
| 2.3 | `feat: ajouter les indicateurs et les entrées de sensations` | Bornes contrôlées par déclencheur, une entrée par joueur et par jour, échelle figée après la première réponse | D1, D2, refus d'un changement d'échelle | Fusionnée | [#14](https://github.com/leonardgst/Training-charge/pull/14) |
| 2.4 | `feat: protéger les accès du staff` | Profil préparateur exigé par URL, `suivi/acces.py`, liste blanche, administration fermée aux préparateurs | A1 complet, A2, A3, A6, index en double | Fusionnée | [#15](https://github.com/leonardgst/Training-charge/pull/15) |
| 2.5 | `feat: générer la démonstration et effacer un joueur` | `generer_demo` à graine fixe (U19 et une seconde catégorie), effacement par l'administrateur | D3, D4 | Fusionnée | [#16](https://github.com/leonardgst/Training-charge/pull/16) |

## Critères de fin (Definition of Done)

- [x] A1, A2, A3, A6 et D1 à D4 au vert : 235 tests (unitaires, intégration, bout en bout), couverture de `suivi/` à 99 %. La part de D4 sur la révocation et le refus du lien joueur attend `LienJoueur` (phase 5)
- [x] Migrations rejouées depuis zéro en CI et sur chaque preview : job `migrations` (avec chargement de la démonstration) et preview Neon verts sur les PR #12 à #16
- [x] Aucune donnée réelle : tout vient de `generer_demo` (graine fixe, noms fictifs), le job `audit` (gitleaks) est vert
- [x] Recette manuelle faite (section ci-dessous)
- [x] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 3

## Décisions prises (liens vers les ADR)

- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès applicatif et refus par défaut
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur

## Recette manuelle

À dérouler par toi, base locale neuve puis environnement déployé. Note le résultat à côté de chaque ligne ; je ne coche rien à ta place.

Base locale (`docker compose down -v && docker compose up -d db`, puis `uv run --env-file .env python manage.py migrate` et `uv run --env-file .env python manage.py generer_demo`) :

- [x] La commande affiche 33 joueurs et un mot de passe, une seule fois ; la relancer sur la base chargée est refusée.
- [x] Connecté en `prep_u19`, `/` s'affiche ; `/admin/` renvoie à la page de connexion de l'administration.
- [x] Connecté en `prep_u17`, même constat.
- [x] Connecté en `admin_demo`, `/admin/` s'ouvre (ordinateur et téléphone) ; les joueurs, les catégories, les préparateurs et les indicateurs sont listés.
- [x] Dans l'administration, créer un joueur sans nom est refusé avec un message de formulaire.
- [x] Dans l'administration, changer les bornes d'un indicateur déjà utilisé est refusé par la base ; l'administration peut afficher une erreur brute plutôt qu'un message soigné (limite connue).
- [x] Dans l'administration, effacer un joueur affiche la liste de ce qui sera supprimé ; après confirmation, il disparaît de la liste des joueurs et ses séances restent pour les autres.
- [x] Un visiteur sans session qui ouvre `/admin/` ou `/` est renvoyé vers une connexion.

Environnement déployé :

- [x] La preview de la PR de clôture s'ouvre sur ton téléphone et `/sante/` répond. PR déjà fusionnée avant la recette, preview supprimée : non testé, remplacé par la vérification de la production sur téléphone.
- [x] Après fusion, le déploiement de production (migrations par le rôle de migration) attend ton approbation, puis `/sante/` répond et `/admin/` demande une connexion.

## Écarts par rapport au plan

- Niveau de collaboration relevé de 3 à 4 par le mainteneur le 2026-10-13, avant la PR 2.1 (le cadrage prévoyait le niveau 3 pour toute la phase).
- `suivi/horloge.py` (fonction unique de la date du jour, exigée par `CLAUDE.md`) n'était pas dans le plan : ajoutée en PR 2.5, avec un test qui interdit `date.today()` ailleurs.
- Le job `migrations` charge désormais la démonstration (extension du workflow de CI prévue par D3, faite en PR 2.5).
- Deux empreintes dans `.gitleaksignore` : faux positifs de gitleaks sur des mots de passe fictifs de tests, corrigés dans le code mais présents dans l'historique de la PR 2.4 (poussée forcée interdite).

## Rétrospective : ce qui a marché, ce qui a coincé

**Ce qui a marché**
- Faire porter les règles par la base : contraintes `CHECK`, unicités et déclencheurs vérifiés par SQL direct sous le rôle d'exécution, donc indépendamment de Django.
- Les méta-tests du catalogue (A2) : chaque détecteur est testé en lui injectant une anomalie dans une transaction annulée, ce qui évite un test d'accès qui passe parce qu'il ne regarde rien.
- La démonstration à graine fixe, déduite du calendrier plutôt que recopiée de la sortie, sert à la fois de jeu de test (D3), de contrôle de CI et de matériau pour les phases 3 à 6.
- Une PR par couche, chacune relue et verte avant la suivante : aucune PR n'a dépassé la limite de relecture.

**Ce qui a coincé**
- gitleaks scanne tout l'historique : un mot de passe fictif de test a fait échouer le job `audit` de la PR 2.4. Corrigé par un mot de passe généré à l'exécution et deux empreintes ignorées, car l'historique ne se réécrit pas.
- Le classifieur de Claude Code bloque les modifications des fichiers de permissions et de `CLAUDE.md` : ces commits ont été faits par le mainteneur.
- Une erreur de borne dans mon premier test D3 (date de départ du joueur archivé) : corrigée dans la PR 2.5 et signalée comme telle.
- Un délai de 10 s de l'API Neon a fait échouer une preview une fois ; relancée, verte.

**Limites connues, documentées dans les PR**
- Les déclencheurs de complétude et d'échelle ne verrouillent pas les lignes : deux transactions concurrentes pourraient les contourner. Sans effet avec un préparateur par catégorie ; à revoir si la saisie devient concurrente.
- Le droit `CONNECT` de `PUBLIC` sur la base n'est pas dans le catalogue de CI ; à contrôler contre la production en phase 7.
- Un superutilisateur sans profil préparateur reçoit un 403 sur `/` (voulu : il utilise `/admin/`).

**À reprendre**
- Mesurer le réveil de Neon avec une vraie connexion : aucune page ne touche encore la base de production ; à faire avec la connexion de la PR 4.1.
- Ajouter Dependabot, toujours non fait.
- Aligner la case « niveau 3 » du modèle de PR sur la règle de `CLAUDE.md` si le mainteneur le souhaite.
