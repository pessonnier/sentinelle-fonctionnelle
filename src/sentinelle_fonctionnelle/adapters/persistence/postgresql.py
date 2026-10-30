"""Persistance PostgreSQL partagée avec appartenances et révisions atomiques."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import json
from typing import Any, Callable, Iterator, Mapping
from uuid import UUID

from sentinelle_fonctionnelle.application.projects import (
    ConcurrentProjectUpdate,
    ProjectRole,
)
from sentinelle_fonctionnelle.domain import (
    ExecutionResultSummary,
    HierarchyNode,
    NodeKind,
    Project,
    TestPlan,
)

from .sqlite import (
    _dump_data_binding,
    _dump_design_dialogue,
    _dump_specification,
    _load_data_binding,
    _load_design_dialogue,
    _load_specification,
)


class PostgreSQLConfigurationError(RuntimeError):
    """Le mode en ligne ne peut pas initialiser sa persistance."""


class PostgreSQLProjectRepository:
    """Stocke l'agrégat en JSONB et l'accès utilisateur en tables dédiées."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        dsn: str,
        *,
        connect: Callable[..., Any] | None = None,
    ) -> None:
        if not dsn.startswith(("postgresql://", "postgres://")):
            raise PostgreSQLConfigurationError(
                "La base partagée doit être une URL PostgreSQL."
            )
        self.dsn = dsn
        self._connect_factory = connect

    def migrate(self) -> None:
        statements = (
            """CREATE TABLE IF NOT EXISTS sentinelle_schema (
                 singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
                 version integer NOT NULL)""",
            """INSERT INTO sentinelle_schema(singleton, version) VALUES (true, 1)
                 ON CONFLICT (singleton) DO NOTHING""",
            """CREATE TABLE IF NOT EXISTS projects (
                 id uuid PRIMARY KEY, document jsonb NOT NULL,
                 revision bigint NOT NULL CHECK (revision >= 1))""",
            """CREATE TABLE IF NOT EXISTS project_memberships (
                 project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                 subject text NOT NULL, role text NOT NULL
                 CHECK (role IN ('owner','editor','viewer')),
                 PRIMARY KEY(project_id, subject))""",
            """CREATE INDEX IF NOT EXISTS memberships_subject_idx
                 ON project_memberships(subject)""",
        )
        with self._connection() as connection, connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
            cursor.execute("SELECT version FROM sentinelle_schema WHERE singleton")
            version = int(_row_value(cursor.fetchone(), "version", 0))
            if version != self.SCHEMA_VERSION:
                raise PostgreSQLConfigurationError(
                    f"Version PostgreSQL incompatible : {version}."
                )

    def add(self, project: Project, *, owner_subject: str) -> None:
        document = json.dumps(_project_document(project), ensure_ascii=False)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO projects(id, document, revision) VALUES (%s, %s::jsonb, 1)",
                (str(project.id), document),
            )
            cursor.execute(
                """INSERT INTO project_memberships(project_id, subject, role)
                   VALUES (%s, %s, %s)""",
                (str(project.id), owner_subject, ProjectRole.OWNER.value),
            )

    def save(self, project: Project, *, expected_revision: int | None = None) -> int:
        if expected_revision is None:
            raise ConcurrentProjectUpdate(
                "Le mode online exige la révision lue avant toute écriture."
            )
        document = json.dumps(_project_document(project), ensure_ascii=False)
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """UPDATE projects SET document = %s::jsonb, revision = revision + 1
                   WHERE id = %s AND revision = %s RETURNING revision""",
                (document, str(project.id), expected_revision),
            )
            row = cursor.fetchone()
            if row is None:
                raise ConcurrentProjectUpdate(
                    "Le projet a changé ; rechargez-le avant de recommencer."
                )
            return int(_row_value(row, "revision", 0))

    def get(self, project_id: UUID) -> Project | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT document FROM projects WHERE id = %s", (str(project_id),)
            )
            row = cursor.fetchone()
        return _project_from_document(_row_value(row, "document", 0)) if row else None

    def list_for_subject(self, subject: str) -> tuple[Project, ...]:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT p.document FROM projects p JOIN project_memberships m
                   ON m.project_id = p.id WHERE m.subject = %s ORDER BY p.id""",
                (subject,),
            )
            rows = cursor.fetchall()
        return tuple(
            _project_from_document(_row_value(row, "document", 0)) for row in rows
        )

    def role_for(self, project_id: UUID, subject: str) -> ProjectRole | None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT role FROM project_memberships
                   WHERE project_id = %s AND subject = %s""",
                (str(project_id), subject),
            )
            row = cursor.fetchone()
        return ProjectRole(_row_value(row, "role", 0)) if row else None

    def set_role(self, project_id: UUID, subject: str, role: ProjectRole) -> None:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO project_memberships(project_id, subject, role)
                   VALUES (%s, %s, %s) ON CONFLICT(project_id, subject)
                   DO UPDATE SET role = EXCLUDED.role""",
                (str(project_id), subject, ProjectRole(role).value),
            )

    def revision_for(self, project_id: UUID) -> int:
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT revision FROM projects WHERE id = %s", (str(project_id),)
            )
            row = cursor.fetchone()
        if row is None:
            raise LookupError("Projet introuvable.")
        return int(_row_value(row, "revision", 0))

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        connect = self._connect_factory
        if connect is None:
            try:
                import psycopg
            except ImportError as error:
                raise PostgreSQLConfigurationError(
                    "Installez l'extra 'online' pour utiliser PostgreSQL."
                ) from error
            connect = psycopg.connect
        try:
            with connect(self.dsn) as connection:
                yield connection
        except (PostgreSQLConfigurationError, ConcurrentProjectUpdate):
            raise
        except Exception as error:
            raise PostgreSQLConfigurationError(
                "Connexion ou transaction PostgreSQL impossible."
            ) from error


def _row_value(row: Any, key: str, index: int) -> Any:
    return row[key] if isinstance(row, Mapping) else row[index]


def _project_document(project: Project) -> dict[str, Any]:
    plans: list[dict[str, Any]] = []
    for plan in project.test_sets:
        nodes = []
        for node in plan.nodes:
            nodes.append(
                {
                    "id": str(node.id),
                    "kind": node.kind.value,
                    "name": node.name,
                    "parent_id": str(node.parent_id) if node.parent_id else None,
                    "order": node.order,
                    "tags": list(node.tags),
                    "objective": node.objective,
                    "test_type": node.test_type,
                    "preconditions": list(node.preconditions),
                    "postconditions": list(node.postconditions),
                    "execution_declaration": list(node.execution_declaration),
                    "archived": node.archived,
                    "specification": _dump_specification(node.specification),
                    "data_binding": _dump_data_binding(node.data_binding),
                    "design_dialogue": _dump_design_dialogue(node.design_dialogue),
                    "history": [
                        {
                            "occurred_at": result.occurred_at.isoformat(),
                            "succeeded": result.succeeded,
                            "duration_ms": result.duration_ms,
                        }
                        for result in node.result_history
                    ],
                }
            )
        plans.append(
            {
                "id": str(plan.id),
                "name": plan.name,
                "objective": plan.objective,
                "target": plan.target,
                "scope": plan.scope,
                "test_approach_id": plan.test_approach_id,
                "test_approach_version": plan.test_approach_version,
                "legacy_approach_text": plan.legacy_approach_text,
                "risks": list(plan.risks),
                "entry_criteria": list(plan.entry_criteria),
                "exit_criteria": list(plan.exit_criteria),
                "resources": plan.resources,
                "constraints": plan.constraints,
                "schedule": plan.schedule,
                "test_type": plan.test_type,
                "tags": list(plan.tags),
                "execution_declaration": list(plan.execution_declaration),
                "nodes": nodes,
            }
        )
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "web_target": project.web_target,
        "security_policy": project.security_policy,
        "archived": project.archived,
        "test_plans": plans,
    }


def _project_from_document(raw: Any) -> Project:
    document = json.loads(raw) if isinstance(raw, str) else dict(raw)
    plans: dict[UUID, TestPlan] = {}
    for plan_data in document.get("test_plans", []):
        nodes: dict[UUID, HierarchyNode] = {}
        for node_data in plan_data.get("nodes", []):
            node_id = UUID(node_data["id"])
            nodes[node_id] = HierarchyNode(
                id=node_id,
                kind=NodeKind(node_data["kind"]),
                name=node_data["name"],
                parent_id=(
                    UUID(node_data["parent_id"]) if node_data.get("parent_id") else None
                ),
                order=int(node_data["order"]),
                tags=tuple(node_data.get("tags", [])),
                objective=node_data.get("objective", ""),
                test_type=node_data.get("test_type", ""),
                preconditions=tuple(node_data.get("preconditions", [])),
                postconditions=tuple(node_data.get("postconditions", [])),
                execution_declaration=tuple(node_data.get("execution_declaration", [])),
                archived=bool(node_data.get("archived")),
                specification=_load_specification(node_data.get("specification")),
                data_binding=_load_data_binding(node_data.get("data_binding")),
                design_dialogue=_load_design_dialogue(node_data.get("design_dialogue")),
                _result_history=[
                    ExecutionResultSummary(
                        occurred_at=datetime.fromisoformat(item["occurred_at"]),
                        succeeded=bool(item["succeeded"]),
                        duration_ms=int(item["duration_ms"]),
                    )
                    for item in node_data.get("history", [])
                ],
            )
        plan_id = UUID(plan_data["id"])
        plans[plan_id] = TestPlan(
            id=plan_id,
            name=plan_data["name"],
            objective=plan_data["objective"],
            target=plan_data["target"],
            scope=plan_data.get("scope", ""),
            test_approach_id=plan_data.get("test_approach_id", ""),
            test_approach_version=int(plan_data.get("test_approach_version", 1)),
            legacy_approach_text=plan_data.get("legacy_approach_text", ""),
            risks=tuple(plan_data.get("risks", [])),
            entry_criteria=tuple(plan_data.get("entry_criteria", [])),
            exit_criteria=tuple(plan_data.get("exit_criteria", [])),
            resources=plan_data.get("resources", ""),
            constraints=plan_data.get("constraints", ""),
            schedule=plan_data.get("schedule", ""),
            test_type=plan_data.get("test_type", "acceptance"),
            tags=tuple(plan_data.get("tags", [])),
            execution_declaration=tuple(plan_data.get("execution_declaration", [])),
            _nodes=nodes,
        )
    return Project(
        id=UUID(document["id"]),
        name=document["name"],
        description=document["description"],
        web_target=document["web_target"],
        security_policy=document["security_policy"],
        archived=bool(document.get("archived")),
        _test_sets=plans,
    )
