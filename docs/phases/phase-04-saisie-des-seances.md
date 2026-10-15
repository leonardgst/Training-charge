# Phase 04 — Saisie des séances

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En clôture : recette à faire | — | — | v0.4.0 (à poser après la recette) |

## Objectif

Le préparateur remplace son fichier Excel : il se connecte, crée une séance, saisit la grille RPE au clavier, l'enregistre en brouillon puis la valide, et retrouve, corrige ou supprime ses séances.

Niveau de collaboration : 4 pour la phase entière, PR 4.2 et PR qui touchent aux règles d'accès ou aux migrations comprises (décision du mainteneur le 2026-10-15 en validant cette fiche). Claude Code travaille sur une branche, commite, pousse et ouvre les PR ; le mainteneur relit et fusionne. Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur. Estimation : 18 heures (cadrage, section 9).

## Livrables

- [x] Connexion et structure des pages (gabarit de base, navigation, mise en page tablette et téléphone)
- [x] Gestion des joueurs de sa catégorie (US-15)
- [x] Création d'une séance et de ses participants (US-03)
- [x] Grille RPE, brouillon puis validation, charges affichées sur la séance validée (US-04, US-05)
- [x] Historique, correction et suppression des séances (US-06)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 4.1 | `feat: ajouter la connexion et la structure des pages` | Gabarit de base, navigation, connexion et déconnexion (message générique), mise en page tablette et téléphone | Intégration de la connexion ; bout en bout de la connexion | Fusionnée | [#29](https://github.com/leonardgst/Training-charge/pull/29) |
| 4.1 bis | `fix: poser la politique de sécurité du contenu` | Politique limitée à l'origine du site sur toute réponse, `Referrer-Policy: same-origin` explicite, test de fumée étendu (ajoutée en cours de phase, écarts) | Intégration des en-têtes ; bout en bout sans violation, administration comprise | Fusionnée | [#30](https://github.com/leonardgst/Training-charge/pull/30) |
| 4.2 | `feat: gérer les joueurs de sa catégorie` | Liste, création, modification, archivage (US-15) | A3 étendu, D1 | Fusionnée | [#31](https://github.com/leonardgst/Training-charge/pull/31) |
| 4.3 | `feat: créer une séance et ses participants` | En-tête, pré-remplissage avec les joueurs actifs, annuaire, retrait d'un absent | D1 (durée), A3 (joueur invité) | Fusionnée | [#32](https://github.com/leonardgst/Training-charge/pull/32) |
| 4.4 | `feat: saisir la grille RPE puis la valider` | Grille au clavier, code couleur, brouillon, validation, charges affichées sur la séance validée (moteur de la phase 3) | D1, E1 sur ordinateur et tablette | Fusionnée | [#33](https://github.com/leonardgst/Training-charge/pull/33) |
| 4.5 | `feat: lister, corriger et supprimer les séances` | Historique, correction directe, suppression confirmée, traçabilité (ADR-0008) | Intégration, `updated_by` | Fusionnée | [#34](https://github.com/leonardgst/Training-charge/pull/34) |

## Critères de fin (Definition of Done)

- [x] Toutes les PR de la phase sont fusionnées, CI verte (six PR, dont la 4.1 bis ajoutée en cours de phase)
- [x] Parcours E1 au vert, sur ordinateur et tablette émulés (`tests/e2e/test_grille.py` : 25 joueurs saisis au clavier, brouillon, validation, charges)
- [x] Couverture de la validation des saisies d'au moins 90 % des branches, imposée en CI (`suivi/forms.py` à 100 % ; le modèle n'a pas de validateur Python, ses plages sont des contraintes de la base)
- [x] Toute requête d'une vue staff passe par `suivi/acces.py` (test sur `suivi/views/`) ; A1 parcourt automatiquement les 15 routes ajoutées, A3 est étendu à chaque écran
- [ ] Utilisable sur tablette : prouvé en tablette émulée par les tests de bout en bout, à confirmer pendant la recette
- [ ] Recette manuelle faite, avec une séance de 25 joueurs chronométrée
- [x] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 5

## Recette manuelle

À dérouler par toi, `main` à jour après la fusion de la PR de clôture ; je ne coche rien à ta place. Ni la production ni les previews ne contiennent de données (la démonstration y est chargée en phase 7) : le parcours se fait sur ta base locale, la production est vérifiée par son déploiement.

**En local, sur ordinateur**

- [ ] Base neuve et démonstration : `docker compose down -v && docker compose up -d db`, puis `uv run --env-file .env python manage.py migrate` et `uv run --env-file .env python manage.py generer_demo` (noter le mot de passe affiché), puis `uv run --env-file .env python manage.py runserver`.
- [ ] Connexion : un mauvais mot de passe donne un message qui ne dit pas quel identifiant est faux ; `prep_u19` arrive sur l'accueil ; `admin_demo` reçoit « Accès refusé » sur `/` et entre dans `/admin/`.
- [ ] Joueurs : ajouter, modifier, archiver puis réactiver un joueur ; archivé, il n'apparaît plus dans « Nouvelle séance ».
- [ ] **Saisie chronométrée** : « Nouvelle séance » (les 24 joueurs U19 actifs sont cochés), puis, dans le bloc « Participants », ajouter un joueur U17 par la recherche : 25 participants. Saisir les 75 RPE au clavier (valeur, puis Tab), enregistrer le brouillon à mi-parcours, terminer et valider. Noter le temps, de l'ouverture de « Nouvelle séance » à la validation (cible : moins de 5 minutes).
- [ ] Pendant la saisie, chaque case prend la couleur de sa valeur ; `12` est signalé comme invalide.
- [ ] Séance validée : vérifier une charge à la main (moyenne des trois RPE × durée × 10).
- [ ] Corriger un RPE, retirer puis ajouter un participant (avec ses trois RPE), changer la durée : les charges suivent, « Dernière modification » est à jour.
- [ ] Supprimer une séance après sa page de confirmation : elle disparaît de l'historique ; la séance en brouillon de la démonstration y est marquée « Brouillon ».
- [ ] Connecté en `prep_u17`, l'adresse d'une séance U19 donne « Page introuvable ».

**Sur tablette et téléphone**

- [ ] La même saisie chronométrée sur une tablette : une vraie si elle atteint ton poste, sinon Chrome en mode appareil (iPad) ; noter le temps et le moyen utilisé. Le clavier numérique s'ouvre sur une vraie tablette.
- [ ] Sur téléphone (ou en mode appareil) : connexion, joueurs, séance, historique, sans défilement horizontal.

**En production**

- [ ] Après la fusion, le déploiement de production attend ton approbation ; son test de fumée est vert (il vérifie désormais la politique de sécurité du contenu et `Referrer-Policy`) ; `/connexion/` s'affiche avec sa mise en page sur ordinateur et sur téléphone. La phase n'ajoute aucune migration.

## Décisions prises (liens vers les ADR)

- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès applicatif et refus par défaut
- [ADR-0007](../adr/0007-echelle-rpe-et-formule-de-charge.md) — Échelle RPE et formule de charge
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur
- [Architecture, section 5](../02-architecture.md#5-modèle-daccès) — En-têtes de sécurité : politique de sécurité du contenu et `Referrer-Policy: same-origin` (décision du mainteneur du 2026-10-15, PR 4.1 bis)

## Écarts par rapport au plan

- Niveau de collaboration : 4 pour toute la phase, par décision du mainteneur le 2026-10-15. Le cadrage prévoyait le niveau 3 pour la PR 4.2 et pour toute PR qui touche aux règles d'accès ou aux migrations (sections 6 et 9).
- PR 4.1 : Pico CSS 2.1.1 copié dans `suivi/static/suivi/vendor/pico/` avec sa licence MIT, avec l'accord du mainteneur (ajout d'une dépendance). Source : paquet npm officiel `@picocss/pico` 2.1.1, dont l'empreinte sha512 a été vérifiée contre celle que publie le registre.
- PR 4.1 : pages d'erreur 403, 404 et 500 en français, sur le gabarit de base, en plus du contenu prévu ; le refus d'un compte sans profil préparateur s'affichait en anglais.
- En-têtes de sécurité : la politique de sécurité du contenu et `Referrer-Policy: no-referrer`, prévues par l'architecture (section 5), ne sont pas posées depuis la phase 1 (Django envoie `Referrer-Policy: same-origin` par défaut). Le mainteneur a décidé le 2026-10-15 de les poser dans une PR `fix:` dédiée, après la PR 4.1 (PR 4.1 bis). Les gabarits de la PR 4.1 n'ont ni script ni style en ligne, et l'administration de Django 5.2 non plus.
- PR 4.1 bis : `Referrer-Policy` reste `same-origin` au lieu de `no-referrer`, par décision du mainteneur le 2026-10-15. Avec `no-referrer`, le navigateur envoie `Origin: null` sur chaque formulaire POST et le contrôle CSRF de Django refuse la connexion (constaté par les tests de bout en bout). L'architecture (section 5) est corrigée ; la page du lien joueur, pour laquelle l'ADR-0006 prévoit `no-referrer`, devra en tenir compte en phase 5 (piège ajouté à `CLAUDE.md`).
- PR 4.2 : le lien du joueur n'est pas révoqué à l'archivage, parce que les liens n'existent pas encore. La révocation à l'archivage (US-15, ADR-0009) arrive avec la génération des liens en phase 5.
- PR 4.2 : la date de naissance est refusée si elle est dans le futur, à la saisie seulement. Une contrainte en base dépendrait de la date du jour, ce que `CHECK` ne permet pas proprement ; aucune règle des spécifications ne fixe de plage.
- PR 4.2 : seuil de 90 % des branches de `suivi/forms.py` imposé en CI, avec l'accord du mainteneur (modification de `ci.yml`).
- PR 4.2 : les fichiers de test d'intégration de la connexion et des joueurs s'appellent `test_vues_*.py`. Sans `__init__.py` dans `tests/`, deux fichiers du même nom (`test_connexion.py` en intégration et en bout en bout, depuis la PR 4.1) empêchent `uv run pytest` de collecter la suite entière ; la CI, qui lance les niveaux séparément, ne le voyait pas. Un test unitaire l'interdit désormais.
- PR 4.3 : les participants ne s'ajoutent et ne se retirent que sur une séance en brouillon. Une séance validée exige les trois RPE de chaque participant (déclencheur de l'ADR-0008) : sa correction, participants compris, est l'objet de la PR 4.5.
- PR 4.3 : la recherche dans l'annuaire porte sur le nom et le prénom, écarte les participants et les joueurs archivés, et s'arrête à 20 résultats. Elle sert aussi à rajouter un joueur de sa catégorie retiré par erreur.
- PR 4.3 : aucune plage n'est imposée à la date d'une séance, faute de règle dans les spécifications ; une séance datée dans le futur n'entre dans les calculs qu'à sa date (C9). Une séance peut être créée sans participant.
- PR 4.3 : une séance créée s'ouvre sur sa page ; la liste des séances arrive avec l'historique (PR 4.5).
- PR 4.4 : les charges affichées sur une séance validée sont les charges de séance de chaque participant, calculées par le moteur (`charges_de_seance` dans l'adaptateur). Elles sont montrées aussi pour un joueur invité : elles ne dépendent que des RPE et de la durée de cette séance, que le préparateur organisateur voit déjà, et non de l'historique de l'invité (R24). Les tableaux de bord arrivent en phase 6.
- PR 4.4 : une séance sans participant ne se valide pas, règle ajoutée faute de sens à une séance validée vide ; une grille ouverte avant un changement de participants est refusée, plutôt que d'effacer des RPE.
- PR 4.4 : code couleur provisoire, du vert (effort léger) au rouge (effort maximal), en onze teintes, à confirmer avec le préparateur. Une valeur hors échelle est signalée pendant la frappe et bloquée par le navigateur (`pattern`), puis refusée par le serveur.
- PR 4.4 : sur une séance en brouillon, la grille ouvre la page et les participants passent dans un bloc repliable : un bouton « Retirer » dans la grille aurait coupé l'ordre de la touche Tab. Le test de bout en bout de la PR 4.3 ouvre désormais ce bloc avant de chercher un joueur, ses vérifications sont inchangées. Une séance validée s'affiche en lecture seule ; sa correction est l'objet de la PR 4.5.
- PR 4.5 : une séance validée se corrige entièrement et reste validée : grille (trois RPE exigés), en-tête, retrait d'un participant (sauf le dernier) et ajout d'un joueur avec ses trois RPE. Les participants en font partie par décision du mainteneur du 2026-10-15, consignée dans l'ADR-0008. Trois tests qui vérifiaient la limite provisoire des PR 4.3 et 4.4 ont été transformés, avec l'accord du mainteneur, pour vérifier le nouveau comportement, sans en supprimer : `test_rien_ne_s_ajoute_a_une_seance_validee` (devenu `test_a_une_seance_validee_un_joueur_ne_s_ajoute_qu_avec_ses_trois_rpe`), `test_personne_ne_se_retire_d_une_seance_validee` (devenu `test_le_dernier_participant_d_une_seance_validee_ne_se_retire_pas`) et `test_une_seance_validee_ne_se_modifie_pas_par_la_grille` (devenu `test_une_seance_validee_ne_perd_jamais_un_rpe_par_la_grille`).
- PR 4.5 : l'historique liste les séances par date décroissante, 30 par page. La suppression passe par une page de confirmation, pour une séance en brouillon comme validée.
- Recette : ni la production ni les previews n'ont de données avant la phase 7, et je n'agis jamais sur une base déployée. La saisie chronométrée se fait donc sur la base locale, avec la démonstration ; la production est vérifiée par son test de fumée.
- Point ouvert à la clôture : aucune plage n'est imposée à la date d'une séance (PR 4.3). Une séance datée dans le futur n'entre dans les calculs qu'à sa date. Refuser les dates futures à la saisie est à décider par le mainteneur.

## Rétrospective : ce qui a marché, ce qui a coincé

**Ce qui a marché**
- Le refus par défaut et le catalogue des routes : chacune des 15 routes ajoutées a été testée par A1 sans qu'aucun test ne soit écrit pour elle, et `suivi/acces.py` a suffi à chaque écran, joueur invité compris.
- Les tests de bout en bout aux trois formats, avec une vérification du débordement : ils ont trouvé de vrais défauts de mise en page (boutons étirés par Pico, tableaux coupés sur téléphone) que les captures ont confirmés.
- Le moteur de la phase 3, appelé par l'adaptateur : les charges de la séance validée n'ont demandé aucune formule dans l'interface, et chaque valeur affichée a été comparée à un calcul fait à la main.
- Des PR courtes, ouvertes et fusionnées dans la journée, avec une question au mainteneur à chaque décision hors de la fiche (Pico, en-têtes, `Referrer-Policy`, seuil de CI, correction des séances validées).

**Ce qui a coincé**
- La fiche et le journal, modifiés par chaque PR aux mêmes lignes : trois fusions de `main` dans une branche pour résoudre des conflits. Ouvrir une PR seulement après la fusion de la précédente, ou mettre à jour la fiche à la fusion plutôt que dans la PR, l'éviterait.
- Une décision d'architecture (`Referrer-Policy: no-referrer`) incompatible avec Django ne s'est révélée qu'avec la première page à formulaire : les en-têtes auraient dû être posés et testés en phase 1, comme le prévoyait l'ADR-0005.
- Des tests écrits pour une limite provisoire (« une séance validée ne se modifie pas ici ») ont dû être transformés dès la PR 4.5, avec l'accord du mainteneur. Mieux vaut ne tester une limite provisoire que si elle protège quelque chose.
- Deux fichiers de test du même nom passaient en CI, qui lance les niveaux séparément, mais pas avec `uv run pytest` : un test l'interdit désormais.
