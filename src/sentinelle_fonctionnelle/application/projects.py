"""Cas d'usage multi-projet communs aux déploiements local et en ligne.

Références : EF-001, EF-001.1, EF-001.2, EF-002, EF-007.5, ENF-008,
ENF-013, ACC-051, ACC-052, ACC-062 et ACC-068.
"""

from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime
from enum import StrEnum
from os import PathLike
from typing import Protocol
from uuid import UUID

from sentinelle_fonctionnelle.domain import (
    DataIterationMode,
    DesignDialogue,
    ExecutionResultSummary,
    FunctionalTestSpecification,
    GenerationWorkflowInput,
    HierarchyNode,
    NodeKind,
    Project,
    SpecificationStyle,
    TabularDataBinding,
    TabularDataSet,
    TestPlan,
    TestSet,
)


class ApplicationMode(StrEnum):
    LOCAL = "local"
    ONLINE = "online"


class ProjectRole(StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class AuthenticationRequired(PermissionError):
    """Le mode en ligne n'a reçu aucune identité authentifiée."""


class AuthorizationDenied(PermissionError):
    """L'identité connue ne possède pas le rôle demandé."""


class ProjectNotFound(LookupError):
    """Projet absent ou inaccessible, sans révéler lequel des deux."""


class ConcurrentProjectUpdate(RuntimeError):
    """La version enregistrée a changé depuis le début de la modification."""


@dataclass(frozen=True, slots=True)
class AuthenticatedIdentity:
    """Identité déjà authentifiée par l'adaptateur de déploiement."""

    subject: str

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("Le sujet de l'identité est obligatoire.")


class ProjectRepository(Protocol):
    """Port de persistance requis par les cas d'usage de projet."""

    def add(self, project: Project, *, owner_subject: str) -> None: ...

    def save(
        self, project: Project, *, expected_revision: int | None = None
    ) -> int: ...

    def revision_for(self, project_id: UUID) -> int: ...

    def get(self, project_id: UUID) -> Project | None: ...

    def list_for_subject(self, subject: str) -> tuple[Project, ...]: ...

    def role_for(
        self,
        project_id: UUID,
        subject: str,
    ) -> ProjectRole | None: ...

    def set_role(
        self,
        project_id: UUID,
        subject: str,
        role: ProjectRole,
    ) -> None: ...


class ProjectApplication:
    """Frontière d'autorisation utilisée de façon identique dans les deux modes."""

    _LOCAL_SUBJECT = "local-user"

    def __init__(
        self,
        *,
        mode: ApplicationMode,
        repository: ProjectRepository,
    ) -> None:
        self.mode = ApplicationMode(mode)
        self._repository = repository

    @classmethod
    def in_memory(cls, mode: ApplicationMode) -> ProjectApplication:
        """Composition de développement conforme au même port que les bases."""

        from sentinelle_fonctionnelle.adapters.persistence.in_memory import (
            InMemoryProjectRepository,
        )

        return cls(mode=mode, repository=InMemoryProjectRepository())

    @classmethod
    def sqlite(cls, database: str | PathLike[str]) -> ProjectApplication:
        """Compose le mode local avec une base SQLite migrée."""

        from sentinelle_fonctionnelle.adapters.persistence.sqlite import (
            SQLiteProjectRepository,
        )

        repository = SQLiteProjectRepository(database)
        repository.migrate()
        return cls(mode=ApplicationMode.LOCAL, repository=repository)

    @classmethod
    def postgresql(cls, dsn: str) -> ProjectApplication:
        """Compose le mode partagé avec transactions PostgreSQL."""

        from sentinelle_fonctionnelle.adapters.persistence.postgresql import (
            PostgreSQLProjectRepository,
        )

        repository = PostgreSQLProjectRepository(dsn)
        repository.migrate()
        return cls(mode=ApplicationMode.ONLINE, repository=repository)

    def create_project(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        name: str,
        description: str,
        web_target: str,
        security_policy: str,
    ) -> Project:
        identity = self._resolve_identity(actor)
        project = Project.create(
            name=name,
            description=description,
            web_target=web_target,
            security_policy=security_policy,
        )
        self._repository.add(project, owner_subject=identity.subject)
        return project

    def list_projects(
        self,
        actor: AuthenticatedIdentity | None,
    ) -> tuple[Project, ...]:
        identity = self._resolve_identity(actor)
        return self._repository.list_for_subject(identity.subject)

    def get_project(
        self,
        actor: AuthenticatedIdentity | None,
        project_id: UUID,
    ) -> Project:
        identity = self._resolve_identity(actor)
        role = self._repository.role_for(project_id, identity.subject)
        project = self._repository.get(project_id)
        if role is None or project is None:
            raise ProjectNotFound("Projet introuvable ou inaccessible.")
        return project

    def update_project(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        name: str,
        description: str,
        web_target: str,
        security_policy: str,
        expected_revision: int | None = None,
    ) -> Project:
        project = self._require_role(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
        )
        if expected_revision is not None:
            project = deepcopy(project)
        project.update_details(
            name=name,
            description=description,
            web_target=web_target,
            security_policy=security_policy,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return project

    def project_revision(
        self,
        actor: AuthenticatedIdentity | None,
        project_id: UUID,
    ) -> int:
        self.get_project(actor, project_id)
        return self._repository.revision_for(project_id)

    def add_member(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        member: AuthenticatedIdentity,
        role: ProjectRole,
    ) -> None:
        self._require_role(actor, project_id, {ProjectRole.OWNER})
        self._repository.set_role(
            project_id,
            member.subject,
            ProjectRole(role),
        )

    def create_test_plan(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        name: str,
        objective: str,
        target: str,
        scope: str,
        test_approach_id: str,
        test_approach_version: int,
        risks: tuple[str, ...] = (),
        entry_criteria: tuple[str, ...] = (),
        exit_criteria: tuple[str, ...] = (),
        resources: str = "",
        constraints: str = "",
        schedule: str = "",
        test_type: str = "acceptance",
        tags: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
        expected_revision: int | None = None,
    ) -> TestPlan:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        test_plan = project.create_test_plan(
            name=name,
            objective=objective,
            target=target,
            scope=scope,
            test_approach_id=test_approach_id,
            test_approach_version=test_approach_version,
            risks=risks,
            entry_criteria=entry_criteria,
            exit_criteria=exit_criteria,
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=tags,
            execution_declaration=execution_declaration,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return test_plan

    def create_test_set(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        name: str,
        objective: str,
        test_type: str,
        target: str,
        tags: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
        expected_revision: int | None = None,
    ) -> TestSet:
        """Compatibilité transitoire avec l'ancien cas d'usage."""

        return self.create_test_plan(
            actor,
            project_id=project_id,
            name=name,
            objective=objective,
            scope=objective,
            test_approach_id="functional-risk-based",
            test_approach_version=1,
            test_type=test_type,
            target=target,
            tags=tags,
            execution_declaration=execution_declaration,
            expected_revision=expected_revision,
        )

    def update_test_plan(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_plan_id: UUID,
        name: str,
        objective: str,
        target: str,
        scope: str,
        test_approach_id: str,
        test_approach_version: int,
        risks: tuple[str, ...] = (),
        entry_criteria: tuple[str, ...] = (),
        exit_criteria: tuple[str, ...] = (),
        resources: str = "",
        constraints: str = "",
        schedule: str = "",
        test_type: str = "acceptance",
        tags: tuple[str, ...] = (),
        expected_revision: int | None = None,
    ) -> TestPlan:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        test_plan = project.test_plan(test_plan_id)
        test_plan.update_details(
            name=name,
            objective=objective,
            target=target,
            scope=scope,
            test_approach_id=test_approach_id,
            test_approach_version=test_approach_version,
            risks=risks,
            entry_criteria=entry_criteria,
            exit_criteria=exit_criteria,
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=tags,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return test_plan

    def add_node(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        kind: NodeKind,
        name: str,
        parent_id: UUID | None = None,
        position: int | None = None,
        tags: tuple[str, ...] = (),
        objective: str = "",
        test_type: str = "",
        preconditions: tuple[str, ...] = (),
        postconditions: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
        expected_revision: int | None = None,
    ) -> HierarchyNode:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        node = project.test_set(test_set_id).add_node(
            kind,
            name,
            parent_id=parent_id,
            position=position,
            tags=tags,
            objective=objective,
            test_type=test_type,
            preconditions=preconditions,
            postconditions=postconditions,
            execution_declaration=execution_declaration,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return node

    def record_result(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        test_id: UUID,
        occurred_at: datetime,
        succeeded: bool,
        duration_ms: int,
        expected_revision: int | None = None,
    ) -> ExecutionResultSummary:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        result = project.test_set(test_set_id).record_result(
            test_id,
            occurred_at=occurred_at,
            succeeded=succeeded,
            duration_ms=duration_ms,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return result

    def move_node(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        node_id: UUID,
        new_parent_id: UUID | None,
        position: int | None = None,
        expected_revision: int | None = None,
    ) -> HierarchyNode:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        node = project.test_set(test_set_id).move_node(
            node_id,
            new_parent_id=new_parent_id,
            position=position,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return node

    def rename_node(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        node_id: UUID,
        name: str,
        expected_revision: int | None = None,
    ) -> HierarchyNode:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        node = project.test_set(test_set_id).rename_node(node_id, name=name)
        self._repository.save(project, expected_revision=expected_revision)
        return node

    def archive_node(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        node_id: UUID,
        expected_revision: int | None = None,
    ) -> tuple[HierarchyNode, ...]:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        nodes = project.test_set(test_set_id).archive_node(node_id)
        self._repository.save(project, expected_revision=expected_revision)
        return nodes

    def define_test(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        test_id: UUID,
        style: SpecificationStyle,
        objective: str,
        actor_name: str,
        source_text: str,
        environment: str = "",
        preconditions: tuple[str, ...] = (),
        data_sets: tuple[str, ...] = (),
        postconditions: tuple[str, ...] = (),
        requirements: tuple[str, ...] = (),
        business_rules: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
        workflow: GenerationWorkflowInput | None = None,
        summary: str = "",
        expected_revision: int | None = None,
    ) -> FunctionalTestSpecification:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        specification = project.test_set(test_set_id).define_test(
            test_id,
            style=style,
            objective=objective,
            actor=actor_name,
            source_text=source_text,
            environment=environment,
            preconditions=preconditions,
            data_sets=data_sets,
            postconditions=postconditions,
            requirements=requirements,
            business_rules=business_rules,
            execution_declaration=execution_declaration,
            workflow=workflow,
            summary=summary,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return specification

    def update_design_dialogue(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        test_id: UUID,
        dialogue: DesignDialogue,
        expected_revision: int | None = None,
    ) -> DesignDialogue:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        saved = project.test_set(test_set_id).update_design_dialogue(
            test_id,
            dialogue=dialogue,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return saved

    def bind_test_data(
        self,
        actor: AuthenticatedIdentity | None,
        *,
        project_id: UUID,
        test_set_id: UUID,
        test_id: UUID,
        data_set: TabularDataSet,
        mode: DataIterationMode,
        max_parallelism: int = 1,
        random_seed: int = 0,
        sample_count: int | None = None,
        expected_revision: int | None = None,
    ) -> TabularDataBinding:
        project = self._require_role_for_update(
            actor,
            project_id,
            {ProjectRole.OWNER, ProjectRole.EDITOR},
            expected_revision,
        )
        binding = project.test_set(test_set_id).bind_test_data(
            test_id,
            data_set=data_set,
            mode=mode,
            max_parallelism=max_parallelism,
            random_seed=random_seed,
            sample_count=sample_count,
        )
        self._repository.save(project, expected_revision=expected_revision)
        return binding

    def _resolve_identity(
        self,
        actor: AuthenticatedIdentity | None,
    ) -> AuthenticatedIdentity:
        if self.mode is ApplicationMode.LOCAL:
            return AuthenticatedIdentity(self._LOCAL_SUBJECT)
        if actor is None:
            raise AuthenticationRequired(
                "Une identité authentifiée est obligatoire en mode en ligne."
            )
        return actor

    def _require_role(
        self,
        actor: AuthenticatedIdentity | None,
        project_id: UUID,
        allowed_roles: set[ProjectRole],
    ) -> Project:
        identity = self._resolve_identity(actor)
        project = self.get_project(identity, project_id)
        role = self._repository.role_for(project_id, identity.subject)
        if role not in allowed_roles:
            raise AuthorizationDenied(
                "Le rôle de l'utilisateur n'autorise pas cette opération."
            )
        return project

    def _require_role_for_update(
        self,
        actor: AuthenticatedIdentity | None,
        project_id: UUID,
        allowed_roles: set[ProjectRole],
        expected_revision: int | None,
    ) -> Project:
        project = self._require_role(actor, project_id, allowed_roles)
        return deepcopy(project) if expected_revision is not None else project
