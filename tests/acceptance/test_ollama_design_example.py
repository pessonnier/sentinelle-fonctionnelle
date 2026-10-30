"""La réponse réelle conservée de Qwen respecte le contrat applicatif strict."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from sentinelle_fonctionnelle.domain import DesignAssistantResponse


ROOT = Path(__file__).resolve().parents[2]


class OllamaDesignExampleAcceptanceTests(unittest.TestCase):
    def test_real_qwen_response_is_an_applicable_developed_case(self) -> None:
        payload = json.loads(
            (
                ROOT
                / "docs"
                / "proofs"
                / "ollama-design-case-response.json"
            ).read_text(encoding="utf-8")
        )

        response = DesignAssistantResponse.from_mapping(payload)

        self.assertEqual((), response.questions)
        self.assertEqual(4, len(response.operations))
        self.assertEqual(
            [
                "fill",
                "fill",
                "click",
                "none",
            ],
            [operation.value["action"] for operation in response.operations],
        )
        self.assertEqual(
            "text",
            response.operations[-1].value["assertion"],
        )
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("{{url.", serialized)
        self.assertIn("{{secret.client-password}}", serialized)


if __name__ == "__main__":
    unittest.main()
