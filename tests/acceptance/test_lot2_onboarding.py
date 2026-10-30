"""Lot 2 — démarrage guidé, erreurs utiles et accessibilité des formulaires."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class Lot2OnboardingAcceptanceTests(unittest.TestCase):
    def test_home_exposes_safe_defaults_progress_and_compact_administration(
        self,
    ) -> None:
        with self._client() as client:
            response = client.get("/")

        self.assertEqual(200, response.status_code)
        self.assertIn("Projet → Plan → Cas → Validation", response.text)
        self.assertIn('class="admin-menu"', response.text)
        self.assertIn("<summary>Administration</summary>", response.text)
        self.assertIn('value="http://127.0.0.1:8000/demo/hr"', response.text)
        self.assertIn('value="demo-only same-origin local-loopback"', response.text)

    def test_invalid_project_is_redisplayed_with_inline_errors(self) -> None:
        with self._client() as client:
            response = client.post(
                "/projects",
                data={
                    "name": "",
                    "description": "À conserver",
                    "web_target": "ftp://example.test",
                    "security_policy": "",
                },
            )

        self.assertEqual(422, response.status_code)
        self.assertIn(
            'id="new-project" class="panel form-panel entity-create-panel"',
            response.text,
        )
        self.assertNotIn('entity-create-panel" hidden', response.text)
        self.assertIn('id="project-name-error" role="alert"', response.text)
        self.assertIn('id="project-web-target-error" role="alert"', response.text)
        self.assertIn('id="project-security-policy-error" role="alert"', response.text)
        self.assertIn('aria-invalid="true"', response.text)
        self.assertIn("À conserver", response.text)

    def test_first_case_shortcut_hides_the_organizational_scaffolding(self) -> None:
        with self._client() as client:
            project = client.post(
                "/projects",
                data={
                    "name": "Portail local",
                    "description": "Parcours principal",
                    "web_target": "http://127.0.0.1:8000/demo/hr",
                    "security_policy": "demo-only same-origin local-loopback",
                },
                follow_redirects=False,
            )
            project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
            plan = client.post(
                f"/projects/{project_id}/test-plans",
                data={
                    "name": "Validation RH",
                    "objective": "Valider la consultation d'un dossier",
                    "scope": "Connexion et consultation",
                    "test_approach": "functional-risk-based@1",
                    "target": "http://127.0.0.1:8000/demo/hr",
                },
                follow_redirects=False,
            )
            plan_id = UUID(plan.headers["x-created-id"])
            self.assertEqual(
                f"/projects/{project_id}/test-plans/{plan_id}",
                plan.headers["location"],
            )

            plan_page = client.get(f"/projects/{project_id}/test-plans/{plan_id}")
            self.assertIn("Créer mon premier cas", plan_page.text)

            created = client.post(
                f"/projects/{project_id}/test-plans/{plan_id}/first-case",
                data={"name": "Consulter un dossier agent"},
                follow_redirects=False,
            )
            case_id = UUID(created.headers["x-created-id"])
            case_page = client.get(created.headers["location"])

            self.assertEqual(303, created.status_code)
            self.assertIn("Consulter un dossier agent", case_page.text)
            self.assertIn("Projet → Plan → Cas → Validation", case_page.text)
            self.assertIn('id="workflow-confirmed"', case_page.text)
            stored_plan = client.app.state.project_application.get_project(
                None, project_id
            ).test_plan(plan_id)
            self.assertEqual(2, len(stored_plan.nodes))
            self.assertEqual("Parcours principal", stored_plan.path(case_id)[0])

    def test_field_help_is_not_an_interactive_control_nested_in_a_label(self) -> None:
        with self._client() as client:
            home = client.get("/")
            script = client.get("/static/app.js")

        self.assertNotIn(
            '<details class="information-disclosure field-label field-help">', home.text
        )
        self.assertIn('class="field-help" data-field-help', home.text)
        self.assertIn("label.htmlFor = control.id", script.text)
        self.assertIn('control.setAttribute("aria-describedby"', script.text)

    def _client(self) -> TestClient:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        settings = ServerSettings(
            database=Path(temporary_directory.name) / "state" / "sentinelle.db"
        )
        return TestClient(create_web_app(settings))


if __name__ == "__main__":
    unittest.main()
