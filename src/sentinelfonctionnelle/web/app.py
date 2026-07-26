"""Application FastAPI locale de conception des plans et cas de test.

Références : EF-001, EF-001.2, EF-002, EF-002.1, EF-007.4,
ACC-060 à ACC-072.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sentinelfonctionnelle.adapters.persistence.sqlite import SCHEMA_VERSION
from sentinelfonctionnelle.adapters.tabular import (
    MAX_FILE_BYTES,
    parse_tabular_data,
)
from sentinelfonctionnelle.application import ProjectApplication
from sentinelfonctionnelle.domain import (
    DataIterationMode,
    HierarchyError,
    HierarchyNode,
    NodeKind,
    OrganizationView,
    SpecificationStyle,
    TabularDataError,
    TestPlan,
)
from sentinelfonctionnelle.web.settings import ServerSettings


PACKAGE_DIRECTORY = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=PACKAGE_DIRECTORY / "templates")


@dataclass(frozen=True, slots=True)
class TreeRow:
    node: HierarchyNode
    depth: int


def create_web_app(settings: ServerSettings | None = None) -> FastAPI:
    """Compose l'application locale autour du service applicatif partagé."""

    effective_settings = settings or ServerSettings()
    effective_settings.prepare()
    project_application = ProjectApplication.sqlite(effective_settings.database)
    app = FastAPI(
        title="SentinelFonctionnelle",
        version="0.1.0.dev0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.state.settings = effective_settings
    app.state.project_application = project_application
    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIRECTORY / "static"),
        name="static",
    )

    @app.exception_handler(HierarchyError)
    @app.exception_handler(TabularDataError)
    async def hierarchy_error(
        request: Request,
        error: HierarchyError | TabularDataError,
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(error)},
            status_code=400,
        )

    @app.get("/health")
    def health() -> dict[str, str | int]:
        return {
            "status": "ok",
            "mode": effective_settings.mode.value,
            "schema_version": SCHEMA_VERSION,
        }

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        projects = project_application.list_projects(actor=None)
        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={"projects": projects},
        )

    @app.post("/projects")
    def create_project(
        name: str = Form(),
        description: str = Form(""),
        web_target: str = Form(),
        security_policy: str = Form(),
    ) -> RedirectResponse:
        project = project_application.create_project(
            actor=None,
            name=name,
            description=description,
            web_target=web_target,
            security_policy=security_policy,
        )
        return RedirectResponse(f"/projects/{project.id}", status_code=303)

    @app.get("/projects/{project_id}", response_class=HTMLResponse)
    def project_page(request: Request, project_id: UUID) -> HTMLResponse:
        project = project_application.get_project(None, project_id)
        plans = tuple(
            {
                "plan": plan,
                "suite_count": sum(
                    node.kind is NodeKind.SUITE and not node.archived
                    for node in plan.nodes
                ),
                "case_count": sum(
                    node.kind is NodeKind.TEST and not node.archived
                    for node in plan.nodes
                ),
            }
            for plan in project.test_plans
        )
        return templates.TemplateResponse(
            request=request,
            name="project.html",
            context={"project": project, "plans": plans},
        )

    @app.post("/projects/{project_id}/test-plans")
    def create_test_plan(
        project_id: UUID,
        name: str = Form(),
        objective: str = Form(),
        scope: str = Form(),
        approach: str = Form(),
        target: str = Form(),
        risks: str = Form(""),
        entry_criteria: str = Form(""),
        exit_criteria: str = Form(""),
        resources: str = Form(""),
        constraints: str = Form(""),
        schedule: str = Form(""),
        test_type: str = Form("acceptance"),
        tags: str = Form(""),
    ) -> RedirectResponse:
        plan = project_application.create_test_plan(
            actor=None,
            project_id=project_id,
            name=name,
            objective=objective,
            scope=scope,
            approach=approach,
            target=target,
            risks=_line_values(risks),
            entry_criteria=_line_values(entry_criteria),
            exit_criteria=_line_values(exit_criteria),
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=_comma_values(tags),
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{plan.id}",
            status_code=303,
            headers={"x-created-id": str(plan.id)},
        )

    @app.get(
        "/projects/{project_id}/test-plans/{test_plan_id}",
        response_class=HTMLResponse,
    )
    def test_plan_page(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        show_archived: bool = Query(False),
        organization: OrganizationView = Query(OrganizationView.TREE),
        q: str = Query(""),
    ) -> HTMLResponse:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        groups = plan.organize_tests(organization, query=q)
        if organization is OrganizationView.TREE and q.strip():
            matching_cases = tuple(
                case for group in groups for case in group.tests
            )
            rows = tuple(
                TreeRow(node=case, depth=0) for case in matching_cases
            )
        else:
            rows = _tree_rows(plan.nodes, show_archived=show_archived)
        containers = tuple(
            node
            for node in plan.nodes
            if node.kind in {NodeKind.SUITE, NodeKind.FOLDER}
            and not node.archived
        )
        return templates.TemplateResponse(
            request=request,
            name="plan.html",
            context={
                "project": project,
                "plan": plan,
                "rows": rows,
                "groups": groups,
                "containers": containers,
                "show_archived": show_archived,
                "organization": organization,
                "organization_views": tuple(OrganizationView),
                "query": q,
            },
        )

    @app.post("/projects/{project_id}/test-plans/{test_plan_id}/details")
    def update_test_plan(
        project_id: UUID,
        test_plan_id: UUID,
        name: str = Form(),
        objective: str = Form(),
        scope: str = Form(),
        approach: str = Form(),
        target: str = Form(),
        risks: str = Form(""),
        entry_criteria: str = Form(""),
        exit_criteria: str = Form(""),
        resources: str = Form(""),
        constraints: str = Form(""),
        schedule: str = Form(""),
        test_type: str = Form("acceptance"),
        tags: str = Form(""),
    ) -> RedirectResponse:
        project_application.update_test_plan(
            actor=None,
            project_id=project_id,
            test_plan_id=test_plan_id,
            name=name,
            objective=objective,
            scope=scope,
            approach=approach,
            target=target,
            risks=_line_values(risks),
            entry_criteria=_line_values(entry_criteria),
            exit_criteria=_line_values(exit_criteria),
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=_comma_values(tags),
        )
        return _plan_redirect(project_id, test_plan_id)

    @app.post("/projects/{project_id}/test-plans/{test_plan_id}/nodes")
    def create_node(
        project_id: UUID,
        test_plan_id: UUID,
        kind: NodeKind = Form(),
        name: str = Form(),
        parent_id: str = Form(""),
        position: str = Form(""),
        tags: str = Form(""),
        objective: str = Form(""),
        test_type: str = Form(""),
        preconditions: str = Form(""),
        postconditions: str = Form(""),
        execution_declaration: str = Form(""),
    ) -> RedirectResponse:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        node = project_application.add_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            kind=kind,
            name=name,
            parent_id=_optional_uuid(parent_id),
            position=_optional_integer(position),
            tags=_comma_values(tags),
            objective=objective,
            test_type=test_type,
            preconditions=_line_values(preconditions),
            postconditions=_line_values(postconditions),
            execution_declaration=_line_values(execution_declaration),
        )
        if node.kind is NodeKind.TEST:
            return RedirectResponse(
                _case_url(project_id, test_plan_id, node.id),
                status_code=303,
                headers={"x-created-id": str(node.id)},
            )
        return _plan_redirect(
            project_id,
            test_plan_id,
            created_id=node.id,
        )

    @app.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/nodes/{node_id}/rename"
    )
    def rename_node(
        project_id: UUID,
        test_plan_id: UUID,
        node_id: UUID,
        name: str = Form(),
    ) -> RedirectResponse:
        project_application.rename_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            node_id=node_id,
            name=name,
        )
        return _plan_redirect(project_id, test_plan_id)

    @app.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/nodes/{node_id}/move"
    )
    def move_node(
        project_id: UUID,
        test_plan_id: UUID,
        node_id: UUID,
        new_parent_id: str = Form(""),
        position: str = Form(""),
    ) -> RedirectResponse:
        project_application.move_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            node_id=node_id,
            new_parent_id=_optional_uuid(new_parent_id),
            position=_optional_integer(position),
        )
        return _plan_redirect(project_id, test_plan_id)

    @app.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/nodes/{node_id}/archive"
    )
    def archive_node(
        project_id: UUID,
        test_plan_id: UUID,
        node_id: UUID,
    ) -> RedirectResponse:
        project_application.archive_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            node_id=node_id,
        )
        return _plan_redirect(
            project_id,
            test_plan_id,
            show_archived=True,
        )

    @app.get(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}",
        response_class=HTMLResponse,
    )
    def case_page(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ) -> HTMLResponse:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError(
                "L'élément sélectionné n'est pas un cas de test."
            )
        parent = plan.node(case.parent_id) if case.parent_id else None
        return templates.TemplateResponse(
            request=request,
            name="case.html",
            context={
                "project": project,
                "plan": plan,
                "case": case,
                "parent": parent,
                "path": plan.path(case.id),
                "container_path": _container_path(plan, case),
                "specification_styles": tuple(SpecificationStyle),
                "data_iteration_modes": tuple(DataIterationMode),
                "expected_results": _expected_results(case),
            },
        )

    @app.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/specification"
    )
    def define_case(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        style: SpecificationStyle = Form(SpecificationStyle.STEPS),
        objective: str = Form(),
        actor_name: str = Form(),
        source_text: str = Form(""),
        step_actions: str = Form(""),
        expected_results: str = Form(""),
        environment: str = Form(""),
        preconditions: str = Form(""),
        data_sets: str = Form(""),
        postconditions: str = Form(""),
        requirements: str = Form(""),
        business_rules: str = Form(""),
        execution_declaration: str = Form(""),
    ) -> RedirectResponse:
        effective_source = _specification_source(
            style=style,
            source_text=source_text,
            step_actions=step_actions,
            expected_results=expected_results,
        )
        project_application.define_test(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            test_id=case_id,
            style=style,
            objective=objective,
            actor_name=actor_name,
            source_text=effective_source,
            environment=environment,
            preconditions=_line_values(preconditions),
            data_sets=_line_values(data_sets),
            postconditions=_line_values(postconditions),
            requirements=_line_values(requirements),
            business_rules=_line_values(business_rules),
            execution_declaration=_line_values(execution_declaration),
        )
        return _case_redirect(project_id, test_plan_id, case_id)

    @app.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/data-binding"
    )
    async def bind_case_data(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        data_file: UploadFile = File(),
        mode: DataIterationMode = Form(),
        max_parallelism: str = Form("1"),
        random_seed: str = Form("0"),
        sample_count: str = Form(""),
    ) -> RedirectResponse:
        content = await data_file.read(MAX_FILE_BYTES + 1)
        data_set = parse_tabular_data(data_file.filename or "", content)
        project_application.bind_test_data(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            test_id=case_id,
            data_set=data_set,
            mode=mode,
            max_parallelism=_required_integer(
                max_parallelism,
                "La concurrence maximale",
            ),
            random_seed=_required_integer(
                random_seed,
                "La graine aléatoire",
            ),
            sample_count=_optional_integer(
                sample_count,
                label="Le nombre de cas",
            ),
        )
        return _case_redirect(project_id, test_plan_id, case_id)

    return app


