"""Routeur catalogue de l'interface locale."""

from __future__ import annotations

from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.domain import (
    NodeKind,
    OrganizationView,
)
from sentinelle_fonctionnelle.web import route_support as support
from sentinelle_fonctionnelle.web.composition import WebServices

DEFAULT_WEB_TARGET = "http://127.0.0.1:8000/demo/hr"
DEFAULT_SECURITY_POLICY = "demo-only same-origin local-loopback"


def _new_project_form(
    *,
    name: str = "",
    description: str = "",
    web_target: str = DEFAULT_WEB_TARGET,
    security_policy: str = DEFAULT_SECURITY_POLICY,
) -> dict[str, str]:
    return {
        "name": name,
        "description": description,
        "web_target": web_target,
        "security_policy": security_policy,
    }


def _new_project_errors(form: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not form["name"].strip():
        errors["name"] = "Saisissez un nom de projet."
    elif len(form["name"].strip()) > 120:
        errors["name"] = "Le nom ne peut pas dépasser 120 caractères."

    target = urlsplit(form["web_target"].strip())
    if target.scheme not in {"http", "https"} or not target.hostname:
        errors["web_target"] = "Saisissez une URL HTTP ou HTTPS absolue."
    elif target.username or target.password:
        errors["web_target"] = "La cible ne doit pas contenir d’identifiants."

    if not form["security_policy"].strip():
        errors["security_policy"] = "Sélectionnez une politique de sécurité."
    return errors


def build_catalogue_router(
    services: WebServices,
    templates: Jinja2Templates,
) -> APIRouter:
    """Construit le routeur catalogue avec ses dépendances explicites."""

    catalogue_router = APIRouter(tags=["catalogue"])
    project_application = services.projects
    test_approach_catalog = services.test_approaches

    @catalogue_router.get("/", response_class=HTMLResponse)
    def home(request: Request) -> HTMLResponse:
        projects = project_application.list_projects(actor=None)
        return templates.TemplateResponse(
            request=request,
            name="home.html",
            context={
                "projects": projects,
                "project_form": _new_project_form(),
                "project_errors": {},
            },
        )

    @catalogue_router.get("/documentation", response_class=HTMLResponse)
    def documentation(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="documentation.html",
            context={},
        )

    @catalogue_router.get("/tutorials/test-case", response_class=HTMLResponse)
    def test_case_tutorial(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="tutorial_case.html",
            context={},
        )

    @catalogue_router.post("/projects")
    def create_project(
        request: Request,
        name: str = Form(""),
        description: str = Form(""),
        web_target: str = Form(""),
        security_policy: str = Form(""),
    ) -> Response:
        form = _new_project_form(
            name=name,
            description=description,
            web_target=web_target,
            security_policy=security_policy,
        )
        errors = _new_project_errors(form)
        if errors:
            return templates.TemplateResponse(
                request=request,
                name="home.html",
                context={
                    "projects": project_application.list_projects(actor=None),
                    "project_form": form,
                    "project_errors": errors,
                },
                status_code=422,
            )
        project = project_application.create_project(
            actor=None,
            name=form["name"],
            description=form["description"],
            web_target=form["web_target"],
            security_policy=form["security_policy"],
        )
        return RedirectResponse(f"/projects/{project.id}", status_code=303)

    @catalogue_router.get("/projects/{project_id}", response_class=HTMLResponse)
    def project_page(
        request: Request,
        project_id: UUID,
        show_archived: bool = Query(False),
    ) -> HTMLResponse:
        project = project_application.get_project(None, project_id)
        plans: list[dict[str, object]] = []
        for plan in project.test_plans:
            approach_profile = test_approach_catalog.get(
                plan.test_approach_id,
                plan.test_approach_version,
            )
            approach_options = list(test_approach_catalog.current_profiles())
            if not any(
                profile.id == approach_profile.id
                and profile.version == approach_profile.version
                for profile in approach_options
            ):
                approach_options.append(approach_profile)
            plans.append(
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
                    "rows": support.tree_rows(
                        plan.nodes,
                        show_archived=show_archived,
                    ),
                    "containers": tuple(
                        node
                        for node in plan.nodes
                        if node.kind in {NodeKind.SUITE, NodeKind.FOLDER}
                        and not node.archived
                    ),
                    "test_approach": approach_profile,
                    "test_approaches": tuple(approach_options),
                }
            )
        return templates.TemplateResponse(
            request=request,
            name="project.html",
            context={
                "project": project,
                "plans": tuple(plans),
                "test_approaches": test_approach_catalog.current_profiles(),
                "show_archived": show_archived,
            },
        )

    @catalogue_router.post("/projects/{project_id}/details")
    def update_project(
        project_id: UUID,
        name: str = Form(),
        description: str = Form(""),
        web_target: str = Form(),
        security_policy: str = Form(),
    ) -> RedirectResponse:
        project_application.update_project(
            actor=None,
            project_id=project_id,
            name=name,
            description=description,
            web_target=web_target,
            security_policy=security_policy,
        )
        return RedirectResponse(
            f"/#project-{project_id}",
            status_code=303,
        )

    @catalogue_router.post("/projects/{project_id}/test-plans")
    def create_test_plan(
        project_id: UUID,
        name: str = Form(),
        objective: str = Form(),
        scope: str = Form(),
        test_approach: str = Form(),
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
        approach_profile = support.selected_test_approach(
            test_approach_catalog,
            test_approach,
        )
        plan = project_application.create_test_plan(
            actor=None,
            project_id=project_id,
            name=name,
            objective=objective,
            scope=scope,
            test_approach_id=approach_profile.id,
            test_approach_version=approach_profile.version,
            target=target,
            risks=support.line_values(risks),
            entry_criteria=support.line_values(entry_criteria),
            exit_criteria=support.line_values(exit_criteria),
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=support.comma_values(tags),
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{plan.id}",
            status_code=303,
            headers={"x-created-id": str(plan.id)},
        )

    @catalogue_router.get(
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
        approach_profile = test_approach_catalog.get(
            plan.test_approach_id,
            plan.test_approach_version,
        )
        approach_options = list(test_approach_catalog.current_profiles())
        if not any(
            profile.id == approach_profile.id
            and profile.version == approach_profile.version
            for profile in approach_options
        ):
            approach_options.append(approach_profile)
        groups = plan.organize_tests(organization, query=q)
        if organization is OrganizationView.TREE and q.strip():
            matching_cases = tuple(case for group in groups for case in group.tests)
            rows = tuple(support.TreeRow(node=case, depth=0) for case in matching_cases)
        else:
            rows = support.tree_rows(plan.nodes, show_archived=show_archived)
        containers = tuple(
            node
            for node in plan.nodes
            if node.kind in {NodeKind.SUITE, NodeKind.FOLDER} and not node.archived
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
                "test_approach": approach_profile,
                "test_approaches": tuple(approach_options),
            },
        )

    @catalogue_router.post("/projects/{project_id}/test-plans/{test_plan_id}/details")
    def update_test_plan(
        project_id: UUID,
        test_plan_id: UUID,
        name: str = Form(),
        objective: str = Form(),
        scope: str = Form(),
        test_approach: str = Form(),
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
        approach_profile = support.selected_test_approach(
            test_approach_catalog,
            test_approach,
        )
        project_application.update_test_plan(
            actor=None,
            project_id=project_id,
            test_plan_id=test_plan_id,
            name=name,
            objective=objective,
            scope=scope,
            test_approach_id=approach_profile.id,
            test_approach_version=approach_profile.version,
            target=target,
            risks=support.line_values(risks),
            entry_criteria=support.line_values(entry_criteria),
            exit_criteria=support.line_values(exit_criteria),
            resources=resources,
            constraints=constraints,
            schedule=schedule,
            test_type=test_type,
            tags=support.comma_values(tags),
        )
        return support.plan_redirect(project_id, test_plan_id)

    @catalogue_router.post("/projects/{project_id}/test-plans/{test_plan_id}/nodes")
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
        node = project_application.add_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            kind=kind,
            name=name,
            parent_id=support.optional_uuid(parent_id),
            position=support.optional_integer(position),
            tags=support.comma_values(tags),
            objective=objective,
            test_type=test_type,
            preconditions=support.line_values(preconditions),
            postconditions=support.line_values(postconditions),
            execution_declaration=support.line_values(execution_declaration),
        )
        if node.kind is NodeKind.TEST:
            return RedirectResponse(
                support.case_url(project_id, test_plan_id, node.id),
                status_code=303,
                headers={"x-created-id": str(node.id)},
            )
        return support.plan_redirect(
            project_id,
            test_plan_id,
            created_id=node.id,
        )

    @catalogue_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/first-case"
    )
    def create_first_case(
        project_id: UUID,
        test_plan_id: UUID,
        name: str = Form(),
    ) -> RedirectResponse:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        suite = next(
            (
                node
                for node in plan.nodes
                if node.kind is NodeKind.SUITE and not node.archived
            ),
            None,
        )
        if suite is None:
            suite = project_application.add_node(
                actor=None,
                project_id=project_id,
                test_set_id=test_plan_id,
                kind=NodeKind.SUITE,
                name="Parcours principal",
                objective="Regrouper les premiers cas fonctionnels du plan.",
                test_type=plan.test_type,
            )
        case = project_application.add_node(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            kind=NodeKind.TEST,
            name=name,
            parent_id=suite.id,
        )
        return RedirectResponse(
            support.case_url(project_id, test_plan_id, case.id),
            status_code=303,
            headers={"x-created-id": str(case.id)},
        )

    @catalogue_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/nodes/{node_id}/rename"
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
        return support.plan_redirect(project_id, test_plan_id)

    @catalogue_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/nodes/{node_id}/move"
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
            new_parent_id=support.optional_uuid(new_parent_id),
            position=support.optional_integer(position),
        )
        return support.plan_redirect(project_id, test_plan_id)

    @catalogue_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/nodes/{node_id}/archive"
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
        return support.plan_redirect(
            project_id,
            test_plan_id,
            show_archived=True,
        )

    return catalogue_router
