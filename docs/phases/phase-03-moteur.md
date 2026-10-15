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
| 3.1 | `test: ajouter le jeu de référence et les cas C1 à C15` | Format, harnais sur base et sans base, cas en `xfail(strict=True)`. Les `attendu.csv` et `provenance.md` sont écrits par le mainteneur. | C1 à C15, en échec attendu | En revue | [#20](https://github.com/leonardgst/Training-charge/pull/20) |
| 3.2 | `feat: calculer la charge du jour sur un calendrier continu` | Types, paramètres, charge de séance, calendrier, adaptateur | C1, C2, C5, C10 | Fusionnée | [#21](https://github.com/leonardgst/Training-charge/pull/21) |
| 3.3 | `feat: calculer la CE courte et la CE longue` | Sommes glissantes, drapeau de fenêtre incomplète | C3, C9 | Fusionnée | [#22](https://github.com/leonardgst/Training-charge/pull/22) |
| 3.4 | `feat: calculer l'intensité` | Référence, historique minimal, écart-type nul | C4, C6, C7 et C8 pour l'intensité, C14 | Fusionnée | [#23](https://github.com/leonardgst/Training-charge/pull/23) |
| 3.5 | `feat: calculer le score et le z-score de sensations` | Normalisation, orientation, pondération, référence | C7 et C8 pour les sensations, C11, C12, C13, C15 | En revue | [#24](https://github.com/leonardgst/Training-charge/pull/24) |

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
- PR 3.1 : le format du jeu de référence est précisé par rapport à la stratégie de tests (section 6, mise à jour dans la même PR) : un `joueurs.csv` obligatoire (la catégorie de référence de chaque joueur ne se déduit pas des autres fichiers, C10 en dépend) ; chaque date d'`attendu.csv` est la date de calcul, ce qui remplace les « dates de calcul » de `cas.toml` ; `reprend` dans `cas.toml` pour C14 ; une valeur attendue nulle se compare avec un écart absolu de 1e-12, l'écart relatif n'ayant pas de sens autour de zéro. À confirmer par le mainteneur avant d'écrire les `attendu.csv`.
- PR 3.1 : les dossiers `C01-*` à `C15-*` n'existent pas encore (écrits par le mainteneur) : les cas échouent donc d'abord faute de dossier, puis faute de moteur. Les deux points de branchement sur le code testé (`tests/reference/execution.py`) sont posés mais refusent de s'exécuter jusqu'à la PR 3.2. Un test `xfail(strict=True)` vérifie la complétude du jeu et se retirera quand le mainteneur aura fourni les quinze dossiers.

- PR 3.2 : `config/calcul.toml` ne contient que `facteur_echelle_charge` ; chaque PR suivante y ajoute les paramètres qu'elle utilise (rien n'est créé « pour plus tard »). Le fichier est validé au démarrage (`SuiviConfig.ready`).
- PR 3.2 : C5, C9, C10 et C15 sont « Intégration » dans la table de la stratégie de tests : le harnais ne les exécute pas sans base (`INTEGRATION_SEULE`). Écarter les brouillons est le rôle de l'adaptateur.
- PR 3.2 : les marques `xfail` de C1, C2, C5 et C10 restent en place, car les dossiers du mainteneur n'existent pas encore ; elles se retirent (la CI l'impose, `strict=True`) dès que ses fichiers sont fusionnés. Les formules sont en attendant prouvées par des tests à valeurs calculées à la main (ADR-0007), qui ne remplacent pas le jeu de référence.
- PR 3.2 : seuil de 95 % des branches de `engine/` imposé en CI, avec l'accord du mainteneur (modification de `ci.yml`) : le job `tests` mesure `engine` et `suivi`, puis `coverage report --include='engine/*' --fail-under=95` échoue sous le seuil. Le seuil de 90 % de la validation des saisies reste à poser avec la phase 4.
- PR 3.2 : mypy strict sur `engine/` passe par les options individuelles d'une section `[[tool.mypy.overrides]]`, `strict = true` n'étant accepté que globalement (il casserait les tests et Django).
- PR 3.3 : `config/calcul.toml` reçoit `fenetre_courte_jours` (7) et `fenetre_longue_jours` (28), validés au démarrage (entiers d'au moins 1, la courte strictement inférieure à la longue). Le drapeau « fenêtre incomplète » est porté par `ChargesGlissantes` (`courte_incomplete`, `longue_incomplete`) ; `attendu.csv` n'a pas de colonne pour lui, l'état de la CE reste donc `ok` et le drapeau est vérifié par des tests à valeurs calculées à la main. Les marques `xfail` de C3 et C9 restent, les dossiers du mainteneur étant absents.
- PR 3.4 : `config/calcul.toml` reçoit `reference_jours` (28), `reference_min_jours` (21) et `tolerance_ecart_type_nul` (1e-9, relative), validés au démarrage (`reference_min_jours` entre 2 et `reference_jours`, l'écart-type d'échantillon exigeant deux points). Les états du moteur sont l'énumération `Etat`, dont les valeurs sont celles de `attendu.csv`. Les marques `xfail` de C4, C6 et C14 restent (dossiers du mainteneur absents) ; C7 et C8 attendent aussi les sensations (PR 3.5). C14 est prouvé en attendant par un test unitaire (facteur ×7, z-scores identiques).
- PR 3.5 : `config/calcul.toml` reçoit `score_poids_min` (0,5), `sensations_reference_jours` (28) et `sensations_reference_min_entrees` (6). Le score du moteur est dans [0, 1] (1 = meilleur état) ; l'affichage sur 10 (ADR-0014, Q5) relève de l'interface. **À confirmer par le mainteneur avant d'écrire les `attendu.csv`** : `score_sensations` y est attendu dans [0, 1], avec l'écart absolu de 1e-6.
- PR 3.5 : l'ADR-0016 (configuration rétroactive) est appliquée par l'adaptateur, qui lit la configuration d'aujourd'hui : seuls les indicateurs actifs, notés et inclus dans le score de la catégorie de référence du joueur comptent. Un indicateur désactivé sort donc du score de tout le passé, mais ses réponses restent en base. Une entrée sans score a l'état `reponses_insuffisantes` pour le score et pour le z-score ; elle est écartée de la référence des autres entrées.
- PR 3.5 : C15 est prouvé en attendant par des tests d'intégration (poids modifié, indicateur ajouté, indicateur désactivé) ; le refus d'un changement d'échelle est déjà garanti par le déclencheur de la migration `0005` (phase 2). Les marques `xfail` restent tant que les dossiers du mainteneur sont absents.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
