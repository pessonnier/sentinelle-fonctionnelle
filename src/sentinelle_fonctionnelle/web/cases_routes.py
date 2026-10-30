"""Routeur cases de l'interface locale."""

from __future__ import annotations

import json
from datetime import datetime
from importlib.util import find_spec
from typing import cast
from uuid import UUID

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.adapters.tabular import MAX_FILE_BYTES, parse_tabular_data
from sentinelle_fonctionnelle.application import (
    assess_workflow_readiness,
    generation_skill_documents,
)
from sentinelle_fonctionnelle.application.authoring_modes import (
    AUTHORING_ASSIST_PROMPTS,
    AUTHORING_SKILLS,
)
from sentinelle_fonctionnelle.application.design_assistant import (
    build_design_llm_request,
)
from sentinelle_fonctionnelle.domain import (
    DataIterationMode,
    DesignAssistantResponse,
    DesignDialogue,
    DesignDialogueError,
    GenerationWorkflowInput,
    HierarchyError,
    NodeKind,
    PreconditionDependencyKind,
    SpecificationStyle,
    WorkflowAction,
    WorkflowAssertion,
    WorkflowAuthoringMode,
    WorkflowError,
    build_design_guidance,
)
from sentinelle_fonctionnelle.web import route_support as support
from sentinelle_fonctionnelle.web.composition import WebServices
from sentinelle_fonctionnelle.web.security import DestinationRejected


