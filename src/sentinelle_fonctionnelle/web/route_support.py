"""Validations, redirections et projections partagées par les routeurs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from uuid import UUID

from fastapi.responses import RedirectResponse

from sentinelle_fonctionnelle.domain import (
    DesignDialogueError,
    GenerationProfileCatalog,
    GenerationWorkflowInput,
    HierarchyError,
    HierarchyNode,
    Project,
    SpecificationStyle,
    TestApproachCatalog,
    TestApproachError,
    TestApproachProfile,
    TestPlan,
    WorkflowError,
    canonical_design_draft,
)


@dataclass(frozen=True, slots=True)
class TreeRow:
    node: HierarchyNode
    depth: int


def tree_rows(
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


def selected_test_approach(
    catalog: TestApproachCatalog,
    value: str,
) -> TestApproachProfile:
    """Résout la valeur explicite ``identifiant@version`` d'un formulaire."""

    profile_id, separator, raw_version = value.strip().partition("@")
    if not separator or not profile_id or not raw_version:
        raise TestApproachError(
            "La sélection d'approche de test doit contenir un identifiant "
            "et une version."
        )
    try:
        version = int(raw_version)
    except ValueError as error:
        raise TestApproachError(
            "La version de l'approche de test doit être un entier."
        ) from error
    profile = catalog.get(profile_id, version)
    if not profile.enabled:
        raise TestApproachError(f"L'approche de test {profile.name} est désactivée.")
    return profile


