# ADR-0017 — Fréquence du questionnaire et badge

| Statut | Date | Phase concernée | Décideur |
| --- | --- | --- | --- |
| Accepté, provisoire : à confirmer par le préparateur | 2026-10-12 | Phase 5 | Toi |

## Contexte

Les documents d'origine disaient « quotidien » à un endroit et « deux fois par semaine à jours fixes » à un autre. Le 2026-10-12, tu as validé que les jours de questionnaire sont paramétrés par catégorie et que « Manquant » ne s'affiche que ces jours-là. Reste la valeur par défaut de la démonstration.

## Q1 — Jours de questionnaire de la démonstration U19

| Option | Conséquence |
| --- | --- |
| A. Tous les jours | Plus de données pour le z-score de sensations ; charge plus forte pour les joueurs (moins d'une minute par jour) |
| B. Deux jours fixes par semaine, par exemple lundi et jeudi | Charge légère ; environ 8 entrées par mois, donc un z-score plus instable ([ADR-0015](0015-zscore-de-sensations.md)) |
| C. Les jours de séance | Lie le questionnaire aux séances, ce que le cadrage exclut |

**Retenu** : A pour la démonstration, qui montre ainsi le graphique dans les meilleures conditions ; le passage à B se fait par configuration.

## Q2 — Accès les autres jours

**Retenu** : le lien fonctionne tous les jours ; seuls les jours de questionnaire attendent une entrée.

## Q3 — Badge dans la grille d'une séance

**Retenu** : le badge porte sur la date de la séance. « Reçu » si une entrée existe à cette date ; « Manquant » si c'est un jour de questionnaire sans entrée ; un tiret sinon.

## Décision

Recommandations acceptées le 2026-10-12 :

- Q1 : questionnaire tous les jours pour la démonstration U19 (`jours_questionnaire` = les sept jours).
- Q2 : le lien fonctionne tous les jours.
- Q3 : badge sur la date de la séance : « Reçu », « Manquant » un jour de questionnaire sans entrée, tiret sinon.

Ces choix sont paramétrables et restent provisoires tant que le préparateur ne les a pas validés (cadrage, règle 9).

## Paramètres et tests concernés

`jours_questionnaire` (par catégorie) ; cas E2.
