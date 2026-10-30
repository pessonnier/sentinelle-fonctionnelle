(() => {
  "use strict";

  const themes = new Set([
    "forest",
    "ocean",
    "plum",
    "sunset",
    "graphite",
    "high-contrast",
    "defense",
  ]);

  try {
    const storedTheme = window.localStorage.getItem("sentinelle-theme");
    if (themes.has(storedTheme)) {
      document.documentElement.dataset.theme = storedTheme;
    }
  } catch (_error) {
    // Le stockage peut être désactivé : le thème Forêt reste utilisable.
  }
})();
