"""Domaine minimal des projets et arborescences.

Références : EF-001, EF-002, EF-007, ACC-002, ACC-003 et ACC-062.
Ce module ne dépend d'aucun framework web, navigateur ou fournisseur LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from .specifications import (
    FunctionalTestSpecification,
    OrganizationView,
    SpecificationError,
    SpecificationStyle,
)
from .tabular_data import (
    DataIterationMode,
    TabularDataBinding,
    TabularDataError,
    TabularDataSet,
)

class HierarchyError(ValueError):
    """Signale une opération qui rendrait l'arborescence invalide."""


class NodeKind(StrEnum):
    """Types de nœuds placés sous un plan de test."""

    SUITE = "suite"
    FOLDER = "folder"
    TEST = "test"

    @property
    def label(self) -> str:
        return {
            self.SUITE: "Suite de tests",
            self.FOLDER: "Dossier",
            self.TEST: "Cas de test",
        }[self]


@dataclass(frozen=True, slots=True)
class ExecutionResultSummary:
    """Historique métier minimal prescrit par le modèle conceptuel."""

    occurred_at: datetime
    succeeded: bool
    duration_ms: int

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise HierarchyError("La date du résultat doit inclure un fuseau horaire.")
        if self.duration_ms < 0:
            raise HierarchyError("La durée d'exécution ne peut pas être négative.")


@dataclass(slots=True)
class HierarchyNode:
    """Nœud avec identité stable, parent, ordre et historique."""

    id: UUID
    kind: NodeKind
    name: str
    parent_id: UUID | None
    order: int
    tags: tuple[str, ...] = ()
    objective: str = ""
    test_type: str = ""
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    execution_declaration: tuple[str, ...] = ()
    archived: bool = False
    specification: FunctionalTestSpecification | None = None
    data_binding: TabularDataBinding | None = None
    _result_history: list[ExecutionResultSummary] = field(
        default_factory=list,
        repr=False,
    )

    @property
    def result_history(self) -> tuple[ExecutionResultSummary, ...]:
        """Expose une vue immuable afin qu'un déplacement ne la remplace pas."""

        return tuple(self._result_history)


