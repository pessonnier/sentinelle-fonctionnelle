"""Démonstration du même contrat fonctionnel dans les deux modes."""

from __future__ import annotations

from typing import Any

from sentinelle_fonctionnelle.application.projects import (
    ApplicationMode,
    AuthenticatedIdentity,
    ProjectApplication,
)
from sentinelle_fonctionnelle.domain import NodeKind


def build_deployment_demo(
    mode: ApplicationMode,
    *,
    subject: str | None = None,
) -> dict[str, Any]:
    application = ProjectApplication.in_memory(mode)
    actor = (
        AuthenticatedIdentity(subject)
        if subject is not None
        else None
    )
    first_project = application.create_project(
        actor,
        name="Projet principal",
        description="Contrat partagé",
        web_target="https://demo.invalid",
        security_policy="demo-only",
    )
    application.create_project(
        actor,
        name="Projet secondaire",
        description="Vérifie le multi-projet",
        web_target="https://secondary.invalid",
        security_policy="demo-only",
    )
    test_set = application.create_test_set(
        actor,
        project_id=first_project.id,
        name="Parcours critiques",
        objective="Vérifier la parité",
        test_type="acceptance",
        target="demo",
    )
    suite = application.add_node(
        actor,
        project_id=first_project.id,
        test_set_id=test_set.id,
        kind=NodeKind.SUITE,
        name="Connexion",
        objective="Vérifier le parcours de connexion",
    )
    test = application.add_node(
        actor,
        project_id=first_project.id,
        test_set_id=test_set.id,
        kind=NodeKind.TEST,
        name="Connexion réussie",
        parent_id=suite.id,
    )
    return {
        "mode": ApplicationMode(mode).value,
        "node_count": len(test_set.nodes),
        "project_names": [
            project.name
            for project in application.list_projects(actor)
        ],
        "case_path": list(test_set.path(test.id)),
        "test_plan_name": test_set.name,
    }
