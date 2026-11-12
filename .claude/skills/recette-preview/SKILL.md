---
name: recette-preview
description: Vérifie la preview Vercel d'une PR (pages publiques, redirections, erreurs d'exécution) avec le serveur MCP de Vercel. À utiliser quand une PR change une page, une route ou un réglage.
argument-hint: "[numéro de la PR]"
---

# Recette d'une preview

PR : $ARGUMENTS.

1. **Adresse** : le job `deployer` publie l'adresse dans un commentaire de la PR, « Preview : <adresse> » (`gh pr view <numéro> --comments`). Pas de commentaire : la preview n'est pas déployée, passe au skill `diagnostic`.
2. **Pages publiques**, lues avec `web_fetch_vercel_url`, qui passe la protection de Vercel :
   - `/sante/` répond `ok` ;
   - `/` mène à la page de connexion ;
   - `/connexion/` affiche le formulaire en français ;
   - une adresse inexistante mène à la connexion ou à la page d'erreur du projet, sans trace technique.
3. **Pages touchées par la PR** : vérifie que chacune redirige vers la connexion sans session et ne produit aucune erreur.
4. **Erreurs d'exécution** : `list_deployments` pour retrouver le déploiement de la preview, puis `get_runtime_errors` et `get_runtime_logs` sur ce déploiement.

Les pages qui demandent une session (saisie, tableaux de bord) ne se vérifient pas ainsi : leur recette passe par les tests de bout en bout et par le mainteneur, sur son téléphone. Dis-le dans le compte rendu.

## Compte rendu

Adresse de la preview, chaque contrôle avec son résultat, les erreurs relevées, et ce qui reste à vérifier par le mainteneur.
