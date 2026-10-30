"""Projet Sentinelle prêt à tester la cible commandes multi-écrans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sentinelle_fonctionnelle.domain import (
    GenerationWorkflowInput,
    HierarchyNode,
    NodeKind,
    SpecificationStyle,
    TestPlan,
)

from .projects import ProjectApplication


PROJECT_NAME = "Exemple — Comptoir des commandes"
PLAN_NAME = "Commande multi-écrans"
SUITE_NAME = "Parcours de commande"
CASE_NAME = "Créer une commande avec remise et plusieurs articles"


@dataclass(frozen=True, slots=True)
class OrdersDemoSeedResult:
    project_id: UUID
    plan_id: UUID
    case_id: UUID
    created: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "project_id": str(self.project_id),
            "plan_id": str(self.plan_id),
            "case_id": str(self.case_id),
            "created": self.created,
        }


def seed_orders_demo_project(
    application: ProjectApplication,
    *,
    base_url: str = "http://127.0.0.1:8000",
) -> OrdersDemoSeedResult:
    target = base_url.rstrip("/") + "/demo/commandes"
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
            "Démonstration multi-écrans avec formulaires, listes déroulantes, "
            "tableaux, calculs et pages de consultation."
        ),
        web_target=target,
        security_policy="demo-only same-origin local-loopback",
    )
    plan = _plan(application, project.id, target)
    suite = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.SUITE,
        name=SUITE_NAME,
        parent_id=None,
        objective="Valider une commande complète sur quatre écrans.",
    )
    case = _node(
        application,
        project.id,
        plan,
        kind=NodeKind.TEST,
        name=CASE_NAME,
        parent_id=suite.id,
        objective=(
            "Saisir le client, deux articles, une remise et contrôler le suivi."
        ),
    )
    workflow = _workflow(base_url.rstrip("/"))
    needs_update = (
        case.specification is None
        or case.specification.workflow is None
        or case.specification.workflow.as_dict() != workflow.as_dict()
    )
    if needs_update:
        application.define_test(
            None,
            project_id=project.id,
            test_set_id=plan.id,
            test_id=case.id,
            style=SpecificationStyle.STEPS,
            objective=(
                "Créer une commande comportant deux claviers et une station USB-C, "
                "puis vérifier le calcul et le statut."
            ),
            actor_name="Ada Martin — acheteuse entreprise",
            source_text="",
            environment="orders-demo-local",
            preconditions=workflow.setup,
            data_sets=(),
            postconditions=workflow.cleanup,
            requirements=("DEMO-ORDER-MULTI-SCREEN", "DEMO-ORDER-CALCULATION"),
            business_rules=(
                "Le code DEMO10 applique dix pour cent de remise.",
                "Le total TTC comprend la remise, la livraison et vingt pour cent de TVA.",
                "Une commande inférieure à 500 euros est confirmée automatiquement.",
            ),
            execution_declaration=("manual",),
            workflow=workflow,
            summary=(
                "Ada Martin renseigne son profil, sélectionne plusieurs articles "
                "dans un tableau, contrôle le total calculé et obtient une commande confirmée."
            ),
        )
    return OrdersDemoSeedResult(
        project_id=project.id,
        plan_id=plan.id,
        case_id=case.id,
        created=created,
    )


def _plan(
    application: ProjectApplication,
    project_id: UUID,
    target: str,
) -> TestPlan:
    project = application.get_project(None, project_id)
    existing = next(
        (plan for plan in project.test_plans if plan.name == PLAN_NAME), None
    )
    if existing is not None:
        return existing
    return application.create_test_plan(
        None,
        project_id=project_id,
        name=PLAN_NAME,
        objective=(
            "Démontrer la conception d’un test fonctionnel traversant plusieurs écrans."
        ),
        target=target,
        scope="Client, articles, récapitulatif calculé, confirmation et suivi.",
        test_approach_id="automated-regression",
        test_approach_version=1,
        risks=(
            "Perte de données entre deux écrans.",
            "Calcul erroné de la remise ou de la TVA.",
            "Valeurs saisies absentes de la consultation finale.",
        ),
        entry_criteria=("La cible commandes locale répond.",),
        exit_criteria=("La commande est confirmée et contient deux lignes.",),
        resources="Navigateur Playwright.",
        constraints="Données synthétiques et stockage éphémère.",
        schedule="Exécution manuelle de démonstration.",
        test_type="acceptance",
        tags=("demo-commandes", "multi-ecrans", "tableau", "calcul"),
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
    objective: str,
) -> HierarchyNode:
    existing = next(
        (
            node
            for node in plan.nodes
            if node.kind is kind and node.name == name and node.parent_id == parent_id
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
        tags=("demo-commandes",),
        objective=objective,
        test_type="acceptance",
        execution_declaration=("manual",),
    )


def _workflow(base_url: str) -> GenerationWorkflowInput:
    client_url = base_url + "/demo/commandes/client"
    pages = [
        _page(
            client_url,
            "Client · Comptoir des commandes",
            "orders-client-v1",
            (
                _element(
                    "page:client#heading",
                    "h1",
                    "heading",
                    "Identifier le demandeur",
                    "heading",
                    "role",
                    "heading|Identifier le demandeur",
                ),
                _element(
                    "page:client#name",
                    "input",
                    "textbox",
                    "Nom ou raison sociale",
                    "text",
                    "label",
                    "Nom ou raison sociale",
                ),
                _element(
                    "page:client#email",
                    "input",
                    "textbox",
                    "Adresse e-mail",
                    "email",
                    "label",
                    "Adresse e-mail",
                ),
                _element(
                    "page:client#type",
                    "select",
                    "combobox",
                    "Type de client",
                    "select",
                    "label",
                    "Type de client",
                    ("Particulier", "Association", "Entreprise", "Administration"),
                ),
                _element(
                    "page:client#date",
                    "input",
                    "textbox",
                    "Date de livraison souhaitée",
                    "date",
                    "label",
                    "Date de livraison souhaitée",
                ),
                _element(
                    "page:client#priority",
                    "input",
                    "radio",
                    "Haute",
                    "radio",
                    "label",
                    "Haute",
                ),
                _element(
                    "page:client#notes",
                    "textarea",
                    "textbox",
                    "Instructions de livraison",
                    "textarea",
                    "label",
                    "Instructions de livraison",
                ),
                _element(
                    "page:client#submit",
                    "button",
                    "button",
                    "Continuer vers les articles",
                    "submit",
                    "role",
                    "button|Continuer vers les articles",
                ),
            ),
        ),
        _page(
            base_url + "/demo/commandes/parser/articles",
            "Articles · Comptoir des commandes",
            "orders-items-v1",
            (
                _element(
                    "page:articles#heading",
                    "h1",
                    "heading",
                    "Composer la commande",
                    "heading",
                    "role",
                    "heading|Composer la commande",
                ),
                _element(
                    "page:articles#keyboard",
                    "input",
                    "spinbutton",
                    "Quantité Clavier mécanique azur",
                    "number",
                    "label",
                    "Quantité Clavier mécanique azur",
                ),
                _element(
                    "page:articles#dock",
                    "input",
                    "spinbutton",
                    "Quantité Station USB-C",
                    "number",
                    "label",
                    "Quantité Station USB-C",
                ),
                _element(
                    "page:articles#delivery",
                    "select",
                    "combobox",
                    "Mode de livraison",
                    "select",
                    "label",
                    "Mode de livraison",
                    ("standard", "express", "pickup"),
                ),
                _element(
                    "page:articles#discount",
                    "input",
                    "textbox",
                    "Code promotionnel",
                    "text",
                    "label",
                    "Code promotionnel",
                ),
                _element(
                    "page:articles#gift",
                    "input",
                    "checkbox",
                    "Ajouter un emballage cadeau (+3,50 €)",
                    "checkbox",
                    "label",
                    "Ajouter un emballage cadeau (+3,50 €)",
                ),
                _element(
                    "page:articles#submit",
                    "button",
                    "button",
                    "Calculer le récapitulatif",
                    "submit",
                    "role",
                    "button|Calculer le récapitulatif",
                ),
            ),
        ),
        _page(
            base_url + "/demo/commandes/parser/recapitulatif",
            "Récapitulatif · Comptoir des commandes",
            "orders-review-v1",
            (
                _element(
                    "page:review#heading",
                    "h1",
                    "heading",
                    "Vérifier le récapitulatif",
                    "heading",
                    "role",
                    "heading|Vérifier le récapitulatif",
                ),
                _element(
                    "page:review#total",
                    "dd",
                    "generic",
                    "287.12 €",
                    "text",
                    "css",
                    "#order-total",
                ),
                _element(
                    "page:review#payment",
                    "select",
                    "combobox",
                    "Mode de paiement",
                    "select",
                    "label",
                    "Mode de paiement",
                    ("invoice", "card", "transfer"),
                ),
                _element(
                    "page:review#terms",
                    "input",
                    "checkbox",
                    "Je confirme les informations et les montants.",
                    "checkbox",
                    "label",
                    "Je confirme les informations et les montants.",
                ),
                _element(
                    "page:review#submit",
                    "button",
                    "button",
                    "Confirmer la commande",
                    "submit",
                    "role",
                    "button|Confirmer la commande",
                ),
            ),
        ),
        _page(
            base_url + "/demo/commandes/parser/suivi",
            "Suivi · Comptoir des commandes",
            "orders-tracking-v1",
            (
                _element(
                    "page:tracking#status",
                    "span",
                    "status",
                    "Confirmée",
                    "text",
                    "css",
                    "#order-status",
                ),
                _element(
                    "page:tracking#rows",
                    "tr",
                    "row",
                    "Lignes de commande",
                    "table-row",
                    "css",
                    "#tracking-table tbody tr",
                ),
            ),
        ),
    ]
    steps = [
        _step(
            "open",
            "Ouvrir la saisie client",
            client_url,
            "navigate",
            "",
            "",
            "visible",
            "page:client#heading",
            "",
        ),
        _step("name", "Saisir le nom", "", "fill", "page:client#name", "Ada Martin"),
        _step(
            "email",
            "Saisir l’e-mail",
            "",
            "fill",
            "page:client#email",
            "ada.martin@example.test",
        ),
        _step(
            "type",
            "Choisir le type de client",
            "",
            "select",
            "page:client#type",
            "Entreprise",
        ),
        _step("date", "Saisir la date", "", "fill", "page:client#date", "2026-11-15"),
        _step(
            "priority", "Choisir la priorité", "", "check", "page:client#priority", ""
        ),
        _step(
            "notes",
            "Saisir les instructions",
            "",
            "fill",
            "page:client#notes",
            "Livrer à l’accueil.",
        ),
        _step(
            "next",
            "Continuer vers les articles",
            "",
            "click",
            "page:client#submit",
            "",
            "visible",
            "page:articles#heading",
            "",
        ),
        _step(
            "keyboard",
            "Ajouter deux claviers",
            "",
            "fill",
            "page:articles#keyboard",
            "2",
        ),
        _step(
            "dock", "Ajouter une station USB-C", "", "fill", "page:articles#dock", "1"
        ),
        _step(
            "delivery",
            "Choisir la livraison standard",
            "",
            "select",
            "page:articles#delivery",
            "standard",
        ),
        _step(
            "discount",
            "Saisir la remise",
            "",
            "fill",
            "page:articles#discount",
            "DEMO10",
        ),
        _step("gift", "Ajouter l’emballage", "", "check", "page:articles#gift", ""),
        _step(
            "calculate",
            "Calculer le récapitulatif",
            "",
            "click",
            "page:articles#submit",
            "",
            "text",
            "page:review#total",
            "287.12 €",
        ),
        _step(
            "payment",
            "Choisir la facture",
            "",
            "select",
            "page:review#payment",
            "invoice",
        ),
        _step(
            "terms", "Confirmer les informations", "", "check", "page:review#terms", ""
        ),
        _step(
            "confirm",
            "Confirmer la commande",
            "",
            "click",
            "page:review#submit",
            "",
            "text",
            "page:tracking#status",
            "Confirmée",
            True,
        ),
        _step(
            "rows",
            "Contrôler les deux lignes",
            "",
            "none",
            "",
            "",
            "count",
            "page:tracking#rows",
            "2",
            True,
        ),
    ]
    setup = "L’application de commandes de démonstration est disponible localement"
    return GenerationWorkflowInput.from_mapping(
        {
            "schema_version": 2,
            "start_url": client_url,
            "environment_profile": "orders-demo-local",
            "actor_profile": "business-buyer",
            "functional_intent": "manage-business-data@1",
            "fixture_refs": [],
            "secret_refs": [],
            "setup": [setup],
            "cleanup": ["Les commandes de démonstration sont éphémères"],
            "evidence_policy": "on_failure",
            "llm_policy": "design_only",
            "llm_access_profile": "ollama-qwen36-128k-11436@1",
            "code_generation_profile": "python-playwright-qwen36-11436@1",
            "timeout_seconds": 30,
            "assumptions": [],
            "authoring_mode": "form",
            "step_narratives": [],
            "scenario_narrative": "",
            "confirmed": True,
            "pages": pages,
            "steps": steps,
            "precondition_dependencies": [
                {
                    "id": "orders-demo-ready",
                    "source": setup,
                    "kind": "technical_dependency",
                    "description": "Vérifier la santé HTTP de la cible locale",
                    "reference": "orders-demo-local",
                    "confirmed": True,
                }
            ],
        }
    )


def _page(
    url: str, title: str, fingerprint: str, elements: tuple[dict[str, Any], ...]
) -> dict[str, Any]:
    return {
        "url": url,
        "title": title,
        "fingerprint": fingerprint,
        "elements": list(elements),
    }


def _element(
    reference: str,
    kind: str,
    role: str,
    label: str,
    input_type: str,
    strategy: str,
    value: str,
    options: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "reference": reference,
        "kind": kind,
        "role": role,
        "label": label,
        "input_type": input_type,
        "locator": {"strategy": strategy, "value": value},
        "options": list(options),
    }


def _step(
    step_id: str,
    name: str,
    page_url: str,
    action: str,
    target: str,
    value: str,
    assertion: str = "none",
    assertion_target: str = "",
    expected: str = "",
    evidence: bool = False,
) -> dict[str, Any]:
    return {
        "id": step_id,
        "name": name,
        "page_url": page_url,
        "precondition": "",
        "action": action,
        "target": target,
        "value": value,
        "assertion": assertion,
        "assertion_target": assertion_target,
        "expected": expected,
        "evidence": evidence,
    }
