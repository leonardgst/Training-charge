# Phase 05 — Questionnaire joueur

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours (ouverte le 2026-11-12) | — | — | v0.5.0 |

## Objectif

Le joueur répond seul, sans compte, et le formulaire externe disparaît : le préparateur génère le lien personnel de chaque joueur, le joueur dépose puis corrige son entrée du jour depuis son téléphone, et la grille RPE montre qui a répondu.

Niveau de collaboration : 5, autonome, pour la phase entière, PR 5.1 et 5.2 comprises (décision du mainteneur le 2026-11-12 en validant cette fiche ; le cadrage, sections 8.2 et 13.4, prévoyait le niveau 3 pour ces deux PR). Claude Code mène chaque PR de la branche à la CI verte ; le mainteneur valide la fusion, la production et les garde-fous ([ADR-0019](../adr/0019-autonomie-de-claude-code.md), [guide](../outillage-claude-code.md)). Les règles « Le mainteneur valide » et « Jamais » de `CLAUDE.md` (section 7) restent en vigueur, et le jeton joueur n'est jamais stocké ni journalisé en clair. Estimation : 14 heures (cadrage, section 13.4).

**Décisions du mainteneur du 2026-11-12, en validant cette fiche :**

1. **Niveau de collaboration** : 5 pour toute la phase.
2. **`Referrer-Policy` de la page du lien joueur** : `same-origin`, comme le reste du site. `no-referrer`, prévu par l'[ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md), fait envoyer `Origin: null` avec le formulaire, que le contrôle CSRF de Django refuse (constaté en PR 4.1 bis). Le jeton n'est transmis qu'au site lui-même, qui le reçoit déjà dans l'adresse. L'ADR-0006 et l'architecture sont mises à jour dans cette PR de validation ; la PR 5.2 pose l'en-tête et le teste.
3. **QR code** (F15) : `segno`, bibliothèque Python sans dépendance, dont le SVG est intégré à la page de génération du lien, sans route séparée ni ressource tierce, puisque le jeton n'est affiché qu'une seule fois. La PR 5.1 l'ajoute et justifie la dépendance.
4. **Recette sur un vrai téléphone** : en réseau local, le téléphone sur le même réseau que le poste, l'application lancée sur la base locale de démonstration. Ni la production ni les previews n'ont de données avant la phase 7 ; le mainteneur a préféré le réseau local à un chargement de la démonstration sur une preview ou en production. La procédure (accès depuis WSL 2, adresse hôte autorisée) est préparée à la fin de la phase.

## Livrables

