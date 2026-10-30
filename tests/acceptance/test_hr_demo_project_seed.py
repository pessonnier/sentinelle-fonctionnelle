"""Projet d’exemple persistant couvrant toute la cible RH intégrée."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sentinelle_fonctionnelle.application import (
    ProjectApplication,
    generate_python_playwright,
    seed_hr_demo_project,
)
from sentinelle_fonctionnelle.application.hr_demo_seed import (
    AUTH_SUITE_NAME,
    FOLDER_NAME,
    NOMINAL_CASE_NAME,
    ONBOARDING_SUITE_NAME,
    PLAN_NAME,
    PROJECT_NAME,
    REJECTED_CASE_NAME,
)


ROOT = Path(__file__).resolve().parents[2]


class HrDemoProjectSeedAcceptanceTests(unittest.TestCase):
    def test_seed_creates_an_idempotent_generable_example_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            application = ProjectApplication.sqlite(
                Path(temporary_directory) / "sentinelle.db"
            )

            first = seed_hr_demo_project(
                application,
                root_directory=ROOT,
            )
            second = seed_hr_demo_project(
                application,
                root_directory=ROOT,
            )

            self.assertTrue(first.created)
            self.assertFalse(second.created)
            self.assertEqual(first.project_id, second.project_id)
            projects = application.list_projects(None)
            self.assertEqual([PROJECT_NAME], [project.name for project in projects])

            project = application.get_project(None, first.project_id)
            plan = project.test_plan(first.plan_id)
            self.assertEqual(PLAN_NAME, plan.name)
            self.assertEqual(
                {
                    FOLDER_NAME,
                    AUTH_SUITE_NAME,
                    ONBOARDING_SUITE_NAME,
                    NOMINAL_CASE_NAME,
                    REJECTED_CASE_NAME,
                },
                {node.name for node in plan.nodes},
            )

            nominal = plan.node(first.nominal_case_id)
            rejected = plan.node(first.rejected_case_id)
            self.assertEqual("saisie-collaborateurs.xlsx", nominal.data_binding.data_set.filename)
            self.assertEqual("connexion-rh.xlsx", rejected.data_binding.data_set.filename)
            self.assertEqual(2, nominal.specification.workflow.schema_version)
            self.assertTrue(nominal.specification.workflow.confirmed)
            self.assertTrue(rejected.specification.workflow.confirmed)
            self.assertEqual(
                "ollama-qwen36-128k-11436@1",
                nominal.specification.workflow.llm_access_profile,
            )
            self.assertEqual(
                "python-playwright-qwen36-11436@1",
                nominal.specification.workflow.code_generation_profile,
            )
            self.assertEqual(
                nominal.specification.workflow.llm_access_profile,
                rejected.specification.workflow.llm_access_profile,
            )
            self.assertEqual(
                nominal.specification.workflow.code_generation_profile,
                rejected.specification.workflow.code_generation_profile,
            )
            self.assertEqual(23, len(nominal.specification.workflow.steps))
            self.assertEqual(6, len(rejected.specification.workflow.steps))

            nominal_artifact = generate_python_playwright(
                {
                    "case_slug": "hr_demo_zoe",
                    "test_name": "test_hr_demo_zoe",
                    "data_files": [],
                    "workflow": nominal.specification.workflow.as_dict(),
                }
            )
            rejected_artifact = generate_python_playwright(
                {
                    "case_slug": "hr_demo_rejected_login",
                    "test_name": "test_hr_demo_rejected_login",
                    "data_files": [],
                    "workflow": rejected.specification.workflow.as_dict(),
                }
            )
            self.assertIn("Zoé Nébuleuse", nominal_artifact.source)
            self.assertIn("EMP-NEB-042", nominal_artifact.source)
            self.assertIn("Les archives cosmiques refusent", rejected_artifact.source)
            self.assertIn("page.locator('[role=\"alert\"]')", rejected_artifact.source)
            self.assertNotIn("{{data.", nominal_artifact.source)
            self.assertNotIn("{{data.", rejected_artifact.source)


if __name__ == "__main__":
    unittest.main()
