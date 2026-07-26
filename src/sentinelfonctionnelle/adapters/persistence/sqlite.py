"""Persistance SQLite du mode local.

Références : EF-001, EF-002, EF-007.5, ENF-001, ENF-013, ACC-053,
ACC-062 et ACC-068.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from os import PathLike
from pathlib import Path
from uuid import UUID

from sentinelfonctionnelle.application.projects import ProjectRole
from sentinelfonctionnelle.domain import (
    DataIterationMode,
    ExecutionResultSummary,
    FunctionalTestSpecification,
    HierarchyNode,
    NodeKind,
    Project,
    SpecificationClause,
    SpecificationStyle,
    TabularDataBinding,
    TabularDataSet,
    TestPlan,
    TestSet,
)


SCHEMA_VERSION = 5


class UnsupportedSchemaVersion(RuntimeError):
    """La base a été créée par une version plus récente de l'application."""


class SQLiteProjectRepository:
    """Adaptateur transactionnel reconstruisant les agrégats du domaine."""

    def __init__(self, database: str | PathLike[str]) -> None:
        self.database = Path(database)

    def migrate(self) -> None:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            row = connection.execute(
                "SELECT MAX(version) AS version FROM schema_migrations"
            ).fetchone()
            current_version = int(row["version"] or 0)
            if current_version > SCHEMA_VERSION:
                raise UnsupportedSchemaVersion(
                    "La base utilise une version de schéma plus récente "
                    f"({current_version} > {SCHEMA_VERSION})."
                )
            if current_version < 1:
                self._migrate_to_version_1(connection)
                current_version = 1
            if current_version < 2:
                self._migrate_to_version_2(connection)
                current_version = 2
            if current_version < 3:
                self._migrate_to_version_3(connection)
                current_version = 3
            if current_version < 4:
                self._migrate_to_version_4(connection)
                current_version = 4
            if current_version < 5:
                self._migrate_to_version_5(connection)

    def add(self, project: Project, *, owner_subject: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (
                    id, name, description, web_target, security_policy, archived
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(project.id),
                    project.name,
                    project.description,
                    project.web_target,
                    project.security_policy,
                    int(project.archived),
                ),
            )
            connection.execute(
                """
                INSERT INTO project_memberships (project_id, subject, role)
                VALUES (?, ?, ?)
                """,
                (str(project.id), owner_subject, ProjectRole.OWNER.value),
            )
            self._insert_graph(connection, project)

    def save(self, project: Project) -> None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE projects
                SET name = ?, description = ?, web_target = ?,
                    security_policy = ?, archived = ?
                WHERE id = ?
                """,
                (
                    project.name,
                    project.description,
                    project.web_target,
                    project.security_policy,
                    int(project.archived),
                    str(project.id),
                ),
            )
            if cursor.rowcount != 1:
                raise LookupError("Projet introuvable.")
            connection.execute(
                "DELETE FROM test_sets WHERE project_id = ?",
                (str(project.id),),
            )
            self._insert_graph(connection, project)

    def get(self, project_id: UUID) -> Project | None:
        with self._connect() as connection:
            return self._load_project(connection, project_id)

    def list_for_subject(self, subject: str) -> tuple[Project, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT projects.id
                FROM projects
                INNER JOIN project_memberships
                    ON project_memberships.project_id = projects.id
                WHERE project_memberships.subject = ?
                ORDER BY projects.sequence
                """,
                (subject,),
            ).fetchall()
            return tuple(
                project
                for row in rows
                if (
                    project := self._load_project(
                        connection,
                        UUID(row["id"]),
                    )
                )
                is not None
            )

    def role_for(
        self,
        project_id: UUID,
        subject: str,
    ) -> ProjectRole | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT role
                FROM project_memberships
                WHERE project_id = ? AND subject = ?
                """,
                (str(project_id), subject),
            ).fetchone()
            return ProjectRole(row["role"]) if row is not None else None

    def set_role(
        self,
        project_id: UUID,
        subject: str,
        role: ProjectRole,
    ) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT 1 FROM projects WHERE id = ?",
                (str(project_id),),
            ).fetchone()
            if existing is None:
                raise LookupError("Projet introuvable.")
            connection.execute(
                """
                INSERT INTO project_memberships (project_id, subject, role)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id, subject)
                DO UPDATE SET role = excluded.role
                """,
                (str(project_id), subject, ProjectRole(role).value),
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _migrate_to_version_1(self, connection: sqlite3.Connection) -> None:
        statements = (
            """
            CREATE TABLE projects (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                web_target TEXT NOT NULL,
                security_policy TEXT NOT NULL,
                archived INTEGER NOT NULL CHECK (archived IN (0, 1))
            )
            """,
            """
            CREATE TABLE project_memberships (
                project_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
                PRIMARY KEY (project_id, subject),
                FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE test_sets (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                objective TEXT NOT NULL,
                test_type TEXT NOT NULL,
                target TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                execution_declaration_json TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE hierarchy_nodes (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                id TEXT NOT NULL UNIQUE,
                test_set_id TEXT NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('suite', 'folder', 'test')),
                name TEXT NOT NULL,
                parent_id TEXT,
                display_order INTEGER NOT NULL CHECK (display_order >= 0),
                tags_json TEXT NOT NULL,
                FOREIGN KEY (test_set_id) REFERENCES test_sets(id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE execution_results (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                test_node_id TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                succeeded INTEGER NOT NULL CHECK (succeeded IN (0, 1)),
                duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
                FOREIGN KEY (test_node_id) REFERENCES hierarchy_nodes(id)
                    ON DELETE CASCADE
            )
            """,
            """
            CREATE INDEX idx_memberships_subject
            ON project_memberships(subject, project_id)
            """,
            """
            CREATE INDEX idx_test_sets_project
            ON test_sets(project_id, sequence)
            """,
            """
            CREATE INDEX idx_nodes_test_set
            ON hierarchy_nodes(test_set_id, sequence)
            """,
        )
        for statement in statements:
            connection.execute(statement)
        connection.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (1, datetime.now().astimezone().isoformat()),
        )

    def _migrate_to_version_2(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            ALTER TABLE hierarchy_nodes
            ADD COLUMN archived INTEGER NOT NULL DEFAULT 0
                CHECK (archived IN (0, 1))
            """
        )
        connection.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (2, datetime.now().astimezone().isoformat()),
        )

    def _migrate_to_version_3(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            ALTER TABLE hierarchy_nodes
            ADD COLUMN specification_json TEXT
            """
        )
        connection.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (3, datetime.now().astimezone().isoformat()),
        )

    def _migrate_to_version_4(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            ALTER TABLE hierarchy_nodes
            ADD COLUMN data_binding_json TEXT
            """
        )
        connection.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (4, datetime.now().astimezone().isoformat()),
        )

    def _migrate_to_version_5(self, connection: sqlite3.Connection) -> None:
        statements = (
            "ALTER TABLE test_sets ADD COLUMN scope TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE test_sets ADD COLUMN approach TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE test_sets ADD COLUMN risks_json TEXT NOT NULL DEFAULT '[]'",
            (
                "ALTER TABLE test_sets ADD COLUMN entry_criteria_json "
                "TEXT NOT NULL DEFAULT '[]'"
            ),
            (
                "ALTER TABLE test_sets ADD COLUMN exit_criteria_json "
                "TEXT NOT NULL DEFAULT '[]'"
            ),
            "ALTER TABLE test_sets ADD COLUMN resources TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE test_sets ADD COLUMN constraints TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE test_sets ADD COLUMN schedule TEXT NOT NULL DEFAULT ''",
            (
                "ALTER TABLE hierarchy_nodes ADD COLUMN objective "
                "TEXT NOT NULL DEFAULT ''"
            ),
            (
                "ALTER TABLE hierarchy_nodes ADD COLUMN test_type "
                "TEXT NOT NULL DEFAULT ''"
            ),
            (
                "ALTER TABLE hierarchy_nodes ADD COLUMN preconditions_json "
                "TEXT NOT NULL DEFAULT '[]'"
            ),
            (
                "ALTER TABLE hierarchy_nodes ADD COLUMN postconditions_json "
                "TEXT NOT NULL DEFAULT '[]'"
            ),
            (
                "ALTER TABLE hierarchy_nodes ADD COLUMN "
                "execution_declaration_json TEXT NOT NULL DEFAULT '[]'"
            ),
        )
        for statement in statements:
            connection.execute(statement)
        connection.execute(
            """
            UPDATE test_sets
            SET scope = objective,
                approach = 'Approche fonctionnelle guidée'
            WHERE scope = '' OR approach = ''
            """
        )
        connection.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (?, ?)
            """,
            (5, datetime.now().astimezone().isoformat()),
        )

    def _insert_graph(
        self,
        connection: sqlite3.Connection,
        project: Project,
    ) -> None:
        for test_set in project.test_sets:
            connection.execute(
                """
                INSERT INTO test_sets (
                    id, project_id, name, objective, test_type, target,
                    tags_json, execution_declaration_json, scope, approach,
                    risks_json, entry_criteria_json, exit_criteria_json,
                    resources, constraints, schedule
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(test_set.id),
                    str(project.id),
                    test_set.name,
                    test_set.objective,
                    test_set.test_type,
                    test_set.target,
                    _dump_tuple(test_set.tags),
                    _dump_tuple(test_set.execution_declaration),
                    test_set.scope,
                    test_set.approach,
                    _dump_tuple(test_set.risks),
                    _dump_tuple(test_set.entry_criteria),
                    _dump_tuple(test_set.exit_criteria),
                    test_set.resources,
                    test_set.constraints,
                    test_set.schedule,
                ),
            )
            for node in test_set.nodes:
                connection.execute(
                    """
                    INSERT INTO hierarchy_nodes (
                        id, test_set_id, kind, name, parent_id,
                        display_order, tags_json, archived, specification_json,
                        data_binding_json, objective, test_type,
                        preconditions_json, postconditions_json,
                        execution_declaration_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(node.id),
                        str(test_set.id),
                        node.kind.value,
                        node.name,
                        str(node.parent_id) if node.parent_id else None,
                        node.order,
                        _dump_tuple(node.tags),
                        int(node.archived),
                        _dump_specification(node.specification),
                        _dump_data_binding(node.data_binding),
                        node.objective,
                        node.test_type,
                        _dump_tuple(node.preconditions),
                        _dump_tuple(node.postconditions),
                        _dump_tuple(node.execution_declaration),
                    ),
                )
                for result in node.result_history:
                    connection.execute(
                        """
                        INSERT INTO execution_results (
                            test_node_id, occurred_at, succeeded, duration_ms
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(node.id),
                            result.occurred_at.isoformat(),
                            int(result.succeeded),
                            result.duration_ms,
                        ),
                    )

    def _load_project(
        self,
        connection: sqlite3.Connection,
        project_id: UUID,
    ) -> Project | None:
        row = connection.execute(
            "SELECT * FROM projects WHERE id = ?",
            (str(project_id),),
        ).fetchone()
        if row is None:
            return None

        test_sets: dict[UUID, TestPlan] = {}
        test_set_rows = connection.execute(
            """
            SELECT *
            FROM test_sets
            WHERE project_id = ?
            ORDER BY sequence
            """,
            (str(project_id),),
        ).fetchall()
        for test_set_row in test_set_rows:
            test_set_id = UUID(test_set_row["id"])
            nodes: dict[UUID, HierarchyNode] = {}
            node_rows = connection.execute(
                """
                SELECT *
                FROM hierarchy_nodes
                WHERE test_set_id = ?
                ORDER BY sequence
                """,
                (str(test_set_id),),
            ).fetchall()
            for node_row in node_rows:
                node_id = UUID(node_row["id"])
                result_rows = connection.execute(
                    """
                    SELECT occurred_at, succeeded, duration_ms
                    FROM execution_results
                    WHERE test_node_id = ?
                    ORDER BY sequence
                    """,
                    (str(node_id),),
                ).fetchall()
                history = [
                    ExecutionResultSummary(
                        occurred_at=datetime.fromisoformat(
                            result_row["occurred_at"]
                        ),
                        succeeded=bool(result_row["succeeded"]),
                        duration_ms=result_row["duration_ms"],
                    )
                    for result_row in result_rows
                ]
                nodes[node_id] = HierarchyNode(
                    id=node_id,
                    kind=NodeKind(node_row["kind"]),
                    name=node_row["name"],
                    parent_id=(
                        UUID(node_row["parent_id"])
                        if node_row["parent_id"]
                        else None
                    ),
                    order=node_row["display_order"],
                    tags=_load_tuple(node_row["tags_json"]),
                    objective=node_row["objective"],
                    test_type=node_row["test_type"],
                    preconditions=_load_tuple(
                        node_row["preconditions_json"]
                    ),
                    postconditions=_load_tuple(
                        node_row["postconditions_json"]
                    ),
                    execution_declaration=_load_tuple(
                        node_row["execution_declaration_json"]
                    ),
                    archived=bool(node_row["archived"]),
                    specification=_load_specification(
                        node_row["specification_json"]
                    ),
                    data_binding=_load_data_binding(
                        node_row["data_binding_json"]
                    ),
                    _result_history=history,
                )
            test_sets[test_set_id] = TestPlan(
                id=test_set_id,
                name=test_set_row["name"],
                objective=test_set_row["objective"],
                target=test_set_row["target"],
                scope=test_set_row["scope"],
                approach=test_set_row["approach"],
                risks=_load_tuple(test_set_row["risks_json"]),
                entry_criteria=_load_tuple(
                    test_set_row["entry_criteria_json"]
                ),
                exit_criteria=_load_tuple(
                    test_set_row["exit_criteria_json"]
                ),
                resources=test_set_row["resources"],
                constraints=test_set_row["constraints"],
                schedule=test_set_row["schedule"],
                test_type=test_set_row["test_type"],
                tags=_load_tuple(test_set_row["tags_json"]),
                execution_declaration=_load_tuple(
                    test_set_row["execution_declaration_json"]
                ),
                _nodes=nodes,
            )

        return Project(
            id=UUID(row["id"]),
            name=row["name"],
            description=row["description"],
            web_target=row["web_target"],
            security_policy=row["security_policy"],
            archived=bool(row["archived"]),
            _test_sets=test_sets,
        )


