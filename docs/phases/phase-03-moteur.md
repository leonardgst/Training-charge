# Phase 03 — Moteur de calcul

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En clôture : recette à faire | — | — | v0.3.0 (à poser après la recette) |

## Objectif

Des chiffres justes, prouvés indépendamment de l'implémentation.

Niveau de collaboration : 4 pour la phase entière (relevé de 3 à 4 par le mainteneur le 2026-10-15). Claude Code travaille sur une branche, commite, pousse et ouvre les PR ; le mainteneur relit et fusionne. Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur. Les fichiers `tests/reference/**/attendu.csv` et `provenance.md` étaient réservés au mainteneur ; il en a confié l'écriture à Claude Code le 2026-10-15 (écarts). Estimation : 24 heures, plus environ 10 heures pour le jeu de référence du mainteneur (cadrage, section 9).

## Livrables

- [x] Jeu de référence avec provenance
- [x] `engine/` (moteur pur, sans Django, typage strict)
- [x] Adaptateur `suivi/calculs.py`
- [x] `config/calcul.toml`

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 3.1 | `test: ajouter le jeu de référence et les cas C1 à C15` | Format, harnais sur base et sans base, cas en `xfail(strict=True)`. Les `attendu.csv` et `provenance.md` sont écrits par le mainteneur. | C1 à C15, en échec attendu | Fusionnée | [#20](https://github.com/leonardgst/Training-charge/pull/20) |
| 3.2 | `feat: calculer la charge du jour sur un calendrier continu` | Types, paramètres, charge de séance, calendrier, adaptateur | C1, C2, C5, C10 | Fusionnée | [#21](https://github.com/leonardgst/Training-charge/pull/21) |
| 3.3 | `feat: calculer la CE courte et la CE longue` | Sommes glissantes, drapeau de fenêtre incomplète | C3, C9 | Fusionnée | [#22](https://github.com/leonardgst/Training-charge/pull/22) |
| 3.4 | `feat: calculer l'intensité` | Référence, historique minimal, écart-type nul | C4, C6, C7 et C8 pour l'intensité, C14 | Fusionnée | [#23](https://github.com/leonardgst/Training-charge/pull/23) |
| 3.5 | `feat: calculer le score et le z-score de sensations` | Normalisation, orientation, pondération, référence | C7 et C8 pour les sensations, C11, C12, C13, C15 | Fusionnée | [#24](https://github.com/leonardgst/Training-charge/pull/24) |
| 3.6 | `test: ajouter les cas C01 à C15 du jeu de référence` | Entrées des quinze cas, script de calcul indépendant, `attendu.csv` et `provenance.md` (accord du mainteneur), retrait des `xfail` | C1 à C15 au vert | Fusionnée | [#25](https://github.com/leonardgst/Training-charge/pull/25) |

## Critères de fin (Definition of Done)

- [x] C1 à C15 au vert, sans aucun `xfail` restant
- [x] Couverture de `engine/` d'au moins 95 % des branches (100 %, seuil imposé en CI)
- [x] Contrôle indépendant du mainteneur consigné dans chaque `provenance.md` : le mainteneur y a renoncé le 2026-10-15, et ce renoncement est consigné dans chaque `provenance.md` (écarts)
- [x] Aucune interface dans cette phase
- [ ] Recette manuelle faite (section ci-dessous, par le mainteneur)
- [x] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 4

## Décisions prises (liens vers les ADR)

- [ADR-0004](../adr/0004-moteur-de-calcul-en-python.md) — Moteur de calcul en Python
- [ADR-0007](../adr/0007-echelle-rpe-et-formule-de-charge.md) — Échelle RPE et formule de charge
- [ADR-0011](../adr/0011-calendrier-et-charges-glissantes.md) — Calendrier et charges glissantes
- [ADR-0012](../adr/0012-zscore-d-intensite.md) — Z-score d'intensité
- [ADR-0013](../adr/0013-absences-longues.md) — Absences longues
- [ADR-0014](../adr/0014-score-de-sensations.md) — Score de sensations
- [ADR-0015](../adr/0015-zscore-de-sensations.md) — Z-score de sensations
- [ADR-0016](../adr/0016-evolution-de-la-configuration.md) — Évolution de la configuration

## Recette manuelle

À dérouler par toi sur ton poste, `main` à jour après la fusion de la PR de clôture ; je ne coche rien à ta place. La phase n'a pas d'interface : la recette porte sur les tests, la configuration et un calcul sur la démonstration.

- [ ] `uv run pytest tests/unit` puis `uv run --env-file .env pytest tests/integration` : tout est vert, aucun `xfail` ni `xpass` dans le résumé.
- [ ] Dans `config/calcul.toml`, mettre `facteur_echelle_charge = 0` : `uv run --env-file .env python manage.py runserver` refuse de démarrer avec un message qui nomme le paramètre. Remettre `10` (le fichier ne doit pas apparaître dans `git status`).
- [ ] Sur la base locale chargée par `generer_demo`, `uv run --env-file .env python manage.py shell -c "from suivi.calculs import calculer_intensite, parametres; from suivi.horloge import aujourd_hui; print(calculer_intensite(1, aujourd_hui(), parametres())[-1])"` affiche une valeur ou un état explicite, sans erreur.
- [ ] Ouvrir `tests/reference/C06-charge-extreme/provenance.md` et `attendu.csv` sur GitHub : le renoncement au contrôle et le point de contrôle à la main sont lisibles.
- [ ] Après la fusion, le déploiement de production attend ton approbation, puis `/sante/` répond (la phase n'ajoute aucune migration).

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
- Jeu de référence : le 2026-10-15, le mainteneur a levé pour cette PR la réserve sur `attendu.csv` et `provenance.md` et confié à Claude Code leur écriture, les fichiers d'entrée des quinze cas (`cas.toml`, CSV) y compris. Les valeurs viennent de `tests/reference/outils/generer_attendu.py`, qui relit les entrées et refait les calculs depuis les ADR en arithmétique exacte, sans importer `engine` ni `suivi` (un test le vérifie). Comparées ensuite au moteur, les quinze cas concordaient sans ajustement. Chaque `provenance.md` donne un point de contrôle calculable à la main. Les entrées, le moteur et le script ont le même auteur.
- Jeu de référence : les marques `xfail(strict=True)` et le registre `PR_PREVUE` sont retirés (les quinze cas passent) ; le test de complétude du jeu n'est plus en `xfail`. Pour C13, `attendu.csv` ne contient pas de `sensations_z` à la date d'une entrée sans score : les ADR ne disent pas l'état attendu.

- Contrôle indépendant : le 2026-10-15, le mainteneur a renoncé à recalculer lui-même les valeurs du jeu de référence (« je te fais absolument confiance »). Le critère de fin est coché sur cette décision, consignée dans chaque `provenance.md`, et non sur un contrôle fait. Conséquence : une erreur de lecture d'une ADR commune au script et au moteur ne serait pas détectée par le jeu de référence ; la validation des formules par le préparateur (cadrage, règle 9) reste le garde-fou métier.

## Rétrospective : ce qui a marché, ce qui a coincé

**Ce qui a marché**
- Un moteur pur sans Django, alimenté par un adaptateur unique : les formules se testent en millisecondes, et les mêmes cas de référence tournent sans base et sur Postgres.
- Le harnais posé avant le moteur, avec des `xfail(strict=True)` : chaque PR savait exactement ce qu'elle devait faire passer, et la CI a imposé de retirer les marques au bon moment.
- Le script de calcul en arithmétique exacte (`Fraction`) : il a concordé avec le moteur sur les quinze cas du premier coup.

**Ce qui a coincé**
- Le jeu de référence attendait le mainteneur, alors que le moteur avançait : les PR 3.2 à 3.5 ont dû prouver leurs formules par des tests à valeurs calculées à la main en attendant. Écrire les entrées des cas dès la PR 3.1 aurait raccourci l'attente.
- Le contrôle indépendant n'a pas eu lieu (écarts) : à décider plus tôt dans la prochaine phase qui en prévoit un.
- Deux points restent ouverts sans bloquer : l'état du z-score de sensations pour une entrée sans score (C13), et le drapeau « fenêtre incomplète », absent de `attendu.csv`.
