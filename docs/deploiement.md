# Déploiement : mise en place et secrets

Ce document explique ce qui a été mis en place pour déployer l'application (PR 1.5 de la [phase 1](phases/phase-01-socle.md)), où vit chaque secret et à quoi il sert. Il ne contient aucune valeur secrète : seulement des noms et des emplacements. La décision d'hébergement est dans l'[ADR-0003](adr/0003-hebergement-vercel-et-neon.md), l'architecture dans la [section déploiement de l'architecture](02-architecture.md).

## 1. Vue d'ensemble

```text
GitHub (dépôt public)
 ├─ CI : qualité, tests, migrations, e2e, audit, build   (obligatoires par ruleset)
 ├─ Previews : une branche Neon par PR + déploiement Vercel de preview
 └─ Production : après CI verte sur main et approbation du mainteneur
        1. migrations avec le rôle de migration (connexion directe à Neon)
        2. déploiement Vercel
        3. test de fumée

Vercel (Hobby) : l'application Django, une fonction Python en région fra1
Neon (Free)    : Postgres 16, région Europe (Francfort), branche « production »
```

Le déploiement est piloté par GitHub Actions avec la CLI Vercel. L'intégration Git automatique de Vercel n'est pas utilisée : les migrations resteraient hors de ton contrôle.

## 2. Ce qui a été mis en place

### Neon

- Un projet Neon, Postgres 16, région AWS Europe (Francfort). Sa branche par défaut s'appelle `production` : c'est le nom que Neon donne à la branche racine de tout nouveau projet.
- Une base `suivi`, propriété du rôle de migration.
- Deux rôles créés en SQL (donc sans `neon_superuser`) :
  - `suivi_migration` : propriétaire du schéma, utilisé uniquement pour migrer ;
  - `suivi_execution` : `SELECT`, `INSERT`, `UPDATE`, `DELETE` sur les tables et `USAGE`, `SELECT` sur les séquences, accordés par défaut à chaque nouvelle table ; aucun droit de modifier le schéma.
- Aucun droit à `PUBLIC` sur la base, le schéma et les fonctions. Ce sont les mêmes règles qu'en local ([`docker/initdb/01-roles.sh`](../docker/initdb/01-roles.sh)).
- Vérification faite sur la base : aucun des deux rôles n'est superutilisateur ni ne peut créer de rôle ou de base, et `suivi_execution` n'a pas le droit `CREATE` sur le schéma `public`.
- Les branches de preview copient les rôles et leurs droits depuis la branche `production`.

### Vercel

- Un projet Vercel, sans l'intégration Git. Framework : Django. Région des fonctions : `fra1`, la même zone que la base (l'offre Hobby n'autorise qu'une seule région).
- Vercel détecte Django grâce à `manage.py` et à `WSGI_APPLICATION`, et lance `collectstatic` lui-même quand `STATIC_ROOT` est défini. Aucun fichier de configuration n'est nécessaire pour l'application, sauf pour la région.
- Le projet contenait un déploiement initial créé avec le préréglage Next.js. L'avertissement de Vercel sur les « Production overrides » décrit cet ancien déploiement : il disparaît au premier déploiement de l'application.

### GitHub

- Un environnement `production` : approbation obligatoire par le mainteneur, déploiement limité à la branche `main`. L'auto-approbation reste permise, le mainteneur étant seul.
- Le ruleset de `main` (PR obligatoire, six jobs de CI obligatoires, aucun contournement) a été activé avec la PR 1.4.

## 3. Où est chaque secret, et à quoi il sert

| Secret | À quoi il sert | Où il est stocké | Qui le lit |
| --- | --- | --- | --- |
| Mot de passe `suivi_migration` | Se connecter à Neon avec le rôle propriétaire du schéma, pour appliquer les migrations en production | Secret `DB_MIGRATION_PASSWORD` de l'environnement GitHub `production` | Le job de déploiement de `main`, après approbation. Jamais l'application, jamais Vercel |
| Mot de passe `suivi_execution` | Connexion de l'application à Neon, par le pooler, avec des droits limités | Variable Vercel `DB_PASSWORD`, type Secret, pour Production et Preview (c'est le nom que lisent les réglages Django ; le rôle `suivi_execution` est indiqué par `DB_USER` au déploiement) | L'application sur Vercel |
| `DJANGO_SECRET_KEY` | Signature des sessions, des cookies et des jetons de Django | Variable Vercel, type Secret, pour Production et Preview | L'application sur Vercel |
| `NEON_API_KEY` | Créer et supprimer les branches Neon des previews, obtenir l'URL de connexion de chaque branche | Secret du dépôt GitHub | Le workflow des previews |
| `VERCEL_TOKEN` | Déployer sur Vercel avec la CLI depuis GitHub Actions | Secret du dépôt GitHub | Les workflows de preview et de production |

Valeurs non secrètes, visibles sans conséquence :

