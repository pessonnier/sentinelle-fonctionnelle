"""Construction minimisée du contexte envoyé au LLM de conception."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Protocol

from sentinelle_fonctionnelle.domain import (
    DesignDialogue,
    DesignGuidance,
    FunctionalIntent,
    LLMAccessProfile,
    canonical_design_draft,
)
from .authoring_modes import authoring_skill_context


class DesignLLM(Protocol):
    def complete(
        self,
        *,
        profile: LLMAccessProfile,
        request: dict[str, Any],
    ) -> Mapping[str, Any]: ...


def build_design_llm_request(
    *,
    draft: Mapping[str, Any],
    dialogue: DesignDialogue,
    guidance: DesignGuidance,
    intent: FunctionalIntent,
    llm_access_profile: str,
    user_message: str,
) -> dict[str, Any]:
    """Produit un contexte fermé, sans localisateur ni valeur de secret."""

    canonical = canonical_design_draft(draft)
    workflow = deepcopy(canonical["workflow"])
    workflow["pages"] = [
        {
            "url": str(page.get("url") or ""),
            "title": str(page.get("title") or ""),
            "elements": [
                {
                    "reference": str(element.get("reference") or ""),
                    "role": str(element.get("role") or ""),
                    "label": str(element.get("label") or ""),
                    "input_type": str(element.get("input_type") or ""),
                    "options": list(element.get("options") or ()),
                }
                for element in page.get("elements", ())
                if isinstance(element, Mapping)
            ],
        }
        for page in workflow.get("pages", ())
        if isinstance(page, Mapping)
    ]
    canonical["workflow"] = workflow
    return {
        "schema_version": 1,
        "prompt_version": "design-dialogue-v1",
        "mission": (
            "Développer avec l’utilisateur un cas de test fonctionnel complet, "
            "précis et directement transformable en code. Poser une question "
            "lorsqu’un fait métier manque et proposer uniquement les "
            "modifications structurées justifiées par le brouillon."
        ),
        "llm_access_profile": llm_access_profile,
        "intent": intent.as_dict(),
        "current_draft": canonical,
        "authoring_skill": authoring_skill_context(workflow),
        "missing_information": [
            item.as_dict() for item in guidance.missing_information
        ],
        "html_fields": [
            item.as_dict() for item in guidance.html_fields
        ],
        "recent_conversation": [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in dialogue.messages[-8:]
        ],
        "user_message": user_message.strip(),
        "response_contract": {
            "root": {
                "exact_fields": [
                    "schema_version",
                    "questions",
                    "operations",
                ],
                "schema_version": 1,
                "questions": "liste de 0 à 8 chaînes courtes",
                "operations": "liste de 0 à 12 opérations",
            },
            "operation": {
                "maximum": 12,
                "exact_fields": [
                    "id",
                    "operation",
                    "path",
                    "value",
                    "label",
                    "reason",
                ],
                "operations": ["add", "replace"],
                "allowed_paths_and_required_operation": {
                    "/objective": "replace",
                    "/actor": "replace",
                    "/preconditions/-": "add",
                    "/postconditions/-": "add",
                    "/requirements/-": "add",
                    "/business_rules/-": "add",
                    "/data_sets/-": "add",
                    "/workflow/actor_profile": "replace",
                    "/workflow/fixture_refs/-": "add",
                    "/workflow/secret_refs/-": "add",
                    "/workflow/setup/-": "add",
                    "/workflow/cleanup/-": "add",
                    "/workflow/assumptions/-": "add",
                    "/workflow/steps/-": "add",
                    "/workflow/steps/{index}/{editable_field}": "replace",
                },
                "editable_step_fields": [
                    "name",
                    "page_url",
                    "precondition",
                    "action",
                    "target",
                    "value",
                    "assertion",
                    "assertion_target",
                    "expected",
                    "evidence",
                ],
            },
            "new_step_value": {
                "exact_fields": [
                    "id",
                    "name",
                    "page_url",
                    "precondition",
                    "action",
                    "target",
                    "value",
                    "assertion",
                    "assertion_target",
                    "expected",
                    "evidence",
                ],
                "action_enum": [
                    "none",
                    "navigate",
                    "click",
                    "fill",
                    "select",
                    "check",
                    "uncheck",
                    "upload",
                ],
                "assertion_enum": [
                    "none",
                    "visible",
                    "hidden",
                    "text",
                    "value",
                    "checked",
                    "enabled",
                    "url",
                    "count",
                ],
                "constraints": [
                    "Une étape contient une action ou une assertion.",
                    "navigate exige page_url.",
                    "click, fill, select, check, uncheck et upload exigent target.",
                    "fill, select et upload exigent value.",
                    "Une assertion autre que none ou url exige assertion_target.",
                    "text, value, url et count exigent expected.",
                ],
            },
            "valid_response_example": {
                "schema_version": 1,
                "questions": [
                    "Quelle référence de secret le runner doit-il résoudre ?"
                ],
                "operations": [
                    {
                        "id": "ajouter-etape",
                        "operation": "add",
                        "path": "/workflow/steps/-",
                        "value": {
                            "id": "step-proposee",
                            "name": "Saisir la donnée",
                            "page_url": "",
                            "precondition": "",
                            "action": "fill",
                            "target": "page:exemple#champ",
                            "value": "{{fixture.donnee}}",
                            "assertion": "value",
                            "assertion_target": "page:exemple#champ",
                            "expected": "{{fixture.donnee}}",
                            "evidence": False,
                        },
                        "label": "Ajouter la saisie",
                        "reason": "Le champ analysé accepte une saisie observable.",
                    }
                ],
            },
            "forbidden_paths": [
                "/workflow/confirmed",
                "/workflow/pages",
                "/workflow/llm_access_profile",
                "/workflow/code_generation_profile",
            ],
            "forbidden": [
                "confirmer le workflow",
                "modifier les profils LLM ou de génération",
                "inventer une valeur secrète",
                "modifier les pages analysées",
                "présenter un contrôle comme exécuté",
            ],
        },
        "quality_rules": [
            "Un cas couvre un seul comportement métier.",
            "Chaque action manipulant une page utilise une référence HTML connue.",
            "Le parcours contient au moins une validation observable.",
            "Une valeur secrète est toujours une référence {{secret.nom}}.",
            "Une donnée variable utilise {{data.nom}} ou {{fixture.nom}}.",
            "Ne pas inventer un résultat, un compte, une donnée ou une exigence.",
            "Préférer des étapes courtes, ordonnées et nommées.",
            "Questionner l’utilisateur plutôt que masquer une ambiguïté.",
            "Ne jamais demander la valeur d’un secret ; demander uniquement le nom de sa référence.",
            "Ne pas proposer une référence de fixture ou de secret déjà présente.",
            "Ne proposer aucune opération qui dépend de la réponse à une question encore ouverte.",
            "Ne jamais fabriquer une URL, une référence ou un espace de noms de jeton.",
            "Une référence fixture ou secret existante est une donnée complète : ne jamais demander sa valeur résolue.",
            "Ne jamais remplacer une redirection attendue de l’application par une action navigate du test.",
            "Vérifier schema_version et la forme exacte de chaque étape avant de répondre.",
        ],
    }


def build_connectivity_request() -> dict[str, Any]:
    """Construit la sonde minimale qui vérifie aussi le mode JSON structuré."""

    return {
        "schema_version": 1,
        "prompt_version": "connectivity-v1",
        "mission": (
            "Vérifier la capacité de réponse JSON du modèle. Répondre exactement "
            "avec le contrat demandé, sans texte supplémentaire."
        ),
        "response_contract": {
            "schema_version": 1,
            "questions": [],
            "operations": [],
        },
    }
