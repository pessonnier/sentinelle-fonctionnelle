"""Validation locale auditable d’un artefact Playwright généré."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
import unittest

from sentinelle_fonctionnelle.application import (
    ExecutionRunnerError,
    run_generated_playwright,
)


ROOT = Path(__file__).resolve().parents[2]


class ExecutionRunnerAcceptanceTests(unittest.TestCase):
    def test_runner_uses_no_shell_and_writes_a_structured_report(self) -> None:
        calls: list[tuple[list[str], Path, dict[str, str], int]] = []

        def fake_runner(
            command: list[str],
            *,
            cwd: Path,
            env: dict[str, str],
            timeout: int,
        ) -> CompletedProcess[str]:
            calls.append((command, cwd, env, timeout))
            junit = Path(command[command.index("--junitxml") + 1])
            junit.write_text("<testsuites tests=\"2\" failures=\"0\"/>", "utf-8")
            return CompletedProcess(command, 0, "2 passed", "")

        with TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "execution"
            report = run_generated_playwright(
                test_path=ROOT / "tests" / "generated" / "test_hr_demo_workflow.py",
                base_url="http://127.0.0.1:8770",
                output_directory=output,
                root_directory=ROOT,
                timeout_seconds=90,
                command_runner=fake_runner,
            )

            persisted = json.loads((output / "execution.json").read_text("utf-8"))

        self.assertEqual("passed", report.status)
        self.assertEqual(0, report.exit_code)
        self.assertEqual(report.execution_id, persisted["execution_id"])
        self.assertEqual(2, persisted["collected_case_count"])
        self.assertIn("--browser", calls[0][0])
        self.assertEqual("http://127.0.0.1:8770", calls[0][2]["HR_DEMO_BASE_URL"])

    def test_runner_refuses_remote_targets_and_tests_outside_generated_area(self) -> None:
        with TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "execution"
            with self.assertRaisesRegex(ExecutionRunnerError, "boucle locale"):
                run_generated_playwright(
                    test_path=ROOT / "tests" / "generated" / "test_hr_demo_workflow.py",
                    base_url="https://production.example.test",
                    output_directory=output,
                    root_directory=ROOT,
                )
            with self.assertRaisesRegex(ExecutionRunnerError, "tests/generated"):
                run_generated_playwright(
                    test_path=ROOT / "tests" / "acceptance" / "test_hierarchy.py",
                    base_url="http://127.0.0.1:8770",
                    output_directory=output,
                    root_directory=ROOT,
                )

    def test_runner_refuses_code_modified_after_generation(self) -> None:
        generated_root = ROOT / "tests" / "generated"
        source = generated_root / "test_hr_demo_workflow.py"
        manifest = generated_root / "test_hr_demo_workflow.manifest.json"
        with TemporaryDirectory(dir=generated_root) as directory:
            candidate = Path(directory) / "test_tampered.py"
            candidate_manifest = candidate.with_suffix(".manifest.json")
            shutil.copyfile(source, candidate)
            shutil.copyfile(manifest, candidate_manifest)
            candidate.write_text(
                candidate.read_text("utf-8") + "\n# modification manuelle\n",
                "utf-8",
            )

            with self.assertRaisesRegex(ExecutionRunnerError, "empreinte"):
                run_generated_playwright(
                    test_path=candidate,
                    base_url="http://127.0.0.1:8770",
                    output_directory=Path(directory) / "execution",
                    root_directory=ROOT,
                )


if __name__ == "__main__":
    unittest.main()
