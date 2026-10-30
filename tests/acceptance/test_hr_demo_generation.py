"""Données XLSX et génération Playwright du parcours RH."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from sentinelle_fonctionnelle.adapters.tabular import parse_tabular_data
from sentinelle_fonctionnelle.application import (
    CodeGenerationError,
    generate_python_playwright,
    generate_python_playwright_file,
)


ROOT = Path(__file__).resolve().parents[2]


class HrDemoGenerationAcceptanceTests(unittest.TestCase):
    def test_both_workbooks_are_importable_and_keep_expected_columns(self) -> None:
        login_path = ROOT / "outputs" / "hr-demo" / "connexion-rh.xlsx"
        employees_path = (
            ROOT / "outputs" / "hr-demo" / "saisie-collaborateurs.xlsx"
        )
        login = parse_tabular_data(login_path.name, login_path.read_bytes())
        employees = parse_tabular_data(
            employees_path.name,
            employees_path.read_bytes(),
        )

        self.assertEqual(3, login.row_count)
        self.assertEqual("camille.cactus@example.test", login.rows[0][1])
        self.assertIn("portal_code", login.headers)
        self.assertEqual(3, employees.row_count)
        self.assertIn("manager_budget", employees.headers)
        self.assertIn("expected_title", employees.headers)
        self.assertEqual("Zoé", employees.rows[0][2])

    def test_confirmed_workflow_generates_compilable_playwright(self) -> None:
        document = json.loads(
            (
                ROOT / "config" / "examples" / "hr-demo-workflow.json"
            ).read_text(encoding="utf-8")
        )

        artifact = generate_python_playwright(document)

        compile(artifact.source, artifact.case_slug + ".py", "exec")
        self.assertEqual(
            "test_manager_creates_employee_from_xlsx",
            artifact.test_name,
        )
        self.assertIn("parse_tabular_data", artifact.source)
        self.assertIn("page.get_by_label('Code du portail astral'", artifact.source)
        self.assertIn("page.get_by_test_id('animal-totem')", artifact.source)
        self.assertIn("expect(page.locator('#js-result-cards'))", artifact.source)
        self.assertNotIn("Cactus!2026", artifact.source)
        self.assertNotIn("Zoé", artifact.source)

    def test_explicit_data_matrix_generates_two_auditable_cases(self) -> None:
        workflow_path = ROOT / "config" / "examples" / "hr-demo-workflow.json"
        document = json.loads(workflow_path.read_text(encoding="utf-8"))

        artifact = generate_python_playwright(document)

        self.assertEqual(2, artifact.data_case_count)
        self.assertIn("@pytest.mark.parametrize", artifact.source)
        self.assertIn("manager-zoe-nebuleuse", artifact.source)
        self.assertIn("manager-iris-comete", artifact.source)
        self.assertIn("{{data.login.email}}", workflow_path.read_text("utf-8"))
        self.assertIn("{{data.employee.first_name}}", workflow_path.read_text("utf-8"))

    def test_file_generation_writes_reproducible_integrity_manifest(self) -> None:
        workflow_path = ROOT / "config" / "examples" / "hr-demo-workflow.json"
        output_path = ROOT / "tests" / "generated" / "test_hr_demo_workflow.py"
        manifest_path = output_path.with_suffix(".manifest.json")

        first = generate_python_playwright_file(
            workflow_path,
            output_path,
            root_directory=ROOT,
        )
        second = generate_python_playwright_file(
            workflow_path,
            output_path,
            root_directory=ROOT,
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(first.source_sha256, second.source_sha256)
        self.assertEqual(first.workflow_sha256, second.workflow_sha256)
        self.assertEqual(first.source_sha256, manifest["source_sha256"])
        self.assertEqual(2, manifest["data_case_count"])
        self.assertEqual(
            {"login", "employee"},
            {source["id"] for source in manifest["data_sources"]},
        )
        self.assertTrue(all(source["sha256"] for source in manifest["data_sources"]))

    def test_matrix_rejects_implicit_or_incomplete_row_associations(self) -> None:
        document = json.loads(
            (
                ROOT / "config" / "examples" / "hr-demo-workflow.json"
            ).read_text(encoding="utf-8")
        )
        document["data_cases"][0]["rows"].pop("employee")

        with self.assertRaisesRegex(
            CodeGenerationError,
            "exactement une ligne de chaque source",
        ):
            generate_python_playwright(document)


if __name__ == "__main__":
    unittest.main()
