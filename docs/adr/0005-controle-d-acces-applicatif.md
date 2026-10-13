# ADR-0005 — Contrôle d'accès applicatif et refus par défaut

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi, sur ma proposition |

## Contexte

Le cadrage exige un refus par défaut sur chaque table, vue et fonction exposée, et des tests A1 et A2 fondés sur un catalogue plutôt que sur une liste écrite à la main. Avec Django ([ADR-0002](0002-django-et-rendu-serveur.md)), la base n'est pas exposée : ce qui est exposé, ce sont les URL de l'application.

## Options

1. **Règles par ligne en base (RLS)**, avec l'identité de l'utilisateur transmise à chaque requête. Deux implémentations des règles (Python et SQL), et un passage de variable de session fragile derrière le pooler de Neon, qui fonctionne par transaction.
2. **Contrôle applicatif à point unique**, avec une base fermée à tout autre client.

## Décision

Option 2, en quatre couches :

1. **Base fermée.** Seule l'application se connecte, avec un rôle d'exécution sans droit sur le schéma. Aucun droit pour `PUBLIC`, aucune fonction `SECURITY DEFINER`, aucune vue en V1.
2. **Session obligatoire par défaut.** `LoginRequiredMiddleware` refuse toute vue sans session. La liste blanche est explicite : page de connexion, page du lien joueur, contrôle de santé.
3. **Rôle vérifié par URL.** Toute URL staff exige un profil préparateur ; l'administration exige le superutilisateur.
4. **Périmètre unique.** Toute vue staff obtient ses requêtes par `suivi/acces.py` :

| Fonction | Contenu |
| --- | --- |
| `joueurs_suivis(preparateur)` | Joueurs dont la catégorie de référence est celle du préparateur |
| `annuaire(preparateur)` | Joueurs actifs de toutes les catégories, limités au nom, au prénom et à la catégorie de référence |
| `seances_organisees(preparateur)` | Séances de sa catégorie |
| `participations_visibles(preparateur)` | Participations de ses joueurs suivis, et participations aux séances qu'il organise |
| `entrees_visibles(preparateur)` | Entrées de sensations de ses joueurs suivis |

Écriture des joueurs, décidée le 2026-10-12 (cadrage 6.7) : le préparateur crée, modifie et archive les joueurs de sa catégorie ; l'effacement définitif reste réservé à l'administrateur ([ADR-0009](0009-suppression-et-archivage-d-un-joueur.md)).

Règle du joueur invité, acceptée le 2026-10-12 : le préparateur organisateur lit et écrit la participation de l'invité à ses propres séances, mais ne voit ni son historique, ni ses charges calculées, ni ses sensations.

## Conséquences

- A1 parcourt le résolveur d'URL de Django : toute route ajoutée est testée automatiquement, anonymement, en GET et en POST.
- A1 lit aussi le catalogue de Postgres : droits accordés à `PUBLIC`, fonctions `SECURITY DEFINER`, vues sans `security_invoker`, droits de schéma du rôle d'exécution.
- A2 vérifie que ces deux contrôles détectent bien une route non protégée et un objet trop ouvert.
- Une vue qui interrogerait directement `Joueur.objects` contournerait le périmètre. La relecture le vérifie ; une règle d'analyse automatique pourra être ajoutée si le cas se présente.
- Les en-têtes de sécurité (CSP, `X-Frame-Options`, `Referrer-Policy`, HSTS, cookies sécurisés) sont posés dès la phase 1 et vérifiés par `manage.py check --deploy` et par le test de fumée.

## Mise en œuvre (phase 2)

- **Couche 3** : `suivi.middleware.ProfilPreparateurRequisMiddleware`, placé après `LoginRequiredMiddleware`, répond 403 à tout compte connecté sans profil préparateur sur une vue qui n'est ni de la liste blanche (`login_not_required`) ni de l'administration. Un superutilisateur sans profil n'entre donc pas sur les pages du staff : l'administrateur n'est pas un préparateur.
- **Administration** : `suivi.site_admin.SiteAdmin` remplace le site par défaut et exige `is_superuser` au lieu de `is_staff`. Un préparateur n'y entre pas, même si son drapeau `is_staff` était posé par erreur. La déconnexion de l'administration reste ouverte à tout compte connecté.
- **Couche 4** : `suivi/acces.py` expose les cinq fonctions du tableau ; un test vérifie qu'aucune vue de `suivi/views/` n'utilise `.objects`.
- **A1 et A2** : le catalogue de Postgres (droits de `PUBLIC` sur les tables, vues, séquences, fonctions et le schéma, fonctions `SECURITY DEFINER`, vues sans `security_invoker`, droit de création du rôle d'exécution) et le catalogue des routes sont des fonctions de `tests/integration/catalogue_acces.py`. A2 exécute les mêmes fonctions après avoir introduit exprès une table ouverte, une fonction `SECURITY DEFINER`, une vue sans garde, un droit de schéma ou une route publique oubliée, et exige que chacune soit détectée.
- Le droit `CONNECT` de `PUBLIC` sur la base n'est pas dans le catalogue de la CI : la base de test est créée par `pytest-django`. Il est vérifié par la mise en place de la base (script des rôles) et le sera contre la base de production avant la mise en service (phase 7).
