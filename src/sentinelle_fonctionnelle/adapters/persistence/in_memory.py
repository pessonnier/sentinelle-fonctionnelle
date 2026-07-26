"""Dépôt en mémoire utilisé par les tests de contrat et les démonstrations."""

from __future__ import annotations

from uuid import UUID

from sentinelle_fonctionnelle.application.projects import ProjectRole
from sentinelle_fonctionnelle.domain import Project


class InMemoryProjectRepository:
    """Implémentation sans état global du port ProjectRepository."""

    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}
        self._memberships: dict[UUID, dict[str, ProjectRole]] = {}

    def add(self, project: Project, *, owner_subject: str) -> None:
        if project.id in self._projects:
            raise ValueError(f"Projet déjà présent : {project.id}")
        self._projects[project.id] = project
        self._memberships[project.id] = {
            owner_subject: ProjectRole.OWNER,
        }

    def get(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    def save(self, project: Project) -> None:
        if project.id not in self._projects:
            raise LookupError("Projet introuvable.")
        self._projects[project.id] = project

    def list_for_subject(self, subject: str) -> tuple[Project, ...]:
        return tuple(
            project
            for project_id, project in self._projects.items()
            if subject in self._memberships.get(project_id, {})
        )

    def role_for(
        self,
        project_id: UUID,
        subject: str,
    ) -> ProjectRole | None:
        return self._memberships.get(project_id, {}).get(subject)

    def set_role(
        self,
        project_id: UUID,
        subject: str,
        role: ProjectRole,
    ) -> None:
        if project_id not in self._projects:
            raise LookupError("Projet introuvable.")
        self._memberships[project_id][subject] = ProjectRole(role)
