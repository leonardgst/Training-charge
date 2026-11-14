# Phase 06 — Tableaux de bord

| Statut | Prévue | Terminée le | Tag Git |
| --- | --- | --- | --- |
| En cours | — | — | v0.6.0 |

## Objectif

Rendre visible ce que le moteur calcule : le préparateur ouvre « Forme actuelle » pour repérer les joueurs dont l'intensité dépasse leur moyenne alors que leurs sensations se dégradent, consulte la fiche d'un joueur (charge, sensations), revient à une date passée, et consulte ou exporte les données brutes de sa catégorie (US-10 à US-13, F11, F12, F16).

Niveau de collaboration : 5, autonome, par défaut ([ADR-0019](../adr/0019-autonomie-de-claude-code.md)), pour la phase entière ; le cadrage (section 13.4) prévoyait le niveau 4. Claude Code mène chaque PR de la branche à la CI verte ; le mainteneur valide la fiche, la fusion de chaque PR et la production ([guide](../outillage-claude-code.md)). Les règles « Le mainteneur valide » et « Jamais » de `CLAUDE.md` (section 7) restent en vigueur. Estimation : 20 heures (cadrage, section 13.4).

**Aucune formule dans l'interface** : les gabarits, le JavaScript et les spécifications Vega-Lite n'affichent que des valeurs produites par le moteur (`engine/`) via l'adaptateur `suivi/calculs.py`. Les calculs propres à « Forme actuelle » (choix de l'entrée de sensations la plus récente de D − 3 à D, couleur (intensité − sensations) / 2 bornée par `couleur_borne`, états « absent depuis N jours » et « pas d'entrée récente ») vivent dans `engine/`, avec leurs paramètres `fraicheur_entree_jours` et `couleur_borne` ajoutés à `config/calcul.toml`, à `Parametres` et à la validation de `lire_parametres`, et leurs tests unitaires (seuil de 95 % des branches) : c'est la PR 6.1a. Il en va de même du total de la heatmap, qui est le `score_sensations` du moteur (R19, ADR-0014), avec son état `reponses_insuffisantes` ; le passage sur 10 et le sens des indicateurs inversés sont décidés par le moteur, jamais par le gabarit ni le JavaScript.

## Points à trancher par le mainteneur en validant cette fiche

