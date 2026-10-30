"""Catalogue DOM rendu après une exploration authentifiée bornée."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from sentinelle_fonctionnelle.application.rendered_page_analysis import (
    RenderedPageAnalysisError,
    RenderedPageSnapshot,
    _apply_page,
    analyze_rendered_page,
    parse_exploration_plan,
)
from sentinelle_fonctionnelle.domain.workflow import AnalyzedPage


ROOT = Path(__file__).resolve().parents[2]
PLAN_PATH = ROOT / "config/examples/hr-demo-rendered-page-plan.json"
WORKFLOW_PATH = ROOT / "config/examples/hr-demo-workflow.json"


class _FakeExplorer:
    def __init__(self, html: str) -> None:
        self.html = html
        self.actions = ()

    def explore(self, plan, actions):
        self.actions = actions
        return RenderedPageSnapshot(
            final_url="http://127.0.0.1:8775/demo/hr/saisie",
            title="Saisie",
            html=self.html,
            browser="fake-chromium",
            source_html="<html><body><h1>Déclarer un nouveau talent</h1></body></html>",
        )


class RenderedPageAnalysisAcceptanceTests(unittest.TestCase):
    def test_data_is_resolved_but_never_exposed_by_the_catalog(self) -> None:
        document = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        explorer = _FakeExplorer(
            """
            <html><head><title>Saisie</title></head><body>
              <h1>Déclarer un nouveau talent</h1>
              <label for="manager-budget">Budget d’accueil autorisé</label>
              <input id="manager-budget" name="manager_budget" type="number">
              <label for="favorite-color">Couleur d’aura préférée</label>
              <input id="favorite-color" name="favorite_color" type="color">
              <label for="manager-dynamic-note">Note dynamique du manager</label>
              <input id="manager-dynamic-note" name="manager_dynamic_note">
            </body></html>
            """
        )
        artifact = analyze_rendered_page(
            document,
            root_directory=ROOT,
            explorer=explorer,
        )
        references = {element.reference for element in artifact.page.elements}
        self.assertIn("page:saisie#favorite-color", references)
        self.assertIn("page:saisie#manager-budget", references)
        self.assertIn("page:saisie#manager-dynamic-note", references)
        self.assertEqual("camille.cactus@example.test", explorer.actions[0].value)
        serialized = json.dumps(artifact.as_dict(), ensure_ascii=False)
        self.assertNotIn("Cactus!2026", serialized)
        self.assertNotIn("camille.cactus@example.test", serialized)
        self.assertEqual({"login": "LOGIN-MANAGER-OK"}, artifact.data_case_ids)
        self.assertEqual(
            (
                "page:saisie#manager-budget",
                "page:saisie#favorite-color",
                "page:saisie#manager-dynamic-note",
            ),
            artifact.rendered_only_references,
        )

    def test_remote_origin_unknown_action_and_too_many_actions_are_rejected(self) -> None:
        document = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        remote = copy.deepcopy(document)
        remote["start_url"] = "https://example.test:443/login"
        with self.assertRaisesRegex(RenderedPageAnalysisError, "boucle locale"):
            parse_exploration_plan(remote)

        script = copy.deepcopy(document)
        script["actions"][0]["action"] = "javascript"
        with self.assertRaisesRegex(RenderedPageAnalysisError, "interdite"):
            parse_exploration_plan(script)

        oversized = copy.deepcopy(document)
        oversized["actions"] = oversized["actions"] * 4
        with self.assertRaisesRegex(RenderedPageAnalysisError, "20 actions"):
            parse_exploration_plan(oversized)

    def test_catalog_application_preserves_workflow_references(self) -> None:
        document = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        rendered = AnalyzedPage.from_mapping(
            {
                "url": "http://127.0.0.1:8000/demo/hr/saisie",
                "title": "Saisie rendue",
                "fingerprint": "rendered-sha",
                "elements": [
                    {
                        "reference": "page:saisie#declarer-un-nouveau-talent",
                        "kind": "h1",
                        "role": "heading",
                        "label": "Déclarer un nouveau talent",
                        "input_type": "heading",
                        "locator": {
                            "strategy": "role",
                            "value": "heading|Déclarer un nouveau talent",
                        },
                        "options": [],
                    },
                    *document["workflow"]["pages"][1]["elements"][1:],
                    {
                        "reference": "page:saisie#manager-dynamic-note",
                        "kind": "input",
                        "role": "textbox",
                        "label": "Note dynamique du manager",
                        "input_type": "text",
                        "locator": {
                            "strategy": "label",
                            "value": "Note dynamique du manager",
                        },
                        "options": [],
                    },
                ],
            }
        )
        updated, matched, new = _apply_page(document, rendered)
        page = updated["workflow"]["pages"][1]
        references = {element["reference"] for element in page["elements"]}
        self.assertIn("page:saisie#heading", references)
        self.assertIn("page:saisie#manager-dynamic-note", references)
        self.assertGreater(matched, 10)
        self.assertEqual(1, new)

    def test_catalog_application_refuses_to_remove_a_used_target(self) -> None:
        document = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
        rendered = AnalyzedPage.from_mapping(
            {
                "url": "http://127.0.0.1:8000/demo/hr/saisie",
                "title": "Catalogue incomplet",
                "fingerprint": "incomplete",
                "elements": document["workflow"]["pages"][1]["elements"][1:],
            }
        )
        with self.assertRaisesRegex(
            RenderedPageAnalysisError,
            "page:saisie#heading",
        ):
            _apply_page(document, rendered)


if __name__ == "__main__":
    unittest.main()
