"""ACC-054 — tutoriel HTML du mode local."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TUTORIAL = ROOT / "docs" / "tutorial-local.html"
VALIDATOR = (
    ROOT
    / "skills"
    / "write-implementation-html-docs"
    / "scripts"
    / "validate_html_doc.py"
)


class LocalTutorialDocumentationTests(unittest.TestCase):
    def test_tutorial_is_structured_traceable_and_current(self) -> None:
        self.assertTrue(TUTORIAL.is_file(), "Le tutoriel HTML doit exister.")
        completed = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(TUTORIAL),
                "--spec",
                str(ROOT / "docs" / "SPECIFICATIONS.md"),
                "--status",
                str(ROOT / "docs" / "IMPLEMENTATION_STATUS.md"),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_tutorial_documents_real_commands_and_current_limits(self) -> None:
        content = TUTORIAL.read_text(encoding="utf-8")
        for command in (
            "sentinelle_fonctionnelle.cli serve",
            "demo-hierarchy",
            "demo-deployment --mode local",
            "demo-persistence",
            "unittest discover",
        ):
            self.assertIn(command, content)
        self.assertIn("SQLite", content)
        self.assertIn("FastAPI", content)
        self.assertIn("interface web", content)
        self.assertIn("Pas encore disponible", content)
        self.assertIn("SENTINELLE_FONCTIONNELLE_DATABASE", content)
        self.assertIn("ACC-060", content)
        self.assertIn("proofs/iteration-005.md", content)
        self.assertIn("ACC-063", content)
        self.assertIn("ACC-064", content)
        self.assertIn("ACC-065", content)
        self.assertIn("proofs/iteration-006.md", content)
        self.assertIn("Pas-à-pas", content)
        self.assertIn("Given/When/Then", content)
        self.assertIn("Tableau d’exemples", content)
        self.assertIn("Checklist", content)
        self.assertIn("ACC-066", content)
        self.assertIn("ACC-067", content)
        self.assertIn("ACC-068", content)
        self.assertIn("proofs/iteration-007.md", content)
        self.assertIn("modele-donnees-tests.xlsx", content)
        self.assertIn("Parallèle", content)
        self.assertIn("Aléatoire", content)
        self.assertIn('"schema_version":8', content)
        self.assertIn("ACC-069", content)
        self.assertIn("ACC-070", content)
        self.assertIn("ACC-071", content)
        self.assertIn("ACC-072", content)
        self.assertNotIn("interface web FastAPI est non disponible", content)
        self.assertNotIn("C:\\Users\\", content)
        self.assertNotIn("D:\\minidev\\", content)


if __name__ == "__main__":
    unittest.main()
