"""Contrôle de connexion et de capacité JSON d’un profil LLM."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class _ConnectivityLLM:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.profiles: list[object] = []
        self.messages: list[str] = []
        self.catalog_profiles: list[object] = []

    def probe(self, *, profile: object) -> dict[str, Any]:
        self.profiles.append(profile)
        return {
            "engine": "Ollama",
            "engine_version": "0.32.3",
            "model_available": True,
        }

    def complete(
        self,
        *,
        profile: object,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        self.requests.append(request)
        return {
            "schema_version": 1,
            "questions": [],
            "operations": [],
        }

    def chat(self, *, profile: object, message: str) -> str:
        self.profiles.append(profile)
        self.messages.append(message)
        return "Le modèle répond sans enregistrer le message."

    def list_models(self, *, profile: object) -> tuple[str, ...]:
        self.catalog_profiles.append(profile)
        return ("gemma3:latest", "qwen-local:latest")


class LLMConnectivityAcceptanceTests(unittest.TestCase):
    def test_profile_separates_connectivity_inference_and_interaction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_web_app(
                ServerSettings(
                    database=Path(temporary_directory) / "sentinelle.db"
                )
            )
            profile = app.state.generation_profile_catalog.create_llm_access(
                profile_id="ollama-qwen",
                name="Ollama Qwen",
                provider="ollama",
                base_url="http://127.0.0.1:11434/v1",
                model="qwen-local:latest",
                api_key_environment="",
                organization_environment="",
                request_timeout_seconds=300,
                max_retries=0,
                enabled=False,
            )
            fake = _ConnectivityLLM()
            app.state.design_llm = fake

            with TestClient(app) as client:
                catalog = client.post(
                    "/configuration/llm-models",
                    data={
                        "provider": "ollama",
                        "base_url": "http://127.0.0.1:11434/v1",
                        "api_key_environment": "",
                        "organization_environment": "",
                        "request_timeout_seconds": "300",
                    },
                )
                self.assertEqual(200, catalog.status_code)
                self.assertEqual(
                    ["gemma3:latest", "qwen-local:latest"],
                    catalog.json()["models"],
                )
                self.assertEqual(2, catalog.json()["count"])
                self.assertEqual(
                    "http://127.0.0.1:11434/v1",
                    fake.catalog_profiles[0].base_url,
                )
                self.assertEqual(30, fake.catalog_profiles[0].request_timeout_seconds)

                response = client.post(
                    "/configuration/llm-access-profiles/ollama-qwen"
                    "/versions/1/connectivity"
                )
                self.assertEqual(200, response.status_code)
                result = response.json()
                self.assertEqual("ok", result["status"])
                self.assertEqual(profile.reference, result["profile"])
                self.assertEqual("Ollama", result["engine"])
                self.assertEqual("0.32.3", result["engine_version"])
                self.assertTrue(result["model_available"])
                self.assertFalse(fake.requests)

                structured = client.post(
                    "/configuration/llm-access-profiles/ollama-qwen"
                    "/versions/1/structured-test"
                )
                self.assertEqual(200, structured.status_code)
                self.assertTrue(structured.json()["structured_json"])
                self.assertEqual(
                    "connectivity-v1",
                    fake.requests[0]["prompt_version"],
                )
                self.assertNotIn("api_key", str(fake.requests[0]).casefold())

                interaction = client.post(
                    "/configuration/llm-access-profiles/ollama-qwen"
                    "/versions/1/interact",
                    data={"message": "  Présente ce modèle.  "},
                )
                self.assertEqual(200, interaction.status_code)
                self.assertEqual(
                    "Le modèle répond sans enregistrer le message.",
                    interaction.json()["answer"],
                )
                self.assertEqual(["Présente ce modèle."], fake.messages)

                empty_message = client.post(
                    "/configuration/llm-access-profiles/ollama-qwen"
                    "/versions/1/interact",
                    data={"message": "   "},
                )
                self.assertEqual(400, empty_message.status_code)
                self.assertEqual(["Présente ce modèle."], fake.messages)

                configuration = client.get("/configuration/llm-access")
                self.assertIn(
                    "Vérifier le serveur et le modèle",
                    configuration.text,
                )
                self.assertIn("Tester l’inférence JSON", configuration.text)
                self.assertIn("Interagir avec le LLM", configuration.text)
                self.assertIn("Envoyer au LLM", configuration.text)
                self.assertIn(
                    "/versions/1/connectivity",
                    configuration.text,
                )
                self.assertIn(
                    "/versions/1/structured-test",
                    configuration.text,
                )
                self.assertIn(
                    "/versions/1/interact",
                    configuration.text,
                )


if __name__ == "__main__":
    unittest.main()