| Nom | Emplacement | Contenu |
| --- | --- | --- |
| `NEON_PROJECT_ID`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` | Variables du dépôt GitHub | Identifiants de projet et d'organisation |
| `DB_HOST_DIRECT` | Variable de l'environnement `production` | Hôte Neon direct, pour les migrations |
| `DB_HOST_POOLED` | Variable de l'environnement `production` | Le même hôte avec `-pooler`, pour l'application |

### Pourquoi deux hôtes

Le pooler de Neon (PgBouncer en mode transaction) convient à l'application, qui ouvre beaucoup de connexions courtes. Il n'accepte ni `SET`, ni curseur persistant, ni verrou de session : les migrations passent donc par la connexion directe, comme la documentation de Neon le recommande. Côté Django, la connexion n'est jamais persistante (`CONN_MAX_AGE = 0`) et les curseurs côté serveur sont désactivés en production.

### Ce que cette séparation garantit

- L'application ne connaît jamais le mot de passe du rôle qui peut changer le schéma : une faille de l'application ne permettrait pas de supprimer ou de modifier les tables.
- Les migrations de production ne partent que de `main`, dans l'environnement `production`, donc après l'approbation du mainteneur.
- Aucun secret n'est dans le dépôt. Les mots de passe sont conservés dans un gestionnaire de mots de passe, hors du dépôt.

## 4. Workflows et réglages dans le dépôt

| Fichier | Rôle |
| --- | --- |
| [`ci.yml`](../.github/workflows/ci.yml) | Six jobs obligatoires ; `qualite` lance aussi `check --deploy` avec les réglages HTTPS |
| [`preview.yml`](../.github/workflows/preview.yml) | Sur chaque PR du dépôt : branche Neon `pr-<numéro>`, migrations par le rôle de migration (connexion directe), déploiement Vercel de preview, adresse commentée dans la PR. À la fermeture de la PR : suppression de la branche Neon |
| [`deploy.yml`](../.github/workflows/deploy.yml) | Après une CI verte sur `main` et ton approbation dans l'environnement `production` : migrations, déploiement en production, test de fumée |
| [`vercel.json`](../vercel.json) | Région des fonctions (`fra1`) |
| [`.vercelignore`](../.vercelignore) | Fichiers non envoyés à Vercel (tests, documentation, CI) |
| [`config/settings.py`](../config/settings.py) | `DJANGO_HTTPS=true` active la redirection HTTPS, les cookies sécurisés et HSTS ; `DB_SSLMODE` ; curseurs côté serveur désactivés |
| [`tests/smoke/test_fumee.py`](../tests/smoke/test_fumee.py) | Test de fumée, lancé avec `SMOKE_URL` |

Les valeurs non secrètes du déploiement (`DJANGO_HTTPS`, `DJANGO_ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_SSLMODE`, `DB_HOST`) sont passées par les workflows : elles sont versionnées et relues en PR. Seuls `DJANGO_SECRET_KEY` et `DB_PASSWORD` vivent dans Vercel.

## 5. Points d'attention

- **`NEON_API_KEY`** a des droits étendus sur tout le projet Neon, branche de production comprise. Elle n'est lue que par le workflow des previews. Les PR venant d'un fork n'ont pas accès aux secrets. Une clé limitée au projet est préférable.
- **Previews** : les branches Neon héritent des rôles de `production`, donc `suivi_execution` a le même mot de passe sur une preview. Aucun secret supplémentaire n'est à stocker. Seul l'hôte change d'une PR à l'autre.
- **Hypothèses à confirmer par la première exécution de `preview.yml`** : l'action Neon retrouve le mot de passe d'un rôle créé en SQL ; elle réutilise la branche d'une PR déjà créée à chaque poussée ; le pooler accepte les requêtes préparées de `psycopg`. Si l'une échoue, le journal et la fiche de phase le consignent.
- **Variables Vercel de type Secret** : elles ne se relisent plus après l'enregistrement, c'est voulu. Pour en changer la valeur, il faut supprimer la variable et la recréer.
- **Les limites de l'offre gratuite** sont dans l'[ADR-0003](adr/0003-hebergement-vercel-et-neon.md) : 10 branches Neon, aucune sauvegarde au-delà de 6 heures, usage non commercial.

## 6. Procédures

### Changer un mot de passe de rôle Neon

1. Dans l'éditeur SQL de Neon, sur la branche `production` : `ALTER ROLE suivi_migration PASSWORD '…';` (ou `suivi_execution`).
2. Mettre à jour le secret correspondant (GitHub ou Vercel) puis le gestionnaire de mots de passe.
3. Redéployer. Les branches de preview déjà créées gardent l'ancien mot de passe : les supprimer et les recréer.

### Récupérer les hôtes de la base

Console Neon, bouton **Connect** de la branche `production`, base `suivi`, rôle `suivi_migration`. L'hôte est le texte entre `@` et `/` de la chaîne de connexion ; la bascule « Connection pooling » donne la forme avec `-pooler`. Ne jamais copier la chaîne entière : elle contient le mot de passe.

## 7. Historique de la mise en place

La mise en place a été faite en une session avec Claude Code, en niveau 3. Les étapes qui demandent un compte ou un secret sont faites par le mainteneur : création des comptes et projets Neon et Vercel, exécution du SQL des rôles dans la console de Neon, saisie des secrets dans GitHub et Vercel. Claude Code ne lit ni ne reçoit jamais ces valeurs.

Une exception, une seule fois et sur accord explicite du mainteneur : la CLI Vercel a été utilisée en lecture seule pour relever l'identifiant du projet et de l'organisation, puis déconnectée.
