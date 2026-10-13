# Phase 02 — Modèle de données et accès

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| À commencer | — | — | v0.2.0 |

## Objectif

Un schéma contraint et un modèle d'accès prouvé, avant toute interface.

Niveau de collaboration : 4 pour la phase entière (relevé de 3 à 4 par le mainteneur le 2026-10-13). Claude Code travaille sur une branche et ouvre les PR ; le mainteneur relit et fusionne. Estimation : 20 heures (cadrage, section 9).

## Livrables

- [ ] Modèles et migrations
- [ ] Contraintes et déclencheurs
- [ ] Couche d'accès (`suivi/acces.py`) et refus par défaut vérifié par le catalogue des URL
- [ ] Administration réservée au superutilisateur
- [ ] Données de démonstration générées par script, sans aucune donnée réelle

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 2.1 | `feat: ajouter les catégories, les préparateurs et les joueurs` | Modèles, contraintes, clé étrangère vers les comptes, archivage, administration | D1 (champs obligatoires), D4 (archivage), `updated_at` | Fusionnée | [#12](https://github.com/leonardgst/Training-charge/pull/12) |
| 2.2 | `feat: ajouter les séances et les participations` | RPE de 0 à 10, durée de 1 à 300, unicité, déclencheur de complétude à la validation | D1, D2, déclencheur | Fusionnée | [#13](https://github.com/leonardgst/Training-charge/pull/13) |
| 2.3 | `feat: ajouter les indicateurs et les entrées de sensations` | Bornes contrôlées par déclencheur, une entrée par joueur et par jour, échelle figée après la première réponse | D1, D2, refus d'un changement d'échelle | Fusionnée | [#14](https://github.com/leonardgst/Training-charge/pull/14) |
| 2.4 | `feat: protéger les accès du staff` | Profil préparateur exigé par URL, `suivi/acces.py`, liste blanche, administration fermée aux préparateurs | A1 complet, A2, A3, A6, index en double | En revue | — |
| 2.5 | `feat: générer la démonstration et effacer un joueur` | `generer_demo` à graine fixe (U19 et une seconde catégorie), effacement par l'administrateur | D3, D4 | À faire | — |

## Critères de fin (Definition of Done)

- [ ] A1, A2, A3, A6 et D1 à D4 au vert
- [ ] Migrations rejouées depuis zéro en CI et sur chaque preview
- [ ] Aucune donnée réelle
- [ ] Recette manuelle faite
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 3

## Décisions prises (liens vers les ADR)

- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès applicatif et refus par défaut
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur

## Écarts par rapport au plan

Aucun pour l'instant.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
