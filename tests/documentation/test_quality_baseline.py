"""Contrat du contrôle qualité reproductible du lot 0."""

from __future__ import annotations

import unittest
from pathlib import Path

from tools.check_quality import (
    FORMATTED_BASELINE,
    TYPED_BASELINE,
    find_broken_document_links,
    find_constraint_mismatches,
)


ROOT = Path(__file__).resolve().parents[2]


class QualityBaselineDocumentationTests(unittest.TestCase):
    def test_documentation_has_no_broken_local_link(self) -> None:
        self.assertEqual((), find_broken_document_links(ROOT))

    def test_quality_baselines_reference_existing_python_files(self) -> None:
        for relative_path in (*FORMATTED_BASELINE, *TYPED_BASELINE):
            path = ROOT / relative_path
            self.assertTrue(path.is_file(), relative_path)
            self.assertEqual(".py", path.suffix)

    def test_reproducible_constraint_covers_runtime_and_quality_tools(self) -> None:
        constraints = (ROOT / "requirements" / "constraints-py312.txt").read_text(
            encoding="utf-8"
        )
        for dependency in ("fastapi", "playwright", "pytest", "ruff", "mypy"):
            self.assertRegex(constraints, rf"(?im)^{dependency}==[^\s]+$")

        self.assertEqual((), find_constraint_mismatches(ROOT))


if __name__ == "__main__":
    unittest.main()
