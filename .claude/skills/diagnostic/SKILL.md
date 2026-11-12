---
name: diagnostic
description: Diagnostique dans un contexte séparé un run GitHub Actions rouge, une preview qui ne répond pas ou un test de fumée en échec, et rend la cause avec sa preuve. À utiliser dès qu'un job de CI, de preview ou de déploiement échoue.
argument-hint: "[numéro de PR, nom de branche ou identifiant de run]"
context: fork
agent: ops
---

Diagnostique l'échec lié à : $ARGUMENTS.

1. Retrouve le run en échec le plus récent (`gh run list`, puis `gh run view <identifiant> --log-failed`).
2. Situe l'étape en cause et rassemble la preuve : extrait du journal, état de la branche Neon, journaux ou erreurs du déploiement Vercel.
3. Reproduis en local si c'est un job de CI.
4. Rends : la cause probable et sa preuve, la correction proposée (fichier et changement), et qui doit agir, Claude ou le mainteneur.
