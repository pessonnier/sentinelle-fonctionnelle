"""Démonstration de persistance et redémarrage du mode local."""

from __future__ import annotations

from datetime import UTC, datetime
from os import PathLike
from typing import Any

from sentinelfonctionnelle.application.projects import ProjectApplication
from sentinelfonctionnelle.domain import NodeKind


def build_persistence_demo(
    database: str | PathLike[str],
) -> dict[str, Any]:
    first_process = ProjectApplication.sqlite(database)
    primary = first_process.create_project(
        None,
        name="Projet principal",
        description="Persisté localement",
        web_target="https://demo.invalid",
        security_policy="demo-only",
    )
    first_process.create_project(
        None,
        name="Projet secondaire",
        description="Vérifie le multi-projet",
        web_target="https://secondary.invalid",
        security_policy="demo-only",
    )
    test_set = first_process.create_test_set(
        None,
        project_id=primary.id,
        name="Parcours critiques",
        objective="Vérifier le redémarrage",
        test_type="acceptance",
        target="demo",
    )
    suite = first_process.add_node(
        None,
        project_id=primary.id,
        test_set_id=test_set.id,
        kind=NodeKind.SUITE,
        name="Régression",
        objective="Exécuter les contrôles de régression",
    )
    subsuite = first_process.add_node(
        None,
        project_id=primary.id,
        test_set_id=test_set.id,
        kind=NodeKind.SUITE,
        name="Paiement",
        parent_id=suite.id,
        objective="Vérifier le parcours de paiement",
    )
    test = first_process.add_node(
        None,
        project_id=primary.id,
        test_set_id=test_set.id,
        kind=NodeKind.TEST,
        name="Paiement refusé",
        parent_id=subsuite.id,
    )
    first_process.record_result(
        None,
        project_id=primary.id,
        test_set_id=test_set.id,
        test_id=test.id,
        occurred_at=datetime(2026, 7, 25, 20, 30, tzinfo=UTC),
        succeeded=False,
        duration_ms=840,
    )
    first_process.move_node(
        None,
        project_id=primary.id,
        test_set_id=test_set.id,
        node_id=test.id,
        new_parent_id=suite.id,
        position=0,
    )

    restarted = ProjectApplication.sqlite(database)
    restored_project = restarted.get_project(None, primary.id)
    restored_set = restored_project.test_set(test_set.id)
    restored_test = restored_set.node(test.id)
    return {
        "history_count": len(restored_test.result_history),
        "identity_preserved": restored_test.id == test.id,
        "project_count": len(restarted.list_projects(None)),
        "restored_path": list(restored_set.path(restored_test.id)),
    }
