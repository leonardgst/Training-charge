# ADR-0004 — Moteur de calcul en Python pur

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi, sur ma proposition |

## Contexte

Le cadrage (section 6.4) demande où vit le moteur de calcul, avec trois contraintes : une seule implémentation des formules ; des tests qui tournent en local et en CI sur le jeu de référence ; des paramètres (fenêtres, poids) modifiables sans réécrire les formules. Trois défauts de calcul de la première tentative (annexe A, n° 7, 8 et 9) vivaient dans des vues SQL.

## Options

1. **En base**, par des vues ou fonctions SQL à fonctions fenêtrées. Proche des données, mais calendrier continu, fenêtres paramétrées et score pondéré deviennent verbeux en SQL ; tests en SQL ou par un outil supplémentaire ; risque de vues exécutées avec les droits de leur propriétaire (annexe A, n° 2).
2. **En Python avec pandas.** Fenêtres glissantes prêtes à l'emploi, mais une dépendance lourde pour quelques milliers de lignes, et une sémantique de fenêtre (par lignes ou par durée) facile à mal choisir.
3. **En Python pur**, bibliothèque standard seulement.

## Décision

Option 3 :

- Package `engine/`, sans aucun import de Django, ce qu'un test vérifie. Il n'utilise que `datetime`, `dataclasses`, `statistics` et `math`.
- **Entrées** : enregistrements immuables (participations des séances validées, réponses, configuration des indicateurs) et un objet `Parametres`.
- **Sorties** : séries par joueur et par jour, et par entrée de sensations. Chaque grandeur est une valeur ou un état explicite (`HISTORIQUE_INSUFFISANT`, `NON_CALCULABLE`, `REPONSES_INSUFFISANTES`).
- **Adaptateur** : `suivi/calculs.py` est le seul code qui lit la base pour le moteur. Il ne charge que les séances validées (C5) et les données datées au plus tard de la date de calcul (C9).
- **Paramètres** : fenêtres, seuils, facteur d'échelle et fuseau dans `config/calcul.toml`, versionné et validé au démarrage. Les poids, bornes et sens des indicateurs sont des données par catégorie, en base.
- **Stockage** : aucun résultat stocké en V1 ; tout est recalculé à la demande.

## Conséquences

- Les formules s'écrivent une fois, dans le langage que tu maîtrises le mieux, avec un typage strict.
- Les cas C1 à C15 tournent deux fois : sans base pour un retour rapide, et via l'adaptateur sur un vrai Postgres, version qui fait foi (cadrage 7.7).
- Modifier une fenêtre est une PR sur `config/calcul.toml`, jouée par la CI. Les paramètres ne changent pas sans test.
- Si le volume grandit (plusieurs catégories, plusieurs saisons), une mise en cache des séries pourra être ajoutée par une ADR, sans toucher aux formules.
