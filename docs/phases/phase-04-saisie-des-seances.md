# Phase 04 — Saisie des séances

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | — | — | v0.4.0 |

## Objectif

Le préparateur remplace son fichier Excel : il se connecte, crée une séance, saisit la grille RPE au clavier, l'enregistre en brouillon puis la valide, et retrouve, corrige ou supprime ses séances.

Niveau de collaboration : 4 pour la phase entière, PR 4.2 et PR qui touchent aux règles d'accès ou aux migrations comprises (décision du mainteneur le 2026-10-15 en validant cette fiche). Claude Code travaille sur une branche, commite, pousse et ouvre les PR ; le mainteneur relit et fusionne. Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur. Estimation : 18 heures (cadrage, section 9).

## Livrables

- [ ] Connexion et structure des pages (gabarit de base, navigation, mise en page tablette et téléphone)
- [ ] Gestion des joueurs de sa catégorie (US-15)
- [ ] Création d'une séance et de ses participants (US-03)
- [ ] Grille RPE, brouillon puis validation, charges affichées sur la séance validée (US-04, US-05)
- [ ] Historique, correction et suppression des séances (US-06)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 4.1 | `feat: ajouter la connexion et la structure des pages` | Gabarit de base, navigation, connexion et déconnexion (message générique), mise en page tablette et téléphone | Intégration de la connexion ; bout en bout de la connexion | En revue | [#29](https://github.com/leonardgst/Training-charge/pull/29) |
| 4.2 | `feat: gérer les joueurs de sa catégorie` | Liste, création, modification, archivage (US-15) | A3 étendu, D1 | À commencer | — |
| 4.3 | `feat: créer une séance et ses participants` | En-tête, pré-remplissage avec les joueurs actifs, annuaire, retrait d'un absent | D1 (durée), A3 (joueur invité) | À commencer | — |
| 4.4 | `feat: saisir la grille RPE puis la valider` | Grille au clavier, code couleur, brouillon, validation, charges affichées sur la séance validée (moteur de la phase 3) | D1, E1 sur ordinateur et tablette | À commencer | — |
| 4.5 | `feat: lister, corriger et supprimer les séances` | Historique, correction directe, suppression confirmée, traçabilité (ADR-0008) | Intégration, `updated_by` | À commencer | — |

## Critères de fin (Definition of Done)

- [ ] Toutes les PR de la phase sont fusionnées, CI verte
- [ ] Parcours E1 au vert, sur ordinateur et tablette émulés
- [ ] Couverture de la validation des saisies (`suivi/forms.py` et validateurs du modèle) d'au moins 90 % des branches, imposée en CI
- [ ] Toute requête d'une vue staff passe par `suivi/acces.py` ; A1 et A3 étendus aux nouvelles routes
- [ ] Utilisable sur tablette
- [ ] Recette manuelle faite, avec une séance de 25 joueurs chronométrée
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 5

## Recette manuelle

Liste préparée à la fin de la phase ; elle comprendra la saisie chronométrée d'une séance de 25 joueurs sur tablette.

## Décisions prises (liens vers les ADR)

- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès applicatif et refus par défaut
- [ADR-0007](../adr/0007-echelle-rpe-et-formule-de-charge.md) — Échelle RPE et formule de charge
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur

## Écarts par rapport au plan

- Niveau de collaboration : 4 pour toute la phase, par décision du mainteneur le 2026-10-15. Le cadrage prévoyait le niveau 3 pour la PR 4.2 et pour toute PR qui touche aux règles d'accès ou aux migrations (sections 6 et 9).
- PR 4.1 : Pico CSS 2.1.1 copié dans `suivi/static/suivi/vendor/pico/` avec sa licence MIT, avec l'accord du mainteneur (ajout d'une dépendance). Source : paquet npm officiel `@picocss/pico` 2.1.1, dont l'empreinte sha512 a été vérifiée contre celle que publie le registre.
- PR 4.1 : pages d'erreur 403, 404 et 500 en français, sur le gabarit de base, en plus du contenu prévu ; le refus d'un compte sans profil préparateur s'affichait en anglais.
- En-têtes de sécurité : la politique de sécurité du contenu et `Referrer-Policy: no-referrer`, prévues par l'architecture (section 5), ne sont pas posées depuis la phase 1 (Django envoie `Referrer-Policy: same-origin` par défaut). Le mainteneur a décidé le 2026-10-15 de les poser dans une PR `fix:` dédiée, après la PR 4.1. Les gabarits de la PR 4.1 n'ont ni script ni style en ligne, et l'administration de Django 5.2 non plus.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
