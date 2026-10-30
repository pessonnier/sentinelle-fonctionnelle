"""ACC-033 et contribution ACC-034 — préconditions confirmées et contrôles locaux."""

from __future__ import annotations

import unittest

from sentinelle_fonctionnelle.application import (
    assess_workflow_readiness,
    generate_python_playwright,
)
from sentinelle_fonctionnelle.domain import GenerationWorkflowInput, WorkflowError


def _workflow(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 2,
        "start_url": "http://127.0.0.1:8000/demo/hr/login",
        "environment_profile": "demo-rh@1",
        "actor_profile": "manager-rh",
        "functional_intent": "authentication-login-success@1",
        "fixture_refs": ["manager-rh"],
        "secret_refs": ["manager-password"],
        "setup": ["Un responsable RH actif existe"],
        "cleanup": ["Fermer la session"],
        "evidence_policy": "on_failure",
        "llm_policy": "disabled",
        "llm_access_profile": "",
        "code_generation_profile": "",
        "timeout_seconds": 30,
        "assumptions": [],
        "authoring_mode": "form",
        "step_narratives": [],
        "scenario_narrative": "",
        "confirmed": False,
        "pages": [],
        "steps": [
            {
                "id": "step-1",
                "name": "Afficher la connexion",
                "page_url": "http://127.0.0.1:8000/demo/hr/login",
                "precondition": "",
                "action": "navigate",
                "target": "",
                "value": "",
                "assertion": "url",
                "assertion_target": "",
                "expected": "http://127.0.0.1:8000/demo/hr/login",
                "evidence": False,
            }
        ],
        "precondition_dependencies": [],
    }
    value.update(changes)
    return value


class PreconditionReadinessAcceptanceTests(unittest.TestCase):
    def test_a_version_two_workflow_requires_confirmed_precondition_translations(self) -> None:
        draft = GenerationWorkflowInput.from_mapping(_workflow())
        self.assertFalse(draft.confirmed)

        with self.assertRaisesRegex(WorkflowError, "doit être traduite"):
            GenerationWorkflowInput.from_mapping(_workflow(confirmed=True))

        confirmed = GenerationWorkflowInput.from_mapping(
            _workflow(
                confirmed=True,
                precondition_dependencies=[
                    {
                        "id": "precondition-1",
                        "source": "Un responsable RH actif existe",
                        "kind": "fixture",
                        "description": "Charger le compte responsable RH actif",
                        "reference": "manager-rh",
                        "confirmed": True,
                    }
                ],
            )
        )

        self.assertTrue(confirmed.confirmed)
        self.assertEqual("fixture", confirmed.precondition_dependencies[0].kind.value)
        self.assertEqual(
            confirmed.as_dict(),
            GenerationWorkflowInput.from_mapping(confirmed.as_dict()).as_dict(),
        )
        artifact = generate_python_playwright(
            {
                "case_slug": "precondition_manager",
                "test_name": "test_precondition_manager",
                "data_files": [],
                "workflow": confirmed.as_dict(),
            }
        )
        self.assertIn("Traductions de préconditions confirmées", artifact.source)
        self.assertIn("référence manager-rh", artifact.source)
        self.assertEqual(
            "fixture",
            artifact.manifest["precondition_dependencies"][0]["kind"],
        )

    def test_system_failures_are_blocking_and_cannot_be_declared_successful(self) -> None:
        workflow = GenerationWorkflowInput.from_mapping(
            _workflow(
                precondition_dependencies=[
                    {
                        "id": "precondition-1",
                        "source": "Un responsable RH actif existe",
                        "kind": "fixture",
                        "description": "Charger le compte responsable RH actif",
                        "reference": "manager-rh",
                        "confirmed": False,
                    }
                ]
            )
        )

        blocked = assess_workflow_readiness(
            workflow,
            project_target="http://127.0.0.1:8000/demo/hr",
            available_secret_refs=(),
            browser_available=False,
        )

        self.assertFalse(blocked.ready)
        failed_codes = {
            check.code for check in blocked.checks if check.status.value == "failed"
        }
        self.assertEqual(
            {"precondition-review", "secret-references", "browser-runtime"},
            failed_codes,
        )

        ready = assess_workflow_readiness(
            GenerationWorkflowInput.from_mapping(
                _workflow(
                    precondition_dependencies=[
                        {
                            "id": "precondition-1",
                            "source": "Un responsable RH actif existe",
                            "kind": "fixture",
                            "description": "Charger le compte responsable RH actif",
                            "reference": "manager-rh",
                            "confirmed": True,
                        }
                    ]
                )
            ),
            project_target="http://127.0.0.1:8000/demo/hr",
            available_secret_refs=("manager-password",),
            browser_available=True,
        )
        self.assertTrue(ready.ready)
        self.assertTrue(all(check.status.value == "passed" for check in ready.checks))

    def test_fixture_translation_must_reference_a_declared_data_set(self) -> None:
        workflow = GenerationWorkflowInput.from_mapping(
            _workflow(
                fixture_refs=[],
                precondition_dependencies=[
                    {
                        "id": "precondition-1",
                        "source": "Un responsable RH actif existe",
                        "kind": "fixture",
                        "description": "Charger le compte responsable RH actif",
                        "reference": "manager-rh",
                        "confirmed": True,
                    }
                ],
            )
        )

        readiness = assess_workflow_readiness(
            workflow,
            project_target="http://127.0.0.1:8000",
            available_secret_refs=("manager-password",),
        )

        fixture_check = next(
            check for check in readiness.checks if check.code == "fixture-references"
        )
        self.assertEqual("failed", fixture_check.status.value)
        self.assertIn("manager-rh", fixture_check.detail)


if __name__ == "__main__":
    unittest.main()
