# Provenance — C15-configuration-en-cours-de-saison

| Outil | Auteur | Date | Contrôle du mainteneur |
| --- | --- | --- | --- |
| [`outils/generer_attendu.py`](../outils/generer_attendu.py) | Claude Code (Sonnet 5.5), à la demande du mainteneur | 2026-10-15 | À consigner par le mainteneur |

## Méthode

Les valeurs de `attendu.csv` viennent du script ci-dessus, qui relit les fichiers d'entrée de ce dossier et refait les calculs depuis les ADR 0007, 0011, 0012, 0014 et 0015, en arithmétique exacte (`Fraction`), sans importer `engine` ni `suivi`. Les valeurs sont écrites avec quinze chiffres significatifs. Les dates et grandeurs choisies sont celles de la `description` de `cas.toml`.

Comparées ensuite aux résultats du moteur, elles concordaient sans aucun ajustement ; aucune valeur n'a été recopiée de la sortie du moteur.

## Point de contrôle à la main

configuration actuelle : fatigue pèse 3 ; le 2026-01-10, plaisir 7 donne 0,7, fatigue 3 inversée donne 0,7, énergie 6 donne 0,6, soit (0,7 + 3 × 0,7 + 0,6) / 5 = 0,68 ; les entrées d'avant l'ajout d'énergie sont scorées sans elle.

## Limites

Les entrées, le moteur et ce calcul ont le même auteur : l'indépendance vient d'un script écrit à partir des ADR sans réutiliser le code du moteur (que son auteur connaissait), et du contrôle du mainteneur, non encore consigné.
