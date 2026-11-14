# ADR-0020 — Vega sous une politique de sécurité du contenu stricte

| Statut | Date | Décideur |
| --- | --- | --- |
| Accepté | 2026-11-14 | Toi, sur ma proposition (point 4 de la fiche de la phase 6, confirmé le 2026-11-14) |

## Contexte

La politique de sécurité du contenu du site n'autorise que sa propre origine (`default-src 'self'`) et les images `data:`, ni script ni style en ligne, ni `unsafe-eval` ([ADR-0002](0002-django-et-rendu-serveur.md), architecture, section 5). Vega évalue ses expressions avec le constructeur `Function`, et `vega-embed` comme `vega-tooltip` injectent une balise `<style>` : les deux sont refusés par cette politique. La phase 6 doit afficher des graphiques sans l'assouplir.

## Options

1. **Assouplir la politique** (`'unsafe-eval'`, `'unsafe-inline'` pour les styles) : fonctionne, mais affaiblit la protection de toutes les pages, y compris le formulaire de connexion.
2. **Vega par défaut sur une page à politique propre** : même défaut, avec une exception à maintenir sur une route.
3. **Interpréteur d'expressions de Vega** (`vega-interpreter`, que `vega-embed` embarque, activé par l'option `ast: true`) et styles par défaut désactivés, mise en forme dans `suivi.css` : la politique ne change pas. Défaut : une dépendance JavaScript de plus, et un sous-ensemble d'expressions Vega (suffisant, les spécifications n'en utilisent aucune).

## Décision

Option 3.

- `vega` 6.4.0, `vega-lite` 6.5.0 et `vega-embed` 7.3.0 (qui embarque `vega-interpreter` 2.3.2), fichiers `build/*.min.js` des paquets npm et licences copiés dans `suivi/static/suivi/vendor/vega/`, comme Pico CSS. Aucun chargement depuis un réseau de diffusion. Empreintes SHA-256 : `vega.min.js` `8f6a3587cf8d4f42c7e08120e3eb05d067e746d554e39d2dcf52acc0bd5ba28f`, `vega-lite.min.js` `83e215e84e308ee8688fa6503ba0f1cf8a3c05c0d61df2841a0b92bf86809e00`, `vega-embed.min.js` `b1455caba2fb1a72fb46025ba0ba1316e2dbc7f0dd40a3f6040172bf9c08ba91` (fichiers servis par jsDelivr depuis ces paquets). Le module `vega-interpreter.min.js` autonome n'est pas copié : c'est un module ES, inutilisable comme script classique.
- `suivi/static/suivi/js/forme.js` appelle `vegaEmbed` avec `ast: true`, `defaultStyle: false`, `tooltip: { disableDefaultStyle: true }` et le rendu SVG ; l'infobulle est mise en forme par `suivi.css`.
- La spécification est construite en Python (`suivi/graphiques.py`) et transmise à la page dans un bloc `application/json` (`json_script`), jamais exécuté.
- Chaque graphique est accompagné d'un tableau de ses valeurs (spécifications, section 7).
- Un test de bout en bout (`tests/e2e/test_forme_actuelle.py`) échoue à la moindre violation de la politique ou exception de la page, graphique et infobulle compris, aux trois formats ; un test unitaire refuse tout module ES dans `vendor/`.
- **Suivi des versions** : `pip-audit` ne voit pas ces fichiers. Les versions sont consignées ici ; leur mise à jour passe par une PR qui remplace les fichiers et cette ADR, à la recette mensuelle (cadrage, PR 7.4).

## Conséquences

- La politique de sécurité du contenu reste inchangée pour tout le site.
- Une expression Vega non gérée par l'interpréteur (calcul dans la spécification) échouerait : cela garde aussi les formules hors du JavaScript.
- Le poids des fichiers (environ 850 Ko, servis une fois puis mis en cache) n'est chargé que sur la page « Forme actuelle ».
