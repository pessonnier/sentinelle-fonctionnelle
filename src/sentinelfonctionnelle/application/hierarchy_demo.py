"""Cas d'usage observable de la première tranche verticale."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sentinelfonctionnelle.domain.hierarchy import NodeKind, Project


def build_hierarchy_demo() -> dict[str, Any]:
    """Crée l'arborescence ACC-002 puis exerce le déplacement ACC-003."""

    project = Project.create(
        name="Boutique de démonstration",
        description="Tests fonctionnels du parcours d'achat",
        web_target="https://demo.invalid",
        security_policy="demo-only",
    )
    test_plan = project.create_test_plan(
        name="Parcours critiques",
        objective="Valider les principaux parcours client",
        scope="Commande et paiement",
        approach="Tests d'acceptation orientés risques",
        test_type="acceptance",
        target="demo",
    )
    suite = test_plan.add_node(
        NodeKind.SUITE,
        "Régression",
        objective="Exécuter les contrôles de régression",
    )
    subsuite = test_plan.add_node(
        NodeKind.SUITE,
        "Paiement",
        parent_id=suite.id,
        objective="Vérifier le parcours de paiement",
    )
    test_plan.add_node(
        NodeKind.TEST,
        "Paiement accepté",
        parent_id=subsuite.id,
    )
    moved_case = test_plan.add_node(
        NodeKind.TEST,
        "Paiement refusé",
        parent_id=subsuite.id,
    )
    test_plan.record_result(
        moved_case.id,
        occurred_at=datetime(2026, 7, 25, 18, 0, tzinfo=UTC),
        succeeded=True,
        duration_ms=725,
    )
    original_id = moved_case.id
    test_plan.move_node(
        moved_case.id,
        new_parent_id=suite.id,
        position=0,
    )

    return {
        "project_id": str(project.id),
        "test_plan_id": str(test_plan.id),
        "node_count": len(test_plan.nodes),
        "case_count": sum(
            node.kind is NodeKind.TEST
            for node in test_plan.nodes
        ),
        "moved_case": {
            "id": str(moved_case.id),
            "original_id": str(original_id),
            "history_count": len(moved_case.result_history),
            "path": list(test_plan.path(moved_case.id)),
        },
    }
