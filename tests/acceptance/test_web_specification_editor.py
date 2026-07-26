"""ACC-063 à ACC-065 — éditeur web sans YAML et vues calculées."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class WebSpecificationEditorAcceptanceTests(unittest.TestCase):
    def test_editor_saves_four_styles_and_exposes_organization_views(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            settings = ServerSettings(
                database=Path(temporary_directory) / "sentinel.db"
            )
            with TestClient(create_web_app(settings)) as client:
                project = client.post(
                    "/projects",
                    data={
                        "name": "Éditeur fonctionnel",
                        "description": "Spécification sans YAML",
                        "web_target": "https://editor.demo.invalid",
                        "security_policy": "demo-only",
                    },
                    follow_redirects=False,
                )
                project_id = UUID(project.headers["location"].rsplit("/", 1)[-1])
                created_plan = client.post(
                    f"/projects/{project_id}/test-plans",
                    data={
                        "name": "Connexion",
                        "objective": "Définir les parcours",
                        "scope": "Authentification des clients",
                        "approach": "Cas nominaux et erreurs métier",
                        "test_type": "acceptance",
                        "target": "recette",
                        "tags": "authentification",
                    },
                    follow_redirects=False,
                )
                test_plan_id = UUID(created_plan.headers["x-created-id"])
                created_suite = client.post(
                    f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
                    data={
                        "kind": "suite",
                        "name": "Accès client",
                        "objective": "Vérifier les accès au portail",
                    },
                    follow_redirects=False,
                )
                suite_id = UUID(created_suite.headers["x-created-id"])

                styles = {
                    "steps": (
                        "Pas-à-pas",
                        "Saisir un identifiant => Le champ est renseigné",
                    ),
                    "gherkin": (
                        "Given/When/Then",
                        "Étant donné un client\nQuand il se connecte\n"
                        "Alors le tableau de bord apparaît",
                    ),
                    "examples": (
                        "Tableau d’exemples",
                        "profil ; résultat\nclient ; autorisé",
                    ),
                    "checklist": (
                        "Checklist",
                        "Le titre est visible\nLe bouton est actif",
                    ),
                }
                test_ids: list[UUID] = []
                for style, (_, source_text) in styles.items():
                    created_node = client.post(
                        f"/projects/{project_id}/test-plans/{test_plan_id}/nodes",
                        data={
                            "kind": "test",
                            "name": f"Cas {style}",
                            "tags": f"authentification, {style}",
                            "parent_id": str(suite_id),
                        },
                        follow_redirects=False,
                    )
                    test_id = UUID(created_node.headers["x-created-id"])
                    test_ids.append(test_id)
                    saved = client.post(
                        f"/projects/{project_id}/test-plans/{test_plan_id}"
                        f"/cases/{test_id}/specification",
                        data={
                            "style": style,
                            "objective": f"Vérifier le mode {style}",
                            "actor_name": "Client",
                            "environment": "recette",
                            "preconditions": "Le compte existe",
                            "data_sets": "client-standard",
                            "postconditions": "La session est fermée",
                            "requirements": "REQ-AUTH-01",
                            "business_rules": "BR-SEC-02",
                            "execution_declaration": "on_merge_request",
                            "source_text": source_text,
                        },
                        follow_redirects=False,
                    )
                    self.assertEqual(303, saved.status_code)
                    editor = client.get(
                        f"/projects/{project_id}/test-plans/{test_plan_id}"
                        f"/cases/{test_id}"
                    )
                    self.assertIn("Version 1", editor.text)
                    self.assertIn(f"Vérifier le mode {style}", editor.text)

                plan_url = (
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                )
                page = client.get(plan_url)
                self.assertIn("Accès client", page.text)
                self.assertNotIn("Écrivez du YAML", page.text)

                for organization, group in (
                    ("tag", "authentification"),
                    ("requirement", "REQ-AUTH-01"),
                    ("business_rule", "BR-SEC-02"),
                    ("style", "Pas-à-pas"),
                ):
                    grouped = client.get(
                        f"{plan_url}?organization={organization}"
                    )
                    self.assertEqual(200, grouped.status_code)
                    self.assertIn(group, grouped.text)

                searched = client.get(
                    f"{plan_url}?organization=tree&q=gherkin"
                )
                self.assertIn(str(test_ids[1]), searched.text)
                self.assertNotIn(str(test_ids[0]), searched.text)

            with TestClient(create_web_app(settings)) as restarted:
                restored = restarted.get(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    "?organization=style"
                )
                self.assertIn("Given/When/Then", restored.text)
                restored_case = restarted.get(
                    f"/projects/{project_id}/test-plans/{test_plan_id}"
                    f"/cases/{test_ids[1]}"
                )
                self.assertIn("Version 1", restored_case.text)


if __name__ == "__main__":
    unittest.main()
