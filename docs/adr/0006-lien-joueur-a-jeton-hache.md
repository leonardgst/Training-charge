# ADR-0006 — Lien joueur à jeton haché

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-10-12 | Toi, sur ma proposition |

## Contexte

Le joueur dépose son entrée du jour par un lien personnel, sans compte. Le cadrage exige un jeton aléatoire et long, stocké haché, révocable et régénérable, qui ne permet que de déposer l'entrée du jour. Le 2026-10-12, tu as ajouté que le joueur peut corriger son entrée du jour. La première tentative stockait le jeton en clair, sans révocation (annexe A, n° 4).

## Décision

| Aspect | Choix |
| --- | --- |
| Génération | `secrets.token_urlsafe(32)` : 256 bits d'aléa, 43 caractères |
| Stockage | Seule l'empreinte SHA-256 est stockée, avec un index unique. Un hachage lent (Argon2, bcrypt) n'apporte rien sur un secret de 256 bits, et son sel empêcherait l'index de recherche. |
| Affichage | Le lien et son QR code ne sont montrés qu'une fois, à la génération. Ils sont introuvables ensuite. |
| Révocation | Champ `revoked_at`. Au plus un lien actif par joueur, garanti par un index unique partiel. Archiver ou supprimer un joueur révoque son lien. |
| Régénération | Révoque le lien actif et en crée un nouveau, dans une seule transaction |
| Expiration | Aucune expiration automatique en V1 ; la révocation est manuelle |
| URL | `/q/<jeton>` |
| Portée | Une seule vue accepte le jeton. En GET, elle affiche le formulaire du jour, pré-rempli si l'entrée existe. En POST, elle crée ou modifie l'entrée du jour. Aucune autre donnée n'est atteignable. |
| Refus | Jeton inconnu, révoqué ou remplacé : même réponse 404, sans indice sur la cause |
| En-têtes | `Referrer-Policy: no-referrer`, `Cache-Control: no-store` ; aucune ressource tierce sur la page |

## Options écartées

- **Jeton signé sans stockage** : impossible à révoquer.
- **Lien magique par courriel ou SMS** : collecte de coordonnées de mineurs et service tiers.
- **Échange du jeton contre un cookie puis redirection** : retire le jeton des requêtes suivantes, mais pas de la première. Gain faible en V1.

## Conséquences

- Risque résiduel : le jeton figure dans l'URL, donc dans l'historique du navigateur et les journaux de requêtes de l'hébergeur. Il est accepté pour une démonstration sur données fictives et devra être réexaminé avant tout usage réel.
- Une limitation du nombre de tentatives est inutile : deviner un jeton de 256 bits est hors de portée.
- Tests : A4 et A5, plus une recherche du jeton en clair dans toutes les colonnes textuelles de la base.
