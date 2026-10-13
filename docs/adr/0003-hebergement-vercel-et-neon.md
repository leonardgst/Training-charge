# ADR-0003 — Hébergement sur Vercel et Neon

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi, sur ma proposition |

## Contexte

Contraintes : 0 € sans carte bancaire enregistrée ; déploiement indépendant de ton poste ; application de démonstration consultée de façon irrégulière ; un joueur doit remplir son questionnaire en moins d'une minute, ce qui exclut un réveil d'une minute ; données fictives seulement ; dépôt public.

Limites vérifiées le 2026-10-12 :

| Service | Offre gratuite | Point bloquant |
| --- | --- | --- |
| Vercel Hobby | Django pris en charge sans configuration depuis avril 2026 ; fonctions Python jusqu'à 500 Mo | Usage personnel et non commercial uniquement |
| Neon Free | 0,5 Go et 100 CU-heures par projet et par mois ; 10 branches ; mise à l'échelle zéro après 5 minutes, réveil automatique ; restauration possible sur 6 heures ; sans carte bancaire | Aucune sauvegarde au-delà de 6 heures |
| Supabase Free | 500 Mo, 2 projets | Pause après 7 jours de faible activité, réactivation manuelle ; pas de sauvegarde quotidienne |
| Render Free | Service web et Postgres | Mise en veille après 15 minutes, réveil d'environ une minute ; base supprimée 30 jours après sa création, sans sauvegarde |
| Fly.io, Cloud Run, Scaleway | Selon le service | Carte bancaire exigée |

## Options

1. **Vercel et Neon.**
2. **Render et Neon.** Réveil trop lent pour le joueur.
3. **Supabase seul, utilisé comme Postgres.** Pause manuelle gênante pour une démonstration.

## Décision

Option 1 :

- Application sur Vercel Hobby, avec une région de fonctions européenne, la plus proche de la base. Vérifié en phase 1 : l'offre Hobby permet une seule région, réglée par `regions` dans `vercel.json` (`fra1`, près de la base de Francfort).
- Base sur Neon Free, région européenne, chaîne de connexion passant par le pooler de Neon.
- Déploiement piloté par GitHub Actions avec la CLI Vercel, sans l'intégration Git automatique :
  - **Sur chaque PR** : création d'une branche Neon, migrations, données de démonstration, déploiement de preview. La branche est supprimée à la fermeture de la PR.
  - **Sur `main`** : job dans l'environnement GitHub `production`, qui attend ton approbation, puis migrations avec le rôle de migration, déploiement en production et test de fumée.
- Les migrations passent par la connexion directe de Neon, l'application par le pooler (mode transaction : pas de curseur côté serveur, connexions non persistantes).
- Vercel ne connaît que l'identifiant du rôle d'exécution, stocké en variable « Sensitive ». L'identifiant du rôle de migration ne vit que dans les secrets de l'environnement GitHub.

## Conséquences

- **Coût** : 0 €. Usage personnel et non commercial : une démonstration présentée à titre personnel entre dans ce cadre. Un usage réel par le club n'y entrerait plus, ce qui est cohérent avec ta décision du 2026-10-12 : l'usage réel est un chantier distinct.
- **Premier affichage** : réveil de la base et démarrage de la fonction en quelques secondes après une inactivité. Mesure en phase 1, cible inférieure à 10 secondes.
- **Previews** : protégées par l'authentification Vercel ; pour la recette sur téléphone, il faut être connecté à Vercel sur ce téléphone. Les 10 branches Neon limitent le nombre de previews ouvertes en même temps, ce qui est sans effet pour un développeur seul.
- **Sauvegardes** : la fenêtre de 6 heures ne suffit pas. La phase 7 ajoute une sauvegarde planifiée par GitHub Actions : export chiffré avant stockage, puisque l'export contient les empreintes de mots de passe et que les artefacts d'un dépôt public sont téléchargeables, puis test de restauration. Les workflows planifiés d'un dépôt public sont désactivés après 60 jours sans activité : la recette mensuelle le surveille.
- **Sécurité** : l'incident Vercel d'avril 2026 a exposé, chez une partie des clients, les variables d'environnement non marquées « Sensitive ». Toutes nos variables le sont, et la procédure de rotation des secrets figure dans le guide d'exploitation de la phase 7.
- **Portabilité** : Django et Postgres standard. Changer d'hébergeur revient à modifier la configuration et le workflow de déploiement, pas le code.

## Sources

- https://vercel.com/changelog/zero-configuration-django-support.md
- https://vercel.com/docs/limits/fair-use-guidelines
- https://vercel.com/docs/functions/limitations
- https://vercel.com/kb/bulletin/vercel-april-2026-security-incident
- https://neon.com/faqs/free-plan-limits-and-quotas
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://render.com/docs/free