@dataclass(slots=True)
class TestPlan:
    """Plan de test contenant des suites, dossiers et cas de test."""

    id: UUID
    name: str
    objective: str
    target: str
    scope: str = ""
    approach: str = ""
    risks: tuple[str, ...] = ()
    entry_criteria: tuple[str, ...] = ()
    exit_criteria: tuple[str, ...] = ()
    resources: str = ""
    constraints: str = ""
    schedule: str = ""
    test_type: str = "acceptance"
    tags: tuple[str, ...] = ()
    execution_declaration: tuple[str, ...] = ()
    _nodes: dict[UUID, HierarchyNode] = field(default_factory=dict, repr=False)

    def update_details(
        self,
        *,
        name: str,
        objective: str,
        target: str,
        scope: str,
        approach: str,
        risks: tuple[str, ...] = (),
        entry_criteria: tuple[str, ...] = (),
        exit_criteria: tuple[str, ...] = (),
        resources: str = "",
        constraints: str = "",
        schedule: str = "",
        test_type: str = "acceptance",
        tags: tuple[str, ...] = (),
    ) -> None:
        self.name = _required_text(name, "Le nom du plan de test")
        self.objective = _required_text(
            objective,
            "L'objectif du plan de test",
        )
        self.target = _required_text(target, "La cible du plan de test")
        self.scope = _required_text(scope, "Le périmètre du plan de test")
        self.approach = _required_text(
            approach,
            "L'approche du plan de test",
        )
        self.risks = tuple(risks)
        self.entry_criteria = tuple(entry_criteria)
        self.exit_criteria = tuple(exit_criteria)
        self.resources = resources.strip()
        self.constraints = constraints.strip()
        self.schedule = schedule.strip()
        self.test_type = _required_text(test_type, "Le type par défaut")
        self.tags = tuple(tags)

    def add_node(
        self,
        kind: NodeKind,
        name: str,
        *,
        parent_id: UUID | None = None,
        position: int | None = None,
        tags: tuple[str, ...] = (),
        objective: str = "",
        test_type: str = "",
        preconditions: tuple[str, ...] = (),
        postconditions: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
    ) -> HierarchyNode:
        """Ajoute un nœud valide à une position déterministe."""

        normalized_name = _required_text(name, "Le nom du nœud")
        normalized_kind = NodeKind(kind)
        self._validate_parent(parent_id, child_kind=normalized_kind)
        parent = self.node(parent_id) if parent_id is not None else None
        self._validate_unique_name(
            parent_id=parent_id,
            name=normalized_name,
        )
        siblings = self.children(parent_id=parent_id)
        insertion_index = _insertion_index(position, len(siblings))
        self._make_room(parent_id, insertion_index)
        node = HierarchyNode(
            id=uuid4(),
            kind=normalized_kind,
            name=normalized_name,
            parent_id=parent_id,
            order=insertion_index,
            tags=tuple(tags),
            objective=(
                _required_text(
                    objective,
                    "L'objectif d'exécution de la suite",
                )
                if normalized_kind is NodeKind.SUITE
                else ""
            ),
            test_type=(
                test_type.strip()
                or (parent.test_type if parent is not None else "")
                or self.test_type
            ),
            preconditions=(
                tuple(preconditions)
                or (parent.preconditions if parent is not None else ())
            ),
            postconditions=(
                tuple(postconditions)
                or (parent.postconditions if parent is not None else ())
            ),
            execution_declaration=(
                tuple(execution_declaration)
                or (
                    parent.execution_declaration
                    if parent is not None
                    else ()
                )
                or self.execution_declaration
            ),
        )
        self._nodes[node.id] = node
        return node

    def children(
        self,
        *,
        parent_id: UUID | None,
        include_archived: bool = True,
    ) -> list[HierarchyNode]:
        """Retourne les enfants sans charger d'artefacts ou de preuves."""

        return sorted(
            (
                node
                for node in self._nodes.values()
                if node.parent_id == parent_id
                and (include_archived or not node.archived)
            ),
            key=lambda node: (node.order, str(node.id)),
        )

    def node(self, node_id: UUID) -> HierarchyNode:
        try:
            return self._nodes[node_id]
        except KeyError as error:
            raise HierarchyError(f"Nœud inconnu : {node_id}") from error

    def move_node(
        self,
        node_id: UUID,
        *,
        new_parent_id: UUID | None,
        position: int | None = None,
    ) -> HierarchyNode:
        """Déplace le même nœud sans modifier son identité ni son historique."""

        node = self.node(node_id)
        self._validate_parent(new_parent_id, child_kind=node.kind)
        if new_parent_id == node.id:
            raise HierarchyError("Un nœud ne peut pas devenir son propre parent.")
        if new_parent_id is not None and self._is_descendant(
            candidate_id=new_parent_id,
            ancestor_id=node.id,
        ):
            raise HierarchyError("Un nœud ne peut pas être déplacé dans un descendant.")
        self._validate_unique_name(
            parent_id=new_parent_id,
            name=node.name,
            ignored_node_id=node.id,
        )

        old_parent_id = node.parent_id
        old_order = node.order
        self._close_gap(old_parent_id, old_order)
        destination_siblings = self.children(parent_id=new_parent_id)
        insertion_index = _insertion_index(position, len(destination_siblings))
        self._make_room(new_parent_id, insertion_index)
        node.parent_id = new_parent_id
        node.order = insertion_index
        return node

    def rename_node(self, node_id: UUID, *, name: str) -> HierarchyNode:
        """Renomme le nœud sans changer son identité ni son historique."""

        node = self.node(node_id)
        if node.archived:
            raise HierarchyError("Un nœud archivé ne peut pas être renommé.")
        normalized_name = _required_text(name, "Le nom du nœud")
        self._validate_unique_name(
            parent_id=node.parent_id,
            name=normalized_name,
            ignored_node_id=node.id,
        )
        node.name = normalized_name
        return node

    def archive_node(self, node_id: UUID) -> tuple[HierarchyNode, ...]:
        """Archive explicitement un nœud et tous ses descendants."""

        root = self.node(node_id)
        archived: list[HierarchyNode] = []

        def archive_descendants(node: HierarchyNode) -> None:
            node.archived = True
            archived.append(node)
            for child in self.children(parent_id=node.id):
                archive_descendants(child)

        archive_descendants(root)
        return tuple(archived)

    def define_test(
        self,
        node_id: UUID,
        *,
        style: SpecificationStyle,
        objective: str,
        actor: str,
        source_text: str,
        environment: str = "",
        preconditions: tuple[str, ...] = (),
        data_sets: tuple[str, ...] = (),
        postconditions: tuple[str, ...] = (),
        requirements: tuple[str, ...] = (),
        business_rules: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
    ) -> FunctionalTestSpecification:
        node = self.node(node_id)
        if node.kind is not NodeKind.TEST:
            raise HierarchyError(
                "Seul un cas de test peut recevoir une spécification."
            )
        if node.archived:
            raise HierarchyError(
                "Un cas de test archivé ne peut pas être spécifié."
            )
        next_version = (
            node.specification.version + 1 if node.specification is not None else 1
        )
        try:
            specification = FunctionalTestSpecification.create(
                style=style,
                version=next_version,
                objective=objective,
                actor=actor,
                source_text=source_text,
                environment=environment,
                preconditions=preconditions,
                data_sets=data_sets,
                postconditions=postconditions,
                requirements=requirements,
                business_rules=business_rules,
                execution_declaration=execution_declaration,
            )
        except SpecificationError as error:
            raise HierarchyError(str(error)) from error
        node.specification = specification
        return specification

    def organize_tests(
        self,
        view: OrganizationView,
        *,
        query: str = "",
    ) -> tuple[OrganizationGroup, ...]:
        normalized_view = OrganizationView(view)
        normalized_query = query.strip().casefold()
        tests = tuple(
            node
            for node in self._nodes.values()
            if node.kind is NodeKind.TEST
            and not node.archived
            and (
                not normalized_query
                or normalized_query in _node_searchable_text(node)
            )
        )
        if normalized_view is OrganizationView.TREE:
            ordered = tuple(sorted(tests, key=lambda node: (node.order, str(node.id))))
            return (OrganizationGroup("Arbre", ordered),) if ordered else ()

        groups: dict[str, list[HierarchyNode]] = {}
        for node in tests:
            specification = node.specification
            if normalized_view is OrganizationView.TAG:
                labels = node.tags or ("Sans tag",)
            elif normalized_view is OrganizationView.REQUIREMENT:
                labels = (
                    specification.requirements
                    if specification and specification.requirements
                    else ("Sans exigence",)
                )
            elif normalized_view is OrganizationView.BUSINESS_RULE:
                labels = (
                    specification.business_rules
                    if specification and specification.business_rules
                    else ("Sans règle métier",)
                )
            else:
                labels = (
                    (specification.style.label,)
                    if specification
                    else ("Non spécifié",)
                )
            for label in labels:
                groups.setdefault(label, []).append(node)
        return tuple(
            OrganizationGroup(
                label,
                tuple(sorted(nodes, key=lambda node: (node.name.casefold(), str(node.id)))),
            )
            for label, nodes in sorted(groups.items(), key=lambda item: item[0].casefold())
        )

    def bind_test_data(
        self,
        node_id: UUID,
        *,
        data_set: TabularDataSet,
        mode: DataIterationMode,
        max_parallelism: int = 1,
        random_seed: int = 0,
        sample_count: int | None = None,
    ) -> TabularDataBinding:
        node = self.node(node_id)
        if node.kind is not NodeKind.TEST:
            raise HierarchyError(
                "Seul un cas de test peut recevoir des données tabulaires."
            )
        if node.archived:
            raise HierarchyError(
                "Un cas de test archivé ne peut pas recevoir de données."
            )
        next_version = (
            node.data_binding.version + 1 if node.data_binding is not None else 1
        )
        try:
            binding = TabularDataBinding.create(
                version=next_version,
                data_set=data_set,
                mode=mode,
                max_parallelism=max_parallelism,
                random_seed=random_seed,
                sample_count=sample_count,
            )
        except TabularDataError as error:
            raise HierarchyError(str(error)) from error
        node.data_binding = binding
        return binding

    def record_result(
        self,
        node_id: UUID,
        *,
        occurred_at: datetime,
        succeeded: bool,
        duration_ms: int,
    ) -> ExecutionResultSummary:
        node = self.node(node_id)
        if node.kind is not NodeKind.TEST:
            raise HierarchyError(
                "Un résultat d'exécution ne peut être rattaché "
                "qu'à un cas de test."
            )
        result = ExecutionResultSummary(
            occurred_at=occurred_at,
            succeeded=succeeded,
            duration_ms=duration_ms,
        )
        node._result_history.append(result)
        return result

    def path(self, node_id: UUID) -> tuple[str, ...]:
        """Calcule le chemin courant sans l'utiliser comme identité."""

        names: list[str] = []
        current: HierarchyNode | None = self.node(node_id)
        while current is not None:
            names.append(current.name)
            current = (
                self.node(current.parent_id)
                if current.parent_id is not None
                else None
            )
        return tuple(reversed(names))

    @property
    def nodes(self) -> tuple[HierarchyNode, ...]:
        return tuple(self._nodes.values())

    def _validate_parent(
        self,
        parent_id: UUID | None,
        *,
        child_kind: NodeKind,
    ) -> None:
        if parent_id is None:
            if child_kind is NodeKind.TEST:
                raise HierarchyError(
                    "Un cas de test doit appartenir à une suite de tests "
                    "ou à un dossier."
                )
            return
        parent = self.node(parent_id)
        if parent.kind is NodeKind.TEST:
            raise HierarchyError(
                "Un cas de test ne peut pas contenir de nœud enfant."
            )
        if parent.archived:
            raise HierarchyError("Un nœud archivé ne peut pas recevoir d'enfant.")

    def _validate_unique_name(
        self,
        *,
        parent_id: UUID | None,
        name: str,
        ignored_node_id: UUID | None = None,
    ) -> None:
        normalized = name.casefold()
        if any(
            sibling.id != ignored_node_id
            and sibling.name.casefold() == normalized
            and not sibling.archived
            for sibling in self.children(parent_id=parent_id)
        ):
            raise HierarchyError(
                "Deux éléments actifs d'un même parent ne peuvent pas "
                "porter le même nom."
            )

    def _is_descendant(self, *, candidate_id: UUID, ancestor_id: UUID) -> bool:
        current = self.node(candidate_id)
        while current.parent_id is not None:
            if current.parent_id == ancestor_id:
                return True
            current = self.node(current.parent_id)
        return False

    def _make_room(self, parent_id: UUID | None, position: int) -> None:
        for sibling in self.children(parent_id=parent_id):
            if sibling.order >= position:
                sibling.order += 1

    def _close_gap(self, parent_id: UUID | None, position: int) -> None:
        for sibling in self.children(parent_id=parent_id):
            if sibling.order > position:
                sibling.order -= 1


