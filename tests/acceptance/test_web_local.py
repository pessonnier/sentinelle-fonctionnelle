"""ACC-060, ACC-062 et ACC-069 à ACC-072 — parcours web hiérarchique."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelfonctionnelle.web.app import create_web_app
from sentinelfonctionnelle.web.settings import ServerSettings


class LocalWebAcceptanceTests(unittest.TestCase):
    def test_web_workflow_creates_projects_tree_and_restores_them(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "state" / "sentinel.db"
            settings = ServerSettings(database=database)

            with TestClient(create_web_app(settings)) as client:
                health = client.get("/health")
                self.assertEqual(200, health.status_code)
                self.assertEqual(
                    {"status": "ok", "mode": "local", "schema_version": 5},
                    health.json(),
                )
                home = client.get("/")
                self.assertEqual(200, home.status_code)
                self.assertIn("Nouveau projet", home.text)

                first_project_id = self._create_project(
                    client,
                    name="Portail citoyen",
                    target="https://portail.demo.invalid",
                )
                second_project_id = self._create_project(
                    client,
                    name="Back-office",
                    target="https://backoffice.demo.invalid",
                )
                test_plan_id = self._create_test_plan(
                    client,
                    project_id=first_project_id,
                )
                suite_id = self._create_node(
                    client,
                    project_id=first_project_id,
                    test_plan_id=test_plan_id,
                    kind="suite",
                    name="Régression",
                )
                subsuite_id = self._create_node(
                    client,
                    project_id=first_project_id,
                    test_plan_id=test_plan_id,
                    kind="folder",
                    name="Authentification",
                    parent_id=suite_id,
                )
                test_id = self._create_node(
                    client,
                    project_id=first_project_id,
                    test_plan_id=test_plan_id,
                    kind="test",
                    name="Connexion valide",
                    parent_id=subsuite_id,
                )

                project_page = client.get(f"/projects/{first_project_id}")
                self.assertEqual(200, project_page.status_code)
                self.assertIn("Parcours critiques", project_page.text)
                plan_page = client.get(
                    f"/projects/{first_project_id}/test-plans/{test_plan_id}"
                )
                self.assertEqual(200, plan_page.status_code)
                for expected in (
                    "Régression",
                    "Authentification",
                    "Connexion valide",
                ):
                    self.assertIn(expected, plan_page.text)

            with TestClient(create_web_app(settings)) as restarted:
                home = restarted.get("/")
                self.assertIn("Portail citoyen", home.text)
                self.assertIn("Back-office", home.text)
                restored = restarted.get(f"/projects/{first_project_id}")
                self.assertIn("Parcours critiques", restored.text)
                restored_plan = restarted.get(
                    f"/projects/{first_project_id}/test-plans/{test_plan_id}"
                )
                self.assertIn(str(test_id), restored_plan.text)
                self.assertNotEqual(first_project_id, second_project_id)
                self.assertTrue(database.is_file())

    def test_web_rename_move_order_and_recursive_archive_keep_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinel.db"
            )
            with TestClient(create_web_app(settings)) as client:
                project_id = self._create_project(
                    client,
                    name="Édition",
                    target="https://edition.demo.invalid",
                )
                test_plan_id = self._create_test_plan(client, project_id=project_id)
                first_suite = self._create_node(
                    client,
                    project_id=project_id,
                    test_plan_id=test_plan_id,
                    kind="suite",
                    name="Première suite",
                )
                second_suite = self._create_node(
                    client,
                    project_id=project_id,
                    test_plan_id=test_plan_id,
                    kind="suite",
                    name="Deuxième suite",
                )
                test_id = self._create_node(
                    client,
                    project_id=project_id,
                    test_plan_id=test_plan_id,
                    kind="test",
                    name="Ancien nom",
                    parent_id=first_suite,
                )

                renamed = client.post(
                    self._node_url(project_id, test_plan_id, test_id, "rename"),
                    data={"name": "Nom corrigé"},
                    follow_redirects=False,
                )
                self.assertEqual(303, renamed.status_code)
                moved = client.post(
                    self._node_url(project_id, test_plan_id, test_id, "move"),
                    data={"new_parent_id": str(second_suite), "position": "0"},
                    follow_redirects=False,
                )
                self.assertEqual(303, moved.status_code)
                archived = client.post(
                    self._node_url(
                        project_id,
                        test_plan_id,
                        second_suite,
                        "archive",
                    ),
                    follow_redirects=False,
                )
                self.assertEqual(303, archived.status_code)

            with TestClient(create_web_app(settings)) as restarted:
                page = restarted.get(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    "?show_archived=true"
                )
                self.assertIn("Nom corrigé", page.text)
                self.assertIn(str(test_id), page.text)
                self.assertIn("Archivé", page.text)
                project = restarted.app.state.project_application.get_project(
                    None,
                    project_id,
                )
                restored_plan = project.test_plan(test_plan_id)
                restored_test = restored_plan.node(test_id)
                self.assertEqual(test_id, restored_test.id)
                self.assertEqual(second_suite, restored_test.parent_id)
                self.assertEqual(0, restored_test.order)
                self.assertTrue(restored_test.archived)
                self.assertTrue(restored_plan.node(second_suite).archived)

    def test_invalid_parent_identifier_is_refused_without_server_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinel.db"
            )
            with TestClient(create_web_app(settings), raise_server_exceptions=False) as client:
                project_id = self._create_project(
                    client,
                    name="Validation",
                    target="https://validation.demo.invalid",
                )
                test_plan_id = self._create_test_plan(client, project_id=project_id)
                response = client.post(
                    f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
                    data={
                        "kind": "test",
                        "name": "Parent invalide",
                        "parent_id": "pas-un-uuid",
                    },
                )
                self.assertEqual(400, response.status_code)
                self.assertIn("identifiant", response.text)

    def test_case_editor_orders_sections_and_pairs_steps_with_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinel.db"
            )
            with TestClient(create_web_app(settings)) as client:
                project_id = self._create_project(
                    client,
                    name="Parcours cas",
                    target="https://cases.demo.invalid",
                )
                test_plan_id = self._create_test_plan(
                    client,
                    project_id=project_id,
                )
                suite_id = self._create_node(
                    client,
                    project_id=project_id,
                    test_plan_id=test_plan_id,
                    kind="suite",
                    name="Authentification",
                )
                case_id = self._create_node(
                    client,
                    project_id=project_id,
                    test_plan_id=test_plan_id,
                    kind="test",
                    name="Connexion valide",
                    parent_id=suite_id,
                )
                case_url = (
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    f"/cases/{case_id}"
                )

                editor = client.get(case_url)
                section_positions = tuple(
                    editor.text.index(label)
                    for label in (
                        "Contexte",
                        "Étapes de test",
                        "Données de test",
                        "Résultats attendus",
                    )
                )
                self.assertEqual(tuple(sorted(section_positions)), section_positions)
                self.assertIn("Aucun fichier tabulaire associé", editor.text)
                self.assertIn("Authentification", editor.text)

                mismatch = client.post(
                    f"{case_url}/specification",
                    data={
                        "style": "steps",
                        "objective": "Accéder au compte",
                        "actor_name": "Client",
                        "step_actions": "Ouvrir la page\nValider",
                        "expected_results": "La page est visible",
                    },
                )
                self.assertEqual(400, mismatch.status_code)
                self.assertIn("exactement un résultat attendu", mismatch.text)

                saved = client.post(
                    f"{case_url}/specification",
                    data={
                        "style": "steps",
                        "objective": "Accéder au compte",
                        "actor_name": "Client",
                        "step_actions": "Ouvrir la page\nValider",
                        "expected_results": (
                            "La page est visible\nLe tableau de bord apparaît"
                        ),
                        "data_sets": "client-standard",
                    },
                    follow_redirects=False,
                )
                self.assertEqual(303, saved.status_code)
                reopened = client.get(case_url)
                for expected in (
                    "Accéder au compte",
                    "Ouvrir la page",
                    "Valider",
                    "client-standard",
                    "Le tableau de bord apparaît",
                ):
                    self.assertIn(expected, reopened.text)

    @staticmethod
    def _create_project(
        client: TestClient,
        *,
        name: str,
        target: str,
    ) -> UUID:
        response = client.post(
            "/projects",
            data={
                "name": name,
                "description": f"Projet {name}",
                "web_target": target,
                "security_policy": "demo-only",
            },
            follow_redirects=False,
        )
        if response.status_code != 303:
            raise AssertionError(response.text)
        return UUID(response.headers["location"].rsplit("/", 1)[-1])

    @staticmethod
    def _create_test_plan(client: TestClient, *, project_id: UUID) -> UUID:
        response = client.post(
            f"/projects/{project_id}/test-plans",
            data={
                "name": "Parcours critiques",
                "objective": "Sécuriser les fonctions importantes",
                "scope": "Authentification et parcours critiques",
                "approach": "Tests fonctionnels guidés par les risques",
                "test_type": "acceptance",
                "target": "demo",
                "tags": "critique, web",
            },
            follow_redirects=False,
        )
        if response.status_code != 303:
            raise AssertionError(response.text)
        return UUID(response.headers["x-created-id"])

    @staticmethod
    def _create_node(
        client: TestClient,
        *,
        project_id: UUID,
        test_plan_id: UUID,
        kind: str,
        name: str,
        parent_id: UUID | None = None,
    ) -> UUID:
        response = client.post(
            f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
            data={
                "kind": kind,
                "name": name,
                "parent_id": str(parent_id) if parent_id else "",
                "objective": (
                    f"Vérifier {name.lower()}" if kind == "suite" else ""
                ),
            },
            follow_redirects=False,
        )
        if response.status_code != 303:
            raise AssertionError(response.text)
        return UUID(response.headers["x-created-id"])

    @staticmethod
    def _node_url(
        project_id: UUID,
        test_plan_id: UUID,
        node_id: UUID,
        action: str,
    ) -> str:
        return (
            f"/projects/{project_id}/test-plans/{test_plan_id}"
            f"/nodes/{node_id}/{action}"
        )


if __name__ == "__main__":
    unittest.main()