- [ ] Liens joueurs : génération, révocation, régénération, lien et QR code affichés une seule fois, révocation à l'archivage d'un joueur (US-07, F07, F15, ADR-0006, ADR-0009)
- [ ] Questionnaire du jour sur téléphone, limité aux indicateurs de la catégorie de référence, créé puis modifiable le même jour (US-08, US-09, F08, F09)
- [ ] Badge Reçu / Manquant dans la grille RPE, selon les jours de questionnaire de la catégorie (F10, R22, ADR-0017)
- [ ] Correction et suppression d'une entrée passée par le préparateur de la catégorie de référence (F17, ADR-0008)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 5.1 | `feat: générer, révoquer et régénérer les liens joueurs` | Modèle et migration du lien (empreinte SHA-256 unique, un seul lien actif par joueur), pages staff, lien et QR code affichés une seule fois, révocation à l'archivage (reportée de la PR 4.2) ; niveau 5 | A5, D4 (archivage et effacement), jeton absent en clair de toutes les colonnes, test de bout en bout du parcours de génération aux trois formats | Fusionnée | [#53](https://github.com/leonardgst/Training-charge/pull/53) |
| 5.2 | `feat: afficher et enregistrer le questionnaire du jour` | Vue `/q/<jeton>`, seule à accepter le jeton ; formulaire selon les indicateurs actifs de la catégorie de référence ; création puis modification jusqu'à 23 h 59, heure de Paris ; route `/q/<jeton>` sans barre finale et hors de la connexion obligatoire (une redirection exposerait le jeton), adresse construite par `reverse` au lieu du chemin écrit en dur de la PR 5.1, refus d'un joueur inactif (défense en profondeur), `LISTE_BLANCHE` du catalogue d'accès mise à jour ; en-têtes de la page (décision 2 ci-dessus) ; niveau 5 | A4, D1, D2, A5 (même 404 pour un lien invalide, révoqué ou régénéré), D4 (lien refusé après archivage ou effacement) | Fusionnée | [#54](https://github.com/leonardgst/Training-charge/pull/54) |
| 5.3 | `feat: afficher le badge Reçu / Manquant` | Colonne de la grille RPE, jours de questionnaire de la catégorie | E2 sur téléphone | Fusionnée | [#55](https://github.com/leonardgst/Training-charge/pull/55) |
| 5.4 | `feat: corriger une entrée de sensations passée` | Correction et suppression par le préparateur de la catégorie de référence, date et auteur enregistrés | A3, intégration | Fusionnée | [#56](https://github.com/leonardgst/Training-charge/pull/56) |

## Critères de fin (Definition of Done)

- [x] Toutes les PR de la phase sont fusionnées, CI verte (quatre PR : [#53](https://github.com/leonardgst/Training-charge/pull/53), [#54](https://github.com/leonardgst/Training-charge/pull/54), [#55](https://github.com/leonardgst/Training-charge/pull/55), [#56](https://github.com/leonardgst/Training-charge/pull/56) ; CI de `main` verte sur `379e55d`)
- [x] A4 et A5 au vert ; le jeton en clair ne figure dans aucune colonne de la base (`tests/integration/test_vues_questionnaire.py` pour A4 et A5, `test_vues_liens.py` pour la recherche du jeton dans toutes les colonnes texte)
- [x] E2 au vert en format téléphone (`tests/e2e/test_badge_questionnaire.py` : le joueur répond, le badge passe à « Reçu », sur ordinateur, tablette et téléphone ; `test_questionnaire.py` pour le parcours du joueur)
- [x] D1 et D2 étendus au questionnaire, à la saisie comme en base (`test_vues_questionnaire.py` pour la saisie, `test_modele_sensations.py` pour la base ; `test_vues_correction_sensations.py` pour la correction)
- [ ] Recette faite sur un vrai téléphone, avec un questionnaire rempli en moins d'une minute
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 6

## Recette manuelle

Préparée le 2026-11-13 ; à faire par le mainteneur sur un vrai téléphone, en réseau local (décision 4 ci-dessus). Les résultats se reportent ici tels que le mainteneur les donne. Ni la production ni les previews n'ont de données : la recette se fait sur la base locale de démonstration.

**Avant de commencer**

- Le téléphone et le poste sont sur le même réseau Wi-Fi (pas un réseau « invités », qui isole souvent les appareils). Relever l'adresse du poste sur ce réseau, par exemple `192.168.1.20` (Windows : `ipconfig`, ligne « Adresse IPv4 » de la carte Wi-Fi).
- Dans `.env`, `DJANGO_ALLOWED_HOSTS` doit contenir cette adresse en plus des adresses locales : `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20`. Claude ne lit pas ce fichier : à vérifier par le mainteneur. Sans cela, Django répond « Invalid HTTP_HOST header » (400) au téléphone.
- Base neuve avec une démonstration dont le dernier jour est **hier**, pour qu'aucun joueur n'ait d'entrée aujourd'hui : `docker compose down -v && docker compose up -d db`, `uv run --env-file .env python manage.py migrate`, puis `uv run --env-file .env python manage.py generer_demo --fin "$(TZ=Europe/Paris date -d yesterday +%F)"` (noter le mot de passe affiché).
- Lancer le serveur sur toutes les interfaces : `uv run --env-file .env python manage.py runserver 0.0.0.0:8000`.
- Si le téléphone n'atteint pas le poste (WSL 2 en mode NAT, le réglage par défaut) : soit activer le mode « mirrored » (`networkingMode=mirrored` dans `%UserProfile%\.wslconfig`, puis `wsl --shutdown`), soit, dans un PowerShell administrateur, rediriger le port : `netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$((wsl hostname -I).Trim().Split(' ')[0])` (l'adresse de WSL 2 change à chaque redémarrage) ; dans les deux cas, autoriser le port 8000 en entrée dans le pare-feu Windows (réseau privé). À défaire après la recette : `netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0`.
- Contrôle : depuis le téléphone, `http://192.168.1.20:8000/connexion/` affiche la page de connexion.

**Parcours**

1. [ ] **Séance du jour** : sur le poste, ouvrir le site par l'adresse du réseau (`http://192.168.1.20:8000/`, et non `localhost`, sinon le lien généré à l'étape suivante pointerait vers `localhost`, inutilisable au téléphone), se connecter en `prep_u19`, créer une séance à la date d'aujourd'hui avec ses joueurs cochés ; dans la grille, la colonne « Questionnaire » affiche « Manquant » pour tous les joueurs de la catégorie (la démonstration U19 attend un questionnaire tous les jours).
2. [ ] **Lien et QR code** : dans « Joueurs », « Générer le lien » pour un joueur ; le lien et le QR code s'affichent une seule fois. Scanner le QR code avec l'appareil photo du téléphone : la page du questionnaire s'ouvre, avec le prénom du joueur et sans la navigation du staff.
3. [ ] **Remplissage chronométré** : remplir les neuf champs (sept notes de 0 à 10, deux heures) et envoyer ; noter le temps, objectif moins d'une minute. Vérifier que le clavier numérique s'ouvre pour les notes, que les heures s'ouvrent avec le sélecteur d'heure du téléphone, que rien ne déborde ni ne demande de défilement horizontal.
4. [ ] **Valeur refusée** : saisir `11` dans une note ; le navigateur refuse l'envoi (puis, si l'on force, le serveur le refuse).
5. [ ] **Confirmation** : après l'envoi, le message « C’est enregistré, merci » s'affiche, avec les réponses.
6. [ ] **Correction par le joueur** : rouvrir le même lien (recharger la page ou le rouvrir depuis l'historique du navigateur) ; les réponses sont pré-remplies ; en modifier une et renvoyer ; le message de confirmation revient.
7. [ ] **Badge** : sur le poste, recharger la séance du jour ; le joueur passe à « Reçu », les autres restent à « Manquant ».
8. [ ] **Correction d'une entrée passée par le préparateur** : « Joueurs », « Sensations » du même joueur ; une entrée d'un jour passé se corrige (changer une valeur, la liste affiche « corrigée par prep_u19 ») et se supprime (page de confirmation) ; l'entrée du jour n'a ni « Corriger » ni « Supprimer ».
9. [ ] **Lien révoqué** : « Révoquer » le lien du joueur ; recharger la page du téléphone : « Page introuvable », sans indice sur la raison. Régénérer un lien : l'ancien reste introuvable, le nouveau s'ouvre.
10. [ ] **Après la recette** : arrêter le serveur, défaire la redirection de port et la règle de pare-feu si elles ont été ajoutées.

Remarques d'ergonomie à noter ici : lisibilité sur le téléphone, taille des champs, clarté des messages.

## Décisions prises (liens vers les ADR)

- [ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md) — Lien joueur à jeton haché
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur
- [ADR-0010](../adr/0010-indicateurs-et-echelles.md) — Indicateurs et échelles
- [ADR-0016](../adr/0016-evolution-de-la-configuration.md) — Évolution de la configuration
- [ADR-0017](../adr/0017-frequence-du-questionnaire.md) — Fréquence du questionnaire

## Écarts par rapport au plan

- Niveau 5 pour toute la phase (ADR-0019), y compris les PR 5.1 et 5.2 (jeton, migration) et 5.4 (règles d'accès), que le cadrage (sections 8.2, 9 et 13.4) plaçait au niveau 3, par décision du mainteneur le 2026-11-12.
- PR 5.1 : le QR code est une image `data:` intégrée à la page de génération du lien ; l'architecture (sections 2 et 5) le dit désormais, au lieu de réserver les images `data:` aux icônes de Pico CSS.
- PR 5.1 : le lien généré pointe vers `/q/<jeton>`, route créée par la PR 5.2 ; tant que la PR 5.2 n'est pas fusionnée, ce lien répond 404.
- PR 5.1 : la suppression en cascade d'un joueur et la mise à `NULL` de l'auteur d'un lien sont faites par Django, comme pour les autres tables ; une suppression en SQL pur d'un joueur qui a des liens échoue à la validation de la transaction. L'effacement passe par l'administration (ADR-0009).
- PR 5.1 : l'archivage passe par `archiver_joueur` (vue du préparateur) et par `JoueurAdmin.save_model` (administration), qui révoquent tous deux le lien ; une création de lien et un archivage simultanés sont ordonnés par le verrou du joueur.
- PR 5.1 : `tests/integration/test_effacement_joueur.py` donne au joueur invité deux liens (un révoqué, un actif), pour que le test D4 vérifie aussi l'effacement de `lien_joueur` ; aucune assertion n'est retirée ni assouplie.
- `Referrer-Policy: same-origin` sur la page du lien joueur, au lieu de `no-referrer` (ADR-0006), pour la même raison qu'en PR 4.1 bis.
- PR 5.2 : tous les champs du questionnaire sont obligatoires (notes de 0 à 10 saisies au clavier numérique, heures par le sélecteur du téléphone) .
- PR 5.2 : la page porte la date du jour de son chargement ; un envoi reçu après minuit n'est pas rangé dans le nouveau jour, la page se recharge vide avec un message (R16).
- PR 5.2 : `suivi/journal.py` masque `/q/<jeton>` dans les journaux `django.request`, `django.security.csrf` et `django.server`, qui écrivent sinon l'adresse (jeton révoqué ou mal recopié compris), posé au démarrage et non par `LOGGING`. `/q/x` entre dans la `LISTE_BLANCHE` du catalogue d'accès, comme prévu ; son refus est vérifié par A5.
- PR 5.3 : le badge suit les jours de questionnaire de la catégorie de référence du joueur (R22) et porte sur la date de la séance (ADR-0017, Q3) ; une séance à venir n'a pas de « Manquant » (tiret), le jour même oui, puisque le joueur peut répondre jusqu'à 23 h 59. Un joueur invité d'une autre catégorie a toujours un tiret : son entrée n'est pas lisible par le préparateur (ADR-0005).
- PR 5.4 : la correction passe par la liste « Sensations » de chaque joueur (lien depuis la page des joueurs). Un champ laissé vide garde la réponse du joueur, car un indicateur ajouté depuis n'a pas de réponse dans une ancienne entrée ; aucune réponse n'est supprimée, et la date de l'entrée ne se change pas. Les entrées d'un joueur archivé restent corrigeables. Seule une entrée *passée* se corrige (R16) : celle du jour reste au joueur, sans quoi son prochain envoi effacerait la trace de la correction. Un envoi sans réponse modifiée ne compte pas comme une correction.
- PR 5.4 : l'ADR-0008 (Q3) exige « date et auteur » sans historique ; une correction les inscrit dans `updated_at` et `updated_by`, et une suppression, qui ne laisse plus de ligne, est tracée au journal applicatif `suivi.audit` (clé du joueur, date de l'entrée, nom d'utilisateur, sans nom de joueur).
- La PR 5.1 reprend la révocation du lien à l'archivage d'un joueur, prévue par la PR 4.2 mais impossible tant que les liens n'existaient pas.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
