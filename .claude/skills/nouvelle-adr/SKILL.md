---
name: nouvelle-adr
description: Rédige une ADR au format du projet, la numérote, l'indexe et la relie à la fiche de phase. À utiliser pour toute décision technique ou métier non triviale (cadrage, section 10.4).
argument-hint: "[sujet de la décision]"
---

# Rédiger une ADR

Sujet : $ARGUMENTS.

1. **Numéro** : le suivant du plus grand de `docs/adr/` (quatre chiffres). Fichier `docs/adr/<numéro>-<sujet-en-minuscules-sans-accent>.md`.
2. **En-tête** : titre `# ADR-<numéro> — <Sujet>`, puis le tableau `| Statut | Date | Décideur |` (« Accepté », date du jour, « Toi » ou « Toi, sur ma proposition »).
3. **Sections**, dans cet ordre : Contexte, Options (numérotées, chacune avec son défaut), Décision, Conséquences, puis Sources si des faits externes ont été vérifiés (pages ouvertes, avec leur date de vérification dans le contexte).
4. **Index** : une ligne dans `docs/adr/README.md`, dans la table des ADR techniques ou métier.
5. **Fiche de phase** : un lien dans « Décisions prises ».
6. **Question tranchée** : si l'ADR répond à une question ouverte, mets à jour dans la même PR les spécifications (`docs/01-specifications.md`) et les tests concernés.
7. **Décision qui change** : la même PR met à jour l'ADR existante, les spécifications et les tests.

Une décision ne se prend jamais seule : l'ADR consigne ce que le mainteneur a validé. Sans sa validation, propose les options et attends.
