"""Alimente Sentinelle avec un projet d’exemple couvrant la cible RH intégrée."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping
from uuid import UUID

from sentinelle_fonctionnelle.adapters.tabular import parse_tabular_data
from sentinelle_fonctionnelle.domain import (
    DataIterationMode,
    GenerationWorkflowInput,
    HierarchyNode,
    NodeKind,
    SpecificationStyle,
    TestPlan,
)

from .projects import ProjectApplication


PROJECT_NAME = "Exemple — Bureau des Talents Intersidéraux"
PLAN_NAME = "Parcours RH de démonstration"
FOLDER_NAME = "Parcours fonctionnels"
AUTH_SUITE_NAME = "Authentification"
ONBOARDING_SUITE_NAME = "Gestion des collaborateurs"
NOMINAL_CASE_NAME = "Créer et consulter Zoé Nébuleuse"
REJECTED_CASE_NAME = "Refuser une connexion invalide"


@dataclass(frozen=True, slots=True)
class HrDemoSeedResult:
    project_id: UUID
    plan_id: UUID
    nominal_case_id: UUID
    rejected_case_id: UUID
    created: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "project_id": str(self.project_id),
            "plan_id": str(self.plan_id),
            "nominal_case_id": str(self.nominal_case_id),
            "rejected_case_id": str(self.rejected_case_id),
            "created": self.created,
        }


def seed_hr_demo_project(
    application: ProjectApplication,
    *,
    root_directory: Path,
    base_url: str = "http://127.0.0.1:8000",
) -> HrDemoSeedResult:
    """Crée une fois l’exemple persistant et renvoie ses identifiants stables."""

    root = Path(root_directory).resolve()
    target = base_url.rstrip("/") + "/demo/hr"
    workflow_document = json.loads(
        (root / "config/examples/hr-demo-workflow.json").read_text(
            encoding="utf-8"
        )
    )
    login_rows = _rows(
        root / "outputs/hr-demo/connexion-rh.xlsx",
        key_column="case_id",
    )
    employee_rows = _rows(
        root / "outputs/hr-demo/saisie-collaborateurs.xlsx",
        key_column="case_id",
    )

    existing_project = next(
        (
            project
            for project in application.list_projects(None)
            if project.name == PROJECT_NAME
        ),
        None,
    )
    created = existing_project is None
    project = existing_project or application.create_project(
        None,
        name=PROJECT_NAME,
        description=(
            "Exemple complet de conception, génération et exécution Playwright "
            "sur l’application RH loufoque intégrée. Toutes les données sont synthétiques."
        ),
        web_target=target,
        security_policy="demo-only same-origin local-loopback",
    )

    plan = _plan(application, project.id, target)
    folder = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.FOLDER,
        name=FOLDER_NAME,
        parent_id=None,
    )
    authentication = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.SUITE,
        name=AUTH_SUITE_NAME,
        parent_id=folder.id,
        objective="Vérifier l’accès au sas RH avec des profils synthétiques.",
    )
    onboarding = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.SUITE,
        name=ONBOARDING_SUITE_NAME,
        parent_id=folder.id,
        objective=(
            "Créer une fiche avec des champs statiques, JavaScript et liés au rôle."
        ),
    )

    nominal_case = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.TEST,
        name=NOMINAL_CASE_NAME,
        parent_id=onboarding.id,
        objective=(
            "Connecter le manager, créer Zoé Nébuleuse et contrôler la consultation."
        ),
    )
    rejected_case = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.TEST,
        name=REJECTED_CASE_NAME,
        parent_id=authentication.id,
        objective="Refuser les identifiants synthétiques du profil intrus.",
    )

    nominal_workflow = _nominal_workflow(
        workflow_document,
        base_url=base_url,
        login=login_rows["LOGIN-MANAGER-OK"],
        employee=employee_rows["EMPLOYEE-MANAGER-01"],
    )
    nominal_needs_update = (
        nominal_case.specification is None
        or nominal_case.specification.workflow.as_dict()
        != nominal_workflow.as_dict()
    )
    if nominal_needs_update:
        application.define_test(
            None,
            project_id=project.id,
            test_set_id=plan.id,
            test_id=nominal_case.id,
            style=SpecificationStyle.STEPS,
            objective=(
                "Connecter le manager, créer Zoé Nébuleuse et contrôler la consultation."
            ),
            actor_name="Camille Cactus — manager RH",
            source_text="",
            environment="hr-demo-local",
            preconditions=nominal_workflow.setup,
            data_sets=("connexion-rh", "saisie-collaborateurs"),
            postconditions=nominal_workflow.cleanup,
            requirements=("DEMO-RH-ONBOARDING", "DEMO-RH-DYNAMIC-FIELDS"),
            business_rules=(
                "Les champs manager ne sont visibles qu’après une connexion manager.",
                "La consultation restitue les valeurs saisies côté serveur et JavaScript.",
            ),
            execution_declaration=("manual",),
            workflow=nominal_workflow,
            summary=(
                "Camille Cactus crée la fiche synthétique de Zoé Nébuleuse, puis "
                "contrôle le matricule et la synthèse JavaScript de la consultation."
            ),
        )
    if nominal_case.data_binding is None:
        application.bind_test_data(
            None,
            project_id=project.id,
            test_set_id=plan.id,
            test_id=nominal_case.id,
            data_set=parse_tabular_data(
                "saisie-collaborateurs.xlsx",
                (root / "outputs/hr-demo/saisie-collaborateurs.xlsx").read_bytes(),
            ),
            mode=DataIterationMode.SERIAL,
        )

    rejected_workflow = _rejected_workflow(
        workflow_document,
        base_url=base_url,
        login=login_rows["LOGIN-REFUS"],
    )
    rejected_needs_update = (
        rejected_case.specification is None
        or rejected_case.specification.workflow.as_dict()
        != rejected_workflow.as_dict()
    )
    if rejected_needs_update:
        application.define_test(
            None,
            project_id=project.id,
            test_set_id=plan.id,
            test_id=rejected_case.id,
            style=SpecificationStyle.STEPS,
            objective="Refuser les identifiants synthétiques du profil intrus.",
            actor_name="Intrus Météorite — profil refusé",
            source_text="",
            environment="hr-demo-local",
            preconditions=rejected_workflow.setup,
            data_sets=("connexion-rh",),
            postconditions=rejected_workflow.cleanup,
            requirements=("DEMO-RH-AUTH-REJECT",),
            business_rules=(
                "Un compte inconnu reste sur la page de connexion avec une erreur visible.",
            ),
            execution_declaration=("manual",),
            workflow=rejected_workflow,
            summary=(
                "La cible RH refuse le profil synthétique Intrus Météorite et affiche "
                "un message observable sans ouvrir de session."
            ),
        )
    if rejected_case.data_binding is None:
        application.bind_test_data(
            None,
            project_id=project.id,
            test_set_id=plan.id,
            test_id=rejected_case.id,
            data_set=parse_tabular_data(
                "connexion-rh.xlsx",
                (root / "outputs/hr-demo/connexion-rh.xlsx").read_bytes(),
            ),
            mode=DataIterationMode.SERIAL,
        )

    return HrDemoSeedResult(
        project_id=project.id,
        plan_id=plan.id,
        nominal_case_id=nominal_case.id,
        rejected_case_id=rejected_case.id,
        created=created,
    )


def _plan(
    application: ProjectApplication,
    project_id: UUID,
    target: str,
) -> TestPlan:
    project = application.get_project(None, project_id)
    existing = next(
        (plan for plan in project.test_plans if plan.name == PLAN_NAME),
        None,
    )
    if existing is not None:
        return existing
    return application.create_test_plan(
        None,
        project_id=project_id,
        name=PLAN_NAME,
        objective=(
            "Démontrer l’analyse HTML, les données XLSX, la génération et l’exécution."
        ),
        target=target,
        scope="Connexion, saisie manager et consultation d’une fiche collaborateur.",
        test_approach_id="automated-regression",
        test_approach_version=1,
        risks=(
            "Champ JavaScript absent du HTML source.",
            "Champs conditionnels invisibles hors session manager.",
            "Localisateurs fragiles sur le HTML volontairement médiocre.",
        ),
        entry_criteria=("Sentinelle est démarrée sur la boucle locale.",),
        exit_criteria=("Les deux candidats Playwright sont générables et réussissent.",),
        resources="Chromium et classeurs XLSX synthétiques fournis.",
        constraints="Aucun compte réel et aucune sortie de la boucle locale.",
        schedule="Exécution manuelle de démonstration.",
        test_type="acceptance",
        tags=("demo-rh", "playwright", "html-dynamique", "xlsx"),
        execution_declaration=("manual",),
    )


def _node(
    application: ProjectApplication,
    project_id: UUID,
    plan: TestPlan,
    *,
    kind: NodeKind,
    name: str,
    parent_id: UUID | None,
    objective: str = "",
) -> HierarchyNode:
    existing = next(
        (
            node
            for node in plan.nodes
            if node.kind is kind
            and node.name == name
            and node.parent_id == parent_id
        ),
        None,
    )
    if existing is not None:
        return existing
    return application.add_node(
        None,
        project_id=project_id,
        test_set_id=plan.id,
        kind=kind,
        name=name,
        parent_id=parent_id,
        tags=("demo-rh",),
        objective=objective,
        test_type="acceptance" if kind is not NodeKind.FOLDER else "",
        execution_declaration=("manual",) if kind is not NodeKind.FOLDER else (),
    )


def _nominal_workflow(
    document: Mapping[str, Any],
    *,
    base_url: str,
    login: Mapping[str, str],
    employee: Mapping[str, str],
) -> GenerationWorkflowInput:
    workflow = deepcopy(document["workflow"])
    replacements = {
        **{f"{{{{data.login.{key}}}}}": value for key, value in login.items()},
        **{
            f"{{{{data.employee.{key}}}}}": value
            for key, value in employee.items()
        },
    }
    workflow = _replace_values(workflow, replacements)
    return _finalize_workflow(
        workflow,
        base_url=base_url,
        functional_intent="manage-business-data@1",
        setup="L’application RH de démonstration est disponible sur la boucle locale",
        cleanup="La fiche créée est éphémère et disparaît au redémarrage du serveur",
    )


def _rejected_workflow(
    document: Mapping[str, Any],
    *,
    base_url: str,
    login: Mapping[str, str],
) -> GenerationWorkflowInput:
    source = deepcopy(document["workflow"])
    login_page = deepcopy(source["pages"][0])
    login_page["elements"].append(
        {
            "reference": "page:login#error",
            "kind": "div",
            "role": "alert",
            "label": "Les archives cosmiques refusent ces identifiants.",
            "input_type": "text",
            "locator": {
            "strategy": "css",
            "value": '[role="alert"]',
            },
            "options": [],
        }
    )
    steps = deepcopy(source["steps"][:5])
    steps.append(
        {
            "id": "submit-rejected-login",
            "name": "Soumettre les identifiants refusés",
            "page_url": "",
            "precondition": "",
            "action": "click",
            "target": "page:login#submit",
            "value": "",
            "assertion": "text",
            "assertion_target": "page:login#error",
            "expected": "Les archives cosmiques refusent ces identifiants.",
            "evidence": True,
        }
    )
    workflow = {
        **source,
        "pages": [login_page],
        "steps": steps,
        "fixture_refs": ["connexion-rh"],
    }
    workflow = _replace_values(
        workflow,
        {f"{{{{data.login.{key}}}}}": value for key, value in login.items()},
    )
    return _finalize_workflow(
        workflow,
        base_url=base_url,
        functional_intent="handle-error-invalid-empty@1",
        setup="L’application RH de démonstration est disponible sur la boucle locale",
        cleanup="Aucune session ne doit être ouverte après le refus",
    )


def _finalize_workflow(
    workflow: dict[str, Any],
    *,
    base_url: str,
    functional_intent: str,
    setup: str,
    cleanup: str,
) -> GenerationWorkflowInput:
    configured_origin = "http://127.0.0.1:8000"
    effective_origin = base_url.rstrip("/")
    workflow = _replace_values(workflow, {configured_origin: effective_origin})
    workflow.update(
        {
            "schema_version": 2,
            "environment_profile": "hr-demo-local",
            "functional_intent": functional_intent,
            "setup": [setup],
            "cleanup": [cleanup],
            "authoring_mode": "form",
            "step_narratives": [],
            "scenario_narrative": "",
            "assumptions": [],
            "confirmed": True,
            "precondition_dependencies": [
                {
                    "id": "precondition-1",
                    "source": setup,
                    "kind": "technical_dependency",
                    "description": (
                        "Vérifier la santé HTTP de la cible locale avant le parcours"
                    ),
                    "reference": "hr-demo-local",
                    "confirmed": True,
                }
            ],
        }
    )
    return GenerationWorkflowInput.from_mapping(workflow)


def _replace_values(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            key: _replace_values(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_values(item, replacements) for item in value]
    if isinstance(value, str):
        result = value
        for source, replacement in replacements.items():
            result = result.replace(source, str(replacement))
        return result
    return value


def _rows(path: Path, *, key_column: str) -> dict[str, dict[str, str]]:
    data_set = parse_tabular_data(path.name, path.read_bytes())
    key_index = data_set.headers.index(key_column)
    return {
        row[key_index]: dict(zip(data_set.headers, row, strict=True))
        for row in data_set.rows
    }
