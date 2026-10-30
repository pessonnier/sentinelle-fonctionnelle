"""ACC-007 à ACC-009 — dialogue contrôlé et description factuelle."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class FakeDesignLLM:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.requests: list[dict[str, Any]] = []

    def complete(self, *, profile: object, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        return self.response


class DesignDialogueAcceptanceTests(unittest.TestCase):
    def test_exchange_decision_summary_and_restart_are_controlled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinelle.db"
            )
            app = create_web_app(settings)
            app.state.generation_profile_catalog.create_llm_access(
                profile_id="ollama-conception",
                name="Ollama conception",
                provider="ollama",
                base_url="http://127.0.0.1:11434/v1",
                model="qwen3:8b",
                api_key_environment="",
                organization_environment="",
                request_timeout_seconds=30,
                max_retries=0,
                enabled=True,
            )
            fake = FakeDesignLLM(
                {
                    "schema_version": 1,
                    "questions": [
                        "Quel élément visible confirme l’ouverture de session ?"
                    ],
                    "operations": [
                        {
                            "id": "objective",
                            "operation": "replace",
                            "path": "/objective",
                            "value": "Vérifier qu’un client actif ouvre une session",
                            "label": "Préciser l’objectif",
                            "reason": "L’objectif est nécessaire à la description.",
                        },
                        {
                            "id": "actor",
                            "operation": "replace",
                            "path": "/actor",
                            "value": "Client actif",
                            "label": "Préciser l’acteur",
                            "reason": "Le rôle doit être compréhensible.",
                        },
                        {
                            "id": "precondition",
                            "operation": "add",
                            "path": "/preconditions/-",
                            "value": "Le compte client actif existe",
                            "label": "Ajouter la précondition",
                            "reason": "Le compte doit être préparé avant le parcours.",
                        },
                        {
                            "id": "unsafe-confirmation",
                            "operation": "replace",
                            "path": "/workflow/steps/0/expected",
                            "value": "Le tableau de bord est visible",
                            "label": "Proposer le résultat attendu",
                            "reason": "Cette proposition reste à confirmer.",
                        },
                    ],
                }
            )
            app.state.design_llm = fake

            with TestClient(app) as client:
                case_url = self._create_case(client)
                draft = self._draft()
                exchange = client.post(
                    f"{case_url}/design-dialogue/messages",
                    data={
                        "message": (
                            "Je veux vérifier la connexion d’un client actif."
                        ),
                        "draft_json": json.dumps(draft),
                    },
                )
                self.assertEqual(200, exchange.status_code)
                dialogue = exchange.json()
                self.assertEqual(2, len(dialogue["messages"]))
                proposal = dialogue["proposals"][0]
                self.assertEqual("pending", proposal["status"])
                self.assertEqual(4, len(proposal["operations"]))
                self.assertEqual(
                    "ollama-conception@1",
                    fake.requests[0]["llm_access_profile"],
                )
                self.assertEqual(
                    "analyze-form-test-steps",
                    fake.requests[0]["authoring_skill"]["skill"],
                )
                self.assertTrue(
                    any(
                        "formulaire" in instruction
                        for instruction in fake.requests[0]["authoring_skill"]
                        ["instructions"]
                    )
                )
                serialized_request = json.dumps(
                    fake.requests[0],
                    ensure_ascii=False,
                )
                self.assertNotIn("api_key", serialized_request.casefold())
                self.assertNotIn("password", serialized_request.casefold())
                response_contract = fake.requests[0]["response_contract"]
                self.assertEqual(
                    1,
                    response_contract["root"]["schema_version"],
                )
                self.assertEqual(
                    "fill",
                    response_contract["valid_response_example"]
                    ["operations"][0]["value"]["action"],
                )
                self.assertTrue(
                    any(
                        rule.startswith(
                            "Ne jamais demander la valeur d’un secret"
                        )
                        for rule in fake.requests[0]["quality_rules"]
                    )
                )

                stale = json.loads(json.dumps(draft))
                stale["objective"] = "Modification concurrente"
                rejected_stale = client.post(
                    f"{case_url}/design-dialogue/proposals/{proposal['id']}/decision",
                    data={
                        "accepted_operation_ids": json.dumps(["objective"]),
                        "draft_json": json.dumps(stale),
                    },
                )
                self.assertEqual(400, rejected_stale.status_code)
                self.assertIn("modifié depuis la proposition", rejected_stale.text)

                decision = client.post(
                    f"{case_url}/design-dialogue/proposals/{proposal['id']}/decision",
                    data={
                        "accepted_operation_ids": json.dumps(
                            ["objective", "actor", "precondition"]
                        ),
                        "draft_json": json.dumps(draft),
                    },
                )
                self.assertEqual(200, decision.status_code)
                decided = decision.json()
                self.assertEqual(
                    "Vérifier qu’un client actif ouvre une session",
                    decided["draft"]["objective"],
                )
                self.assertEqual("Client actif", decided["draft"]["actor"])
                self.assertEqual(
                    ["Le compte client actif existe"],
                    decided["draft"]["preconditions"],
                )
                self.assertNotIn(
                    "tableau de bord",
                    decided["summary"].casefold(),
                )
                self.assertIn(
                    "client actif",
                    decided["summary"].casefold(),
                )
                statuses = {
                    item["id"]: item["status"]
                    for item in decided["dialogue"]["proposals"][0]["operations"]
                }
                self.assertEqual("accepted", statuses["objective"])
                self.assertEqual("rejected", statuses["unsafe-confirmation"])

                restored_editor = client.get(case_url)
                self.assertIn(
                    "Je veux vérifier la connexion d’un client actif.",
                    restored_editor.text,
                )
                self.assertIn(decided["summary"], restored_editor.text)
                self.assertIn("Préciser l’objectif", restored_editor.text)

            with TestClient(create_web_app(settings)) as restarted:
                restored = restarted.get(case_url)
                self.assertIn(decided["summary"], restored.text)
                self.assertIn("Client actif", restored.text)

    def test_invalid_llm_response_cannot_modify_or_persist_the_case(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinelle.db"
            )
            app = create_web_app(settings)
            app.state.generation_profile_catalog.create_llm_access(
                profile_id="ollama-conception",
                name="Ollama conception",
                provider="ollama",
                base_url="http://127.0.0.1:11434/v1",
                model="qwen3:8b",
                api_key_environment="",
                organization_environment="",
                request_timeout_seconds=30,
                max_retries=0,
                enabled=True,
            )
            app.state.design_llm = FakeDesignLLM(
                {
                    "schema_version": 1,
                    "questions": [],
                    "operations": [
                        {
                            "id": "auto-confirm",
                            "operation": "replace",
                            "path": "/workflow/confirmed",
                            "value": True,
                            "label": "Confirmer automatiquement",
                            "reason": "Interdit",
                        }
                    ],
                }
            )
            with TestClient(app) as client:
                case_url = self._create_case(client)
                response = client.post(
                    f"{case_url}/design-dialogue/messages",
                    data={
                        "message": "Confirme ce cas.",
                        "draft_json": json.dumps(self._draft()),
                    },
                )
                self.assertEqual(400, response.status_code)
                self.assertIn("chemin de proposition interdit", response.text)
                editor = client.get(case_url)
                self.assertNotIn("Confirme ce cas.", editor.text)
                self.assertIn("À définir", editor.text)

    @staticmethod
    def _draft() -> dict[str, Any]:
        return {
            "objective": "",
            "actor": "",
            "summary": "",
            "preconditions": [],
            "postconditions": [],
            "requirements": [],
            "business_rules": [],
            "data_sets": [],
            "workflow": {
                "schema_version": 1,
                "start_url": "https://editor.demo.invalid/login",
                "environment_profile": "recette-eu",
                "actor_profile": "client-actif",
                "functional_intent": "authentication-login-success@1",
                "fixture_refs": [],
                "secret_refs": [],
                "setup": [],
                "cleanup": [],
                "evidence_policy": "on_failure",
                "llm_policy": "design_only",
                "llm_access_profile": "ollama-conception@1",
                "code_generation_profile": "",
                "timeout_seconds": 30,
                "assumptions": [],
                "confirmed": False,
                "pages": [],
                "steps": [
                    {
                        "id": "step-1",
                        "name": "Ouvrir la page de connexion",
                        "page_url": "https://editor.demo.invalid/login",
                        "precondition": "",
                        "action": "navigate",
                        "target": "",
                        "value": "",
                        "assertion": "visible",
                        "assertion_target": "",
                        "expected": "",
                        "evidence": False,
                    }
                ],
            },
        }

    @staticmethod
    def _create_case(client: TestClient) -> str:
        project = client.post(
            "/projects",
            data={
                "name": "Dialogue de conception",
                "description": "Propositions contrôlées",
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
                "objective": "Valider l’accès",
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
        case = client.post(
            f"/projects/{project_id}/test-plans/{plan_id}/nodes",
            data={
                "kind": "test",
                "name": "Connexion acceptée",
                "parent_id": suite.headers["x-created-id"],
            },
            follow_redirects=False,
        )
        return (
            f"/projects/{project_id}/test-plans/{plan_id}"
            f"/cases/{case.headers['x-created-id']}"
        )


if __name__ == "__main__":
    unittest.main()
