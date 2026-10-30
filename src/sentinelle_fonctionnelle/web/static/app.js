(() => {
  "use strict";

  const usedFieldIds = new Set();
  document.querySelectorAll("label").forEach((label, index) => {
    const fieldLabel = label.querySelector(":scope > .field-label");
    const help = label.querySelector(":scope > [data-field-help]");
    const control = label.querySelector(
      "input:not([type='hidden']), select, textarea",
    );
    if (!fieldLabel || !help || !control) {
      return;
    }

    let fieldId = control.id || control.name || `field-${index + 1}`;
    fieldId = fieldId.replace(/[^a-zA-Z0-9_-]+/g, "-");
    let uniqueId = fieldId;
    let suffix = 2;
    while (usedFieldIds.has(uniqueId) || (document.getElementById(uniqueId) && control.id !== uniqueId)) {
      uniqueId = `${fieldId}-${suffix}`;
      suffix += 1;
    }
    usedFieldIds.add(uniqueId);
    control.id = uniqueId;
    label.htmlFor = control.id;

    const helpId = `${uniqueId}-help`;
    help.id = helpId;
    const describedBy = new Set(
      (control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean),
    );
    describedBy.add(helpId);
    control.setAttribute("aria-describedby", Array.from(describedBy).join(" "));
  });

  document.querySelector("[aria-invalid='true']")?.focus();

  const themeSelector = document.querySelector("[data-theme-selector]");
  if (themeSelector) {
    const themes = Array.from(themeSelector.options, (option) => option.value);
    const activeTheme = themes.includes(document.documentElement.dataset.theme)
      ? document.documentElement.dataset.theme
      : "forest";
    themeSelector.value = activeTheme;

    themeSelector.addEventListener("change", () => {
      const selectedTheme = themes.includes(themeSelector.value)
        ? themeSelector.value
        : "forest";
      document.documentElement.dataset.theme = selectedTheme;
      try {
        window.localStorage.setItem("sentinelle-theme", selectedTheme);
      } catch (_error) {
        // Le choix reste actif pour la page même si le stockage est indisponible.
      }
    });
  }

  document.querySelectorAll("[data-create-toggle]").forEach((button) => {
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    const label = button.querySelector("[data-create-label]");
    const icon = button.querySelector(".add-entity-icon");
    if (!panel || !label || !icon) {
      return;
    }

    const setExpanded = (expanded, moveFocus = true) => {
      button.setAttribute("aria-expanded", String(expanded));
      panel.hidden = !expanded;
      label.textContent = expanded
        ? button.dataset.createCloseLabel || "Masquer le formulaire"
        : button.dataset.createOpenLabel || "Ajouter";
      icon.textContent = expanded ? "−" : "+";
      if (!moveFocus) {
        return;
      }
      if (expanded) {
        panel
          .querySelector(
            "input:not([type='hidden']):not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled])",
          )
          ?.focus();
      } else {
        button.focus();
      }
    };

    setExpanded(button.getAttribute("aria-expanded") === "true", false);
    button.addEventListener("click", () => {
      setExpanded(button.getAttribute("aria-expanded") !== "true");
    });
    panel.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setExpanded(false);
      }
    });
  });
})();
