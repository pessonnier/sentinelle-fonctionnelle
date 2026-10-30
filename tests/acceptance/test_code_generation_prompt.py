"""GEN-002.3 — prompt final de génération et traçabilité des skills."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.application import seed_hr_demo_project
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


ROOT = Path(__file__).resolve().parents[2]


class FakeCodeGenerationLLM:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def generate_code(self, *, profile: object, prompt: dict[str, object]):
        self.calls.append({"profile": profile, "prompt": prompt})
        return self.response


class CodeGenerationPromptAcceptanceTests(unittest.TestCase):
    def test_confirmed_case_exposes_prompt_skills_and_generated_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_web_app(
                ServerSettings(database=Path(temporary_directory) / "sentinelle.db")
            )
            seeded = seed_hr_demo_project(
                app.state.project_application,
                root_directory=ROOT,
            )
            case_url = (
                f"/projects/{seeded.project_id}/test-plans/{seeded.plan_id}"
                f"/cases/{seeded.nominal_case_id}"
            )

            with TestClient(app) as client:
                editor = client.get(case_url)
                self.assertEqual(200, editor.status_code)
                self.assertIn("Ouvrir le prompt de génération", editor.text)
                self.assertIn("Télécharger le code généré", editor.text)
                self.assertIn("generate-python-playwright-code@1", editor.text)

                prompt_view = client.get(f"{case_url}/code-generation-request")
                self.assertEqual(200, prompt_view.status_code, prompt_view.text)
                self.assertIn("Prompt de génération du code", prompt_view.text)
                self.assertIn("Demande de production du code", prompt_view.text)
                self.assertIn("generate-python-playwright-code@1", prompt_view.text)
                self.assertIn("Télécharger le JSON", prompt_view.text)
                self.assertIn("Générer avec le LLM local", prompt_view.text)
                self.assertNotIn("Cactus!2026", prompt_view.text)
                self.assertIn("&lt;secret-value-redacted&gt;", prompt_view.text)

                prompt = client.get(f"{case_url}/generation-prompt")
                self.assertEqual(200, prompt.status_code, prompt.text)
                self.assertEqual(
                    prompt.json()["sha256"],
                    prompt.headers["x-prompt-sha256"],
                )
                self.assertIn(
                    "attachment; filename=",
                    prompt.headers["content-disposition"],
                )
                document = prompt.json()
                self.assertEqual("code-generation-v1", document["prompt_version"])
                self.assertEqual(
                    "ollama-qwen36-128k-11436@1",
                    document["llm_access_profile"],
                )
                self.assertEqual(
                    "python-playwright-qwen36-11436@1",
                    document["code_generation_profile"],
                )
                self.assertEqual(
                    [
                        "functional-test-generation@1",
                        "generate-python-playwright-code@1",
                    ],
                    [skill["reference"] for skill in document["skills"]],
                )
                self.assertEqual(
                    ["system", "user"],
                    [message["role"] for message in document["messages"]],
                )
                self.assertIn(
                    "Génère le code",
                    document["messages"][0]["content"],
                )
                self.assertEqual(
                    23,
                    len(document["generation_input"]["workflow"]["steps"]),
                )
                self.assertNotIn("Cactus!2026", prompt.text)
                self.assertIn("<secret-value-redacted>", prompt.text)

                generated = client.get(f"{case_url}/generated-code")
                self.assertEqual(200, generated.status_code, generated.text)
                self.assertIn(
                    "attachment; filename=",
                    generated.headers["content-disposition"],
                )

                expected_path = document["generation_input"]["effective_configuration"][
                    "expected_test_path"
                ]
                fake = FakeCodeGenerationLLM(
                    {
                        "schema_version": 1,
                        "files": [
                            {
                                "path": expected_path,
                                "content": (
                                    "from playwright.sync_api import Page\n\n"
                                    "def test_generated(page: Page) -> None:\n"
                                    "    page.goto('http://127.0.0.1:8000/demo/hr')\n"
                                ),
                            }
                        ],
                        "assumptions": [],
                        "warnings": [],
                    }
                )
                app.state.design_llm = fake
                llm_generated = client.post(f"{case_url}/llm-generated-code")
                self.assertEqual(200, llm_generated.status_code, llm_generated.text)
                self.assertIn("def test_generated", llm_generated.text)
                self.assertEqual(
                    "ollama-qwen36-128k-11436@1",
                    llm_generated.headers["x-llm-profile"],
                )
                self.assertEqual(1, len(fake.calls))
                stored_candidates = app.state.candidate_lifecycle.list_for_case(
                    project_id=seeded.project_id,
                    test_plan_id=seeded.plan_id,
                    case_id=seeded.nominal_case_id,
                    specification_version=1,
                )
                self.assertEqual(1, len(stored_candidates))
                self.assertEqual("llm", stored_candidates[0].origin.value)
                self.assertEqual(document["sha256"], stored_candidates[0].prompt_sha256)
                self.assertEqual(
                    "ollama-qwen36-128k-11436@1",
                    stored_candidates[0].manifest["llm_access_profile"],
                )
                called_profile = fake.calls[0]["profile"]
                self.assertEqual(
                    "http://127.0.0.1:11436/v1",
                    called_profile.base_url,
                )
                called_prompt = fake.calls[0]["prompt"]
                self.assertEqual(
                    ["system", "user"],
                    [message["role"] for message in called_prompt["messages"]],
                )

                fake.response = {
                    "schema_version": 1,
                    "files": [
                        {"path": expected_path, "content": "def test_ok():\n    pass\n"}
                    ],
                    "assumptions": [],
                    "warnings": [],
                    "commentary": "hors contrat",
                }
                refused_extra = client.post(f"{case_url}/llm-generated-code")
                self.assertEqual(400, refused_extra.status_code)
                self.assertIn("propriétés hors contrat", refused_extra.text)

                fake.response = {
                    "schema_version": 1,
                    "files": [{"path": "../outside.py", "content": "pass\n"}],
                    "assumptions": [],
                    "warnings": [],
                }
                refused = client.post(f"{case_url}/llm-generated-code")
                self.assertEqual(400, refused.status_code)
                self.assertIn("sort de la racine autorisée", refused.text)


if __name__ == "__main__":
    unittest.main()
