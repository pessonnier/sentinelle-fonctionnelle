"""Les ressources officielles du thème Défense restent locales et auditables."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / "src" / "sentinelle_fonctionnelle" / "web" / "static"
VENDOR = ROOT / "docs" / "vendor" / "dsfr"


class DefenseThemeReferenceSnapshotTests(unittest.TestCase):
    def test_official_assets_keep_their_audited_fingerprints(self) -> None:
        expected = {
            "dsfr-logo.min.css": (
                "15F30D6475528F71F2852A995C5C33FA"
                "7AEBBB47B0C1274E96DB7DABA8F19E04"
            ),
            "defense-rafale.svg": (
                "690E666FD568D42CD7EA2E51A8756489"
                "6C324629B283A617467DF3164D5B45C4"
            ),
        }
        for filename, fingerprint in expected.items():
            with self.subTest(filename=filename):
                content = (STATIC / filename).read_bytes()
                self.assertGreater(len(content), 3_000)
                self.assertEqual(
                    fingerprint,
                    sha256(content).hexdigest().upper(),
                )

        sources = (VENDOR / "SOURCES.md").read_text(encoding="utf-8")
        license_text = (VENDOR / "LICENSE.md").read_text(encoding="utf-8")
        self.assertIn("2 août 2026", sources)
        self.assertIn("defense.gouv.fr", sources)
        self.assertIn("`1.15.0`", sources)
        self.assertIn("MIT License", license_text)
        self.assertIn("fonte Marianne", license_text)


if __name__ == "__main__":
    unittest.main()
