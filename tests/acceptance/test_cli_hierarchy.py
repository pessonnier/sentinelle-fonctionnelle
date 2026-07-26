"""Point d'entrée réel de la tranche ACC-002/ACC-003."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class HierarchyCliAcceptanceTests(unittest.TestCase):
    def test_demo_hierarchy_exercises_creation_and_move(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "sentinelle_fonctionnelle.cli",
                "demo-hierarchy",
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(4, result["node_count"])
        self.assertEqual(2, result["case_count"])
        self.assertEqual(
            result["moved_case"]["id"],
            result["moved_case"]["original_id"],
        )
        self.assertEqual(1, result["moved_case"]["history_count"])
        self.assertEqual(
            ["Régression", "Paiement refusé"],
            result["moved_case"]["path"],
        )

    def test_local_and_online_commands_expose_equivalent_capabilities(self) -> None:
        local = self._run_cli("demo-deployment", "--mode", "local")
        online = self._run_cli(
            "demo-deployment",
            "--mode",
            "online",
            "--subject",
            "alice",
        )

        self.assertEqual("local", local.pop("mode"))
        self.assertEqual("online", online.pop("mode"))
        self.assertEqual(local, online)

    def test_sqlite_command_restores_data_after_reopening_database(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "sentinel.db"
            result = self._run_cli(
                "demo-persistence",
                "--database",
                str(database),
            )

        self.assertEqual(2, result["project_count"])
        self.assertTrue(result["identity_preserved"])
        self.assertEqual(
            ["Régression", "Paiement refusé"],
            result["restored_path"],
        )
        self.assertEqual(1, result["history_count"])

    def _run_cli(self, *arguments: str) -> dict[str, object]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "src")
        completed = subprocess.run(
            [sys.executable, "-m", "sentinelle_fonctionnelle.cli", *arguments],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)


if __name__ == "__main__":
    unittest.main()
