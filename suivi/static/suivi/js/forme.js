// Dessine les graphiques de la page (« Forme actuelle », charge et sensations de la fiche
// joueur) à partir des spécifications Vega-Lite construites par le serveur
// (suivi/graphiques.py) : aucune formule ici. Chaque <figure data-specification="x"> reçoit
// la spécification du <script id="x"> JSON. Avec `ast: true`, vega-embed 7.3.0 utilise
// l'interpréteur d'expressions qu'il embarque (vega-interpreter) au lieu de l'évaluation par
// `Function`, que la politique de sécurité du contenu interdit ; `defaultStyle` et le style
// de l'infobulle sont désactivés pour la même raison (pas de balise <style> injectée), leur
// mise en forme est dans suivi.css.
"use strict";

(() => {
  const repli = "Le graphique n'a pas pu être affiché ; le tableau ci-dessous donne les valeurs.";
  for (const cible of document.querySelectorAll("figure[data-specification]")) {
    const source = document.getElementById(cible.dataset.specification);
    if (!source) continue;
    if (typeof vegaEmbed === "undefined") {
      cible.textContent = repli;
      continue;
    }
    vegaEmbed(cible, JSON.parse(source.textContent), {
      actions: false,
      ast: true,
      defaultStyle: false,
      renderer: "svg",
      tooltip: { disableDefaultStyle: true },
    }).catch((erreur) => {
      cible.textContent = repli;
      console.error(erreur);
    });
  }
})();
