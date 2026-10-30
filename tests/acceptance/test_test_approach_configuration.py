"""Gestion YAML et sélection versionnée des approches de test."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import UUID

import yaml
from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.domain import TestApproachCatalog
from sentinelle_fonctionnelle.web.app import (
    DEFAULT_TEST_APPROACHES,
    create_web_app,
)
from sentinelle_fonctionnelle.web.settings import ServerSettings


class TestApproachConfigurationAcceptanceTests(unittest.TestCase):
    def test_yaml_catalog_preserves_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            catalog_path = Path(temporary_directory) / "test-approaches.yaml"
            catalog = TestApproachCatalog.open(
                catalog_path,
                defaults_path=DEFAULT_TEST_APPROACHES,
            )
            created = catalog.create(
                profile_id="security-boundaries",
                name="Sécurité et limites",
                description="Couvre les règles d'accès et les limites.",
                test_levels=("test système",),
                test_types=("test fonctionnel",),
                test_design_techniques=("analyse des valeurs limites",),
                risk_based=True,
                automation_strategy="Automatiser les contrôles répétables.",
                evidence_requirements=("capture en cas d'échec",),
                generation_instructions=("tester autour de chaque limite",),
                enabled=True,
            )
            updated = catalog.update(
                created.id,
                name="Sécurité, décisions et limites",
                description="Couvre les règles d'accès, décisions et limites.",
                test_levels=("test système", "test d'acceptation"),
                test_types=("test fonctionnel",),
                test_design_techniques=(
                    "tables de décision",
                    "analyse des valeurs limites",
                ),
                risk_based=True,
                automation_strategy="Automatiser les contrôles stables.",
                evidence_requirements=("capture en cas d'échec",),
                generation_instructions=("tester chaque règle réalisable",),
                enabled=True,
            )

            reopened = TestApproachCatalog.open(catalog_path)
            self.assertEqual(1, created.version)
            self.assertEqual(2, updated.version)
            self.assertEqual(
                "Sécurité et limites",
                reopened.get(created.id, 1).name,
            )
            self.assertEqual(
                "Sécurité, décisions et limites",
                reopened.get(created.id).name,
            )
            document = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
            configured = next(
                approach
                for approach in document["approaches"]
                if approach["id"] == created.id
            )
            self.assertEqual(2, len(configured["versions"]))

    def test_configuration_form_creates_profile_selected_by_test_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = ServerSettings(
                database=root / "sentinelle.db",
                test_approaches=root / "configuration" / "approaches.yaml",
            )
            with TestClient(create_web_app(settings)) as client:
                page = client.get("/configuration/test-approaches")
                self.assertEqual(200, page.status_code)
                self.assertIn("Tests fonctionnels orientés risques", page.text)
                self.assertIn("Créer une approche", page.text)
                self.assertIn('aria-controls="new-test-approach"', page.text)
                self.assertIn(
                    'id="new-test-approach" class="form-panel entity-create-panel" hidden',
                    page.text,
                )

                created = client.post(
                    "/configuration/test-approaches",
                    data={
                        "profile_id": "state-transitions",
                        "name": "Transitions d’états",
                        "description": "Couvre les changements d’état métier.",
                        "test_levels": "test système",
                        "test_types": "test fonctionnel",
                        "test_design_techniques": "transition d’états",
                        "automation_strategy": "Automatiser les transitions stables.",
                        "evidence_requirements": "état final",
                        "generation_instructions": "couvrir chaque transition valide",
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, created.status_code)

                project = client.post(
                    "/projects",
                    data={
                        "name": "Workflow",
                        "description": "États métier",
                        "web_target": "https://workflow.demo.invalid",
                        "security_policy": "demo-only",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
                project_page = client.get(f"/projects/{project_id}")
                self.assertIn("Transitions d’états", project_page.text)

                plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Cycle de vie",
                        "objective": "Valider les transitions",
                        "scope": "États actifs",
                        "test_approach": "state-transitions@1",
                        "target": "demo",
                        "test_type": "acceptance",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, plan.status_code)
                plan_id = UUID(plan.headers["x-created-id"])
                stored = client.app.state.project_application.get_project(
                    None,
                    project_id,
                ).test_plan(plan_id)
                self.assertEqual("state-transitions", stored.test_approach_id)
                self.assertEqual(1, stored.test_approach_version)

                updated = client.post(
                    "/configuration/test-approaches/state-transitions",
                    data={
                        "name": "Transitions et états interdits",
                        "description": (
                            "Couvre les changements d’état valides et invalides."
                        ),
                        "test_levels": "test système",
                        "test_types": "test fonctionnel",
                        "test_design_techniques": "transition d’états",
                        "automation_strategy": (
                            "Automatiser les transitions déterministes."
                        ),
                        "evidence_requirements": "état final",
                        "generation_instructions": (
                            "couvrir chaque transition valide et invalide"
                        ),
                        "enabled": "true",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, updated.status_code)
                current_page = client.get(f"/projects/{project_id}")
                self.assertIn(
                    'value="state-transitions@2"',
                    current_page.text,
                )
                still_pinned = (
                    client.app.state.project_application.get_project(
                        None,
                        project_id,
                    ).test_plan(plan_id)
                )
                self.assertEqual(1, still_pinned.test_approach_version)
                yaml_text = settings.test_approaches.read_text(encoding="utf-8")
                self.assertIn("state-transitions", yaml_text)
                self.assertIn("version: 2", yaml_text)


if __name__ == "__main__":
    unittest.main()
