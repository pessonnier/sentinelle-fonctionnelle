"""Dépôt en mémoire utilisé par les tests de contrat et les démonstrations."""

from __future__ import annotations

from uuid import UUID

from sentinelle_fonctionnelle.application.projects import (
    ConcurrentProjectUpdate,
    ProjectRole,
)
from sentinelle_fonctionnelle.domain import Project


class InMemoryProjectRepository:
    """Implémentation sans état global du port ProjectRepository."""

    def __init__(self) -> None:
        self._projects: dict[UUID, Project] = {}
        self._memberships: dict[UUID, dict[str, ProjectRole]] = {}
        self._revisions: dict[UUID, int] = {}

    def add(self, project: Project, *, owner_subject: str) -> None:
        if project.id in self._projects:
            raise ValueError(f"Projet déjà présent : {project.id}")
        self._projects[project.id] = project
        self._memberships[project.id] = {
            owner_subject: ProjectRole.OWNER,
        }
        self._revisions[project.id] = 1

    def get(self, project_id: UUID) -> Project | None:
        return self._projects.get(project_id)

    def save(self, project: Project, *, expected_revision: int | None = None) -> int:
        if project.id not in self._projects:
            raise LookupError("Projet introuvable.")
        current = self._revisions[project.id]
        if expected_revision is not None and expected_revision != current:
            raise ConcurrentProjectUpdate(
                f"Révision attendue {expected_revision}, révision courante {current}."
            )
        self._projects[project.id] = project
        self._revisions[project.id] = current + 1
        return current + 1

    def revision_for(self, project_id: UUID) -> int:
        try:
            return self._revisions[project_id]
        except KeyError as error:
            raise LookupError("Projet introuvable.") from error

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
