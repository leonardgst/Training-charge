---
name: cloturer-phase
description: Clôt une phase selon la section 10.3 du cadrage (critères, fiche, CHANGELOG, tag annoté, journal, CLAUDE.md). À utiliser quand toutes les PR d'une phase sont fusionnées et que le mainteneur a fait la recette.
argument-hint: "[numéro de la phase]"
disable-model-invocation: true
---

# Clôturer une phase

Phase : $ARGUMENTS.

1. **Critères** : vérifie chaque critère de fin de la fiche, avec une preuve (lien de PR, run de CI vert, résultat de la recette). Un critère non rempli bloque la clôture : dis lequel et ce qui manque.
2. **Recette** : la recette manuelle est faite par le mainteneur. Consigne ses résultats dans la fiche, tels qu'il les donne.
3. **Fiche** : statut « Terminée », date du jour, PR à « Fusionnée » avec leur lien, rétrospective (ce qui a marché, ce qui a coincé).
4. **CHANGELOG** : une section `## [0.<numéro>.0] - <date>` sous « [Non publié] », au format Keep a Changelog (Ajouté, Modifié), à partir des PR de la phase.
5. **Suite** : si la phase suivante est connue, prépare-la avec le skill `ouvrir-phase`, dans une PR distincte ; sinon, fais pointer `CLAUDE.md`, section 9, vers ce qui reste à faire.
6. **Journal** : une ligne datée.
7. **PR** : livre le tout dans une PR `docs:` (skill `livrer-pr`).
8. **Tag**, après la fusion seulement : `git fetch origin main`, puis `git tag -a v0.<numéro>.0 origin/main -m "Phase 0<numéro> terminée : <nom>"` et `git push origin v0.<numéro>.0`. Reporte le tag dans la fiche et le journal à la PR suivante.

Une phase sans version (outillage, par exemple) n'a ni tag ni entrée de CHANGELOG.
