# Phase 03 — Moteur de calcul

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| À commencer | — | — | v0.3.0 |

## Objectif

Des chiffres justes, prouvés indépendamment de l'implémentation.

Niveau de collaboration : 4 pour la phase entière (relevé de 3 à 4 par le mainteneur le 2026-10-15). Claude Code travaille sur une branche, commite, pousse et ouvre les PR ; le mainteneur relit et fusionne. Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur. Les fichiers `tests/reference/**/attendu.csv` et `provenance.md` sont écrits par le mainteneur seul. Estimation : 24 heures, plus environ 10 heures pour le jeu de référence du mainteneur (cadrage, section 9).

## Livrables

- [ ] Jeu de référence avec provenance
- [ ] `engine/` (moteur pur, sans Django, typage strict)
- [ ] Adaptateur `suivi/calculs.py`
- [ ] `config/calcul.toml`

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 3.1 | `test: ajouter le jeu de référence et les cas C1 à C15` | Format, harnais sur base et sans base, cas en `xfail(strict=True)`. Les `attendu.csv` et `provenance.md` sont écrits par le mainteneur. | C1 à C15, en échec attendu | À commencer | — |
| 3.2 | `feat: calculer la charge du jour sur un calendrier continu` | Types, paramètres, charge de séance, calendrier, adaptateur | C1, C2, C5, C10 | À commencer | — |
| 3.3 | `feat: calculer la CE courte et la CE longue` | Sommes glissantes, drapeau de fenêtre incomplète | C3, C9 | À commencer | — |
| 3.4 | `feat: calculer l'intensité` | Référence, historique minimal, écart-type nul | C4, C6, C7 et C8 pour l'intensité, C14 | À commencer | — |
| 3.5 | `feat: calculer le score et le z-score de sensations` | Normalisation, orientation, pondération, référence | C7 et C8 pour les sensations, C11, C12, C13, C15 | À commencer | — |

## Critères de fin (Definition of Done)

- [ ] C1 à C15 au vert, sans aucun `xfail` restant
- [ ] Couverture de `engine/` d'au moins 95 % des branches
- [ ] Contrôle indépendant du mainteneur consigné dans chaque `provenance.md`
- [ ] Aucune interface dans cette phase
- [ ] Recette manuelle faite
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 4

## Décisions prises (liens vers les ADR)

- [ADR-0004](../adr/0004-moteur-de-calcul-en-python.md) — Moteur de calcul en Python
- [ADR-0007](../adr/0007-echelle-rpe-et-formule-de-charge.md) — Échelle RPE et formule de charge
- [ADR-0011](../adr/0011-calendrier-et-charges-glissantes.md) — Calendrier et charges glissantes
- [ADR-0012](../adr/0012-zscore-d-intensite.md) — Z-score d'intensité
- [ADR-0013](../adr/0013-absences-longues.md) — Absences longues
- [ADR-0014](../adr/0014-score-de-sensations.md) — Score de sensations
- [ADR-0015](../adr/0015-zscore-de-sensations.md) — Z-score de sensations
- [ADR-0016](../adr/0016-evolution-de-la-configuration.md) — Évolution de la configuration

## Écarts par rapport au plan

- Niveau de collaboration relevé de 3 à 4 par le mainteneur le 2026-10-15, avant la PR 3.1 (le cadrage prévoyait le niveau 3 pour toute la phase). Les `attendu.csv` et `provenance.md` restent réservés au mainteneur : le passage au niveau 4 ne change pas cette règle, qui est aussi appliquée par `.claude/settings.json`.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