Fiche validée et fusionnée ([#60](https://github.com/leonardgst/Training-charge/pull/60), 2026-11-14). Le même jour, le mainteneur a confirmé le niveau 5 et tous les autres points proposés (Vega, `debut_saison` au 1er juillet, recette en réseau local, état sans repli). Le mainteneur a tranché le point 7 : **couleur du tableau des RPE selon la valeur du RPE**, comme la grille de saisie (PR 6.2). Les autres points restent tels que la fiche les propose.

1. **Jeu de référence E3** : `tests/reference/E3-fiche-joueur/` n'existe pas encore, et le harnais (`registre.py`, README) ne connaît que C01 à C15 ; la PR 6.1b l'étend. Claude écrit les fichiers d'entrée (`joueurs.csv`, `seances.csv`, etc.) ; seuls `attendu.csv` et `provenance.md` sont réservés au mainteneur (`CLAUDE.md`, section 6), qui les produit de façon indépendante du code. E3 porte sur la fiche et sur le point du joueur de référence dans « Forme actuelle », lu dans le tableau de valeurs : à fournir avant la PR 6.1b, qui peut commencer sans, E3 restant alors en attente.
6. **Début de saison** : `debut_saison` (spécifications, section 5, « à valider avant la phase 6 ») : 1er juillet ? La PR 6.5 l'ajoute à `config/calcul.toml` et à `lire_parametres`.
7. **Couleur du tableau des RPE** : selon la valeur du RPE (comme la grille de saisie) ou selon l'intensité du jour (z-score de la CE courte, glossaire) ?
2. **Niveau de collaboration** : 5, comme les phases 4 bis et 5, ou le niveau 4 du cadrage ?
3. **ADR-0018** (graphique « Forme actuelle ») : la PR 6.1 l'applique telle qu'acceptée le 2026-10-12 ; elle reste provisoire et paramétrable, en attendant l'avis du préparateur. Cas non tranché par l'ADR : si l'entrée la plus récente de la fenêtre est en état `reponses_insuffisantes`, prendre une entrée plus ancienne de la fenêtre, ou afficher l'état ? Proposition : l'état, sans repli.
4. **Vega et politique de sécurité du contenu** : la politique actuelle (`suivi/middleware.py`) n'autorise que `'self'` et `data:` pour les images. Proposition : Vega-Lite et `vega-embed` copiés dans `suivi/static/suivi/vendor/`, avec l'interpréteur d'expressions de Vega (`vega-interpreter`, option `ast: true`) pour ne pas avoir à ajouter `'unsafe-eval'` ; la politique ne change pas. C'est un objectif à vérifier, non acquis : `vega-embed` et `vega-tooltip` injectent des balises `<style>` que la politique refuse (architecture, section 5). Il faut aussi copier `vega` et `vega-interpreter`, joindre les licences dans `vendor/` comme pour Pico CSS, et dire dans l'ADR comment les versions JavaScript sont suivies (`pip-audit` ne les voit pas). Une ADR consigne le choix dans la PR 6.1b.
5. **Recette** : sur ordinateur, tablette et téléphone, en réseau local comme en phase 5 (ni la production ni les previews n'ont de données avant la phase 7).

## Livrables

- [x] Graphique « Forme actuelle » : un point par joueur calculable, joueurs sans point listés à côté avec leur état (US-10, F11, ADR-0018)
- [ ] Fiche joueur, charge : tableau des RPE coloré, barres de CE courte et de CE longue, tableaux de valeurs (US-11, F12)
- [ ] Fiche joueur, sensations : barres de la dernière entrée, heatmap sur 7 jours avec total (US-11, F12)
- [ ] Date de rétrospection sur la fiche et sur « Forme actuelle » (US-12, C9)
- [ ] Données brutes depuis le début de la saison et export CSV, limités à la catégorie de référence (US-13, F16, A3)

## PR de la phase

| # | Titre | Contenu | Tests apportés | Statut | Lien |
| --- | --- | --- | --- | --- | --- |
| 6.1a | `feat: calculer la forme actuelle dans le moteur` | Entrée de sensations la plus récente de D − 3 à D, couleur bornée, états sans point ; `fraicheur_entree_jours` et `couleur_borne` dans `config/calcul.toml`, `Parametres` et `lire_parametres` | Unitaires du moteur (95 % des branches) ; C9 sur ces calculs | Fusionnée | [#61](https://github.com/leonardgst/Training-charge/pull/61) |
| 6.1b | `feat: afficher le graphique Forme actuelle` | Vega-Lite, `vega-embed`, `vega` et `vega-interpreter` copiés dans le dépôt avec leurs licences, compatibles avec la politique de sécurité du contenu, spécification construite en Python (`suivi/graphiques.py`), joueurs sans point listés, tableau de valeurs ; ADR sur le mode compatible de Vega ; `gardien-acces` | Unitaires sur la spécification ; A1 (la nouvelle route entre dans le catalogue, `LISTE_BLANCHE` inchangée) ; A3 (seuls les joueurs suivis, ni invité ni autre catégorie) ; E3 (point du joueur de référence, lu dans le tableau) | En revue | — |
| 6.2 | `feat: afficher la charge sur la fiche joueur` | Tableau des RPE coloré, barres de CE, tableaux de valeurs ; le joueur est obtenu par `joueurs_suivis` avant tout appel à l'adaptateur | E1 étendu au tableau de bord ; E3 (charge) ; A3 (fiche d'un joueur d'une autre catégorie ou d'un invité : 404) | À faire | — |
| 6.3 | `feat: afficher les sensations sur la fiche joueur` | Barres de la dernière entrée, heatmap sur 7 jours, total = `score_sensations` du moteur | Unitaires sur la spécification ; E3 (sensations) ; A3 | À faire | — |
| 6.4 | `feat: choisir une date de rétrospection` | Sélecteur sur la fiche et sur « Forme actuelle » | E3, C9 côté interface ; A3 avec le paramètre de date | À faire | — |
| 6.5 | `feat: consulter et exporter les données brutes` | `debut_saison` dans `config/calcul.toml` et `lire_parametres`, tableau depuis le début de saison, export CSV | A3 sur l'export | À faire | — |

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
- [ADR-0005](../adr/0005-controle-d-acces-applicatif.md) — Contrôle d'accès (A3, export, joueur invité)
- [ADR-0008](../adr/0008-cycle-de-vie-des-saisies.md) — Cycle de vie des saisies (C9)
- [ADR-0013](../adr/0013-absences-longues.md) — Absences longues
- [ADR-0014](../adr/0014-score-de-sensations.md) — Score de sensations (total, affichage sur 10)
- [ADR-0018](../adr/0018-graphique-forme-actuelle.md) — Graphique « Forme actuelle » (provisoire)
- [ADR-0020](../adr/0020-vega-sous-politique-de-securite-du-contenu.md) — Vega sous une politique de sécurité du contenu stricte

## Écarts par rapport au plan

- Niveau 5 proposé pour toute la phase, au lieu du niveau 4 du cadrage (confirmé par le mainteneur le 2026-11-14).
- La PR 6.1 du cadrage est coupée en 6.1a (moteur et paramètres) et 6.1b (graphique), pour rester relisible en moins de 20 minutes ; une ADR s'y ajoute.
- PR 6.1b : le volet « Forme actuelle » de E3 attend le jeu de référence du mainteneur ; la PR apporte les tests unitaires, A1 (catalogue), A3 et le parcours de bout en bout, et E3 sera ajouté dès que `tests/reference/E3-fiche-joueur/` existera.
- E3 est réparti sur les PR 6.1b à 6.4, au lieu de la seule PR 6.4.
- Recette en réseau local sur la base de démonstration, au lieu de l'environnement déployé (cadrage, section 7.8), faute de données en production avant la phase 7.

## Rétrospective : ce qui a marché, ce qui a coincé

À remplir à la clôture.
