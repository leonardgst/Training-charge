# Phase 06 — Tableaux de bord

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | — | — | v0.6.0 |

## Objectif

Rendre visible ce que le moteur calcule : le préparateur ouvre « Forme actuelle » pour repérer les joueurs dont l'intensité dépasse leur moyenne alors que leurs sensations se dégradent, consulte la fiche d'un joueur (charge, sensations), revient à une date passée, et consulte ou exporte les données brutes de sa catégorie (US-10 à US-13, F11, F12, F16).

Niveau de collaboration : 5, autonome, par défaut ([ADR-0019](../adr/0019-autonomie-de-claude-code.md)), pour la phase entière ; le cadrage (section 13.4) prévoyait le niveau 4. Claude Code mène chaque PR de la branche à la CI verte ; le mainteneur valide la fiche, la fusion de chaque PR et la production ([guide](../outillage-claude-code.md)). Les règles « Le mainteneur valide » et « Jamais » de `CLAUDE.md` (section 7) restent en vigueur. Estimation : 20 heures (cadrage, section 13.4).

**Aucune formule dans l'interface** : les gabarits, le JavaScript et les spécifications Vega-Lite n'affichent que des valeurs produites par le moteur (`engine/`) via l'adaptateur `suivi/calculs.py`. Les seuls calculs permis côté Python d'affichage sont ceux que l'[ADR-0018](../adr/0018-graphique-forme-actuelle.md) place explicitement dans la construction de la spécification (couleur du point).

## Points à trancher par le mainteneur en validant cette fiche

1. **Jeu de référence E3** : `tests/reference/E3-fiche-joueur/` n'existe pas encore. Son `attendu.csv` et son `provenance.md` sont réservés au mainteneur (`CLAUDE.md`, section 6), qui les produit de façon indépendante du code. Les PR 6.2 et 6.3 en dépendent pour le parcours E3 : à fournir avant la PR 6.2, sinon E3 reste incomplet et la phase ne peut pas se clore. Si le jeu n'est pas prêt, la PR 6.1 (qui n'en a pas besoin) peut commencer.
2. **Niveau de collaboration** : 5, comme les phases 4 bis et 5, ou le niveau 4 du cadrage ?
3. **ADR-0018** (graphique « Forme actuelle ») : « Accepté, provisoire : à confirmer par le préparateur ». Le mainteneur le confirme-t-il tel quel (sensations dégradées en haut, couleur selon (intensité − sensations) / 2, entrée la plus récente des 3 derniers jours) avant la PR 6.1, ou la PR 6.1 est-elle livrée sur l'état provisoire ?
4. **Vega et politique de sécurité du contenu** : la politique actuelle (`suivi/middleware.py`) n'autorise que `'self'` et `data:` pour les images. Proposition : Vega-Lite et `vega-embed` copiés dans `suivi/static/suivi/vendor/`, avec l'interpréteur d'expressions de Vega (`vega-interpreter`, option `ast: true`) pour ne pas avoir à ajouter `'unsafe-eval'` ; la politique ne change pas. Une ADR consignera le choix dans la PR 6.1.
5. **Recette** : sur ordinateur, tablette et téléphone, en réseau local comme en phase 5 (ni la production ni les previews n'ont de données avant la phase 7).

## Livrables

- [ ] Graphique « Forme actuelle » : un point par joueur calculable, joueurs sans point listés à côté avec leur état (US-10, F11, ADR-0018)
- [ ] Fiche joueur, charge : tableau des RPE coloré, barres de CE courte et de CE longue, tableaux de valeurs (US-11, F12)
- [ ] Fiche joueur, sensations : barres de la dernière entrée, heatmap sur 7 jours avec total (US-11, F12)
- [ ] Date de rétrospection sur la fiche et sur « Forme actuelle » (US-12, C9)
- [ ] Données brutes depuis le début de la saison et export CSV, limités à la catégorie de référence (US-13, F16, A3)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 6.1 | `feat: afficher le graphique Forme actuelle` | Vega-Lite et `vega-embed` copiés dans le dépôt et compatibles avec la politique de sécurité du contenu, spécification construite en Python (`suivi/graphiques.py`), liste des joueurs sans point, tableau de valeurs accompagnant le graphique ; ADR sur le mode compatible de Vega | Unitaires sur la spécification ; intégration (périmètre d'accès, `LISTE_BLANCHE` du catalogue) | À faire | — |
| 6.2 | `feat: afficher la charge sur la fiche joueur` | Tableau des RPE coloré, barres de CE, tableaux de valeurs | E1 étendu au tableau de bord ; E3 (valeurs de charge) | À faire | — |
| 6.3 | `feat: afficher les sensations sur la fiche joueur` | Barres de la dernière entrée, heatmap sur 7 jours avec total | Unitaires sur la spécification ; E3 (valeurs de sensations) | À faire | — |
| 6.4 | `feat: choisir une date de rétrospection` | Sélecteur sur la fiche et sur « Forme actuelle » | E3, C9 côté interface | À faire | — |
| 6.5 | `feat: consulter et exporter les données brutes` | Tableau depuis le début de saison, export CSV | A3 sur l'export | À faire | — |

## Critères de fin (Definition of Done)

- [ ] Toutes les PR de la phase sont fusionnées, CI verte
- [ ] E3 au vert, sur le jeu de référence du mainteneur
- [ ] C9 vérifié côté interface : la fiche et « Forme actuelle » à la date D égalent le résultat calculé le jour D
- [ ] A3 au vert sur l'export CSV : seuls les joueurs de la catégorie de référence
- [ ] Les états « historique insuffisant » et « non calculable » sont affichés
- [ ] Aucune formule dans les gabarits ni dans le JavaScript
- [ ] Chaque graphique est accompagné d'un tableau de ses valeurs (spécifications, section 7)
- [ ] Recette manuelle faite
- [ ] Documentation à jour : fiche, journal, `CHANGELOG.md` (section `0.6.0`), `CLAUDE.md` pointant vers la phase 7

## Recette manuelle

À préparer avant la clôture (en réseau local sur la base de démonstration, comme en phase 5). Parcours prévu :

- [ ] « Forme actuelle » : les joueurs à surveiller sont en haut à droite ; la liste des joueurs sans point donne leur état
- [ ] Fiche d'un joueur : RPE colorés, barres de CE, barres de sensations, heatmap sur 7 jours
- [ ] Date de rétrospection : la fiche et le graphique reviennent à la date choisie
- [ ] Données brutes : tableau et export CSV ouvert dans un tableur
- [ ] Lisibilité sur tablette et téléphone

## Décisions prises (liens vers les ADR)

- [ADR-0002](../adr/0002-django-et-rendu-serveur.md) — Django et rendu côté serveur (piège de Vega et de la politique de sécurité du contenu)
- [ADR-0011](../adr/0011-calendrier-et-charges-glissantes.md) — Calendrier et charges glissantes
- [ADR-0012](../adr/0012-zscore-d-intensite.md) — Z-score d'intensité
- [ADR-0015](../adr/0015-zscore-de-sensations.md) — Z-score de sensations
- [ADR-0018](../adr/0018-graphique-forme-actuelle.md) — Graphique « Forme actuelle » (provisoire)

## Écarts par rapport au plan

- Niveau 5 proposé pour toute la phase, au lieu du niveau 4 du cadrage (à confirmer, point 2 ci-dessus).

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
