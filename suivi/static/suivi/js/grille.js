// Code couleur de la grille RPE : chaque case prend la couleur de sa valeur pendant la
// frappe (US-04). Même règle que `niveau_rpe` dans suivi/forms.py ; le serveur reste seul
// juge de la validité. Fichier externe, sans style en ligne : compatible avec la politique
// de sécurité du contenu.
"use strict";

(() => {
  const VALEUR = /^(?:[0-9]|10)$/;

  function colorer(caseRpe) {
    const valeur = caseRpe.value.trim();
    if (valeur === "") {
      delete caseRpe.dataset.niveau;
      caseRpe.removeAttribute("aria-invalid");
    } else if (VALEUR.test(valeur)) {
      caseRpe.dataset.niveau = valeur;
      caseRpe.removeAttribute("aria-invalid");
    } else {
      caseRpe.dataset.niveau = "invalide";
      caseRpe.setAttribute("aria-invalid", "true");
    }
  }

  document.addEventListener("input", (evenement) => {
    if (evenement.target instanceof HTMLInputElement && evenement.target.matches("input.rpe")) {
      colorer(evenement.target);
    }
  });
})();