def _dump_tuple(values: tuple[str, ...]) -> str:
    return json.dumps(values, ensure_ascii=False, separators=(",", ":"))


def _load_tuple(value: str) -> tuple[str, ...]:
    return tuple(json.loads(value))


def _dump_specification(
    specification: FunctionalTestSpecification | None,
) -> str | None:
    if specification is None:
        return None
    return json.dumps(
        {
            "style": specification.style.value,
            "version": specification.version,
            "objective": specification.objective,
            "actor": specification.actor,
            "source_text": specification.source_text,
            "environment": specification.environment,
            "preconditions": specification.preconditions,
            "data_sets": specification.data_sets,
            "postconditions": specification.postconditions,
            "requirements": specification.requirements,
            "business_rules": specification.business_rules,
            "execution_declaration": specification.execution_declaration,
            "clauses": [
                {
                    "keyword": clause.keyword,
                    "text": clause.text,
                    "expected_result": clause.expected_result,
                }
                for clause in specification.clauses
            ],
            "example_headers": specification.example_headers,
            "example_rows": specification.example_rows,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _load_specification(value: str | None) -> FunctionalTestSpecification | None:
    if value is None:
        return None
    data = json.loads(value)
    return FunctionalTestSpecification(
        style=SpecificationStyle(data["style"]),
        version=int(data["version"]),
        objective=data["objective"],
        actor=data["actor"],
        source_text=data["source_text"],
        environment=data["environment"],
        preconditions=tuple(data["preconditions"]),
        data_sets=tuple(data["data_sets"]),
        postconditions=tuple(data["postconditions"]),
        requirements=tuple(data["requirements"]),
        business_rules=tuple(data["business_rules"]),
        execution_declaration=tuple(data["execution_declaration"]),
        clauses=tuple(
            SpecificationClause(
                keyword=clause["keyword"],
                text=clause["text"],
                expected_result=clause["expected_result"],
            )
            for clause in data["clauses"]
        ),
        example_headers=tuple(data["example_headers"]),
        example_rows=tuple(tuple(row) for row in data["example_rows"]),
    )


def _dump_data_binding(binding: TabularDataBinding | None) -> str | None:
    if binding is None:
        return None
    return json.dumps(
        {
            "version": binding.version,
            "mode": binding.mode.value,
            "max_parallelism": binding.max_parallelism,
            "random_seed": binding.random_seed,
            "sample_count": binding.sample_count,
            "data_set": {
                "id": str(binding.data_set.id),
                "filename": binding.data_set.filename,
                "fingerprint": binding.data_set.fingerprint,
                "headers": binding.data_set.headers,
                "rows": binding.data_set.rows,
            },
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _load_data_binding(value: str | None) -> TabularDataBinding | None:
    if value is None:
        return None
    data = json.loads(value)
    data_set = data["data_set"]
    return TabularDataBinding(
        version=int(data["version"]),
        data_set=TabularDataSet(
            id=UUID(data_set["id"]),
            filename=data_set["filename"],
            fingerprint=data_set["fingerprint"],
            headers=tuple(data_set["headers"]),
            rows=tuple(tuple(row) for row in data_set["rows"]),
        ),
        mode=DataIterationMode(data["mode"]),
        max_parallelism=int(data["max_parallelism"]),
        random_seed=int(data["random_seed"]),
        sample_count=int(data["sample_count"]),
    )
