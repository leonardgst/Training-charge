// Dessine le graphique « Forme actuelle » à partir de la spécification Vega-Lite construite par
// le serveur (suivi/graphiques.py) : aucune formule ici. Avec `ast: true`, vega-embed
// 7.3.0 utilise l'interpréteur d'expressions qu'il embarque (vega-interpreter) au lieu de
// l'évaluation par `Function`, que la politique de sécurité du contenu interdit ;
// `defaultStyle` et le style de l'infobulle sont désactivés pour la même raison (pas de
// balise <style> injectée), leur mise en forme est dans suivi.css.
"use strict";

(() => {
  const source = document.getElementById("specification-forme");
  const cible = document.getElementById("graphique-forme");
  if (!source || !cible) return;
  const repli = "Le graphique n'a pas pu être affiché ; le tableau ci-dessous donne les valeurs.";
  if (typeof vegaEmbed === "undefined") {
    cible.textContent = repli;
    return;
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
})();