def _tree_rows(
    nodes: tuple[HierarchyNode, ...],
    *,
    show_archived: bool,
) -> tuple[TreeRow, ...]:
    by_parent: dict[UUID | None, list[HierarchyNode]] = {}
    for node in nodes:
        if show_archived or not node.archived:
            by_parent.setdefault(node.parent_id, []).append(node)
    for siblings in by_parent.values():
        siblings.sort(key=lambda item: (item.order, str(item.id)))

    rows: list[TreeRow] = []

    def visit(parent_id: UUID | None, depth: int) -> None:
        for node in by_parent.get(parent_id, []):
            rows.append(TreeRow(node=node, depth=depth))
            visit(node.id, depth + 1)

    visit(None, 0)
    return tuple(rows)


def _container_path(
    plan: TestPlan,
    case: HierarchyNode,
) -> tuple[HierarchyNode, ...]:
    containers: list[HierarchyNode] = []
    parent_id = case.parent_id
    while parent_id is not None:
        container = plan.node(parent_id)
        containers.append(container)
        parent_id = container.parent_id
    return tuple(reversed(containers))


def _project_redirect(project_id: UUID) -> RedirectResponse:
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


def _plan_redirect(
    project_id: UUID,
    test_plan_id: UUID,
    *,
    created_id: UUID | None = None,
    show_archived: bool = False,
) -> RedirectResponse:
    suffix = "?show_archived=true" if show_archived else ""
    headers = {"x-created-id": str(created_id)} if created_id else None
    return RedirectResponse(
        f"/projects/{project_id}/test-plans/{test_plan_id}{suffix}",
        status_code=303,
        headers=headers,
    )


