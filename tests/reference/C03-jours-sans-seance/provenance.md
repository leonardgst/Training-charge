# Provenance — C03-jours-sans-seance

| Outil | Auteur | Date | Contrôle du mainteneur |
| --- | --- | --- | --- |
| [`outils/generer_attendu.py`](../outils/generer_attendu.py) | Claude Code (Sonnet 5.5), à la demande du mainteneur | 2026-10-15 | À consigner par le mainteneur |

## Méthode

Les valeurs de `attendu.csv` viennent du script ci-dessus, qui relit les fichiers d'entrée de ce dossier et refait les calculs depuis les ADR 0007, 0011, 0012, 0014 et 0015, en arithmétique exacte (`Fraction`), sans importer `engine` ni `suivi`. Les valeurs sont écrites avec quinze chiffres significatifs. Les dates et grandeurs choisies sont celles de la `description` de `cas.toml`.

Comparées ensuite aux résultats du moteur, elles concordaient sans aucun ajustement ; aucune valeur n'a été recopiée de la sortie du moteur.

## Point de contrôle à la main

séances de 3000 (lundi) et 4500 (jeudi : 5 × 90 × 10) ; la CE courte vaut 3000 puis 7500 à partir du 2026-01-08 et retombe à 0 le 2026-01-15, la CE longue garde 7500.

## Limites

Les entrées, le moteur et ce calcul ont le même auteur : l'indépendance vient d'un script écrit à partir des ADR sans réutiliser le code du moteur (que son auteur connaissait), et du contrôle du mainteneur, non encore consigné.
