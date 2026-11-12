# Phase 05 — Questionnaire joueur

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours (ouverte le 2026-11-12) | — | — | v0.5.0 |

## Objectif

Le joueur répond seul, sans compte, et le formulaire externe disparaît : le préparateur génère le lien personnel de chaque joueur, le joueur dépose puis corrige son entrée du jour depuis son téléphone, et la grille RPE montre qui a répondu.

Niveau de collaboration : 5, autonome, pour la phase entière, PR 5.1 et 5.2 comprises (décision du mainteneur le 2026-11-12 en validant cette fiche ; le cadrage, sections 8.2 et 13.4, prévoyait le niveau 3 pour ces deux PR). Claude Code mène chaque PR de la branche à la CI verte ; le mainteneur valide la fusion, la production et les garde-fous ([ADR-0019](../adr/0019-autonomie-de-claude-code.md), [guide](../outillage-claude-code.md)). Les règles « Jamais » et « Avec accord seulement » de `CLAUDE.md` restent en vigueur, et le jeton joueur n'est jamais stocké ni journalisé en clair. Estimation : 14 heures (cadrage, section 13.4).

**Décisions du mainteneur du 2026-11-12, en validant cette fiche :**

1. **Niveau de collaboration** : 5 pour toute la phase.
2. **`Referrer-Policy` de la page du lien joueur** : `same-origin`, comme le reste du site. `no-referrer`, prévu par l'[ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md), fait envoyer `Origin: null` avec le formulaire, que le contrôle CSRF de Django refuse (constaté en PR 4.1 bis). Le jeton n'est transmis qu'au site lui-même, qui le reçoit déjà dans l'adresse. La PR 5.2 applique le choix et met à jour l'ADR-0006 et l'architecture.
3. **QR code** (F15) : `segno`, bibliothèque Python sans dépendance, qui produit un SVG servi par l'application (aucune ressource tierce). La PR 5.1 l'ajoute et justifie la dépendance.
4. **Recette sur un vrai téléphone** : en réseau local, le téléphone sur le même réseau que le poste, l'application lancée sur la base locale de démonstration. Ni la production ni les previews n'ont de données avant la phase 7, et Claude n'agit jamais sur une base déployée. La procédure (accès depuis WSL 2, adresse hôte autorisée) est préparée à la fin de la phase.

## Livrables

- [ ] Liens joueurs : génération, révocation, régénération, lien et QR code affichés une seule fois, révocation à l'archivage d'un joueur (US-07, F07, F15, ADR-0006, ADR-0009)
- [ ] Questionnaire du jour sur téléphone, limité aux indicateurs de la catégorie de référence, créé puis modifiable le même jour (US-08, US-09, F08, F09)
- [ ] Badge Reçu / Manquant dans la grille RPE, selon les jours de questionnaire de la catégorie (F10, R22, ADR-0017)
- [ ] Correction et suppression d'une entrée passée par le préparateur de la catégorie de référence (F17, ADR-0008)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 5.1 | `feat: générer, révoquer et régénérer les liens joueurs` | Modèle et migration du lien (empreinte SHA-256 unique, un seul lien actif par joueur), pages staff, lien et QR code affichés une seule fois, révocation à l'archivage (reportée de la PR 4.2) ; niveau 5 | A5, D4 (archivage), jeton absent en clair de toutes les colonnes | À commencer | — |
| 5.2 | `feat: afficher et enregistrer le questionnaire du jour` | Vue `/q/<jeton>`, seule à accepter le jeton ; formulaire selon les indicateurs actifs de la catégorie de référence ; création puis modification jusqu'à 23 h 59, heure de Paris ; en-têtes de la page (point 2 ci-dessus) ; niveau 5 | A4, D1, D2 | À commencer | — |
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

Liste préparée à la fin de la phase ; elle se fera sur un vrai téléphone, en réseau local (décision 4 ci-dessus).

## Décisions prises (liens vers les ADR)

- [ADR-0006](../adr/0006-lien-joueur-a-jeton-hache.md) — Lien joueur à jeton haché
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies
- [ADR-0009](../adr/0009-suppression-et-archivage-d-un-joueur.md) — Suppression et archivage d'un joueur
- [ADR-0010](../adr/0010-indicateurs-et-echelles.md) — Indicateurs et échelles
- [ADR-0016](../adr/0016-evolution-de-la-configuration.md) — Évolution de la configuration
- [ADR-0017](../adr/0017-frequence-du-questionnaire.md) — Fréquence du questionnaire

## Écarts par rapport au plan

- Niveau 5 pour les PR 5.1 et 5.2, au lieu du niveau 3 du cadrage (sections 8.2 et 13.4), par décision du mainteneur le 2026-11-12.
- `Referrer-Policy: same-origin` sur la page du lien joueur, au lieu de `no-referrer` (ADR-0006), pour la même raison qu'en PR 4.1 bis.
- La PR 5.1 reprend la révocation du lien à l'archivage d'un joueur, prévue par la PR 4.2 mais impossible tant que les liens n'existaient pas.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
