"""ACC-074 à ACC-077 — rédaction guidée prête pour la génération."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.domain import GenerationWorkflowInput, WorkflowError
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


LOGIN_HTML = """<!doctype html>
<html lang="fr">
  <head><title>Connexion</title></head>
  <body>
    <main>
      <h1>Se connecter</h1>
      <label for="email">Adresse électronique</label>
      <input id="email" name="email" type="email" placeholder="client@example.net">
      <label>
        Mot de passe
        <input name="password" type="password">
      </label>
      <label for="profile">Profil</label>
      <select id="profile" name="profile">
        <option value="customer">Client</option>
        <option value="manager">Responsable</option>
      </select>
      <button type="submit">Se connecter</button>
      <a href="/forgotten-password">Mot de passe oublié</a>
    </main>
  </body>
</html>
"""


class GuidedWorkflowEditorAcceptanceTests(unittest.TestCase):
    def test_narrative_modes_accept_a_draft_but_require_structured_steps_to_confirm(self) -> None:
        narrative = {
            "schema_version": 1,
            "start_url": "https://editor.demo.invalid/login",
            "environment_profile": "recette-eu",
            "actor_profile": "client",
            "functional_intent": "",
            "fixture_refs": [],
            "secret_refs": [],
            "setup": [],
            "cleanup": [],
            "evidence_policy": "on_failure",
            "llm_policy": "disabled",
            "llm_access_profile": "",
            "code_generation_profile": "",
            "timeout_seconds": 30,
            "assumptions": [],
            "authoring_mode": "scenario_text",
            "step_narratives": [],
            "scenario_narrative": (
                "Le client saisit ses identifiants puis contrôle son tableau de bord."
            ),
            "confirmed": False,
            "pages": [],
            "steps": [],
        }

        draft = GenerationWorkflowInput.from_mapping(narrative)

        self.assertEqual("scenario_text", draft.authoring_mode.value)
        self.assertEqual((), draft.steps)
        with self.assertRaisesRegex(WorkflowError, "structuré avant confirmation"):
            GenerationWorkflowInput.from_mapping({**narrative, "confirmed": True})

    def test_html_page_analysis_exposes_stable_business_fields(self) -> None:
        page = analyze_html_page(
            "https://editor.demo.invalid/login",
            LOGIN_HTML,
        )

        self.assertEqual("Connexion", page.title)
        by_label = {element.label: element for element in page.elements}
        self.assertEqual("textbox", by_label["Adresse électronique"].role)
        self.assertEqual("label", by_label["Adresse électronique"].locator.strategy)
        self.assertEqual("Mot de passe", by_label["Mot de passe"].label)
        self.assertEqual(("Client", "Responsable"), by_label["Profil"].options)
        self.assertEqual("button", by_label["Se connecter"].role)
        self.assertTrue(
            all(element.reference.startswith("page:login#") for element in page.elements)
        )

    def test_html_page_analysis_ignores_help_content_nested_in_a_label(self) -> None:
        page = analyze_html_page(
            "https://editor.demo.invalid/form",
            """
            <label>
              <details class="information-disclosure field-label field-help">
                <summary aria-label="Informations : Adresse électronique">
                  <span aria-hidden="true">ℹ</span>
                  <span>Adresse électronique</span>
                </summary>
                <div>
                  <p>Adresse utilisée pour la connexion.</p>
                  <a href="/documentation#email">Ouvrir la documentation</a>
                </div>
              </details>
              <input id="email" name="email" type="email">
            </label>
            """,
        )

        self.assertEqual(1, len(page.elements))
        self.assertEqual("Adresse électronique", page.elements[0].label)
        self.assertEqual("label", page.elements[0].locator.strategy)

    def test_editor_analyzes_page_saves_workflow_and_exposes_tutorial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinelle.db"
            )
            app = create_web_app(settings)
            app.state.page_loader = lambda _url, **_policy: LOGIN_HTML
            with TestClient(app) as client:
                home = client.get("/")
                self.assertIn('href="/tutorials/test-case"', home.text)
                self.assertIn("Rédiger un cas de test", home.text)

                tutorial = client.get("/tutorials/test-case")
                self.assertEqual(200, tutorial.status_code)
                for expected in (
                    "Configurer le projet",
                    "Traduire et confirmer les préconditions",
                    "Vérifier la préparation",
                    "Analyser une page",
                    "Ajouter et ordonner les étapes",
                    "Finaliser avec le LLM",
                    "Structure de génération",
                    "{{data.email}}",
                ):
                    self.assertIn(expected, tutorial.text)

                project = client.post(
                    "/projects",
                    data={
                        "name": "Éditeur guidé",
                        "description": "Génération Playwright",
                        "web_target": "https://editor.demo.invalid",
                        "security_policy": "same-origin",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
                plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Connexion",
                        "objective": "Valider l'accès",
                        "scope": "Authentification",
                        "test_approach": "automated-regression@1",
                        "target": "https://editor.demo.invalid",
                    },
                    follow_redirects=False,
                )
                plan_id = UUID(plan.headers["x-created-id"])
                suite = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "suite",
                        "name": "Accès client",
                        "objective": "Vérifier la connexion",
                    },
                    follow_redirects=False,
                )
                suite_id = UUID(suite.headers["x-created-id"])
                case = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Connexion acceptée",
                        "parent_id": str(suite_id),
                    },
                    follow_redirects=False,
                )
                case_id = UUID(case.headers["x-created-id"])
                case_url = (
                    f"/projects/{project_id}/test-plans/{plan_id}/cases/{case_id}"
                )

                editor = client.get(case_url)
                self.assertIn("Mode de saisie des étapes", editor.text)
                for expected in (
                    "Ajouter une action",
                    "Un texte par étape",
                    "Description complète du parcours",
                    "Ajouter une donnée",
                    "Ajouter un contrôle à la suite",
                    "Voir le prompt et le skill utilisés",
                    "analyze-form-test-steps",
                    "Prompt de cadrage",
                    "Analyser la page",
                    "Champs utilisables de la page",
                    "Structure envoyée au générateur",
                    "Profil d’acteur",
                    "Politique LLM",
                    "Traduction des préconditions",
                    "Préparer les traductions",
                    "Vérifier la préparation",
                    "Le LLM ne peut pas modifier ces résultats",
                    "{{data.colonne}}",
                    "page:connexion#email",
                ):
                    self.assertIn(expected, editor.text)

                analysis = client.post(
                    f"{case_url}/page-analysis",
                    data={"page_url": "https://editor.demo.invalid/login"},
                )
                self.assertEqual(200, analysis.status_code)
                payload = analysis.json()
                self.assertEqual("Connexion", payload["title"])
                self.assertIn(
                    "Adresse électronique",
                    {element["label"] for element in payload["elements"]},
                )
                login_button_reference = next(
                    element["reference"]
                    for element in payload["elements"]
                    if element["label"] == "Se connecter"
                )
                forbidden_analysis = client.post(
                    f"{case_url}/page-analysis",
                    data={"page_url": "https://other.invalid/login"},
                )
                self.assertEqual(400, forbidden_analysis.status_code)
                self.assertIn(
                    "doit appartenir à la cible web du projet",
                    forbidden_analysis.text,
                )

                workflow = {
                    "schema_version": 1,
                    "start_url": "https://editor.demo.invalid/login",
                    "environment_profile": "recette-eu",
                    "actor_profile": "client-authentifie",
                    "functional_intent": "authentication-login-success@1",
                    "fixture_refs": ["client-standard"],
                    "secret_refs": ["client-password"],
                    "setup": ["Le compte client actif existe"],
                    "cleanup": ["Fermer la session"],
                    "evidence_policy": "on_failure",
                    "llm_policy": "design_only",
                    "timeout_seconds": 30,
                    "assumptions": [],
                    "confirmed": True,
                    "pages": [payload],
                    "steps": [
                        {
                            "id": "step-1",
                            "name": "Ouvrir la connexion",
                            "page_url": "https://editor.demo.invalid/login",
                            "precondition": "",
                            "action": "navigate",
                            "target": "",
                            "value": "",
                            "assertion": "visible",
                            "assertion_target": login_button_reference,
                            "expected": "Se connecter",
                            "evidence": False,
                        },
                        {
                            "id": "step-2",
                            "name": "Saisir l’adresse",
                            "page_url": "https://editor.demo.invalid/login",
                            "precondition": "La page de connexion est visible",
                            "action": "fill",
                            "target": "page:login#email",
                            "value": "{{data.email}}",
                            "assertion": "value",
                            "assertion_target": "page:login#email",
                            "expected": "{{data.email}}",
                            "evidence": True,
                        },
                    ],
                }
                readiness = client.post(
                    f"{case_url}/readiness",
                    data={"workflow_json": json.dumps(workflow)},
                )
                self.assertEqual(200, readiness.status_code, readiness.text)
                readiness_payload = readiness.json()
                self.assertFalse(readiness_payload["ready"])
                self.assertIn(
                    "secret-references",
                    {check["code"] for check in readiness_payload["checks"]},
                )
                saved = client.post(
                    f"{case_url}/specification",
                    data={
                        "objective": "Connecter un client actif",
                        "actor_name": "Client",
                        "environment": "recette-eu",
                        "preconditions": "Le compte existe",
                        "data_sets": "client-standard",
                        "postconditions": "La session est ouverte",
                        "requirements": "REQ-AUTH-01",
                        "business_rules": "BR-AUTH-01",
                        "execution_declaration": "on_merge_request",
                        "workflow_json": json.dumps(workflow),
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, saved.status_code)

                restored_editor = client.get(case_url)
                self.assertIn("Version 1", restored_editor.text)
                self.assertIn("page:login#email", restored_editor.text)
                self.assertIn("client-authentifie", restored_editor.text)
                self.assertIn(
                    "authentication-login-success@1",
                    restored_editor.text,
                )
                self.assertIn("Télécharger le code généré", restored_editor.text)

                generated = client.get(f"{case_url}/generated-code")
                self.assertEqual(200, generated.status_code, generated.text)
                self.assertIn(
                    "attachment; filename=",
                    generated.headers["content-disposition"],
                )
                self.assertIn("from playwright.sync_api import", generated.text)
                self.assertIn("def test_case_", generated.text)
                self.assertNotIn("<pre", generated.text)

            with TestClient(create_web_app(settings)) as restarted:
                restored_case = (
                    restarted.app.state.project_application.get_project(None, project_id)
                    .test_plan(plan_id)
                    .node(case_id)
                )
                self.assertEqual(2, len(restored_case.specification.workflow.steps))
                self.assertEqual(
                    "client-authentifie",
                    restored_case.specification.workflow.actor_profile,
                )
                self.assertEqual(
                    "authentication-login-success@1",
                    restored_case.specification.workflow.functional_intent,
                )
                self.assertTrue(restored_case.specification.workflow.confirmed)


if __name__ == "__main__":
    unittest.main()
