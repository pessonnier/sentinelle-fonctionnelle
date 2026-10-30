"""ACC-078 à ACC-080 — accès LLM et profils de génération configurables."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.domain import GenerationProfileCatalog
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


ROOT = Path(__file__).resolve().parents[2]


class GenerationConfigurationAcceptanceTests(unittest.TestCase):
    def test_default_catalog_preconfigures_both_local_ollama_instances(self) -> None:
        expected = {
            "ollama-qwen36-128k": "http://127.0.0.1:11434/v1",
            "ollama-qwen36-128k-11436": "http://127.0.0.1:11436/v1",
        }
        for path in (
            ROOT / "data" / "generation-profiles.yaml",
            ROOT
            / "src"
            / "sentinelle_fonctionnelle"
            / "configuration"
            / "generation-profiles.yaml",
        ):
            catalog = GenerationProfileCatalog.open(path)
            for profile_id, base_url in expected.items():
                profile = catalog.get_llm_access(profile_id, 1)
                self.assertEqual(base_url, profile.base_url)
                self.assertEqual(
                    "qwen3.6-35b-a3b-q4_K_M_128k:latest",
                    profile.model,
                )
                self.assertTrue(profile.enabled)
            self.assertEqual(
                "ollama-qwen36-128k-11436@1",
                catalog.get_code_generation(
                    "python-playwright-qwen36-11436",
                    1,
                ).llm_profile,
            )

    def test_remote_http_and_unsafe_output_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = ServerSettings(
                database=root / "sentinelle.db",
                generation_profiles=root / "generation-profiles.yaml",
            )
            with TestClient(create_web_app(settings)) as client:
                unsafe_access = client.post(
                    "/configuration/llm-access-profiles",
                    data={
                        "profile_id": "unsafe-remote",
                        "name": "HTTP distant",
                        "provider": "openai-compatible",
                        "base_url": "http://llm.example.invalid/v1",
                        "model": "model",
                        "api_key_environment": "LLM_API_KEY",
                        "request_timeout_seconds": "30",
                        "max_retries": "1",
                        "enabled": "true",
                    },
                )
                self.assertEqual(400, unsafe_access.status_code)
                self.assertIn("HTTPS", unsafe_access.text)

                local_access = client.post(
                    "/configuration/llm-access-profiles",
                    data={
                        "profile_id": "ollama-local",
                        "name": "Ollama local",
                        "provider": "ollama",
                        "base_url": "http://127.0.0.1:11434",
                        "model": "modele-local",
                        "api_key_environment": "",
                        "request_timeout_seconds": "30",
                        "max_retries": "1",
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, local_access.status_code)

                unsafe_generation = client.post(
                    "/configuration/code-generation-profiles",
                    data={
                        "profile_id": "unsafe-output",
                        "name": "Sortie dangereuse",
                        "llm_profile": "ollama-local@1",
                        "language": "python",
                        "framework": "pytest-playwright",
                        "output_root": "../tests",
                        "test_file_pattern": "test_{case_slug}.py",
                        "page_object_pattern": "{page_slug}_page.py",
                        "evidence_mode": "none",
                        "overwrite_policy": "proposal-only",
                        "validation_steps": "syntax",
                        "generation_instructions": "Rester déterministe",
                        "max_generated_files": "5",
                        "enabled": "true",
                    },
                )
                self.assertEqual(400, unsafe_generation.status_code)
                self.assertIn("chemin relatif sûr", unsafe_generation.text)

    def test_profiles_are_versioned_without_persisting_api_key_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = ServerSettings(
                database=root / "sentinelle.db",
                generation_profiles=root / "generation-profiles.yaml",
            )
            with TestClient(create_web_app(settings)) as client:
                legacy = client.get(
                    "/configuration/generation",
                    follow_redirects=False,
                )
                self.assertEqual(307, legacy.status_code)
                self.assertEqual(
                    "/configuration/llm-access",
                    legacy.headers["location"],
                )

                llm_configuration = client.get("/configuration/llm-access")
                self.assertEqual(200, llm_configuration.status_code)
                self.assertIn('id="llm-access"', llm_configuration.text)
                self.assertIn(
                    'action="/configuration/llm-access-profiles"',
                    llm_configuration.text,
                )
                self.assertIn(
                    'data-create-toggle',
                    llm_configuration.text,
                )
                self.assertIn(
                    'aria-controls="new-llm-connection"',
                    llm_configuration.text,
                )
                self.assertIn(
                    '<select name="model" data-model-select required>',
                    llm_configuration.text,
                )
                self.assertEqual(
                    3,
                    llm_configuration.text.count(
                        'class="secondary-button model-refresh-button"'
                    ),
                )
                self.assertNotIn(
                    '<input name="model"',
                    llm_configuration.text,
                )
                self.assertIn(
                    'id="new-llm-connection" class="form-panel entity-create-panel" hidden',
                    llm_configuration.text,
                )
                self.assertNotIn(
                    'id="code-generation"',
                    llm_configuration.text,
                )

                code_configuration = client.get(
                    "/configuration/code-generation"
                )
                self.assertEqual(200, code_configuration.status_code)
                self.assertIn('id="code-generation"', code_configuration.text)
                self.assertIn(
                    'action="/configuration/code-generation-profiles"',
                    code_configuration.text,
                )
                self.assertNotIn('id="llm-access"', code_configuration.text)
                self.assertIn('data-create-toggle', code_configuration.text)
                self.assertIn(
                    'aria-controls="new-code-generation-profile"',
                    code_configuration.text,
                )
                self.assertIn(
                    'id="new-code-generation-profile" class="form-panel entity-create-panel" hidden',
                    code_configuration.text,
                )
                self.assertIn('name="generation_skills"', code_configuration.text)
                self.assertIn(
                    "generate-python-playwright-code@1",
                    code_configuration.text,
                )

                access = client.post(
                    "/configuration/llm-access-profiles",
                    data={
                        "profile_id": "openai-recette",
                        "name": "OpenAI recette",
                        "provider": "openai",
                        "base_url": "https://api.openai.com/v1",
                        "model": "modele-valide-par-le-projet",
                        "api_key_environment": "OPENAI_API_KEY",
                        "organization_environment": "",
                        "request_timeout_seconds": "45",
                        "max_retries": "2",
                        "enabled": "true",
                        "api_key": "sk-ne-doit-jamais-etre-persistee",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, access.status_code)
                self.assertEqual(
                    "/configuration/llm-access#llm-openai-recette",
                    access.headers["location"],
                )

                updated_access = client.post(
                    "/configuration/llm-access-profiles/openai-recette",
                    data={
                        "name": "OpenAI recette",
                        "provider": "openai",
                        "base_url": "https://api.openai.com/v1",
                        "model": "modele-v2-valide-par-le-projet",
                        "api_key_environment": "OPENAI_API_KEY",
                        "organization_environment": "",
                        "request_timeout_seconds": "60",
                        "max_retries": "3",
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, updated_access.status_code)

                generation = client.post(
                    "/configuration/code-generation-profiles",
                    data={
                        "profile_id": "python-playwright",
                        "name": "Python Playwright",
                        "llm_profile": "openai-recette@1",
                        "language": "python",
                        "framework": "pytest-playwright",
                        "output_root": "tests/generated",
                        "test_file_pattern": "test_{case_slug}.py",
                        "page_object_pattern": "{page_slug}_page.py",
                        "use_page_objects": "true",
                        "include_comments": "true",
                        "evidence_mode": "on-failure",
                        "overwrite_policy": "proposal-only",
                        "validation_steps": "syntax\nlint\ntargeted-test",
                        "generation_instructions": (
                            "Utiliser des localisateurs accessibles\n"
                            "Ne jamais écrire les secrets"
                        ),
                        "generation_skills": (
                            "functional-test-generation@1\n"
                            "generate-python-playwright-code@1"
                        ),
                        "max_generated_files": "12",
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, generation.status_code)
                self.assertEqual(
                    "/configuration/code-generation#generation-python-playwright",
                    generation.headers["location"],
                )

                updated_generation = client.post(
                    "/configuration/code-generation-profiles/python-playwright",
                    data={
                        "name": "Python Playwright",
                        "llm_profile": "openai-recette@2",
                        "language": "python",
                        "framework": "pytest-playwright",
                        "output_root": "tests/generated",
                        "test_file_pattern": "test_{case_slug}.py",
                        "page_object_pattern": "{page_slug}_page.py",
                        "use_page_objects": "true",
                        "evidence_mode": "on-failure",
                        "overwrite_policy": "refuse-existing",
                        "validation_steps": "syntax\nformat\nlint\ntargeted-test",
                        "generation_instructions": (
                            "Utiliser des localisateurs accessibles\n"
                            "Ne jamais écrire les secrets"
                        ),
                        "generation_skills": (
                            "functional-test-generation@1\n"
                            "generate-python-playwright-code@1"
                        ),
                        "max_generated_files": "10",
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, updated_generation.status_code)

                restored_llm = client.get("/configuration/llm-access")
                restored_code = client.get("/configuration/code-generation")
                self.assertIn("OpenAI recette", restored_llm.text)
                self.assertNotIn("Python Playwright", restored_llm.text)
                self.assertIn("OPENAI_API_KEY", restored_llm.text)
                self.assertNotIn(
                    "sk-ne-doit-jamais-etre-persistee",
                    restored_llm.text,
                )
                self.assertIn("Python Playwright", restored_code.text)

                project = client.post(
                    "/projects",
                    data={
                        "name": "Portail",
                        "description": "Génération",
                        "web_target": "https://portail.demo.invalid",
                        "security_policy": "same-origin",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
                plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Parcours",
                        "objective": "Générer un test",
                        "scope": "Portail",
                        "test_approach": "automated-regression@1",
                        "target": "https://portail.demo.invalid",
                    },
                    follow_redirects=False,
                )
                plan_id = UUID(plan.headers["x-created-id"])
                suite = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "suite",
                        "name": "Navigation",
                        "objective": "Ouvrir le portail",
                    },
                    follow_redirects=False,
                )
                suite_id = UUID(suite.headers["x-created-id"])
                case = client.post(
                    f"/projects/{project_id}/test-plans/{plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Accueil visible",
                        "parent_id": str(suite_id),
                    },
                    follow_redirects=False,
                )
                case_id = UUID(case.headers["x-created-id"])
                case_url = (
                    f"/projects/{project_id}/test-plans/{plan_id}/cases/{case_id}"
                )
                editor = client.get(case_url)
                self.assertIn("openai-recette@1", editor.text)
                self.assertIn("python-playwright@1", editor.text)

                workflow = {
                    "schema_version": 1,
                    "start_url": "https://portail.demo.invalid",
                    "environment_profile": "recette",
                    "actor_profile": "visiteur",
                    "fixture_refs": [],
                    "secret_refs": [],
                    "setup": [],
                    "cleanup": [],
                    "evidence_policy": "on_failure",
                    "llm_policy": "design_only",
                    "llm_access_profile": "openai-recette@1",
                    "code_generation_profile": "python-playwright@1",
                    "timeout_seconds": 30,
                    "assumptions": [],
                    "confirmed": True,
                    "pages": [],
                    "steps": [
                        {
                            "id": "step-1",
                            "name": "Ouvrir le portail",
                            "page_url": "https://portail.demo.invalid",
                            "precondition": "",
                            "action": "navigate",
                            "target": "",
                            "value": "",
                            "assertion": "url",
                            "assertion_target": "",
                            "expected": "https://portail.demo.invalid",
                            "evidence": False,
                        }
                    ],
                }
                mismatched_workflow = {
                    **workflow,
                    "code_generation_profile": "python-playwright@2",
                }
                mismatched = client.post(
                    f"{case_url}/specification",
                    data={
                        "objective": "Afficher l’accueil",
                        "actor_name": "Visiteur",
                        "environment": "recette",
                        "workflow_json": json.dumps(mismatched_workflow),
                    },
                )
                self.assertEqual(400, mismatched.status_code)
                self.assertIn("un autre accès LLM", mismatched.text)

                saved = client.post(
                    f"{case_url}/specification",
                    data={
                        "objective": "Afficher l’accueil",
                        "actor_name": "Visiteur",
                        "environment": "recette",
                        "workflow_json": json.dumps(workflow),
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, saved.status_code)
                restored_editor = client.get(case_url)
                self.assertIn('"llm_access_profile": "openai-recette@1"', restored_editor.text)
                self.assertIn(
                    '"code_generation_profile": "python-playwright@1"',
                    restored_editor.text,
                )

            document = settings.generation_profiles.read_text(encoding="utf-8")
            self.assertIn("OPENAI_API_KEY", document)
            self.assertIn("python-playwright", document)
            self.assertIn("version: 2", document)
            self.assertNotIn("sk-ne-doit-jamais-etre-persistee", document)

            with TestClient(create_web_app(settings)) as restarted:
                catalog = restarted.app.state.generation_profile_catalog
                self.assertEqual(
                    "openai",
                    catalog.get_llm_access("openai-recette", 1).provider,
                )
                self.assertEqual(
                    "modele-v2-valide-par-le-projet",
                    catalog.get_llm_access("openai-recette", 2).model,
                )
                self.assertEqual(
                    "openai-recette@1",
                    catalog.get_code_generation(
                        "python-playwright",
                        1,
                    ).llm_profile,
                )
                self.assertEqual(
                    "openai-recette@2",
                    catalog.get_code_generation(
                        "python-playwright",
                        2,
                    ).llm_profile,
                )
                self.assertEqual(
                    (
                        "functional-test-generation@1",
                        "generate-python-playwright-code@1",
                    ),
                    catalog.get_code_generation(
                        "python-playwright",
                        2,
                    ).generation_skills,
                )


if __name__ == "__main__":
    unittest.main()
