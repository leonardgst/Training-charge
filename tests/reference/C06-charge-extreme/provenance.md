# Provenance — C06-charge-extreme

| Outil | Auteur | Date | Contrôle du mainteneur |
| --- | --- | --- | --- |
| [`outils/generer_attendu.py`](../outils/generer_attendu.py) | Claude Code (Sonnet 5.5), à la demande du mainteneur | 2026-10-15 | Renoncé par le mainteneur le 2026-10-15 |

## Méthode

Les valeurs de `attendu.csv` viennent du script ci-dessus, qui relit les fichiers d'entrée de ce dossier et refait les calculs depuis les ADR 0007, 0011, 0012, 0014 et 0015, en arithmétique exacte (`Fraction`), sans importer `engine` ni `suivi`. Les valeurs sont écrites avec quinze chiffres significatifs. Les dates et grandeurs choisies sont celles de la `description` de `cas.toml`.

Comparées ensuite aux résultats du moteur, elles concordaient sans aucun ajustement ; aucune valeur n'a été recopiée de la sortie du moteur.

## Point de contrôle à la main

séance extrême du 2026-02-09 : (10 + 10 + 10) / 3 × 150 × 10 = 15000 ; son z-score d'intensité (environ 4,35) est très supérieur à 2.

## Contrôle du mainteneur

Le 2026-10-15, le mainteneur a renoncé à recalculer ces valeurs lui-même et a accepté le calcul du script tel quel. Ce renoncement est consigné dans les écarts de la fiche de la phase 3.

## Limites

Les entrées, le moteur et ce calcul ont le même auteur. L'indépendance repose sur un script écrit à partir des ADR, sans réutiliser le code du moteur (que son auteur connaissait), et sur la concordance des deux calculs. Aucun contrôle humain indépendant n'a été fait : une erreur de lecture d'une ADR commune au script et au moteur ne serait pas détectée.
