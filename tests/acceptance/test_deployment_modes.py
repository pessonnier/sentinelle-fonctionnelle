"""ACC-051 et ACC-052 — multi-utilisateur et parité des déploiements."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sentinelfonctionnelle.application.projects import (
    ApplicationMode,
    AuthenticatedIdentity,
    AuthenticationRequired,
    AuthorizationDenied,
    ProjectApplication,
    ProjectNotFound,
    ProjectRole,
)
from sentinelfonctionnelle.domain import NodeKind


class OnlineIsolationAcceptanceTests(unittest.TestCase):
    """ACC-051 — chaque utilisateur ne voit que ses projets autorisés."""

    def setUp(self) -> None:
        self.application = ProjectApplication.in_memory(ApplicationMode.ONLINE)
        self.alice = AuthenticatedIdentity("alice")
        self.bob = AuthenticatedIdentity("bob")

    def test_online_mode_requires_an_authenticated_identity(self) -> None:
        with self.assertRaises(AuthenticationRequired):
            self.application.list_projects(actor=None)

        with self.assertRaises(AuthenticationRequired):
            self.application.create_project(
                actor=None,
                name="Projet anonyme",
                description="Refus attendu",
                web_target="https://anonymous.invalid",
                security_policy="restricted",
            )

    def test_projects_are_filtered_and_direct_ids_do_not_grant_access(self) -> None:
        alice_project = self.application.create_project(
            actor=self.alice,
            name="Projet Alice",
            description="Visible uniquement par Alice",
            web_target="https://alice.invalid",
            security_policy="restricted",
        )
        bob_project = self.application.create_project(
            actor=self.bob,
            name="Projet Bob",
            description="Visible uniquement par Bob",
            web_target="https://bob.invalid",
            security_policy="restricted",
        )

        self.assertEqual(
            ["Projet Alice"],
            [project.name for project in self.application.list_projects(self.alice)],
        )
        self.assertEqual(
            ["Projet Bob"],
            [project.name for project in self.application.list_projects(self.bob)],
        )
        with self.assertRaises(ProjectNotFound):
            self.application.get_project(self.alice, bob_project.id)
        with self.assertRaises(ProjectNotFound):
            self.application.get_project(self.bob, alice_project.id)

    def test_viewer_can_consult_a_shared_project_but_cannot_modify_it(self) -> None:
        project = self.application.create_project(
            actor=self.alice,
            name="Projet partagé",
            description="Alice autorise Bob en lecture",
            web_target="https://shared.invalid",
            security_policy="restricted",
        )
        self.application.add_member(
            actor=self.alice,
            project_id=project.id,
            member=self.bob,
            role=ProjectRole.VIEWER,
        )

        self.assertEqual(project, self.application.get_project(self.bob, project.id))
        with self.assertRaises(AuthorizationDenied):
            self.application.create_test_set(
                actor=self.bob,
                project_id=project.id,
                name="Modification interdite",
                objective="Vérifier le rôle viewer",
                test_type="acceptance",
                target="shared",
            )


class DeploymentParityAcceptanceTests(unittest.TestCase):
    """ACC-052 — le même contrat métier s’exécute dans les deux modes."""

    def test_local_and_online_modes_expose_the_same_project_capabilities(self) -> None:
        local = ProjectApplication.in_memory(ApplicationMode.LOCAL)
        online = ProjectApplication.in_memory(ApplicationMode.ONLINE)
        online_actor = AuthenticatedIdentity("online-owner")

        local_result = self._exercise_project_contract(local, actor=None)
        online_result = self._exercise_project_contract(online, actor=online_actor)

        self.assertEqual(local_result, online_result)

    def _exercise_project_contract(
        self,
        application: ProjectApplication,
        *,
        actor: AuthenticatedIdentity | None,
    ) -> dict[str, object]:
        first_project = application.create_project(
            actor=actor,
            name="Projet principal",
            description="Contrat partagé",
            web_target="https://demo.invalid",
            security_policy="demo-only",
        )
        application.create_project(
            actor=actor,
            name="Projet secondaire",
            description="Vérifie le multi-projet",
            web_target="https://secondary.invalid",
            security_policy="demo-only",
        )
        test_set = application.create_test_set(
            actor=actor,
            project_id=first_project.id,
            name="Parcours critiques",
            objective="Vérifier la parité",
            test_type="acceptance",
            target="demo",
        )
        suite = application.add_node(
            actor=actor,
            project_id=first_project.id,
            test_set_id=test_set.id,
            kind=NodeKind.SUITE,
            name="Connexion",
            objective="Vérifier le parcours de connexion",
        )
        test = application.add_node(
            actor=actor,
            project_id=first_project.id,
            test_set_id=test_set.id,
            kind=NodeKind.TEST,
            name="Connexion réussie",
            parent_id=suite.id,
        )

        return {
            "project_names": [
                project.name
                for project in application.list_projects(actor)
            ],
            "test_set_name": test_set.name,
            "test_path": list(test_set.path(test.id)),
        }


if __name__ == "__main__":
    unittest.main()
