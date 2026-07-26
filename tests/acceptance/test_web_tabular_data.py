"""ACC-068 — import tabulaire et aperçu du plan dans l'interface web."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelfonctionnelle.web.app import create_web_app
from sentinelfonctionnelle.web.settings import ServerSettings


class WebTabularDataAcceptanceTests(unittest.TestCase):
    def test_csv_can_be_bound_previewed_and_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinel.db"
            )
            with TestClient(create_web_app(settings)) as client:
                created_project = client.post(
                    "/projects",
                    data={
                        "name": "Données de recette",
                        "description": "Plusieurs saisies",
                        "web_target": "https://data.demo.invalid",
                        "security_policy": "demo-only",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(
                    created_project.headers["location"].rsplit("/", 1)[-1]
                )
                created_plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Formulaires",
                        "objective": "Paramétrer les saisies",
                        "scope": "Création de compte",
                        "approach": "Itérations pilotées par les données",
                        "test_type": "acceptance",
                        "target": "recette",
                    },
                    follow_redirects=False,
                )
                test_plan_id = UUID(created_plan.headers["x-created-id"])
                created_suite = client.post(
                    f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
                    data={
                        "kind": "suite",
                        "name": "Comptes",
                        "objective": "Vérifier la gestion des comptes",
                    },
                    follow_redirects=False,
                )
                suite_id = UUID(created_suite.headers["x-created-id"])
                created_test = client.post(
                    f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Créer un compte",
                        "parent_id": str(suite_id),
                    },
                    follow_redirects=False,
                )
                test_id = UUID(created_test.headers["x-created-id"])

                response = client.post(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    f"/cases/{test_id}/data-binding",
                    data={
                        "mode": "parallel",
                        "max_parallelism": "2",
                        "random_seed": "42",
                        "sample_count": "",
                    },
                    files={
                        "data_file": (
                            "comptes.csv",
                            (
                                "courriel;profil\n"
                                "alice@example.invalid;standard\n"
                                "bob@example.invalid;premium\n"
                                "chloe@example.invalid;standard\n"
                            ).encode(),
                            "text/csv",
                        )
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, response.status_code)

                page = client.get(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    f"/cases/{test_id}"
                )
                self.assertIn("comptes.csv", page.text)
                self.assertIn("3 cas", page.text)
                self.assertIn("Parallèle", page.text)
                self.assertIn("2 lots", page.text)
                self.assertIn("alice@example.invalid", page.text)
                self.assertIn("bob@example.invalid", page.text)

            with TestClient(create_web_app(settings)) as restarted:
                restored = restarted.get(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    f"/cases/{test_id}"
                )
                self.assertIn("comptes.csv", restored.text)
                self.assertIn("Version 1", restored.text)


if __name__ == "__main__":
    unittest.main()
