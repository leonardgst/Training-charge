## Quoi

<!-- Ce que la PR change, en quelques lignes. -->

## Pourquoi

<!-- Lien vers la fiche de phase et, si besoin, l'ADR ou la règle des spécifications concernée. -->

## Comment c'est testé

- Tests ajoutés ou modifiés :
- Cas de la section 7 du cadrage couverts (C, A, D, E) :
- Commandes exécutées et leur sortie :

```text
$ uv run pytest …
```

- Pour une correction de bug : sortie du test qui échouait avant la correction.

## Ce qui n'est pas fait

<!-- Limites connues, suites prévues (avec la PR ou la phase où elles arrivent). -->

## Vérifications

- [ ] Les tests de ce qui est ajouté ou modifié sont dans cette PR
- [ ] Aucun test supprimé, désactivé ou assoupli (sinon : accord explicite du mainteneur, lien)
- [ ] Aucune valeur attendue recopiée de la sortie du code ; `attendu.csv` et `provenance.md` non modifiés par Claude
- [ ] Documentation à jour dans la même PR : fiche de phase, ADR, spécifications, journal
- [ ] Aucun secret ni aucune donnée réelle
- [ ] Niveau de collaboration respecté (niveau 3 pour les migrations, les accès, le jeton joueur et le moteur)
- [ ] Commits au format Conventional Commits, à l'impératif, au message exact
