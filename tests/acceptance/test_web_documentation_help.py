"""Documentation intégrée et aide contextuelle de tous les formulaires."""

from __future__ import annotations

import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class _HelpCoverageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.forms = 0
        self.form_help = 0
        self.visible_fields = 0
        self.field_labels = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "form":
            self.forms += 1
        if "form-help" in classes:
            self.form_help += 1
        if "field-label" in classes:
            self.field_labels += 1
        if tag in {"input", "select", "textarea"}:
            if "data-theme-selector" in attributes:
                return
            if tag != "input" or attributes.get("type", "text") != "hidden":
                self.visible_fields += 1


class WebDocumentationHelpAcceptanceTests(unittest.TestCase):
    def test_documentation_is_embedded_and_all_visible_fields_have_help(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinelle.db"
            )
            with TestClient(create_web_app(settings)) as client:
                documentation = client.get("/documentation")
                self.assertEqual(200, documentation.status_code)
                for expected in (
                    "Documentation fonctionnelle",
                    "Projet",
                    "Plan de test",
                    "Suites de tests et dossiers",
                    "Cas de test",
                    "GitLab CI et GitHub Actions",
                    "GITLAB_BASE_URL",
                    "OpenAI, Ollama et",
                    "Mistral sont les fournisseurs attendus",
                    "Connexion à OpenAI",
                    "Connexion à Ollama",
                    "Connexion à Mistral",
                    "astérisque rouge",
                    "Présentation, ajout progressif et thèmes",
                    "Contraste élevé",
                    "Défense — ministère des Armées",
                    "Ministère des Armées et des Anciens combattants",
                    "pictogramme Rafale",
                    "Prompt final et code candidat",
                    "Skills",
                    "Ouvrir le prompt de génération",
                ):
                    self.assertIn(expected, documentation.text)

                stylesheet = client.get("/static/app.css")
                self.assertEqual(200, stylesheet.status_code)
                self.assertIn(
                    "label:has(input:required, select:required, textarea:required)",
                    stylesheet.text,
                )
                self.assertIn('* Champs obligatoires', stylesheet.text)
                self.assertIn('html[data-theme="ocean"]', stylesheet.text)
                self.assertIn('html[data-theme="high-contrast"]', stylesheet.text)
                self.assertIn('html[data-theme="defense"]', stylesheet.text)

                tutorial = client.get("/tutorials/test-case")
                self.assertEqual(200, tutorial.status_code)
                self.assertIn("Se repérer dans l’interface", tutorial.text)
                self.assertIn("+ Ajouter un projet", tutorial.text)
                self.assertIn("Voir les skills du prompt de génération", tutorial.text)
                self.assertIn("&lt;secret-value-redacted&gt;", tutorial.text)

                home = client.get("/")
                self._assert_help_coverage(home.text)
                self.assertIn('href="/documentation"', home.text)

                llm_configuration = client.get("/configuration/llm-access")
                self._assert_help_coverage(llm_configuration.text)
                self.assertIn(
                    "Aucun secret n’est enregistré",
                    llm_configuration.text,
                )

                code_configuration = client.get(
                    "/configuration/code-generation"
                )
                self._assert_help_coverage(code_configuration.text)
                self.assertNotIn(
                    "Aucun secret n’est enregistré",
                    code_configuration.text,
                )

                project_response = client.post(
                    "/projects",
                    data={
                        "name": "Portail citoyen",
                        "description": "Parcours critiques",
                        "web_target": "https://portail.demo.invalid",
                        "security_policy": "demo-only",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project_response.headers["location"].split("/")[-1])
                project_page = client.get(f"/projects/{project_id}")
                self._assert_help_coverage(project_page.text)

                plan_response = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Commande",
                        "objective": "Valider la commande",
                        "scope": "Panier et paiement",
                        "test_approach": "functional-risk-based@1",
                        "target": "https://portail.demo.invalid",
                    },
                    follow_redirects=False,
                )
                plan_id = UUID(plan_response.headers["x-created-id"])
                folder_response = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "folder",
                        "name": "Commande",
                        "tags": "parcours",
                    },
                    follow_redirects=False,
                )
                folder_id = UUID(folder_response.headers["x-created-id"])
                suite_response = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "suite",
                        "name": "Parcours nominal",
                        "objective": "Valider le parcours nominal",
                        "parent_id": str(folder_id),
                    },
                    follow_redirects=False,
                )
                suite_id = UUID(suite_response.headers["x-created-id"])
                case_response = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Paiement accepté",
                        "parent_id": str(suite_id),
                    },
                    follow_redirects=False,
                )
                case_id = UUID(case_response.headers["x-created-id"])

                unified_page = client.get(f"/projects/{project_id}")
                self._assert_help_coverage(unified_page.text)
                self.assertIn("Plans, dossiers, suites et cas", unified_page.text)
                self.assertIn("Modifier le plan", unified_page.text)
                self.assertNotIn("Modifier le projet", unified_page.text)
                hierarchy_positions = [
                    unified_page.text.index(identifier)
                    for identifier in (
                        f'id="plan-{plan_id}"',
                        f'id="node-{folder_id}"',
                        f'id="node-{suite_id}"',
                        f'id="node-{case_id}"',
                    )
                ]
                self.assertEqual(sorted(hierarchy_positions), hierarchy_positions)

                plan_page = client.get(
                    f"/projects/{project_id}/test-plans/{plan_id}"
                )
                self._assert_help_coverage(plan_page.text)
                self.assertNotIn('class="flow-strip"', plan_page.text)
                self.assertIn("Nouveau dossier", plan_page.text)
                self.assertIn(
                    'aria-label="Ajouter une suite de tests dans Commande"',
                    plan_page.text,
                )
                self.assertIn(
                    'aria-label="Ajouter un cas de test dans Parcours nominal"',
                    plan_page.text,
                )
                self.assertIn(
                    f'name="parent_id" value="{folder_id}"',
                    plan_page.text,
                )
                self.assertIn(
                    f'name="parent_id" value="{suite_id}"',
                    plan_page.text,
                )
                self.assertIn(
                    'aria-label="Modifier le plan de test"',
                    plan_page.text,
                )
                self.assertIn(
                    'id="plan-settings"',
                    plan_page.text,
                )
                case_page = client.get(
                    f"/projects/{project_id}/test-plans/{plan_id}/cases/{case_id}"
                )
                self._assert_help_coverage(case_page.text)

    def _assert_help_coverage(self, html: str) -> None:
        parser = _HelpCoverageParser()
        parser.feed(html)
        self.assertGreater(parser.forms, 0)
        self.assertEqual(parser.forms, parser.form_help)
        self.assertEqual(parser.visible_fields, parser.field_labels)
        self.assertIn("Ouvrir la documentation", html)
        self.assertIn("ℹ", html)
        self.assertNotIn("Aide du formulaire", html)
        self.assertNotIn('aria-label="Aide :', html)
