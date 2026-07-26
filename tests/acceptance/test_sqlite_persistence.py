"""ACC-053 — persistance locale et migrations SQLite."""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sentinelfonctionnelle.application.projects import ProjectApplication
from sentinelfonctionnelle.domain import NodeKind


class SQLitePersistenceAcceptanceTests(unittest.TestCase):
    def test_restart_restores_projects_tree_move_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "sentinel.db"
            first_process = ProjectApplication.sqlite(database)
            primary = first_process.create_project(
                actor=None,
                name="Projet principal",
                description="Persisté localement",
                web_target="https://demo.invalid",
                security_policy="demo-only",
            )
            secondary = first_process.create_project(
                actor=None,
                name="Projet secondaire",
                description="Vérifie le multi-projet",
                web_target="https://secondary.invalid",
                security_policy="demo-only",
            )
            test_set = first_process.create_test_set(
                actor=None,
                project_id=primary.id,
                name="Parcours critiques",
                objective="Vérifier le redémarrage",
                test_type="acceptance",
                target="demo",
            )
            suite = first_process.add_node(
                actor=None,
                project_id=primary.id,
                test_set_id=test_set.id,
                kind=NodeKind.SUITE,
                name="Régression",
                objective="Exécuter les contrôles de régression",
            )
            subsuite = first_process.add_node(
                actor=None,
                project_id=primary.id,
                test_set_id=test_set.id,
                kind=NodeKind.SUITE,
                name="Paiement",
                parent_id=suite.id,
                objective="Vérifier le parcours de paiement",
            )
            test = first_process.add_node(
                actor=None,
                project_id=primary.id,
                test_set_id=test_set.id,
                kind=NodeKind.TEST,
                name="Paiement refusé",
                parent_id=subsuite.id,
            )
            occurred_at = datetime(2026, 7, 25, 20, 30, tzinfo=UTC)
            first_process.record_result(
                actor=None,
                project_id=primary.id,
                test_set_id=test_set.id,
                test_id=test.id,
                occurred_at=occurred_at,
                succeeded=False,
                duration_ms=840,
            )
            first_process.move_node(
                actor=None,
                project_id=primary.id,
                test_set_id=test_set.id,
                node_id=test.id,
                new_parent_id=suite.id,
                position=0,
            )

            restarted = ProjectApplication.sqlite(database)
            restored_projects = restarted.list_projects(actor=None)
            restored_primary = restarted.get_project(None, primary.id)
            restored_secondary = restarted.get_project(None, secondary.id)
            restored_set = restored_primary.test_set(test_set.id)
            restored_test = restored_set.node(test.id)

            self.assertEqual(
                ["Projet principal", "Projet secondaire"],
                [project.name for project in restored_projects],
            )
            self.assertEqual(primary.id, restored_primary.id)
            self.assertEqual(secondary.id, restored_secondary.id)
            self.assertEqual(
                ("Régression", "Paiement refusé"),
                restored_set.path(restored_test.id),
            )
            self.assertEqual(0, restored_test.order)
            self.assertEqual(1, len(restored_test.result_history))
            self.assertEqual(occurred_at, restored_test.result_history[0].occurred_at)
            self.assertFalse(restored_test.result_history[0].succeeded)
            self.assertEqual(840, restored_test.result_history[0].duration_ms)

            migrated_again = ProjectApplication.sqlite(database)
            self.assertEqual(
                [primary.id, secondary.id],
                [project.id for project in migrated_again.list_projects(None)],
            )


if __name__ == "__main__":
    unittest.main()
