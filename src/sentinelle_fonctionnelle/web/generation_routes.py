"""Routeur generation de l'interface locale."""

from __future__ import annotations

import json
from importlib.util import find_spec
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.application import (
    CodeGenerationError,
    CodeGenerationPromptError,
    assess_workflow_readiness,
    build_code_generation_prompt,
    export_approved_candidate,
    generate_python_playwright,
    validate_code_generation_response,
)
from sentinelle_fonctionnelle.domain import (
    CandidateOrigin,
    HierarchyError,
    NodeKind,
)
from sentinelle_fonctionnelle.web import route_support as support
from sentinelle_fonctionnelle.web.composition import WebServices


def build_generation_router(
    services: WebServices,
    templates: Jinja2Templates,
) -> APIRouter:
    """Construit le routeur generation avec ses dépendances explicites."""

    generation_router = APIRouter(tags=["generation"])
    project_application = services.projects
    generation_profile_catalog = services.generation_profiles
    candidate_lifecycle = services.candidates

    def _build_case_generation_prompt_artifact(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ):
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        if case.kind is not NodeKind.TEST or case.specification is None:
            raise HierarchyError("Ce cas ne possède pas de workflow générable.")
        specification = case.specification
        workflow = specification.workflow
        if workflow is None or not workflow.confirmed:
            raise HierarchyError(
                "Confirmez le workflow avant d’ouvrir le prompt de génération."
            )
        if not workflow.code_generation_profile:
            raise HierarchyError("Sélectionnez un profil de génération de code.")
        if not workflow.llm_access_profile:
            raise HierarchyError("Sélectionnez un profil d’accès LLM.")
        generation_id, generation_version = support.versioned_profile_reference(
            workflow.code_generation_profile
        )
        llm_id, llm_version = support.versioned_profile_reference(
            workflow.llm_access_profile
        )
        generation_profile = generation_profile_catalog.get_code_generation(
            generation_id,
            generation_version,
        )
        llm_profile = generation_profile_catalog.get_llm_access(
            llm_id,
            llm_version,
        )
        try:
            artifact = build_code_generation_prompt(
                case_id=str(case.id),
                case_name=case.name,
                specification_version=specification.version,
                objective=specification.objective,
                actor=specification.actor,
                summary=specification.summary,
                workflow=workflow.as_dict(),
                code_profile=generation_profile,
                llm_profile=llm_profile,
            )
        except CodeGenerationPromptError as error:
            raise HierarchyError(
                f"Le prompt de génération ne peut pas être produit : {error}"
            ) from error
        return artifact, project, plan, case

    def _case_context(project_id: UUID, test_plan_id: UUID, case_id: UUID):
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        if case.kind is not NodeKind.TEST or case.specification is None:
            raise HierarchyError("Ce cas ne possède pas de workflow générable.")
        workflow = case.specification.workflow
        if workflow is None or not workflow.confirmed:
            raise HierarchyError("Confirmez le workflow avant de générer un candidat.")
        return project, plan, case, workflow

    def _deterministic_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        *,
        customization_source: UUID | None = None,
    ):
        project, plan, case, workflow = _case_context(project_id, test_plan_id, case_id)
        if workflow.schema_version >= 2:
            readiness = assess_workflow_readiness(
                workflow,
                project_target=project.web_target,
                available_secret_refs=support.available_secret_refs(
                    workflow.secret_refs
                ),
                browser_available=find_spec("playwright") is not None,
            )
            if not readiness.ready:
                failed = "; ".join(
                    check.detail
                    for check in readiness.checks
                    if check.blocking and check.status.value == "failed"
                )
                raise HierarchyError(
                    "La préparation du cas bloque la génération : " + failed
                )
        case_slug = f"case_{case.id.hex}"
        try:
            artifact = generate_python_playwright(
                {
                    "case_slug": case_slug,
                    "test_name": f"test_{case_slug}",
                    "data_files": [],
                    "workflow": workflow.as_dict(),
                }
            )
        except CodeGenerationError as error:
            raise HierarchyError(
                f"Le code ne peut pas encore être généré : {error}"
            ) from error
        specification = case.specification
        specification_sha256 = candidate_lifecycle.specification_fingerprint(
            specification_version=specification.version,
            workflow=workflow.as_dict(),
        )
        candidate_files = ((f"tests/cases/test_{case_slug}.py", artifact.source),)
        manifest = {
            **dict(artifact.manifest),
            "project_id": str(project.id),
            "test_plan_id": str(plan.id),
            "case_id": str(case.id),
            "specification_version": specification.version,
            "specification_sha256": specification_sha256,
            "test_type": case.test_type or plan.test_type,
            "tags": list(case.tags),
            "ci_declaration": list(specification.execution_declaration),
            "files": [
                {
                    "path": f"tests/cases/test_{case_slug}.py",
                    "sha256": artifact.source_sha256,
                }
            ],
        }
        if customization_source is not None:
            source_candidate = candidate_lifecycle.get(customization_source)
            if (
                source_candidate.project_id != project.id
                or source_candidate.test_plan_id != plan.id
                or source_candidate.case_id != case.id
            ):
                raise HierarchyError(
                    "Le candidat personnalisé n'appartient pas à ce cas de test."
                )
            candidate_files, reapplication = candidate_lifecycle.reapply_customizations(
                source_candidate,
                candidate_files,
            )
            manifest["customization"] = source_candidate.manifest["customization"]
            manifest["customization_reapplication"] = reapplication
            if reapplication["conflicts"]:
                manifest["customization_conflicts"] = reapplication["conflicts"]
        stored = candidate_lifecycle.create(
            project_id=project.id,
            test_plan_id=plan.id,
            case_id=case.id,
            origin=CandidateOrigin.DETERMINISTIC,
            specification_version=specification.version,
            specification_sha256=specification_sha256,
            files=candidate_files,
            manifest=manifest,
        )
        return stored, artifact, project, plan, case

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/generation-prompt"
    )
    def open_case_generation_prompt(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ) -> JSONResponse:
        artifact, _, _, _ = _build_case_generation_prompt_artifact(
            project_id,
            test_plan_id,
            case_id,
        )
        return JSONResponse(
            artifact.as_dict(),
            headers={
                "X-Prompt-SHA256": artifact.sha256,
                "Content-Disposition": (
                    f'attachment; filename="generation-prompt-{case_id}.json"'
                ),
            },
        )

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/code-generation-request",
        response_class=HTMLResponse,
    )
    def view_case_generation_prompt(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ) -> HTMLResponse:
        artifact, project, plan, case = _build_case_generation_prompt_artifact(
            project_id,
            test_plan_id,
            case_id,
        )
        document = artifact.as_dict()
        return templates.TemplateResponse(
            request=request,
            name="generation_prompt.html",
            context={
                "project": project,
                "plan": plan,
                "case": case,
                "artifact": document,
                "artifact_json": json.dumps(
                    document,
                    ensure_ascii=False,
                    indent=2,
                ),
                "system_message": document["messages"][0]["content"],
                "user_message": document["messages"][1]["content"],
            },
        )

    @generation_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/llm-generated-code"
    )
    def generate_case_code_with_llm(
        request: Request,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ) -> Response:
        prompt, project, plan, case = _build_case_generation_prompt_artifact(
            project_id,
            test_plan_id,
            case_id,
        )
        prompt_document = prompt.as_dict()
        llm_id, llm_version = support.versioned_profile_reference(
            str(prompt_document["llm_access_profile"])
        )
        generation_id, generation_version = support.versioned_profile_reference(
            str(prompt_document["code_generation_profile"])
        )
        llm_profile = generation_profile_catalog.get_llm_access(
            llm_id,
            llm_version,
        )
        generation_profile = generation_profile_catalog.get_code_generation(
            generation_id,
            generation_version,
        )
        raw_response = request.app.state.design_llm.generate_code(
            profile=llm_profile,
            prompt=prompt_document,
        )
        try:
            candidate = validate_code_generation_response(
                raw_response,
                prompt=prompt,
                profile=generation_profile,
            )
        except CodeGenerationPromptError as error:
            raise HierarchyError(
                f"La réponse du LLM de génération est refusée : {error}"
            ) from error
        specification = case.specification
        if specification is None or specification.workflow is None:
            raise HierarchyError("Le cas ne possède plus de définition générable.")
        specification_sha256 = candidate_lifecycle.specification_fingerprint(
            specification_version=specification.version,
            workflow=specification.workflow.as_dict(),
        )
        stored_candidate = candidate_lifecycle.create(
            project_id=project.id,
            test_plan_id=plan.id,
            case_id=case.id,
            origin=CandidateOrigin.LLM,
            specification_version=specification.version,
            specification_sha256=specification_sha256,
            files=tuple((item.path, item.content) for item in candidate.files),
            manifest={
                "schema_version": 1,
                "project_id": str(project.id),
                "test_plan_id": str(plan.id),
                "case_id": str(case.id),
                "specification_version": specification.version,
                "specification_sha256": specification_sha256,
                "prompt_sha256": prompt.sha256,
                "llm_access_profile": llm_profile.reference,
                "model": llm_profile.model,
                "code_generation_profile": generation_profile.reference,
                "files": [
                    {"path": item.path, "sha256": item.sha256}
                    for item in candidate.files
                ],
                "assumptions": list(candidate.assumptions),
                "warnings": list(candidate.warnings),
            },
            prompt_sha256=prompt.sha256,
        )
        common_headers = {
            "X-Prompt-SHA256": prompt.sha256,
            "X-Candidate-SHA256": stored_candidate.candidate_sha256,
            "X-Candidate-ID": str(stored_candidate.id),
            "X-LLM-Profile": llm_profile.reference,
            "X-LLM-Model": llm_profile.model,
            "X-Generated-Files": str(len(candidate.files)),
            "X-Generation-Assumptions": str(len(candidate.assumptions)),
            "X-Generation-Warnings": str(len(candidate.warnings)),
        }
        if (
            len(candidate.files) == 1
            and not candidate.assumptions
            and not candidate.warnings
        ):
            generated_file = candidate.primary_file
            return Response(
                generated_file.content,
                media_type=(
                    "text/x-python; charset=utf-8"
                    if generation_profile.language == "python"
                    else "text/typescript; charset=utf-8"
                ),
                headers={
                    **common_headers,
                    "X-Source-SHA256": generated_file.sha256,
                    "Content-Disposition": (
                        'attachment; filename="'
                        + PurePosixPath(generated_file.path).name
                        + '"'
                    ),
                },
            )
        archive = BytesIO()
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for generated_file in candidate.files:
                bundle.writestr(generated_file.path, generated_file.content)
            bundle.writestr(
                "sentinelle-candidate.json",
                json.dumps(
                    {
                        "schema_version": 1,
                        "prompt_sha256": prompt.sha256,
                        "candidate_sha256": candidate.sha256,
                        "llm_access_profile": llm_profile.reference,
                        "model": llm_profile.model,
                        "files": [
                            {
                                "path": generated_file.path,
                                "sha256": generated_file.sha256,
                            }
                            for generated_file in candidate.files
                        ],
                        "assumptions": candidate.assumptions,
                        "warnings": candidate.warnings,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
        return Response(
            archive.getvalue(),
            media_type="application/zip",
            headers={
                **common_headers,
                "Content-Disposition": (
                    f'attachment; filename="candidate-{case_id}.zip"'
                ),
            },
        )

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}"
        "/cases/{case_id}/generated-code"
    )
    def download_generated_case_code(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
    ) -> Response:
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        if case.kind is not NodeKind.TEST or case.specification is None:
            raise HierarchyError("Ce cas ne possède pas de workflow générable.")
        workflow = case.specification.workflow
        if workflow is None or not workflow.confirmed:
            raise HierarchyError(
                "Confirmez le workflow avant de télécharger le code généré."
            )
        if workflow.schema_version >= 2:
            readiness = assess_workflow_readiness(
                workflow,
                project_target=project.web_target,
                available_secret_refs=support.available_secret_refs(
                    workflow.secret_refs
                ),
                browser_available=find_spec("playwright") is not None,
            )
            if not readiness.ready:
                failed = "; ".join(
                    check.detail
                    for check in readiness.checks
                    if check.blocking and check.status.value == "failed"
                )
                raise HierarchyError(
                    "La préparation du cas bloque la génération : " + failed
                )
        case_slug = f"case_{case.id.hex}"
        try:
            artifact = generate_python_playwright(
                {
                    "case_slug": case_slug,
                    "test_name": f"test_{case_slug}",
                    "data_files": [],
                    "workflow": workflow.as_dict(),
                }
            )
        except CodeGenerationError as error:
            raise HierarchyError(
                f"Le code ne peut pas encore être généré : {error}"
            ) from error
        return Response(
            artifact.source,
            media_type="text/x-python; charset=utf-8",
            headers={
                "Content-Disposition": (f'attachment; filename="test_{case_slug}.py"'),
                "X-Source-SHA256": artifact.source_sha256,
            },
        )

    @generation_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}/candidates"
    )
    def create_case_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        customization_source: str = Form(""),
    ) -> RedirectResponse:
        source_id: UUID | None = None
        if customization_source.strip():
            try:
                source_id = UUID(customization_source)
            except ValueError as error:
                raise HierarchyError(
                    "La source de personnalisation est invalide."
                ) from error
        _deterministic_candidate(
            project_id,
            test_plan_id,
            case_id,
            customization_source=source_id,
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}#candidates",
            status_code=303,
        )

    def _case_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
    ):
        project = project_application.get_project(None, project_id)
        plan = project.test_plan(test_plan_id)
        case = plan.node(case_id)
        candidate = candidate_lifecycle.get(candidate_id)
        if (
            candidate.project_id != project.id
            or candidate.test_plan_id != plan.id
            or candidate.case_id != case.id
        ):
            raise HierarchyError("Le candidat n'appartient pas à ce cas de test.")
        return candidate, project, plan, case

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/download"
    )
    def download_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
    ) -> Response:
        candidate, _, _, _ = _case_candidate(
            project_id, test_plan_id, case_id, candidate_id
        )
        if len(candidate.files) == 1:
            generated_file = candidate.files[0]
            return Response(
                generated_file.content,
                media_type="text/x-python; charset=utf-8",
                headers={
                    "X-Candidate-SHA256": candidate.candidate_sha256,
                    "X-Source-SHA256": generated_file.sha256,
                    "Content-Disposition": (
                        'attachment; filename="'
                        + PurePosixPath(generated_file.path).name
                        + '"'
                    ),
                },
            )
        archive = BytesIO()
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
            for generated_file in candidate.files:
                bundle.writestr(generated_file.path, generated_file.content)
            bundle.writestr(
                "sentinelle-candidate.json",
                json.dumps(candidate.manifest, ensure_ascii=False, indent=2) + "\n",
            )
        return Response(
            archive.getvalue(),
            media_type="application/zip",
            headers={
                "X-Candidate-SHA256": candidate.candidate_sha256,
                "Content-Disposition": (
                    f'attachment; filename="candidate-{candidate.id}.zip"'
                ),
            },
        )

    @generation_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/customize"
    )
    async def customize_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
        source_file: UploadFile = File(),
    ) -> RedirectResponse:
        candidate, _, _, _ = _case_candidate(
            project_id, test_plan_id, case_id, candidate_id
        )
        python_files = [item for item in candidate.files if item.path.endswith(".py")]
        if len(python_files) != 1:
            raise HierarchyError(
                "La personnalisation guidée exige exactement un fichier Python."
            )
        content = await source_file.read(1_048_577)
        if len(content) > 1_048_576:
            raise HierarchyError("Le fichier personnalisé dépasse la limite de 1 Mio.")
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise HierarchyError(
                "Le fichier personnalisé doit être encodé en UTF-8."
            ) from error
        candidate_lifecycle.customize(
            candidate.id,
            path=python_files[0].path,
            content=source,
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}#candidates",
            status_code=303,
        )

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/ci-bundle"
    )
    def download_candidate_ci_bundle(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
    ) -> Response:
        candidate, project, plan, case = _case_candidate(
            project_id, test_plan_id, case_id, candidate_id
        )
        specification = case.specification
        if specification is None:
            raise HierarchyError("Le cas ne possède plus de définition structurée.")
        artifact = export_approved_candidate(
            candidate,
            project_name=project.name,
            plan_name=plan.name,
            case_name=case.name,
            environment=specification.environment or "development",
            specification={
                "objective": specification.objective,
                "summary": specification.summary,
                "actor": specification.actor,
                "preconditions": list(specification.preconditions),
                "data_sets": list(specification.data_sets),
                "postconditions": list(specification.postconditions),
                "requirements": list(specification.requirements),
                "business_rules": list(specification.business_rules),
                "execution_declaration": list(specification.execution_declaration),
                "steps": [
                    {
                        "action": clause.text,
                        "expected_result": clause.expected_result,
                    }
                    for clause in specification.clauses
                ],
            },
        )
        return Response(
            artifact.content,
            media_type="application/zip",
            headers={
                "X-Bundle-SHA256": artifact.sha256,
                "Content-Disposition": (
                    f'attachment; filename="sentinelle-bundle-{candidate.id}.zip"'
                ),
            },
        )

    @generation_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/execute"
    )
    def execute_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
        browser: str = Form("chromium"),
    ) -> RedirectResponse:
        _, project, _, _ = _case_candidate(
            project_id, test_plan_id, case_id, candidate_id
        )
        target = urlsplit(project.web_target)
        candidate_lifecycle.execute(
            candidate_id,
            base_url=f"{target.scheme}://{target.netloc}",
            browser=browser,
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}#candidates",
            status_code=303,
        )

    @generation_router.post(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/decision"
    )
    def decide_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
        decision: str = Form(),
        reason: str = Form(""),
    ) -> RedirectResponse:
        _case_candidate(project_id, test_plan_id, case_id, candidate_id)
        if decision not in {"approve", "reject"}:
            raise HierarchyError("La décision demandée est inconnue.")
        candidate_lifecycle.decide(
            candidate_id,
            approved=decision == "approve",
            reason=reason,
        )
        return RedirectResponse(
            f"/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}#candidates",
            status_code=303,
        )

    @generation_router.get(
        "/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"
        "/candidates/{candidate_id}/comparison"
    )
    def compare_candidate(
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        candidate_id: UUID,
    ) -> JSONResponse:
        candidate, _, _, _ = _case_candidate(
            project_id, test_plan_id, case_id, candidate_id
        )
        history = candidate_lifecycle.list_for_case(
            project_id=project_id, test_plan_id=test_plan_id, case_id=case_id
        )
        index = next(i for i, item in enumerate(history) if item.id == candidate.id)
        previous = history[index + 1] if index + 1 < len(history) else None
        comparison = candidate_lifecycle.compare(candidate, previous)
        return JSONResponse(
            {
                "previous_id": (
                    str(comparison.previous_id) if comparison.previous_id else None
                ),
                "current_id": str(comparison.current_id),
                "added": comparison.added,
                "changed": comparison.changed,
                "removed": comparison.removed,
            }
        )

    return generation_router
