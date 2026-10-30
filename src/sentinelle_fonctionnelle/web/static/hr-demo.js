(() => {
  "use strict";

  const page = document.body.dataset.page;

  if (page === "login") {
    window.setTimeout(() => {
      const host = document.querySelector("#portal-code-host");
      host.innerHTML = `
        <div class="field generated-field" data-rendered-by="javascript">
          <label for="portal-code">Code du portail astral</label>
          <input
            id="portal-code"
            name="portal_code"
            autocomplete="one-time-code"
            placeholder="CACTUS-42"
            required
          >
          <small>Champ absent du HTML initial et injecté après 120 ms.</small>
        </div>
      `;
    }, 120);
  }

  if (page === "employee-form") {
    window.setTimeout(() => {
      const role = document.body.dataset.role;
      const host = document.querySelector("#dynamic-employee-fields");
      host.innerHTML = `
        <div class="field-grid" data-rendered-by="javascript">
          <div class="field">
            <label for="favorite-color">Couleur d’aura préférée</label>
            <input id="favorite-color" name="favorite_color" type="color" value="#ff4fd8">
          </div>
          <div class="field">
            <label for="energy-level">Niveau de panache</label>
            <input id="energy-level" name="energy_level" type="range" min="0" max="100" value="50">
            <output id="energy-output" for="energy-level">50</output>
          </div>
          <div class="field">
            <label for="remote-days">Jours de téléportation par semaine</label>
            <input id="remote-days" name="remote_days" type="number" min="0" max="5" value="2">
          </div>
          ${
            role === "manager"
              ? `<div class="field">
                   <label for="manager-dynamic-note">Note dynamique du manager</label>
                   <input id="manager-dynamic-note" name="manager_dynamic_note" value="Visible uniquement après connexion manager">
                 </div>`
              : ""
          }
        </div>
      `;
      const energy = document.querySelector("#energy-level");
      const output = document.querySelector("#energy-output");
      energy.addEventListener("input", () => {
        output.value = energy.value;
        output.textContent = energy.value;
      });
    }, 180);
  }

  if (page === "consultation") {
    const payload = JSON.parse(
      document.querySelector("#record-data").textContent,
    );
    window.setTimeout(() => {
      document.querySelector("#js-result-cards").innerHTML = [
        ["Couleur d’aura", payload.favorite_color || "Non précisée"],
        ["Niveau de panache", `${payload.energy_level || "0"} / 100`],
        ["Téléportation", `${payload.remote_days || "0"} jours / semaine`],
        ["Compétences", payload.skills || "Mystérieuses"],
      ]
        .map(
          ([label, value]) => `
            <article class="data-card" data-rendered-by="javascript">
              <span>${label}</span>
              <strong>${value}</strong>
            </article>
          `,
        )
        .join("");
    }, 140);
  }

  class RhSkillCloud extends HTMLElement {
    connectedCallback() {
      if (this.dataset.ready) return;
      this.dataset.ready = "true";
      const inputName = this.dataset.inputName || "skills";
      this.innerHTML = `
        <div class="field generated-field" data-rendered-by="custom-element">
          <label for="skill-cloud-input">Compétences séparées par une virgule</label>
          <input
            id="skill-cloud-input"
            name="${inputName}"
            placeholder="Python, paie quantique, diplomatie"
          >
        </div>
      `;
    }
  }
  customElements.define("rh-skill-cloud", RhSkillCloud);
})();
