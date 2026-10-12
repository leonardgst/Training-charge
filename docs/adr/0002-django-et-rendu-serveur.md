# ADR-0002 — Django et rendu côté serveur

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi, sur ma proposition |

## Contexte

Tes niveaux : Python 3, SQL 3, JavaScript et TypeScript 0, HTML et CSS 1, déploiement 0. Ta priorité est de livrer, et tes compétences à développer sont les tests, la CI et la sécurité d'accès. La première tentative avait choisi Next.js et Supabase ; ses failles les plus graves (annexe A, n° 1 et 2) venaient d'une base exposée au navigateur et protégée par des règles en base incomplètes.

## Options

1. **Next.js, Supabase, Vercel** (piste de la première tentative). Base interrogée depuis le navigateur sous des règles par ligne. Demande d'apprendre TypeScript et React, et de garantir des règles par ligne sur chaque table, vue et fonction.
2. **FastAPI et gabarits.** Léger, mais authentification, administration, migrations, formulaires et protection CSRF sont à assembler.
3. **Django, rendu côté serveur.** Authentification, administration, ORM et migrations, formulaires, CSRF et refus par défaut des vues (`LoginRequiredMiddleware`) sont fournis d'origine. Version 5.2 LTS, supportée jusqu'en avril 2028.

## Décision

Option 3, avec Python 3.12, des gabarits Django, Pico CSS et un petit fichier JavaScript sans framework.

## Conséquences

- Le navigateur ne parle jamais à la base : la surface d'attaque de l'annexe A, n° 1 et 2, disparaît. Les tests A1 et A2 portent sur deux catalogues, celui des URL et celui de la base ([ADR-0005](0005-controle-d-acces-applicatif.md)).
- L'administration Django sert d'outil d'administrateur (comptes, joueurs, indicateurs) sans écran à développer.
- La grille RPE n'utilise que des champs HTML : la navigation au clavier est native, et le code couleur tient en quelques lignes de JavaScript.
- HTMX ou une autre bibliothèque JavaScript ne seront ajoutés que si une PR en démontre le besoin, avec une ADR.
- Piège à retenir : le drapeau Django `is_staff` donne accès à l'administration. Les préparateurs ne l'ont jamais.
- Piège à retenir : Vega évalue ses expressions avec le constructeur `Function`, ce qu'une politique de sécurité du contenu stricte interdit. La phase 6 devra utiliser son mode compatible ou ajuster la politique par une ADR.
