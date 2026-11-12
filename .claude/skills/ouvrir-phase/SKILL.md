---
name: ouvrir-phase
description: Prépare la fiche d'une nouvelle phase à partir du cadrage et la soumet au mainteneur. À utiliser après la clôture d'une phase, avant toute PR de la phase suivante.
argument-hint: "[numéro de la phase]"
disable-model-invocation: true
---

# Ouvrir une phase

Phase : $ARGUMENTS.

1. Lis le plan de la phase dans le cadrage, section 13.4 (objectif, livrables, PR, tests, critères de fin), et les écarts déjà décidés dans les fiches précédentes et le journal.
2. Crée `docs/phases/phase-<numéro sur deux chiffres>-<nom-court>.md` selon le modèle du cadrage, section 10.2 : statut « En cours », tag `v0.<numéro>.0`, objectif, livrables, tableau des PR (statut « À faire »), critères de fin, recette manuelle à préparer, décisions prises, écarts. Prends exemple sur la fiche de la phase précédente.
3. Indique le niveau de collaboration de la phase et l'estimation du cadrage (section 9).
4. Fais pointer `CLAUDE.md`, section 9, vers la nouvelle fiche.
5. Ajoute une ligne au journal.
6. Livre le tout dans une PR `docs:` (skill `livrer-pr`) et demande au mainteneur de valider la fiche : aucune PR de la phase ne commence avant sa validation.