@dataclass(slots=True)
class Project:
    """Projet contenant plusieurs plans de test indépendants."""

    id: UUID
    name: str
    description: str
    web_target: str
    security_policy: str
    archived: bool = False
    _test_sets: dict[UUID, TestSet] = field(default_factory=dict, repr=False)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        description: str,
        web_target: str,
        security_policy: str,
    ) -> Project:
        return cls(
            id=uuid4(),
            name=_required_text(name, "Le nom du projet"),
            description=description.strip(),
            web_target=_required_text(web_target, "La cible web"),
            security_policy=_required_text(
                security_policy,
                "La politique de sécurité",
            ),
        )

    def create_test_plan(
        self,
        *,
        name: str,
        objective: str,
        target: str,
        scope: str = "",
        approach: str = "",
        risks: tuple[str, ...] = (),
        entry_criteria: tuple[str, ...] = (),
        exit_criteria: tuple[str, ...] = (),
        resources: str = "",
        constraints: str = "",
        schedule: str = "",
        test_type: str = "acceptance",
        tags: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
    ) -> TestPlan:
        if self.archived:
            raise HierarchyError("Un projet archivé ne peut pas être modifié.")
        test_plan = TestPlan(
            id=uuid4(),
            name=_required_text(name, "Le nom du plan de test"),
            objective=_required_text(objective, "L'objectif du plan de test"),
            target=_required_text(target, "La cible du plan de test"),
            scope=_required_text(scope, "Le périmètre du plan de test"),
            approach=_required_text(approach, "L'approche du plan de test"),
            risks=tuple(risks),
            entry_criteria=tuple(entry_criteria),
            exit_criteria=tuple(exit_criteria),
            resources=resources.strip(),
            constraints=constraints.strip(),
            schedule=schedule.strip(),
            test_type=_required_text(test_type, "Le type par défaut"),
            tags=tuple(tags),
            execution_declaration=tuple(execution_declaration),
        )
        self._test_sets[test_plan.id] = test_plan
        return test_plan

    def create_test_set(
        self,
        *,
        name: str,
        objective: str,
        test_type: str,
        target: str,
        tags: tuple[str, ...] = (),
        execution_declaration: tuple[str, ...] = (),
    ) -> TestPlan:
        """Compatibilité transitoire avec l'ancien vocabulaire."""

        return self.create_test_plan(
            name=name,
            objective=objective,
            scope=objective,
            approach="Approche fonctionnelle guidée",
            test_type=test_type,
            target=target,
            tags=tags,
            execution_declaration=execution_declaration,
        )

    @property
    def test_plans(self) -> tuple[TestPlan, ...]:
        return tuple(self._test_sets.values())

    @property
    def test_sets(self) -> tuple[TestPlan, ...]:
        """Compatibilité transitoire avec l'ancien nom."""

        return self.test_plans

    def test_plan(self, test_plan_id: UUID) -> TestPlan:
        try:
            return self._test_sets[test_plan_id]
        except KeyError as error:
            raise HierarchyError(
                f"Plan de test inconnu : {test_plan_id}"
            ) from error

    def test_set(self, test_set_id: UUID) -> TestPlan:
        """Compatibilité transitoire avec l'ancien nom."""

        return self.test_plan(test_set_id)


TestSet = TestPlan


def _required_text(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HierarchyError(f"{label} est obligatoire.")
    return normalized


def _insertion_index(position: int | None, sibling_count: int) -> int:
    if position is None:
        return sibling_count
    if position < 0 or position > sibling_count:
        raise HierarchyError(
            f"Position {position} invalide pour {sibling_count} élément(s)."
        )
    return position


@dataclass(frozen=True, slots=True)
class OrganizationGroup:
    label: str
    tests: tuple[HierarchyNode, ...]


def _node_searchable_text(node: HierarchyNode) -> str:
    values = (node.name, *node.tags)
    base = " ".join(values).casefold()
    if node.specification is None:
        specification_text = ""
    else:
        specification_text = node.specification.searchable_text
    data_text = ""
    if node.data_binding is not None:
        data_text = " ".join(
            (
                node.data_binding.data_set.filename,
                *node.data_binding.data_set.headers,
            )
        ).casefold()
    return f"{base} {specification_text} {data_text}"
