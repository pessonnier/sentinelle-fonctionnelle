(() => {
  "use strict";

  const form = document.querySelector("#guided-case-form");
  if (!form) return;

  const initial = JSON.parse(
    document.querySelector("#workflow-initial").textContent || "{}",
  );
  const template = document.querySelector("#workflow-step-template");
  const stepsContainer = document.querySelector("#workflow-steps");
  const workflowInput = document.querySelector("#workflow-json");
  const preview = document.querySelector("#workflow-preview");
  const readiness = document.querySelector("#workflow-readiness");
  const fieldList = document.querySelector("#page-field-list");
  const fieldCount = document.querySelector("#field-count");
  const fieldOptions = document.querySelector("#page-element-options");
  const analysisButton = document.querySelector("#analyze-page");
  const analysisUrl = document.querySelector("#page-analysis-url");
  const analysisStatus = document.querySelector("#page-analysis-status");
  const confirmation = document.querySelector("#workflow-confirmed");
  const functionalIntent = document.querySelector("#functional-intent");
  const guidanceButton = document.querySelector("#refresh-design-guidance");
  const guidanceStatus = document.querySelector("#design-guidance-status");
  const missingInformationList = document.querySelector(
    "#missing-information-list",
  );
  const missingInformationCount = document.querySelector(
    "#missing-information-count",
  );
  const htmlCapabilitiesList = document.querySelector(
    "#html-capabilities-list",
  );
  const htmlCapabilitiesCount = document.querySelector(
    "#html-capabilities-count",
  );
  const assistantScript = document.querySelector("script[data-guidance-url]");
  const dialogueInitial = JSON.parse(
    document.querySelector("#design-dialogue-initial")?.textContent || "{}",
  );
  const dialogueHistory = document.querySelector("#design-dialogue-history");
  const proposalsContainer = document.querySelector("#design-proposals");
  const designMessage = document.querySelector("#design-message");
  const sendDesignMessage = document.querySelector("#send-design-message");
  const dialogueStatus = document.querySelector("#design-dialogue-status");
  const authoringModeInputs = [
    ...form.querySelectorAll('[name="authoring_mode"]'),
  ];
  const authoringPanels = [...form.querySelectorAll("[data-authoring-panel]")];
  const narrativeTemplate = document.querySelector("#step-narrative-template");
  const narrativeList = document.querySelector("#step-narrative-list");
  const scenarioNarrative = document.querySelector("#scenario-narrative");
  const fixtureTemplate = document.querySelector("#fixture-ref-template");
  const fixtureList = document.querySelector("#fixture-ref-list");
  const fixtureInput = document.querySelector("#fixture-refs");
  const preconditionTemplate = document.querySelector(
    "#precondition-dependency-template",
  );
  const preconditionList = document.querySelector(
    "#precondition-dependency-list",
  );
  const preconditionStatus = document.querySelector(
    "#precondition-dependency-status",
  );
  const readinessButton = document.querySelector("#check-system-readiness");
  const readinessResults = document.querySelector("#system-readiness-results");
  const pages = Array.isArray(initial.pages) ? [...initial.pages] : [];
  let lastTargetInput = null;

  const lines = (value) =>
    value
      .split(/\r?\n/)
      .map((item) => item.trim())
      .filter(Boolean);

  const authoringMode = () =>
    authoringModeInputs.find((input) => input.checked)?.value || "form";

  function stepToNarrative(step, index) {
    const parts = [`Étape ${index + 1} — ${step.name || "À préciser"}.`];
    if (step.precondition) parts.push(`Avant : ${step.precondition}.`);
    if (step.action !== "none") {
      parts.push(
        `Action : ${step.action}${step.target ? ` sur ${step.target}` : ""}${step.value ? ` avec ${step.value}` : ""}.`,
      );
    }
    if (step.assertion !== "none") {
      parts.push(
        `Contrôle : ${step.assertion}${step.assertion_target ? ` sur ${step.assertion_target}` : ""}${step.expected ? ` ; attendu ${step.expected}` : ""}.`,
      );
    }
    return parts.join(" ");
  }

  function validCanonicalStep(step) {
    if (!step.name) return false;
    if (
      ["click", "fill", "select", "check", "uncheck", "upload"].includes(
        step.action,
      ) &&
      !step.target
    ) return false;
    if (["fill", "select", "upload"].includes(step.action) && !step.value) {
      return false;
    }
    if (
      !["none", "url"].includes(step.assertion) &&
      !step.assertion_target
    ) return false;
    return step.action !== "none" || step.assertion !== "none";
  }

  function collectStepNarratives() {
    return [...narrativeList.querySelectorAll("[data-step-narrative]")]
      .map((control) => control.value.trim())
      .filter(Boolean);
  }

  function collectFixtureRefs() {
    return [...fixtureList.querySelectorAll("[data-fixture-ref]")]
      .map((control) => control.value.trim())
      .filter(Boolean);
  }

  function collectPreconditionDependencies() {
    return [...preconditionList.querySelectorAll(".precondition-dependency-card")]
      .map((card, index) => ({
        id: `precondition-${index + 1}`,
        source: card.querySelector("[data-precondition-source]").value.trim(),
        kind: card.querySelector("[data-precondition-kind]").value,
        description: card
          .querySelector("[data-precondition-description]")
          .value.trim(),
        reference: card
          .querySelector("[data-precondition-reference]")
          .value.trim(),
        confirmed: card.querySelector("[data-precondition-confirmed]").checked,
      }))
      .filter((item) => item.source);
  }

  function syncFixtureInput() {
    fixtureInput.value = collectFixtureRefs().join("\n");
  }

  const defaultStep = (index) => ({
    id: `step-${index}`,
    name: "",
    page_url:
      document.querySelector("#start-url").value ||
      document.querySelector("#page-analysis-url").value,
    precondition: "",
    action: "click",
    target: "",
    value: "",
    assertion: "visible",
    assertion_target: "",
    expected: "",
    evidence: false,
  });

  const field = (card, name) => card.querySelector(`[data-field="${name}"]`);

  function stepFromCard(card, index) {
    return {
      id: `step-${index + 1}`,
      name: field(card, "name").value.trim(),
      page_url: field(card, "page_url").value.trim(),
      precondition: field(card, "precondition").value.trim(),
      action: field(card, "action").value,
      target: field(card, "target").value.trim(),
      value: field(card, "value").value.trim(),
      assertion: field(card, "assertion").value,
      assertion_target: field(card, "assertion_target").value.trim(),
      expected: field(card, "expected").value.trim(),
      evidence: field(card, "evidence").checked,
    };
  }

  function collectSteps() {
    return [...stepsContainer.querySelectorAll(".workflow-step-card")].map(
      stepFromCard,
    );
  }

  function buildWorkflow() {
    syncFixtureInput();
    const mode = authoringMode();
    const collectedSteps = collectSteps();
    return {
      schema_version: 2,
      start_url: document.querySelector("#start-url").value.trim(),
      environment_profile: document
        .querySelector("#environment-profile")
        .value.trim(),
      actor_profile: document.querySelector("#actor-profile").value.trim(),
      functional_intent: functionalIntent.value,
      fixture_refs: collectFixtureRefs(),
      secret_refs: lines(document.querySelector("#secret-refs").value),
      setup: lines(document.querySelector("#setup-lines").value),
      cleanup: lines(document.querySelector("#cleanup-lines").value),
      evidence_policy: document.querySelector("#evidence-policy").value,
      llm_policy: document.querySelector("#llm-policy").value,
      llm_access_profile: document
        .querySelector("#llm-access-profile")
        .value,
      code_generation_profile: document
        .querySelector("#code-generation-profile")
        .value,
      timeout_seconds:
        Number(document.querySelector("#timeout-seconds").value) || 30,
      assumptions: lines(document.querySelector("#assumptions").value),
      confirmed: confirmation.checked,
      authoring_mode: mode,
      step_narratives: collectStepNarratives(),
      scenario_narrative: scenarioNarrative.value.trim(),
      pages,
      steps:
        mode === "form"
          ? collectedSteps
          : collectedSteps.filter(validCanonicalStep),
      precondition_dependencies: collectPreconditionDependencies(),
    };
  }

  function buildDraft() {
    return {
      objective: form.querySelector('[name="objective"]').value.trim(),
      actor: form.querySelector('[name="actor_name"]').value.trim(),
      summary: document.querySelector("#case-summary").value.trim(),
      preconditions: lines(document.querySelector("#setup-lines").value),
      postconditions: lines(document.querySelector("#cleanup-lines").value),
      requirements: lines(document.querySelector("#requirements-lines").value),
      business_rules: lines(
        document.querySelector("#business-rules-lines").value,
      ),
      data_sets: lines(document.querySelector("#fixture-refs").value),
      workflow: buildWorkflow(),
    };
  }

  function issues(workflow) {
    const found = [];
    if (!workflow.start_url) found.push("page de départ manquante");
    if (!workflow.environment_profile) found.push("environnement manquant");
    if (!workflow.actor_profile) found.push("profil d’acteur manquant");
    if (!workflow.functional_intent) {
      found.push("intention fonctionnelle manquante");
    }
    if (
      workflow.llm_policy !== "disabled" &&
      !workflow.llm_access_profile
    ) {
      found.push("accès LLM manquant");
    }
    if (
      workflow.llm_policy !== "disabled" &&
      !workflow.code_generation_profile
    ) {
      found.push("profil de génération manquant");
    }
    if (!workflow.steps.length) found.push("aucune étape");
    if (!workflow.steps.some((step) => step.assertion !== "none")) {
      found.push("aucune validation observable");
    }
    workflow.steps.forEach((step, index) => {
      if (!step.name) found.push(`nom de l’étape ${index + 1} manquant`);
      if (
        ["click", "fill", "select", "check", "uncheck", "upload"].includes(
          step.action,
        ) &&
        !step.target
      ) {
        found.push(`cible de l’étape ${index + 1} manquante`);
      }
      if (
        !["none", "url"].includes(step.assertion) &&
        !step.assertion_target
      ) {
        found.push(`cible de validation ${index + 1} manquante`);
      }
    });
    if (workflow.assumptions.length) found.push("hypothèses encore ouvertes");
    const confirmedSources = new Set(
      workflow.precondition_dependencies
        .filter((item) => item.confirmed)
        .map((item) => item.source),
    );
    workflow.setup.forEach((source) => {
      if (!confirmedSources.has(source)) {
        found.push(`traduction non confirmée : ${source}`);
      }
    });
    return found;
  }

  function updatePreview() {
    const workflow = buildWorkflow();
    const serialized = JSON.stringify(workflow, null, 2);
    workflowInput.value = JSON.stringify(workflow);
    preview.textContent = serialized;
    const problems = issues(workflow);
    readiness.textContent =
      workflow.confirmed && !problems.length
        ? "Prêt pour la génération"
        : `${problems.length} point${problems.length > 1 ? "s" : ""} à traiter`;
    readiness.classList.toggle(
      "ready",
      workflow.confirmed && !problems.length,
    );
    confirmation.setCustomValidity(
      workflow.confirmed && workflow.assumptions.length
        ? "Résolvez les hypothèses avant de confirmer la définition."
        : "",
    );
  }

  function wireCard(card) {
    card.querySelectorAll("input, select").forEach((control) => {
      control.addEventListener("input", updatePreview);
      control.addEventListener("change", updatePreview);
    });
    card
      .querySelectorAll('[data-field="target"], [data-field="assertion_target"]')
      .forEach((control) => {
        control.addEventListener("focus", () => {
          lastTargetInput = control;
        });
      });
    card.querySelector("[data-remove]").addEventListener("click", () => {
      if (stepsContainer.children.length === 1) {
        card.querySelectorAll("input").forEach((input) => {
          if (input.type === "checkbox") input.checked = false;
          else input.value = "";
        });
        field(card, "action").value = "click";
        field(card, "assertion").value = "visible";
      } else {
        card.remove();
      }
      renumber();
      updatePreview();
    });
    card.querySelector("[data-duplicate]").addEventListener("click", () => {
      const current = stepFromCard(card, stepsContainer.children.length);
      const duplicate = createCard({
        ...current,
        id: `step-${stepsContainer.children.length + 1}`,
        name: current.name ? `${current.name} — copie` : "",
      });
      card.after(duplicate);
      renumber();
      updatePreview();
    });
    card.querySelector("[data-add-validation]").addEventListener("click", () => {
      const current = stepFromCard(card, stepsContainer.children.length);
      const control = createCard({
        ...defaultStep(stepsContainer.children.length + 1),
        name: "Contrôler le résultat",
        page_url: current.page_url,
        action: "none",
        assertion: "visible",
      });
      card.after(control);
      renumber();
      updatePreview();
      control.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    card.querySelectorAll("[data-move]").forEach((button) => {
      button.addEventListener("click", () => {
        if (button.dataset.move === "up" && card.previousElementSibling) {
          card.previousElementSibling.before(card);
        }
        if (button.dataset.move === "down" && card.nextElementSibling) {
          card.nextElementSibling.after(card);
        }
        renumber();
        updatePreview();
      });
    });
  }

  function createCard(step) {
    const card = template.content.firstElementChild.cloneNode(true);
    [
      "name",
      "page_url",
      "precondition",
      "action",
      "target",
      "value",
      "assertion",
      "assertion_target",
      "expected",
    ].forEach((name) => {
      field(card, name).value = step[name] ?? "";
    });
    field(card, "evidence").checked = Boolean(step.evidence);
    wireCard(card);
    return card;
  }

  function renumber() {
    [...stepsContainer.children].forEach((card, index) => {
      card.querySelector("[data-step-number]").textContent = String(index + 1);
      card.dataset.stepId = `step-${index + 1}`;
      const up = card.querySelector('[data-move="up"]');
      const down = card.querySelector('[data-move="down"]');
      up.disabled = index === 0;
      down.disabled = index === stepsContainer.children.length - 1;
    });
  }

  function renderSteps(steps) {
    stepsContainer.replaceChildren();
    (steps.length ? steps : [defaultStep(1)]).forEach((step) => {
      stepsContainer.append(createCard(step));
    });
    renumber();
  }

  function renumberNarratives() {
    [...narrativeList.children].forEach((card, index) => {
      card.querySelector("[data-narrative-number]").textContent = String(index + 1);
    });
  }

  function createNarrativeCard(value = "") {
    const card = narrativeTemplate.content.firstElementChild.cloneNode(true);
    const control = card.querySelector("[data-step-narrative]");
    control.value = value;
    control.addEventListener("input", updatePreview);
    card.querySelector("[data-remove-narrative]").addEventListener("click", () => {
      if (narrativeList.children.length === 1) control.value = "";
      else card.remove();
      renumberNarratives();
      updatePreview();
    });
    return card;
  }

  function renderNarratives(values) {
    narrativeList.replaceChildren();
    (values.length ? values : [""]).forEach((value) => {
      narrativeList.append(createNarrativeCard(value));
    });
    renumberNarratives();
  }

  function createFixtureRow(value = "") {
    const row = fixtureTemplate.content.firstElementChild.cloneNode(true);
    const control = row.querySelector("[data-fixture-ref]");
    control.value = value;
    control.addEventListener("input", () => {
      syncFixtureInput();
      updatePreview();
    });
    row.querySelector("[data-remove-fixture]").addEventListener("click", () => {
      if (fixtureList.children.length === 1) control.value = "";
      else row.remove();
      syncFixtureInput();
      updatePreview();
    });
    return row;
  }

  function renderFixtureRefs(values) {
    fixtureList.replaceChildren();
    (values.length ? values : [""]).forEach((value) => {
      fixtureList.append(createFixtureRow(value));
    });
    syncFixtureInput();
  }

  function configurePreconditionReference(card) {
    const kind = card.querySelector("[data-precondition-kind]").value;
    const reference = card.querySelector("[data-precondition-reference]");
    const required = ["fixture", "technical_dependency"].includes(kind);
    reference.required = required;
    reference.closest("label").classList.toggle("required-field", required);
  }

  function createPreconditionDependency(item = {}) {
    const card = preconditionTemplate.content.firstElementChild.cloneNode(true);
    card.querySelector("[data-precondition-source]").value = item.source || "";
    card.querySelector("[data-precondition-kind]").value =
      item.kind || "verification";
    card.querySelector("[data-precondition-description]").value =
      item.description || item.source || "";
    card.querySelector("[data-precondition-reference]").value =
      item.reference || "";
    card.querySelector("[data-precondition-confirmed]").checked = Boolean(
      item.confirmed,
    );
    card.querySelector("[data-precondition-kind]").addEventListener("change", () => {
      configurePreconditionReference(card);
      card.querySelector("[data-precondition-confirmed]").checked = false;
      updatePreview();
    });
    card.querySelectorAll("input").forEach((control) => {
      if (!control.hasAttribute("readonly")) {
        control.addEventListener("input", () => {
          if (!control.hasAttribute("data-precondition-confirmed")) {
            card.querySelector("[data-precondition-confirmed]").checked = false;
          }
          updatePreview();
        });
        control.addEventListener("change", updatePreview);
      }
    });
    configurePreconditionReference(card);
    return card;
  }

  function renderPreconditionDependencies(values) {
    preconditionList.replaceChildren();
    values.forEach((value) => {
      preconditionList.append(createPreconditionDependency(value));
    });
    preconditionStatus.textContent = values.length
      ? `${values.length} traduction(s) à relire et confirmer.`
      : "Aucune précondition métier à traduire.";
  }

  function syncPreconditionDependencies() {
    const existing = new Map(
      collectPreconditionDependencies().map((item) => [item.source, item]),
    );
    const values = lines(document.querySelector("#setup-lines").value).map(
      (source) =>
        existing.get(source) || {
          source,
          kind: "verification",
          description: source,
          reference: "",
          confirmed: false,
        },
    );
    renderPreconditionDependencies(values);
    updatePreview();
  }

  function renderSystemReadiness(result) {
    readinessResults.replaceChildren();
    const summary = document.createElement("strong");
    summary.textContent = result.ready
      ? "Préparation vérifiée"
      : "Préparation bloquée";
    const list = document.createElement("ul");
    (result.checks || []).forEach((check) => {
      const item = document.createElement("li");
      item.className = `readiness-check readiness-${check.status}`;
      item.textContent = `${check.label} — ${check.detail}`;
      list.append(item);
    });
    readinessResults.append(summary, list);
  }

  async function checkSystemReadiness() {
    readinessButton.disabled = true;
    readinessResults.textContent = "Contrôle local en cours…";
    try {
      const body = new FormData();
      body.append("workflow_json", JSON.stringify(buildWorkflow()));
      const response = await fetch(assistantScript.dataset.readinessUrl, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          new DOMParser().parseFromString(text, "text/html").body.textContent.trim(),
        );
      }
      renderSystemReadiness(await response.json());
    } catch (error) {
      readinessResults.textContent =
        error.message || "Le contrôle de préparation a échoué.";
    } finally {
      readinessButton.disabled = false;
    }
  }

  function syncAuthoringPanels() {
    const mode = authoringMode();
    authoringPanels.forEach((panel) => {
      panel.hidden = panel.dataset.authoringPanel !== mode;
    });
    updatePreview();
  }

  function selectReference(reference) {
    if (lastTargetInput && document.contains(lastTargetInput)) {
      lastTargetInput.value = reference;
      lastTargetInput.dispatchEvent(new Event("input", { bubbles: true }));
      lastTargetInput.focus();
      return;
    }
    const firstEmpty = stepsContainer.querySelector(
      '[data-field="target"]:placeholder-shown, [data-field="assertion_target"]:placeholder-shown',
    );
    if (firstEmpty) {
      firstEmpty.value = reference;
      firstEmpty.dispatchEvent(new Event("input", { bubbles: true }));
      firstEmpty.focus();
    }
  }

  function renderPalette() {
    const elements = pages.flatMap((page) =>
      page.elements.map((element) => ({ ...element, pageTitle: page.title })),
    );
    fieldCount.textContent = String(elements.length);
    fieldOptions.replaceChildren();
    elements.forEach((element) => {
      const option = document.createElement("option");
      option.value = element.reference;
      option.label = `${element.label} · ${element.role}`;
      fieldOptions.append(option);
    });
    if (!elements.length) {
      fieldList.innerHTML =
        '<p class="empty-palette">Analysez une page pour afficher ses champs, boutons, liens et éléments vérifiables.</p>';
      return;
    }
    fieldList.replaceChildren();
    elements.forEach((element) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "page-field-card";
      const heading = document.createElement("span");
      heading.className = "page-field-card-heading";
      const label = document.createElement("strong");
      label.textContent = element.label;
      const role = document.createElement("span");
      role.className = "field-role";
      role.textContent = element.role;
      heading.append(label, role);
      const reference = document.createElement("code");
      reference.textContent = element.reference;
      const locator = document.createElement("small");
      locator.textContent = `${element.locator.strategy} · ${element.locator.value}`;
      button.append(heading, reference, locator);
      if (element.options?.length) {
        const options = document.createElement("small");
        options.textContent = `Options : ${element.options.join(", ")}`;
        button.append(options);
      }
      button.addEventListener("click", () =>
        selectReference(element.reference),
      );
      fieldList.append(button);
    });
  }

  const actionLabels = {
    click: "cliquer",
    fill: "saisir",
    select: "sélectionner",
    check: "cocher",
    uncheck: "décocher",
    upload: "téléverser",
  };

  const assertionLabels = {
    visible: "visibilité",
    hidden: "masquage",
    text: "texte",
    value: "valeur",
    enabled: "activation",
    checked: "état coché",
  };

  function emptyGuidance(container, message) {
    const paragraph = document.createElement("p");
    paragraph.className = "empty-palette";
    paragraph.textContent = message;
    container.replaceChildren(paragraph);
  }

  function focusGuidanceTarget(target) {
    const control =
      document.getElementById(target) ||
      form.querySelector(`[name="${CSS.escape(target)}"]`);
    if (!control) return;
    control.scrollIntoView({ behavior: "smooth", block: "center" });
    if (typeof control.focus === "function") control.focus();
  }

  function renderDesignGuidance(guidance) {
    const missing = guidance.missing_information || [];
    const fields = guidance.html_fields || [];
    missingInformationCount.textContent = String(missing.length);
    htmlCapabilitiesCount.textContent = String(fields.length);
    guidanceStatus.replaceChildren();
    const progress = document.createElement("strong");
    progress.textContent = `${guidance.completeness_percent}% du cadrage renseigné`;
    const explanation = document.createElement("span");
    explanation.textContent = missing.length
      ? `${missing.length} information${missing.length > 1 ? "s" : ""} utile${missing.length > 1 ? "s" : ""} à préciser avant la finalisation.`
      : "Les informations attendues par cette intention sont présentes.";
    guidanceStatus.append(progress, explanation);

    if (!missing.length) {
      emptyGuidance(
        missingInformationList,
        "Aucune question déterministe restante pour cette intention.",
      );
    } else {
      missingInformationList.replaceChildren();
      missing.forEach((item) => {
        const card = document.createElement("article");
        card.className = "guidance-card";
        const label = document.createElement("strong");
        label.textContent = item.label;
        const question = document.createElement("p");
        question.textContent = item.question;
        const utility = document.createElement("small");
        utility.textContent = `Utilité : ${item.utility}`;
        const focusButton = document.createElement("button");
        focusButton.type = "button";
        focusButton.className = "text-button";
        focusButton.textContent = "Compléter le champ concerné";
        focusButton.addEventListener("click", () =>
          focusGuidanceTarget(item.target),
        );
        card.append(label, question, utility, focusButton);
        missingInformationList.append(card);
      });
    }

    if (!fields.length) {
      emptyGuidance(
        htmlCapabilitiesList,
        "Analysez une page pour obtenir les actions et validations compatibles.",
      );
    } else {
      htmlCapabilitiesList.replaceChildren();
      fields.forEach((item) => {
        const card = document.createElement("article");
        card.className = "guidance-card html-guidance-card";
        const heading = document.createElement("div");
        heading.className = "guidance-card-heading";
        const label = document.createElement("strong");
        label.textContent = item.label;
        const role = document.createElement("span");
        role.className = "field-role";
        role.textContent = item.role;
        heading.append(label, role);
        const reference = document.createElement("code");
        reference.textContent = item.reference;
        const actions = document.createElement("p");
        actions.textContent = item.actions.length
          ? `Actions : ${item.actions.map((value) => actionLabels[value] || value).join(", ")}`
          : "Actions : aucune — élément destiné à l’observation";
        const assertions = document.createElement("p");
        assertions.textContent = `Validations : ${item.assertions
          .map((value) => assertionLabels[value] || value)
          .join(", ")}`;
        const utility = document.createElement("small");
        utility.textContent = item.utility;
        card.append(heading, reference, actions, assertions, utility);
        if (item.value_examples.length) {
          const values = document.createElement("small");
          values.textContent = `Valeurs possibles : ${item.value_examples.join(", ")}`;
          card.append(values);
        }
        const useButton = document.createElement("button");
        useButton.type = "button";
        useButton.className = "text-button";
        useButton.textContent = "Utiliser cette référence";
        useButton.addEventListener("click", () => selectReference(item.reference));
        card.append(useButton);
        htmlCapabilitiesList.append(card);
      });
    }
  }

  async function requestDesignGuidance() {
    if (!functionalIntent.value) {
      functionalIntent.reportValidity();
      guidanceStatus.querySelector("span").textContent =
        "Choisissez d’abord une intention fonctionnelle.";
      return;
    }
    guidanceButton.disabled = true;
    guidanceStatus.replaceChildren();
    const loading = document.createElement("strong");
    loading.textContent = "Analyse du brouillon…";
    guidanceStatus.append(loading);
    try {
      const body = new FormData();
      body.append("intent_reference", functionalIntent.value);
      body.append(
        "objective",
        form.querySelector('[name="objective"]').value.trim(),
      );
      body.append(
        "actor",
        form.querySelector('[name="actor_name"]').value.trim(),
      );
      body.append(
        "preconditions",
        form.querySelector('[name="preconditions"]').value,
      );
      body.append(
        "postconditions",
        form.querySelector('[name="postconditions"]').value,
      );
      body.append("workflow_json", JSON.stringify(buildWorkflow()));
      const response = await fetch(assistantScript.dataset.guidanceUrl, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          new DOMParser().parseFromString(text, "text/html").body.textContent.trim(),
        );
      }
      renderDesignGuidance(await response.json());
    } catch (error) {
      guidanceStatus.replaceChildren();
      const failure = document.createElement("strong");
      failure.textContent = "Diagnostic indisponible";
      const detail = document.createElement("span");
      detail.textContent = error.message || "Le diagnostic a échoué.";
      guidanceStatus.append(failure, detail);
    } finally {
      guidanceButton.disabled = false;
    }
  }

  function renderDialogue(dialogue) {
    const messages = dialogue.messages || [];
    if (!messages.length) {
      emptyGuidance(
        dialogueHistory,
        "Décrivez le comportement à préciser ou demandez au LLM de relire le brouillon.",
      );
    } else {
      dialogueHistory.replaceChildren();
      messages.forEach((message) => {
        const article = document.createElement("article");
        article.className = `dialogue-message ${message.role}`;
        const role = document.createElement("strong");
        role.textContent = message.role === "user" ? "Vous" : "Assistant";
        const content = document.createElement("p");
        content.textContent = message.content;
        article.append(role, content);
        dialogueHistory.append(article);
      });
    }

    proposalsContainer.replaceChildren();
    (dialogue.proposals || []).forEach((proposal) => {
      const article = document.createElement("article");
      article.className = "design-proposal";
      const heading = document.createElement("div");
      heading.className = "assistant-result-heading";
      const title = document.createElement("strong");
      title.textContent =
        proposal.status === "pending"
          ? "Proposition à décider"
          : "Proposition décidée";
      const state = document.createElement("span");
      state.className = "count-badge";
      state.textContent =
        proposal.status === "pending" ? "En attente" : "Décidée";
      heading.append(title, state);
      article.append(heading);

      if (proposal.questions?.length) {
        const questions = document.createElement("ul");
        questions.className = "proposal-questions";
        proposal.questions.forEach((question) => {
          const item = document.createElement("li");
          item.textContent = question;
          questions.append(item);
        });
        article.append(questions);
      }

      const operationList = document.createElement("div");
      operationList.className = "proposal-operation-list";
      (proposal.operations || []).forEach((operation) => {
        const row = document.createElement("label");
        row.className = "proposal-operation";
        if (proposal.status === "pending") {
          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.value = operation.id;
          checkbox.dataset.proposalOperation = "";
          row.append(checkbox);
        } else {
          const badge = document.createElement("span");
          badge.className = `operation-status ${operation.status}`;
          badge.textContent =
            operation.status === "accepted" ? "Acceptée" : "Refusée";
          row.append(badge);
        }
        const description = document.createElement("span");
        const label = document.createElement("strong");
        label.textContent = operation.label;
        const reason = document.createElement("small");
        reason.textContent = operation.reason;
        const value = document.createElement("code");
        value.textContent = `${operation.path} ← ${JSON.stringify(operation.value)}`;
        description.append(label, reason, value);
        row.append(description);
        operationList.append(row);
      });
      article.append(operationList);

      if (proposal.status === "pending") {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "secondary-button";
        button.textContent = "Appliquer la sélection";
        button.addEventListener("click", () =>
          decideProposal(proposal.id, article, button),
        );
        article.append(button);
      }
      proposalsContainer.append(article);
    });
  }

  function applyDraft(draft, summary) {
    form.querySelector('[name="objective"]').value = draft.objective || "";
    form.querySelector('[name="actor_name"]').value = draft.actor || "";
    document.querySelector("#setup-lines").value =
      (draft.preconditions || []).join("\n");
    document.querySelector("#cleanup-lines").value =
      (draft.postconditions || []).join("\n");
    document.querySelector("#requirements-lines").value =
      (draft.requirements || []).join("\n");
    document.querySelector("#business-rules-lines").value =
      (draft.business_rules || []).join("\n");
    document.querySelector("#case-summary").value = summary || draft.summary || "";

    const workflow = draft.workflow || {};
    document.querySelector("#setup-lines").value =
      (workflow.setup || draft.preconditions || []).join("\n");
    document.querySelector("#cleanup-lines").value =
      (workflow.cleanup || draft.postconditions || []).join("\n");
    renderFixtureRefs(workflow.fixture_refs || draft.data_sets || []);
    document.querySelector("#start-url").value = workflow.start_url || "";
    document.querySelector("#environment-profile").value =
      workflow.environment_profile || "";
    document.querySelector("#actor-profile").value =
      workflow.actor_profile || "";
    functionalIntent.value = workflow.functional_intent || "";
    document.querySelector("#secret-refs").value =
      (workflow.secret_refs || []).join("\n");
    document.querySelector("#assumptions").value =
      (workflow.assumptions || []).join("\n");
    document.querySelector("#evidence-policy").value =
      workflow.evidence_policy || "on_failure";
    document.querySelector("#llm-policy").value =
      workflow.llm_policy || "design_only";
    document.querySelector("#llm-access-profile").value =
      workflow.llm_access_profile || "";
    document.querySelector("#code-generation-profile").value =
      workflow.code_generation_profile || "";
    document.querySelector("#timeout-seconds").value =
      workflow.timeout_seconds || 30;
    renderPreconditionDependencies(
      Array.isArray(workflow.precondition_dependencies)
        ? workflow.precondition_dependencies
        : [],
    );
    syncPreconditionDependencies();
    confirmation.checked = Boolean(workflow.confirmed);
    const requestedMode = workflow.authoring_mode || "form";
    const modeInput = authoringModeInputs.find(
      (input) => input.value === requestedMode,
    );
    if (modeInput) modeInput.checked = true;
    renderNarratives(
      Array.isArray(workflow.step_narratives)
        ? workflow.step_narratives
        : [],
    );
    scenarioNarrative.value = workflow.scenario_narrative || "";
    pages.splice(
      0,
      pages.length,
      ...(Array.isArray(workflow.pages) ? workflow.pages : []),
    );
    renderSteps(Array.isArray(workflow.steps) ? workflow.steps : []);
    syncAuthoringPanels();
    renderPalette();
    updatePreview();
  }

  async function decideProposal(proposalId, article, button) {
    const accepted = [
      ...article.querySelectorAll("[data-proposal-operation]:checked"),
    ].map((checkbox) => checkbox.value);
    button.disabled = true;
    dialogueStatus.textContent = "Application de la décision…";
    try {
      const body = new FormData();
      body.append("accepted_operation_ids", JSON.stringify(accepted));
      body.append("draft_json", JSON.stringify(buildDraft()));
      const response = await fetch(
        `${assistantScript.dataset.decisionUrl}/${proposalId}/decision`,
        { method: "POST", body },
      );
      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          new DOMParser().parseFromString(text, "text/html").body.textContent.trim(),
        );
      }
      const result = await response.json();
      applyDraft(result.draft, result.summary);
      renderDialogue(result.dialogue);
      dialogueStatus.textContent =
        "Décision enregistrée. La description a été reconstruite depuis les données acceptées.";
    } catch (error) {
      dialogueStatus.textContent =
        error.message || "La décision n’a pas pu être appliquée.";
      button.disabled = false;
    }
  }

  async function exchangeDesignMessage() {
    if (!designMessage.value.trim()) {
      designMessage.setCustomValidity("Saisissez un message.");
      designMessage.reportValidity();
      designMessage.setCustomValidity("");
      return;
    }
    sendDesignMessage.disabled = true;
    dialogueStatus.textContent = "Préparation des questions et propositions…";
    try {
      const body = new FormData();
      body.append("message", designMessage.value.trim());
      body.append("draft_json", JSON.stringify(buildDraft()));
      const response = await fetch(assistantScript.dataset.dialogueUrl, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          new DOMParser().parseFromString(text, "text/html").body.textContent.trim(),
        );
      }
      renderDialogue(await response.json());
      designMessage.value = "";
      dialogueStatus.textContent =
        "Réponse reçue. Vérifiez chaque proposition avant de l’accepter.";
    } catch (error) {
      dialogueStatus.textContent =
        error.message || "Le dialogue LLM n’est pas disponible.";
    } finally {
      sendDesignMessage.disabled = false;
    }
  }

  document.querySelector("#add-step").addEventListener("click", () => {
    stepsContainer.append(createCard(defaultStep(stepsContainer.children.length + 1)));
    renumber();
    updatePreview();
    stepsContainer.lastElementChild.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  });

  document.querySelector("#add-step-narrative").addEventListener("click", () => {
    const card = createNarrativeCard();
    narrativeList.append(card);
    renumberNarratives();
    updatePreview();
    card.querySelector("textarea").focus();
  });

  document.querySelector("#add-fixture-ref").addEventListener("click", () => {
    const row = createFixtureRow();
    fixtureList.append(row);
    syncFixtureInput();
    updatePreview();
    row.querySelector("input").focus();
  });

  document
    .querySelector("#sync-precondition-dependencies")
    .addEventListener("click", syncPreconditionDependencies);
  readinessButton.addEventListener("click", checkSystemReadiness);

  authoringModeInputs.forEach((input) => {
    input.addEventListener("change", syncAuthoringPanels);
  });

  document.querySelectorAll("[data-assist-mode]").forEach((button) => {
    button.addEventListener("click", async () => {
      designMessage.value = button.dataset.assistPrompt;
      await exchangeDesignMessage();
    });
  });

  document
    .querySelector("#code-generation-profile")
    .addEventListener("change", (event) => {
      const selected = event.target.selectedOptions[0];
      if (selected?.dataset.llmProfile) {
        document.querySelector("#llm-access-profile").value =
          selected.dataset.llmProfile;
      }
      updatePreview();
    });

  analysisButton.addEventListener("click", async () => {
    const pageUrl = analysisUrl.value.trim();
    if (!pageUrl) {
      analysisUrl.reportValidity();
      return;
    }
    analysisButton.disabled = true;
    analysisStatus.textContent = "Analyse en cours…";
    try {
      const body = new FormData();
      body.append("page_url", pageUrl);
      const response = await fetch(
        document.currentScript?.dataset.analysisUrl ||
          document.querySelector('script[data-analysis-url]').dataset.analysisUrl,
        { method: "POST", body },
      );
      if (!response.ok) {
        const text = await response.text();
        throw new Error(
          new DOMParser().parseFromString(text, "text/html").body.textContent.trim(),
        );
      }
      const page = await response.json();
      const existing = pages.findIndex((item) => item.url === page.url);
      if (existing >= 0) pages.splice(existing, 1, page);
      else pages.push(page);
      analysisStatus.textContent = `${page.elements.length} élément(s) utilisable(s) détecté(s).`;
      renderPalette();
      updatePreview();
      if (functionalIntent.value) await requestDesignGuidance();
    } catch (error) {
      analysisStatus.textContent = error.message || "L’analyse a échoué.";
    } finally {
      analysisButton.disabled = false;
    }
  });

  guidanceButton.addEventListener("click", requestDesignGuidance);
  sendDesignMessage.addEventListener("click", exchangeDesignMessage);
  document.querySelectorAll("[data-design-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      designMessage.value = button.dataset.designPrompt;
      designMessage.focus();
    });
  });
  functionalIntent.addEventListener("change", () => {
    updatePreview();
    if (functionalIntent.value) requestDesignGuidance();
  });

  document.querySelector("#copy-workflow").addEventListener("click", async () => {
    await navigator.clipboard.writeText(preview.textContent);
    const button = document.querySelector("#copy-workflow");
    const previous = button.textContent;
    button.textContent = "Structure copiée";
    setTimeout(() => {
      button.textContent = previous;
    }, 1600);
  });

  form.addEventListener("input", updatePreview);
  form.addEventListener("change", updatePreview);
  form.addEventListener("submit", (event) => {
    updatePreview();
    if (!form.checkValidity()) {
      event.preventDefault();
      form.reportValidity();
    }
  });

  renderSteps(Array.isArray(initial.steps) ? initial.steps : []);
  renderNarratives(
    Array.isArray(initial.step_narratives) && initial.step_narratives.length
      ? initial.step_narratives
      : (initial.steps || []).map(stepToNarrative),
  );
  scenarioNarrative.value =
    initial.scenario_narrative ||
    (initial.authoring_mode === "scenario_text"
      ? (initial.steps || []).map(stepToNarrative).join("\n\n")
      : "");
  renderFixtureRefs(
    Array.isArray(initial.fixture_refs)
      ? initial.fixture_refs
      : lines(fixtureInput.value),
  );
  renderPreconditionDependencies(
    Array.isArray(initial.precondition_dependencies)
      ? initial.precondition_dependencies
      : [],
  );
  syncPreconditionDependencies();
  syncAuthoringPanels();
  renderPalette();
  renderDialogue(dialogueInitial);
  updatePreview();
  if (functionalIntent.value) requestDesignGuidance();
})();
