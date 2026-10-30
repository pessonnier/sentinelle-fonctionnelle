"""La documentation indispensable au générateur reste disponible hors ligne."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "docs" / "vendor" / "playwright"


class PlaywrightReferenceSnapshotTests(unittest.TestCase):
    def test_official_pages_are_preserved_with_audited_fingerprints(self) -> None:
        expected = {
            "api-testing.html": (
                "E9B3BA978656B6216D94914FF7B9D9CE"
                "6EDE77A712D0FDCAA264DEB08D5A88ED"
            ),
            "assertions.html": (
                "602FE1B5C12A3326C50D7F8DCE6BE36"
                "A6B39FED47C6BC702604F328C8D80D322"
            ),
            "authentication.html": (
                "1B5AC6D627E7D3B955762AF301309C7D0"
                "A581BA3885253A34A0AED77B35D533F"
            ),
            "locators.html": (
                "3DD3A7592A1DEEF3414F325788D75417"
                "E380BBFE189872FA0A70E1C1B1A51152"
            ),
            "pytest-plugin.html": (
                "010D67144C1BE072362B4D232FB51666B"
                "B21F58D0CF5CDA022D9A877945131E8"
            ),
        }
        for filename, fingerprint in expected.items():
            with self.subTest(filename=filename):
                content = (VENDOR / filename).read_bytes()
                self.assertGreater(len(content), 20_000)
                self.assertEqual(fingerprint, sha256(content).hexdigest().upper())

        sources = (VENDOR / "SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("https://playwright.dev/python/docs/locators", sources)
        self.assertIn("27 juillet 2026", sources)


if __name__ == "__main__":
    unittest.main()
