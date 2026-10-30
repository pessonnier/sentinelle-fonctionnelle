"""ACC-032 et préparation ACC-007 — assistant de conception guidé."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.domain import (
    FunctionalIntentCatalog,
    build_design_guidance,
)
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


LOGIN_HTML = """<!doctype html>
<html lang="fr">
  <head><title>Connexion</title></head>
  <body>
    <h1>Se connecter</h1>
    <label for="email">Adresse électronique</label>
    <input id="email" name="email" type="email">
    <label for="password">Mot de passe</label>
    <input id="password" name="password" type="password">
    <label for="remember">Mémoriser la session</label>
    <input id="remember" name="remember" type="checkbox">
    <button type="submit">Se connecter</button>
  </body>
</html>
"""


class DesignGuidanceAcceptanceTests(unittest.TestCase):
    def test_catalog_drives_missing_questions_and_html_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog = FunctionalIntentCatalog.open(
                Path(temporary_directory) / "test-intents.yaml",
                defaults_path=(
                    Path(__file__).parents[2]
                    / "src"
                    / "sentinelle_fonctionnelle"
                    / "configuration"
                    / "test-intents.yaml"
                ),
            )
            intent = catalog.get("authentication-login-success", 1)
            self.assertEqual(
                "Se connecter avec succès",
                intent.label,
            )
            self.assertGreaterEqual(len(catalog.current_intents()), 13)

            page = analyze_html_page(
                "https://editor.demo.invalid/login",
                LOGIN_HTML,
            )
            guidance = build_design_guidance(
                intent=intent,
                objective="",
                actor="",
                preconditions=(),
                postconditions=(),
                workflow={
                    "start_url": "https://editor.demo.invalid/login",
                    "fixture_refs": [],
                    "secret_refs": [],
                    "pages": [page.as_dict()],
                    "steps": [],
                },
            )

            missing_keys = {item.key for item in guidance.missing_information}
            self.assertIn("objective", missing_keys)
            self.assertIn("actor", missing_keys)
            self.assertIn("credentials", missing_keys)
            self.assertIn("observable-result", missing_keys)
            self.assertTrue(
                all(item.question and item.utility for item in guidance.missing_information)
            )

            by_label = {
                item.label: item for item in guidance.html_fields
            }
            self.assertEqual(("fill",), by_label["Adresse électronique"].actions)
            self.assertIn("value", by_label["Adresse électronique"].assertions)
            self.assertEqual(
                ("check", "uncheck"),
                by_label["Mémoriser la session"].actions,
            )
            self.assertEqual(("click",), by_label["Se connecter"].actions)
            self.assertEqual((), by_label["Se connecter"].value_examples)

    def test_editor_exposes_guidance_documentation_and_tutorial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinelle.db"
            )
            app = create_web_app(settings)
            with TestClient(app) as client:
                project = client.post(
                    "/projects",
                    data={
                        "name": "Assistant guidé",
                        "description": "Dialogue de conception",
                        "web_target": "https://editor.demo.invalid",
                        "security_policy": "same-origin",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
                plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Authentification",
                        "objective": "Valider la connexion",
                        "scope": "Connexion",
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
                        "name": "Connexion",
                        "objective": "Regrouper les parcours de connexion",
                    },
                    follow_redirects=False,
                )
                case = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Connexion acceptée",
                        "parent_id": suite.headers["x-created-id"],
                    },
                    follow_redirects=False,
                )
                case_id = UUID(case.headers["x-created-id"])
                case_url = (
                    f"/projects/{project_id}/test-plans/{plan_id}/cases/{case_id}"
                )

                editor = client.get(case_url)
                for expected in (
                    "Assistant de conception",
                    "Intention fonctionnelle",
                    "Analyser les informations manquantes",
                    "Pourquoi ces questions sont utiles",
                    "Se connecter avec succès",
                    "Ce que les champs HTML permettent de faire",
                ):
                    self.assertIn(expected, editor.text)

                guidance = client.post(
                    f"{case_url}/design-guidance",
                    data={
                        "intent_reference": "authentication-login-success@1",
                        "objective": "",
                        "actor": "",
                        "preconditions": "",
                        "postconditions": "",
                        "workflow_json": json.dumps(
                            {
                                "start_url": "https://editor.demo.invalid/login",
                                "fixture_refs": [],
                                "secret_refs": [],
                                "pages": [
                                    analyze_html_page(
                                        "https://editor.demo.invalid/login",
                                        LOGIN_HTML,
                                    ).as_dict()
                                ],
                                "steps": [],
                            }
                        ),
                    },
                )
                self.assertEqual(200, guidance.status_code)
                payload = guidance.json()
                self.assertEqual(
                    "authentication-login-success@1",
                    payload["intent"]["reference"],
                )
                self.assertTrue(
                    any(
                        item["question"].startswith(
                            "Quel comportement métier précis"
                        )
                        for item in payload["missing_information"]
                    )
                )
                self.assertIn(
                    "Adresse électronique",
                    {item["label"] for item in payload["html_fields"]},
                )

                documentation = client.get("/documentation")
                self.assertIn(
                    "Dialogue guidé par les informations manquantes",
                    documentation.text,
                )
                self.assertIn(
                    "Capacités déduites des champs HTML",
                    documentation.text,
                )
                tutorial = client.get("/tutorials/test-case")
                self.assertIn(
                    "Utiliser l’assistant de conception",
                    tutorial.text,
                )
                self.assertIn(
                    "Comprendre les suggestions issues de la page",
                    tutorial.text,
                )

            self.assertTrue(settings.test_intents.is_file())


if __name__ == "__main__":
    unittest.main()