def _case_url(project_id: UUID, test_plan_id: UUID, case_id: UUID) -> str:
    return (
        f"/projects/{project_id}/test-plans/{test_plan_id}"
        f"/cases/{case_id}"
    )


def _case_redirect(
    project_id: UUID,
    test_plan_id: UUID,
    case_id: UUID,
) -> RedirectResponse:
    return RedirectResponse(
        _case_url(project_id, test_plan_id, case_id),
        status_code=303,
    )


def _expected_results(case: HierarchyNode) -> tuple[str, ...]:
    specification = case.specification
    if specification is None:
        return ()
    results = tuple(
        clause.expected_result
        for clause in specification.clauses
        if clause.expected_result
    )
    if results:
        return results
    return tuple(
        clause.text
        for clause in specification.clauses
        if clause.keyword in {"Alors", "Vérifier"}
    )


def _specification_source(
    *,
    style: SpecificationStyle,
    source_text: str,
    step_actions: str,
    expected_results: str,
) -> str:
    if style != SpecificationStyle.STEPS or not step_actions.strip():
        return source_text
    actions = _text_lines(step_actions)
    results = _text_lines(expected_results)
    if len(actions) != len(results):
        raise HierarchyError(
            "Chaque étape de test doit posséder exactement un résultat attendu."
        )
    if not actions:
        raise HierarchyError("Au moins une étape de test est obligatoire.")
    return "\n".join(
        f"{action} => {result}"
        for action, result in zip(actions, results, strict=True)
    )


def _optional_uuid(value: str) -> UUID | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return UUID(normalized)
    except ValueError as error:
        raise HierarchyError("L'identifiant du parent est invalide.") from error


def _optional_integer(
    value: str,
    *,
    label: str = "La position",
) -> int | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return int(normalized)
    except ValueError as error:
        raise HierarchyError(f"{label} doit être un entier.") from error


def _required_integer(value: str, label: str) -> int:
    normalized = value.strip()
    if not normalized:
        raise HierarchyError(f"{label} est obligatoire.")
    try:
        return int(normalized)
    except ValueError as error:
        raise HierarchyError(f"{label} doit être un entier.") from error


def _comma_values(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def _line_values(value: str) -> tuple[str, ...]:
    normalized = value.replace(",", "\n")
    return tuple(line.strip() for line in normalized.splitlines() if line.strip())


def _text_lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())
