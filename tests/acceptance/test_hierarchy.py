"""ACC-002, ACC-003 et ACC-070 — hiérarchie des plans et cas de test."""

from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sentinelle_fonctionnelle.domain.hierarchy import HierarchyError, NodeKind, Project


class HierarchyAcceptanceTests(unittest.TestCase):
    """Comportements observables de la première tranche verticale."""

    def setUp(self) -> None:
        self.project = Project.create(
            name="Boutique de démonstration",
            description="Tests fonctionnels du parcours d'achat",
            web_target="https://demo.invalid",
            security_policy="demo-only",
        )
        self.test_plan = self.project.create_test_plan(
            name="Parcours critiques",
            objective="Valider les principaux parcours client",
            scope="Commande et paiement",
            test_approach_id="functional-risk-based",
            test_approach_version=1,
            test_type="acceptance",
            target="demo",
        )

    def test_acc_002_creates_a_suite_subsuite_and_two_cases(self) -> None:
        suite = self.test_plan.add_node(
            NodeKind.SUITE,
            "Commande",
            objective="Vérifier le parcours de commande",
        )
        subsuite = self.test_plan.add_node(
            NodeKind.SUITE,
            "Paiement",
            parent_id=suite.id,
            objective="Vérifier les modes de paiement",
        )
        first_case = self.test_plan.add_node(
            NodeKind.TEST,
            "Paiement accepté",
            parent_id=subsuite.id,
        )
        second_case = self.test_plan.add_node(
            NodeKind.TEST,
            "Paiement refusé",
            parent_id=subsuite.id,
        )

        self.assertEqual(
            [suite],
            self.test_plan.children(parent_id=None),
        )
        self.assertEqual(
            [subsuite],
            self.test_plan.children(parent_id=suite.id),
        )
        self.assertEqual(
            [first_case, second_case],
            self.test_plan.children(parent_id=subsuite.id),
        )
        self.assertEqual(
            ("Commande", "Paiement", "Paiement accepté"),
            self.test_plan.path(first_case.id),
        )

    def test_acc_003_move_preserves_identity_and_result_history(self) -> None:
        source_suite = self.test_plan.add_node(
            NodeKind.SUITE,
            "À classer",
            objective="Qualifier les nouveaux cas",
        )
        target_suite = self.test_plan.add_node(
            NodeKind.SUITE,
            "Régression",
            objective="Exécuter les contrôles de non-régression",
        )
        case = self.test_plan.add_node(
            NodeKind.TEST,
            "Connexion client",
            parent_id=source_suite.id,
        )
        occurred_at = datetime(2026, 7, 25, 18, 0, tzinfo=UTC)
        self.test_plan.record_result(
            case.id,
            occurred_at=occurred_at,
            succeeded=True,
            duration_ms=725,
        )
        original_id = case.id
        original_history = case.result_history

        moved = self.test_plan.move_node(
            case.id,
            new_parent_id=target_suite.id,
            position=0,
        )

        self.assertEqual(original_id, moved.id)
        self.assertEqual(original_history, moved.result_history)
        self.assertEqual(
            ("Régression", "Connexion client"),
            self.test_plan.path(case.id),
        )
        self.assertEqual([], self.test_plan.children(parent_id=source_suite.id))
        self.assertEqual([moved], self.test_plan.children(parent_id=target_suite.id))

    def test_acc_070_case_requires_a_suite_or_folder_parent(self) -> None:
        with self.assertRaisesRegex(
            HierarchyError,
            "doit appartenir à une suite de tests ou à un dossier",
        ):
            self.test_plan.add_node(NodeKind.TEST, "Cas sans parent")

        suite = self.test_plan.add_node(
            NodeKind.SUITE,
            "Régression",
            objective="Vérifier les accès existants",
            test_type="regression",
            preconditions=("Le service est disponible",),
            postconditions=("La session est fermée",),
            execution_declaration=("on_merge_request",),
        )
        case = self.test_plan.add_node(
            NodeKind.TEST,
            "Connexion valide",
            parent_id=suite.id,
        )
        self.assertEqual("regression", case.test_type)
        self.assertEqual(("Le service est disponible",), case.preconditions)
        self.assertEqual(("La session est fermée",), case.postconditions)
        self.assertEqual(("on_merge_request",), case.execution_declaration)
        with self.assertRaisesRegex(
            HierarchyError,
            "ne peut pas contenir",
        ):
            self.test_plan.add_node(
                NodeKind.FOLDER,
                "Enfant interdit",
                parent_id=case.id,
            )


if __name__ == "__main__":
    unittest.main()