def container_path(
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


def project_redirect(project_id: UUID) -> RedirectResponse:
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


def plan_redirect(
    project_id: UUID,
    test_plan_id: UUID,
    *,
    created_id: UUID | None = None,
    show_archived: bool = False,
) -> RedirectResponse:
    suffix = "?show_archived=true" if show_archived else ""
    headers = {"x-created-id": str(created_id)} if created_id else None
    return RedirectResponse(
        f"/projects/{project_id}{suffix}#plan-{test_plan_id}",
        status_code=303,
        headers=headers,
    )


def case_url(project_id: UUID, test_plan_id: UUID, case_id: UUID) -> str:
    return f"/projects/{project_id}/test-plans/{test_plan_id}/cases/{case_id}"


def case_redirect(
    project_id: UUID,
    test_plan_id: UUID,
    case_id: UUID,
) -> RedirectResponse:
    return RedirectResponse(
        case_url(project_id, test_plan_id, case_id),
        status_code=303,
    )


def expected_results(case: HierarchyNode) -> tuple[str, ...]:
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


def specification_source(
    *,
    style: SpecificationStyle,
    source_text: str,
    step_actions: str,
    expected_results: str,
) -> str:
    if style != SpecificationStyle.STEPS or not step_actions.strip():
        return source_text
    actions = text_lines(step_actions)
    results = text_lines(expected_results)
    if len(actions) != len(results):
        raise HierarchyError(
            "Chaque étape de test doit posséder exactement un résultat attendu."
        )
    if not actions:
        raise HierarchyError("Au moins une étape de test est obligatoire.")
    return "\n".join(
        f"{action} => {result}" for action, result in zip(actions, results, strict=True)
    )


def generation_workflow(value: str) -> GenerationWorkflowInput | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        data = json.loads(normalized)
    except json.JSONDecodeError as error:
        raise WorkflowError(
            "La structure de génération n’est pas un document JSON valide."
        ) from error
    if not isinstance(data, dict):
        raise WorkflowError("La structure de génération doit être un objet JSON.")
    return GenerationWorkflowInput.from_mapping(data)


def design_draft_from_json(value: str) -> dict[str, object]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as error:
        raise DesignDialogueError(
            "Le brouillon du dialogue n’est pas un JSON valide."
        ) from error
    if not isinstance(data, dict):
        raise DesignDialogueError("Le brouillon du dialogue doit être un objet JSON.")
    return canonical_design_draft(data)


def design_operation_ids(value: str) -> tuple[str, ...]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as error:
        raise DesignDialogueError(
            "La décision de dialogue n’est pas un JSON valide."
        ) from error
    if not isinstance(data, list) or any(not isinstance(item, str) for item in data):
        raise DesignDialogueError("La décision doit contenir une liste d’identifiants.")
    if len(data) > 12:
        raise DesignDialogueError(
            "Une décision ne peut contenir plus de 12 propositions."
        )
    return tuple(data)


def editor_draft(
    case: HierarchyNode,
    workflow: dict[str, object],
) -> dict[str, object]:
    if case.design_dialogue is not None and case.design_dialogue.accepted_draft:
        return canonical_design_draft(case.design_dialogue.accepted_draft)
    specification = case.specification
    return canonical_design_draft(
        {
            "objective": (specification.objective if specification is not None else ""),
            "actor": (specification.actor if specification is not None else ""),
            "summary": (specification.summary if specification is not None else ""),
            "preconditions": (
                list(specification.preconditions) if specification is not None else []
            ),
            "postconditions": (
                list(specification.postconditions) if specification is not None else []
            ),
            "requirements": (
                list(specification.requirements) if specification is not None else []
            ),
            "business_rules": (
                list(specification.business_rules) if specification is not None else []
            ),
            "data_sets": (
                list(specification.data_sets) if specification is not None else []
            ),
            "workflow": workflow,
        }
    )


def workflow_for_editor(
    project: Project,
    plan: TestPlan,
    case: HierarchyNode,
) -> dict[str, object]:
    if case.design_dialogue is not None and isinstance(
        case.design_dialogue.accepted_draft.get("workflow"),
        dict,
    ):
        return dict(case.design_dialogue.accepted_draft["workflow"])
    specification = case.specification
    if specification is not None and specification.workflow is not None:
        return specification.workflow.as_dict()

    start_url = (
        specification.environment
        if specification is not None
        and specification.environment.startswith(("http://", "https://"))
        else project.web_target
    )
    legacy_steps = []
    if specification is not None:
        for index, clause in enumerate(specification.clauses, start=1):
            legacy_steps.append(
                {
                    "id": f"step-{index}",
                    "name": f"Étape {index}",
                    "page_url": start_url,
                    "precondition": "",
                    "action": "wait",
                    "target": "",
                    "value": clause.text,
                    "assertion": ("text" if clause.expected_result else "none"),
                    "assertion_target": "",
                    "expected": clause.expected_result or "",
                    "evidence": False,
                }
            )
    if not legacy_steps:
        legacy_steps.append(
            {
                "id": "step-1",
                "name": "Ouvrir la page de départ",
                "page_url": start_url,
                "precondition": "",
                "action": "navigate",
                "target": "",
                "value": "",
                "assertion": "visible",
                "assertion_target": "",
                "expected": "",
                "evidence": False,
            }
        )
    return {
        "schema_version": 1,
        "start_url": start_url,
        "environment_profile": (
            specification.environment
            if specification is not None and specification.environment
            else plan.target
        ),
        "actor_profile": (specification.actor if specification is not None else ""),
        "functional_intent": "",
        "fixture_refs": (
            list(specification.data_sets) if specification is not None else []
        ),
        "secret_refs": [],
        "setup": (
            list(specification.preconditions) if specification is not None else []
        ),
        "cleanup": (
            list(specification.postconditions) if specification is not None else []
        ),
        "evidence_policy": "on_failure",
        "llm_policy": "design_only",
        "llm_access_profile": "",
        "code_generation_profile": "",
        "timeout_seconds": 30,
        "assumptions": (
            ["Requalifier les anciennes étapes dans le nouvel éditeur."]
            if specification is not None
            else []
        ),
        "authoring_mode": "form",
        "step_narratives": [],
        "scenario_narrative": "",
        "confirmed": False,
        "pages": [],
        "steps": legacy_steps,
    }


def allowed_page_url(project_target: str, value: str) -> str:
    candidate = urljoin(project_target.rstrip("/") + "/", value.strip())
    project = urlparse(project_target)
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HierarchyError("La page doit être une URL HTTP ou HTTPS absolue.")
    if (parsed.scheme.casefold(), parsed.netloc.casefold()) != (
        project.scheme.casefold(),
        project.netloc.casefold(),
    ):
        raise HierarchyError(
            "La page à analyser doit appartenir à la cible web du projet."
        )
    if parsed.username or parsed.password:
        raise HierarchyError("Une URL de page ne peut contenir d’identifiants.")
    return candidate


def validate_workflow_destinations(
    workflow: GenerationWorkflowInput,
    project_target: str,
) -> None:
    allowed_page_url(project_target, workflow.start_url)
    for page in workflow.pages:
        allowed_page_url(project_target, page.url)
    for step in workflow.steps:
        if step.page_url:
            allowed_page_url(project_target, step.page_url)


def validate_generation_profile_references(
    workflow: GenerationWorkflowInput,
    catalog: GenerationProfileCatalog,
) -> None:
    if workflow.llm_access_profile:
        llm_id, llm_version = versioned_profile_reference(workflow.llm_access_profile)
        catalog.get_llm_access(llm_id, llm_version)
    if workflow.code_generation_profile:
        generation_id, generation_version = versioned_profile_reference(
            workflow.code_generation_profile
        )
        generation_profile = catalog.get_code_generation(
            generation_id,
            generation_version,
        )
        if (
            workflow.llm_access_profile
            and generation_profile.llm_profile != workflow.llm_access_profile
        ):
            raise WorkflowError(
                "Le profil de génération sélectionné utilise un autre accès LLM."
            )


def versioned_profile_reference(value: str) -> tuple[str, int]:
    profile_id, version = value.rsplit("@", 1)
    return profile_id, int(version)


def optional_uuid(value: str) -> UUID | None:
    normalized = value.strip()
    if not normalized:
        return None
    try:
        return UUID(normalized)
    except ValueError as error:
        raise HierarchyError("L'identifiant du parent est invalide.") from error


def optional_integer(
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


def required_integer(value: str, label: str) -> int:
    normalized = value.strip()
    if not normalized:
        raise HierarchyError(f"{label} est obligatoire.")
    try:
        return int(normalized)
    except ValueError as error:
        raise HierarchyError(f"{label} doit être un entier.") from error


def comma_values(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(",") if part.strip())


def line_values(value: str) -> tuple[str, ...]:
    normalized = value.replace(",", "\n")
    return tuple(line.strip() for line in normalized.splitlines() if line.strip())


def available_secret_refs(references: tuple[str, ...]) -> tuple[str, ...]:
    """Résout uniquement la présence d’un secret, jamais sa valeur."""

    available: list[str] = []
    for reference in references:
        environment_name = "SENTINELLE_SECRET_" + "".join(
            character.upper() if character.isalnum() else "_" for character in reference
        )
        if os.environ.get(environment_name):
            available.append(reference)
    return tuple(available)


def text_lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.splitlines() if line.strip())
