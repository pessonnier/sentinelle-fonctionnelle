"""La documentation indispensable au profil Ollama reste auditable hors ligne."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "docs" / "vendor" / "ollama"


class OllamaReferenceSnapshotTests(unittest.TestCase):
    def test_official_pages_are_preserved_with_audited_fingerprints(self) -> None:
        expected = {
            "openai-compatibility.html": (
                "1C7E6779F63D7AF2C6E798B7F86DB323"
                "093F53A85C9AA33F978598D002A63601"
            ),
            "structured-outputs.html": (
                "BEAD27EFC0B9BE8AD187E6C498A95670"
                "D54CFAD09C6882592223BA3D190B7D9A"
            ),
            "modelfile.html": (
                "117EC405AB9DB5FCDFB93C93BE095C92"
                "E5ABFF9541969B93FFACB1228133E639"
            ),
            "qwen3.6-tags.html": (
                "C24D5BC2F0DF8E58037A918A8EC8119D"
                "8CF89F92DFBDB5A1F00BE8B2CE12FAC1"
            ),
        }
        for filename, fingerprint in expected.items():
            with self.subTest(filename=filename):
                content = (VENDOR / filename).read_bytes()
                self.assertGreater(len(content), 100_000)
                self.assertEqual(fingerprint, sha256(content).hexdigest().upper())

        sources = (VENDOR / "SOURCES.md").read_text(encoding="utf-8")
        procedure = (ROOT / "docs" / "llm" / "ollama.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("29 juillet 2026", sources)
        self.assertIn("api/openai-compatibility", sources)
        self.assertIn("qwen3.6-35b-a3b-q4_K_M_128k:latest", procedure)
        self.assertIn("112,3 s", procedure)


if __name__ == "__main__":
    unittest.main()