def build_cases_router(
    services: WebServices,
    templates: Jinja2Templates,
) -> APIRouter:
    """Construit le routeur cases avec ses dépendances explicites."""

    cases_router = APIRouter(tags=["cases"])
    project_application = services.projects
    generation_profile_catalog = services.generation_profiles
    functional_intent_catalog = services.functional_intents
    candidate_lifecycle = services.candidates

    @cases_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}",
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
            raise HierarchyError("L'élément sélectionné n'est pas un cas de test.")
        parent = plan.node(case.parent_id) if case.parent_id else None
        workflow = support.workflow_for_editor(project, plan, case)
        editor_draft = support.editor_draft(case, workflow)
        dialogue = case.design_dialogue or DesignDialogue.empty()
        candidates = candidate_lifecycle.list_for_case(
            project_id=project.id,
            test_plan_id=plan.id,
            case_id=case.id,
            specification_version=(
                case.specification.version if case.specification is not None else None
            ),
        )
        candidate_history = tuple(
            {
                "candidate": candidate,
                "comparison": candidate_lifecycle.compare(
                    candidate,
                    candidates[index + 1] if index + 1 < len(candidates) else None,
                ),
            }
            for index, candidate in enumerate(candidates)
        )
        selected_generation_skills: tuple[dict[str, object], ...] = ()
        code_generation_reference = str(workflow.get("code_generation_profile") or "")
        if code_generation_reference:
            generation_id, generation_version = support.versioned_profile_reference(
                code_generation_reference
            )
            generation_profile = generation_profile_catalog.get_code_generation(
                generation_id,
                generation_version,
            )
            selected_generation_skills = generation_skill_documents(
                generation_profile.generation_skills
            )
        return templates.TemplateResponse(
            request=request,
            name="case_guided.html",
            context={
                "project": project,
                "plan": plan,
                "case": case,
                "parent": parent,
                "path": plan.path(case.id),
                "container_path": support.container_path(plan, case),
                "specification_styles": tuple(SpecificationStyle),
                "data_iteration_modes": tuple(DataIterationMode),
                "expected_results": support.expected_results(case),
                "workflow": workflow,
                "editor_draft": editor_draft,
                "design_dialogue": dialogue,
                "design_dialogue_data": dialogue.as_dict(),
                "workflow_actions": tuple(WorkflowAction),
                "workflow_assertions": tuple(WorkflowAssertion),
                "workflow_authoring_modes": tuple(WorkflowAuthoringMode),
                "precondition_dependency_kinds": tuple(PreconditionDependencyKind),
                "authoring_assist_prompts": AUTHORING_ASSIST_PROMPTS,
                "authoring_skills": AUTHORING_SKILLS,
                "llm_access_profiles": (generation_profile_catalog.llm_access_profiles),
                "code_generation_profiles": (
                    generation_profile_catalog.code_generation_profiles
                ),
                "selected_generation_skills": selected_generation_skills,
                "functional_intents": (functional_intent_catalog.current_intents()),
                "candidate_history": candidate_history,
            },
        )

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}/page-analysis"
    )
    def analyze_case_page(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        page_url: str = Form(),
    ) -> JSONResponse:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError("L’élément sélectionné n’est pas un cas de test.")
        allowed_url = support.allowed_page_url(project.web_target, page_url)
        try:
            html = request.app.state.page_loader(
                allowed_url,
                project_target=project.web_target,
                security_policy=project.security_policy,
            )
        except (OSError, DestinationRejected, ValueError) as error:
            raise HierarchyError(
                f"La page ne peut pas être analysée : {error}."
            ) from error
        return JSONResponse(analyze_html_page(allowed_url, html).as_dict())

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}/readiness"
    )
    def check_case_readiness(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        workflow_json: str = Form(),
    ) -> JSONResponse:
        project = project_application.get_project(None, project_id)
        case = project.test_plan(test_plan_id).node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError("L’élément sélectionné n’est pas un cas de test.")
        if len(workflow_json.encode("utf-8")) > 512 * 1024:
            raise WorkflowError("Le workflow à contrôler dépasse la limite de 512 Kio.")
        try:
            readiness_document = json.loads(workflow_json)
        except json.JSONDecodeError as error:
            raise WorkflowError(
                "Le workflow à contrôler n’est pas un JSON valide."
            ) from error
        if not isinstance(readiness_document, dict):
            raise WorkflowError("Le workflow à contrôler doit être un objet JSON.")
        # La préparation doit expliquer les blocages avant la confirmation : on
        # évalue donc le brouillon sans laisser la validation finale court-circuiter
        # les contrôles détaillés ci-dessous.
        readiness_document = {**readiness_document, "confirmed": False}
        workflow = GenerationWorkflowInput.from_mapping(readiness_document)
        return JSONResponse(
            assess_workflow_readiness(
                workflow,
                project_target=project.web_target,
                available_secret_refs=support.available_secret_refs(
                    workflow.secret_refs
                ),
                browser_available=find_spec("playwright") is not None,
            ).as_dict()
        )

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/design-guidance"
    )
    def design_case_guidance(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        intent_reference: str = Form(),
        objective: str = Form(""),
        actor: str = Form(""),
        preconditions: str = Form(""),
        postconditions: str = Form(""),
        workflow_json: str = Form("{}"),
    ) -> JSONResponse:
        project = project_application.get_project(None, project_id)
        case = project.test_plan(test_plan_id).node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError("L’élément sélectionné n’est pas un cas de test.")
        if len(workflow_json.encode("utf-8")) > 512 * 1024:
            raise WorkflowError("Le brouillon transmis à l’assistant dépasse 512 Kio.")
        try:
            workflow = json.loads(workflow_json)
        except json.JSONDecodeError as error:
            raise WorkflowError(
                "Le brouillon transmis à l’assistant n’est pas un JSON valide."
            ) from error
        if not isinstance(workflow, dict):
            raise WorkflowError(
                "Le brouillon transmis à l’assistant doit être un objet JSON."
            )
        intent = functional_intent_catalog.get_reference(intent_reference)
        return JSONResponse(
            build_design_guidance(
                intent=intent,
                objective=objective,
                actor=actor,
                preconditions=support.line_values(preconditions),
                postconditions=support.line_values(postconditions),
                workflow=workflow,
            ).as_dict()
        )

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/design-dialogue/messages"
    )
    def exchange_design_message(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        message: str = Form(),
        draft_json: str = Form(),
    ) -> JSONResponse:
        project = project_application.get_project(None, project_id)
        case = project.test_plan(test_plan_id).node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError("L’élément sélectionné n’est pas un cas de test.")
        draft = support.design_draft_from_json(draft_json)
        workflow = cast(dict[str, object], draft["workflow"])
        if workflow.get("llm_policy") == "disabled":
            raise DesignDialogueError(
                "La politique LLM du brouillon désactive le dialogue."
            )
        llm_reference = str(workflow.get("llm_access_profile") or "").strip()
        if not llm_reference:
            raise DesignDialogueError(
                "Sélectionnez un profil d’accès LLM avant le dialogue."
            )
        intent_reference = str(workflow.get("functional_intent") or "").strip()
        if not intent_reference:
            raise DesignDialogueError(
                "Sélectionnez une intention fonctionnelle avant le dialogue."
            )
        llm_id, llm_version = support.versioned_profile_reference(llm_reference)
        llm_profile = generation_profile_catalog.get_llm_access(
            llm_id,
            llm_version,
        )
        intent = functional_intent_catalog.get_reference(intent_reference)
        guidance = build_design_guidance(
            intent=intent,
            objective=str(draft["objective"]),
            actor=str(draft["actor"]),
            preconditions=tuple(cast(list[str], draft["preconditions"])),
            postconditions=tuple(cast(list[str], draft["postconditions"])),
            workflow=workflow,
        )
        current = case.design_dialogue or DesignDialogue.empty()
        request_payload = build_design_llm_request(
            draft=draft,
            dialogue=current,
            guidance=guidance,
            intent=intent,
            llm_access_profile=llm_reference,
            user_message=message,
        )
        raw_response = request.app.state.design_llm.complete(
            profile=llm_profile,
            request=request_payload,
        )
        assistant_response = DesignAssistantResponse.from_mapping(raw_response)
        updated = current.with_exchange(
            user_message=message,
            response=assistant_response,
            draft=draft,
            llm_access_profile=llm_reference,
            functional_intent=intent_reference,
            now=datetime.now().astimezone(),
        )
        project_application.update_design_dialogue(
            None,
            project_id=project_id,
            test_set_id=test_plan_id,
            test_id=case_id,
            dialogue=updated,
        )
        return JSONResponse(updated.as_dict())

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/design-dialogue/proposals/{proposal_id}/decision"
    )
    def decide_design_proposal(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        proposal_id: str,
        accepted_operation_ids: str = Form("[]"),
        draft_json: str = Form(),
    ) -> JSONResponse:
        project = project_application.get_project(None, project_id)
        case = project.test_plan(test_plan_id).node(case_id)
        if case.kind is not NodeKind.TEST:
            raise HierarchyError("L’élément sélectionné n’est pas un cas de test.")
        if case.design_dialogue is None:
            raise DesignDialogueError("Aucun dialogue de conception n’est disponible.")
        draft = support.design_draft_from_json(draft_json)
        accepted = support.design_operation_ids(accepted_operation_ids)
        updated, patched, summary = case.design_dialogue.decide(
            proposal_id=proposal_id,
            accepted_operation_ids=accepted,
            draft=draft,
            now=datetime.now().astimezone(),
        )
        project_application.update_design_dialogue(
            None,
            project_id=project_id,
            test_set_id=test_plan_id,
            test_id=case_id,
            dialogue=updated,
        )
        return JSONResponse(
            {
                "dialogue": updated.as_dict(),
                "draft": patched,
                "summary": summary,
            }
        )

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}/specification"
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
        workflow_json: str = Form(""),
        summary: str = Form(""),
    ) -> RedirectResponse:
        workflow = support.generation_workflow(workflow_json)
        if workflow is not None:
            project = project_application.get_project(None, project_id)
            support.validate_workflow_destinations(workflow, project.web_target)
            if workflow.functional_intent:
                functional_intent_catalog.get_reference(workflow.functional_intent)
            support.validate_generation_profile_references(
                workflow,
                generation_profile_catalog,
            )
        effective_source = (
            ""
            if workflow is not None
            else support.specification_source(
                style=style,
                source_text=source_text,
                step_actions=step_actions,
                expected_results=expected_results,
            )
        )
        specification = project_application.define_test(
            actor=None,
            project_id=project_id,
            test_set_id=test_plan_id,
            test_id=case_id,
            style=style,
            objective=objective,
            actor_name=actor_name,
            source_text=effective_source,
            environment=environment,
            preconditions=support.line_values(preconditions),
            data_sets=support.line_values(data_sets),
            postconditions=support.line_values(postconditions),
            requirements=support.line_values(requirements),
            business_rules=support.line_values(business_rules),
            execution_declaration=support.line_values(execution_declaration),
            workflow=workflow,
            summary=summary,
        )
        candidate_lifecycle.list_for_case(
            project_id=project_id,
            test_plan_id=test_plan_id,
            case_id=case_id,
            specification_version=specification.version,
        )
        return support.case_redirect(project_id, test_plan_id, case_id)

    @cases_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}/data-binding"
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
            max_parallelism=support.required_integer(
                max_parallelism,
                "La concurrence maximale",
            ),
            random_seed=support.required_integer(
                random_seed,
                "La graine aléatoire",
            ),
            sample_count=support.optional_integer(
                sample_count,
                label="Le nombre de cas",
            ),
        )
        return support.case_redirect(project_id, test_plan_id, case_id)

    return cases_router
