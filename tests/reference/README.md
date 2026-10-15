# Jeu de référence

Valeurs attendues du moteur de calcul, produites **indépendamment du code** par le mainteneur. Stratégie complète : [docs/03-strategie-tests.md](../../docs/03-strategie-tests.md), section 6.

## Un dossier par cas

Le cas `C06` vit dans `C06-<description>/` ; le préfixe suffit à le retrouver. Les cas sont `C01` à `C15` (table de la section 8 de la stratégie).

| Fichier | Colonnes | Obligatoire |
| --- | --- | --- |
| `cas.toml` | `description`, `reprend` (préfixe d'un autre cas), `[parametres]` (surcharges de `config/calcul.toml`) | oui |
| `joueurs.csv` | `joueur, categorie` | oui |
| `seances.csv` | `id, date, categorie, type, duree_min, statut` | si le cas a des séances |
| `participations.csv` | `seance_id, joueur, rpe_cardio, rpe_musculaire, rpe_teta` | si le cas a des séances |
| `indicateurs.csv` | `categorie, code, type, borne_min, borne_max, sens, poids, inclus_score` | si le cas a des sensations |
| `reponses.csv` | `joueur, date, indicateur, valeur` | si le cas a des sensations |
| `attendu.csv` | `joueur, date, grandeur, valeur, etat` | oui |
| `provenance.md` | outil, auteur, date, méthode du calcul indépendant, contrôle du mainteneur | oui |

- Les dates sont au format ISO (`2026-01-05`), les booléens s'écrivent `true` ou `false`, une cellule vide de RPE signifie « non saisi ».
- `grandeur` : `charge_jour`, `ce_courte`, `ce_longue`, `intensite`, `score_sensations`, `sensations_z`.
- `etat` : `ok`, `historique_insuffisant`, `non_calculable`, `reponses_insuffisantes`. `valeur` est renseignée si et seulement si `etat` vaut `ok`, avec au moins dix chiffres significatifs.
- **Chaque date d'`attendu.csv` est aussi la date de calcul** : le test calcule à cette date en ne voyant que les données datées au plus tard de ce jour. Des données plus tardives dans les CSV d'entrée sont donc ignorées (C9).
- `reprend = "C06"` reprend les fichiers d'entrée du cas `C06` ; un fichier présent dans le dossier l'emporte, et `[parametres]` complète ceux du cas repris (C14).

## Tolérances

| Grandeur | Comparaison |
| --- | --- |
| `charge_jour`, `ce_courte`, `ce_longue` | écart relatif inférieur à 1e-9 ; pour une valeur attendue nulle, écart absolu inférieur à 1e-12 |
| `intensite`, `score_sensations`, `sensations_z` | écart absolu inférieur à 1e-6 |
| `etat` | égalité exacte |

## Règles

- Seul le mainteneur écrit `attendu.csv` et `provenance.md`, ou en confie explicitement l'écriture au script de `outils/`, qui n'importe ni `engine` ni `suivi`. Une valeur sans provenance n'est pas une valeur attendue.
- Les valeurs ne sont jamais recopiées de la sortie du code.

## Harnais

| Module | Rôle |
| --- | --- |
| `harnais.py` | lecture, validation du format, comparaison avec tolérances (sans Django) |
| `execution.py` | chargement d'un cas dans Postgres par l'ORM, appels du moteur (sans base) et de l'adaptateur (sur base) |
| `registre.py` | cas C01 à C15 |
| `synthese.py` | cas fictif écrit à la volée pour tester le harnais lui-même |

Les tests : `tests/unit/test_reference_sans_base.py` (retour rapide), `tests/integration/test_reference_sur_base.py` (fait foi), `tests/unit/test_reference_format.py` et `tests/unit/test_harnais_reference.py`.
