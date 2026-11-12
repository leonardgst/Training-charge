# Phase 05 — Questionnaire joueur

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| À commencer : fiche à valider par le mainteneur | — | — | v0.5.0 |

## Objectif

Le joueur répond seul, sans compte, et le formulaire externe disparaît : le préparateur génère le lien personnel de chaque joueur, le joueur dépose puis corrige son entrée du jour depuis son téléphone, et la grille RPE montre qui a répondu.

Niveau de collaboration proposé : 4 pour la phase, et 3 pour les PR 5.1 et 5.2, qui touchent au jeton (cadrage, sections 8.2 et 13.4). `CLAUDE.md` ne prévoit plus le niveau 3 que si le mainteneur le redemande. Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur. Estimation : 14 heures (cadrage, section 13.4).

**À trancher par le mainteneur en validant cette fiche :**

1. **Niveau de collaboration** des PR 5.1 et 5.2 : 3, comme le prévoit le cadrage, ou 4, comme pour la phase 4.
2. **`Referrer-Policy` de la page du lien joueur.** L'[ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md) y prévoit `no-referrer`. Or, avec cette valeur, le navigateur envoie `Origin: null` avec le formulaire, et le contrôle CSRF de Django refuse l'envoi du questionnaire (constaté en PR 4.1 bis). Options :
   - `same-origin`, comme le reste du site : le jeton n'est transmis qu'au site lui-même, qui le reçoit déjà dans l'adresse (recommandé) ;
   - `strict-origin` : seule l'origine est transmise, sans le chemin qui contient le jeton ;
   - `no-referrer`, en exemptant cette seule vue du contrôle CSRF : le jeton de 256 bits tient alors lieu de secret du formulaire.

   La PR 5.2 appliquera le choix et mettra à jour l'ADR-0006 et l'architecture.
3. **QR code** (F15, Should) : il demande une dépendance, donc ton accord. Proposition : `segno`, bibliothèque Python sans dépendance, qui produit un SVG servi par l'application (aucune ressource tierce). Sinon, F15 est reporté et seul le lien est affiché.
4. **Recette sur un vrai téléphone** : ni la production ni les previews n'ont de données avant la phase 7, et je n'agis jamais sur une base déployée. Options : charger toi-même la démonstration sur une branche de preview, avancer à la fin de cette phase le chargement de la démonstration en production prévu en phase 7, ou faire la recette sur ton réseau local.

## Livrables

- [ ] Liens joueurs : génération, révocation, régénération, lien et QR code affichés une seule fois, révocation à l'archivage d'un joueur (US-07, F07, F15, ADR-0006, ADR-0009)
- [ ] Questionnaire du jour sur téléphone, limité aux indicateurs de la catégorie de référence, créé puis modifiable le même jour (US-08, US-09, F08, F09)
- [ ] Badge Reçu / Manquant dans la grille RPE, selon les jours de questionnaire de la catégorie (F10, R22, ADR-0017)
- [ ] Correction et suppression d'une entrée passée par le préparateur de la catégorie de référence (F17, ADR-0008)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 5.1 | `feat: générer, révoquer et régénérer les liens joueurs` | Modèle et migration du lien (empreinte SHA-256 unique, un seul lien actif par joueur), pages staff, lien et QR code affichés une seule fois, révocation à l'archivage (reportée de la PR 4.2) ; niveau 3 proposé | A5, D4 (archivage), jeton absent en clair de toutes les colonnes | À commencer | — |
| 5.2 | `feat: afficher et enregistrer le questionnaire du jour` | Vue `/q/<jeton>`, seule à accepter le jeton ; formulaire selon les indicateurs actifs de la catégorie de référence ; création puis modification jusqu'à 23 h 59, heure de Paris ; en-têtes de la page (point 2 ci-dessus) ; niveau 3 proposé | A4, D1, D2 | À commencer | — |
| 5.3 | `feat: afficher le badge Reçu / Manquant` | Colonne de la grille RPE, jours de questionnaire de la catégorie | E2 sur téléphone | À commencer | — |
| 5.4 | `feat: corriger une entrée de sensations passée` | Correction et suppression par le préparateur de la catégorie de référence, date et auteur enregistrés | A3, intégration | À commencer | — |

## Critères de fin (Definition of Done)

- [ ] Toutes les PR de la phase sont fusionnées, CI verte
- [ ] A4 et A5 au vert ; le jeton en clair ne figure dans aucune colonne de la base
- [ ] E2 au vert en format téléphone
- [ ] D1 et D2 étendus au questionnaire, à la saisie comme en base
- [ ] Recette faite sur un vrai téléphone, avec un questionnaire rempli en moins d'une minute
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md`, `CLAUDE.md` pointant vers la phase 6

## Recette manuelle

Liste préparée à la fin de la phase ; elle se fera sur un vrai téléphone (point 4 ci-dessus).

## Décisions prises (liens vers les ADR)

- [ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md) — Lien joueur à jeton haché
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur
- [ADR-0010](../adr/0010-indicateurs-et-echelles.md) — Indicateurs et échelles
- [ADR-0016](../adr/0016-evolution-de-la-configuration.md) — Évolution de la configuration
- [ADR-0017](../adr/0017-frequence-du-questionnaire.md) — Fréquence du questionnaire

## Écarts par rapport au plan

- La PR 5.1 reprend la révocation du lien à l'archivage d'un joueur, prévue par la PR 4.2 mais impossible tant que les liens n'existaient pas.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
