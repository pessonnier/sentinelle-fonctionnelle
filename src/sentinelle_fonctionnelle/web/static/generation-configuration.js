(() => {
  "use strict";

  async function errorMessage(response) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = await response.json();
      return payload.detail || payload.message || `Erreur HTTP ${response.status}`;
    }
    const text = await response.text();
    const readable = new DOMParser()
      .parseFromString(text, "text/html")
      .body.textContent.trim();
    return readable || `Erreur HTTP ${response.status}`;
  }

  document.querySelectorAll("[data-model-picker]").forEach((picker) => {
    const form = picker.closest("form");
    const select = picker.querySelector("[data-model-select]");
    const button = picker.querySelector("[data-model-refresh]");
    const status = picker.parentElement.querySelector(
      "[data-model-refresh-status]",
    );
    if (!form || !select || !button || !status) {
      return;
    }

    button.addEventListener("click", async () => {
      const baseUrl = form.elements.namedItem("base_url")?.value.trim() || "";
      if (!baseUrl) {
        status.textContent =
          "Saisissez d’abord l’URL de base à interroger.";
        form.elements.namedItem("base_url")?.focus();
        return;
      }

      const currentModel = select.value;
      const body = new FormData();
      for (const name of [
        "provider",
        "base_url",
        "api_key_environment",
        "organization_environment",
        "request_timeout_seconds",
      ]) {
        const control = form.elements.namedItem(name);
        if (control) {
          body.append(name, control.value);
        }
      }

      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      status.textContent = "Chargement des modèles disponibles…";
      try {
        const response = await fetch("/configuration/llm-models", {
          method: "POST",
          body,
        });
        if (!response.ok) {
          throw new Error(await errorMessage(response));
        }
        const result = await response.json();
        const models = Array.isArray(result.models) ? result.models : [];
        const fragment = document.createDocumentFragment();
        if (currentModel && !models.includes(currentModel)) {
          const retained = document.createElement("option");
          retained.value = currentModel;
          retained.textContent = `${currentModel} — actuel, non retourné`;
          fragment.append(retained);
        }
        models.forEach((model) => {
          const option = document.createElement("option");
          option.value = model;
          option.textContent = model;
          fragment.append(option);
        });
        select.replaceChildren(fragment);
        select.value = currentModel || models[0];
        status.textContent =
          `${models.length} modèle${models.length > 1 ? "s" : ""} disponible${models.length > 1 ? "s" : ""}.`;
      } catch (error) {
        status.textContent =
          error.message || "La liste des modèles n’a pas pu être chargée.";
      } finally {
        button.disabled = false;
        button.removeAttribute("aria-busy");
      }
    });
  });

  document.querySelectorAll("[data-connectivity-url]").forEach((button) => {
    button.addEventListener("click", async () => {
      const status = button.parentElement.querySelector(
        "[data-connectivity-status]",
      );
      button.disabled = true;
      status.textContent = `Vérification de ${button.dataset.connectivityProfile}…`;
      try {
        const response = await fetch(button.dataset.connectivityUrl, {
          method: "POST",
        });
        if (!response.ok) {
          throw new Error(await errorMessage(response));
        }
        const result = await response.json();
        if (result.model_available) {
          status.textContent =
            `${result.engine} ${result.engine_version} répond en ${result.duration_ms} ms · modèle ${result.model} disponible.`;
        } else {
          status.textContent =
            `${result.engine} ${result.engine_version} répond, mais le modèle ${result.model} est absent.`;
        }
      } catch (error) {
        status.textContent = error.message || "Le serveur LLM ne répond pas.";
      } finally {
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll("[data-structured-test-url]").forEach((button) => {
    button.addEventListener("click", async () => {
      const status = button.parentElement.querySelector(
        "[data-connectivity-status]",
      );
      button.disabled = true;
      status.textContent =
        `Chargement de ${button.dataset.structuredTestProfile} et test JSON…`;
      try {
        const response = await fetch(button.dataset.structuredTestUrl, {
          method: "POST",
        });
        if (!response.ok) {
          throw new Error(await errorMessage(response));
        }
        const result = await response.json();
        status.textContent =
          `Inférence validée en ${result.duration_ms} ms · JSON structuré accepté · ${result.model}.`;
      } catch (error) {
        status.textContent =
          error.message || "L’inférence structurée a échoué.";
      } finally {
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll("[data-llm-interaction]").forEach((container) => {
    const button = container.querySelector("[data-interaction-url]");
    const message = container.querySelector("[data-llm-message]");
    const status = container.querySelector("[data-interaction-status]");
    const output = container.querySelector("[data-llm-response]");

    button.addEventListener("click", async () => {
      const value = message.value.trim();
      if (!value) {
        status.textContent = "Saisissez un message avant l’envoi.";
        message.focus();
        return;
      }
      button.disabled = true;
      output.hidden = true;
      status.textContent = "Le modèle prépare sa réponse…";
      const body = new FormData();
      body.append("message", value);
      try {
        const response = await fetch(button.dataset.interactionUrl, {
          method: "POST",
          body,
        });
        if (!response.ok) {
          throw new Error(await errorMessage(response));
        }
        const result = await response.json();
        output.textContent = result.answer;
        output.hidden = false;
        status.textContent = `Réponse reçue en ${result.duration_ms} ms.`;
      } catch (error) {
        status.textContent = error.message || "L’appel au modèle a échoué.";
      } finally {
        button.disabled = false;
      }
    });
  });
})();
