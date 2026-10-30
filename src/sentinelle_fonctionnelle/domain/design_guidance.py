"""Diagnostic déterministe préalable au dialogue de conception LLM.

Le service ne modifie jamais un cas. Il explique les informations manquantes et
les manipulations rendues possibles par les pages HTML déjà analysées.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .test_intents import FunctionalIntent, IntentRequirement


@dataclass(frozen=True, slots=True)
class MissingInformation:
    key: str
    label: str
    question: str
    utility: str
    target: str

    def as_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "question": self.question,
            "utility": self.utility,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class HtmlFieldGuidance:
    reference: str
    label: str
    role: str
    actions: tuple[str, ...]
    assertions: tuple[str, ...]
    value_examples: tuple[str, ...]
    utility: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "label": self.label,
            "role": self.role,
            "actions": list(self.actions),
            "assertions": list(self.assertions),
            "value_examples": list(self.value_examples),
            "utility": self.utility,
        }


@dataclass(frozen=True, slots=True)
class DesignGuidance:
    intent: FunctionalIntent
    missing_information: tuple[MissingInformation, ...]
    html_fields: tuple[HtmlFieldGuidance, ...]
    completed_count: int
    expected_count: int

    @property
    def completeness_percent(self) -> int:
        if self.expected_count == 0:
            return 100
        return round(self.completed_count * 100 / self.expected_count)

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.as_dict(),
            "missing_information": [
                item.as_dict() for item in self.missing_information
            ],
            "html_fields": [item.as_dict() for item in self.html_fields],
            "completed_count": self.completed_count,
            "expected_count": self.expected_count,
            "completeness_percent": self.completeness_percent,
        }


def build_design_guidance(
    *,
    intent: FunctionalIntent,
    objective: str,
    actor: str,
    preconditions: Sequence[str],
    postconditions: Sequence[str],
    workflow: Mapping[str, Any],
) -> DesignGuidance:
    """Construit les questions utiles depuis le brouillon courant."""

    missing = tuple(
        _missing(requirement)
        for requirement in intent.required_information
        if not _is_present(
            requirement.key,
            objective=objective,
            actor=actor,
            preconditions=preconditions,
            postconditions=postconditions,
            workflow=workflow,
        )
    )
    html_fields = tuple(
        _field_guidance(element)
        for page in _mappings(workflow.get("pages", ()))
        for element in _mappings(page.get("elements", ()))
    )
    expected_count = len(intent.required_information)
    return DesignGuidance(
        intent=intent,
        missing_information=missing,
        html_fields=html_fields,
        completed_count=expected_count - len(missing),
        expected_count=expected_count,
    )


def _missing(requirement: IntentRequirement) -> MissingInformation:
    return MissingInformation(
        key=requirement.key,
        label=requirement.label,
        question=requirement.question,
        utility=requirement.utility,
        target=requirement.target,
    )


def _is_present(
    key: str,
    *,
    objective: str,
    actor: str,
    preconditions: Sequence[str],
    postconditions: Sequence[str],
    workflow: Mapping[str, Any],
) -> bool:
    steps = _mappings(workflow.get("steps", ()))
    fixture_refs = _values(workflow.get("fixture_refs", ()))
    secret_refs = _values(workflow.get("secret_refs", ()))
    setup = (*preconditions, *_values(workflow.get("setup", ())))
    cleanup = (*postconditions, *_values(workflow.get("cleanup", ())))
    checks = {
        "objective": bool(objective.strip()),
        "actor": bool(actor.strip() and str(workflow.get("actor_profile") or "").strip()),
        "start-page": bool(str(workflow.get("start_url") or "").strip()),
        "preconditions": bool(setup),
        "test-data": bool(fixture_refs),
        "credentials": bool(fixture_refs and secret_refs),
        "steps": any(
            str(step.get("name") or "").strip()
            and str(step.get("action") or "none") != "none"
            for step in steps
        ),
        "observable-result": any(
            str(step.get("assertion") or "none") != "none"
            and (
                str(step.get("assertion") or "") == "url"
                or bool(str(step.get("assertion_target") or "").strip())
            )
            for step in steps
        ),
        "cleanup": bool(cleanup),
        "error-variant": bool(_values(workflow.get("assumptions", ()))),
        "permission": "role" in actor.casefold() or "profil" in actor.casefold(),
        "file": any(
            str(step.get("action") or "") == "upload" for step in steps
        ),
        "filters": any(
            str(step.get("action") or "") in {"fill", "select"} for step in steps
        ),
        "state-transition": bool(objective.strip() and cleanup),
        "performance-threshold": any(
            token in objective.casefold()
            for token in ("seconde", "durée", "temps", "performance")
        ),
    }
    return checks.get(key, False)


def _field_guidance(element: Mapping[str, Any]) -> HtmlFieldGuidance:
    role = str(element.get("role") or "")
    input_type = str(element.get("input_type") or "")
    options = _values(element.get("options", ()))
    actions: tuple[str, ...]
    assertions: tuple[str, ...]
    examples: tuple[str, ...]
    utility: str
    if input_type == "file":
        actions = ("upload",)
        assertions = ("visible", "enabled")
        examples = ("{{fixture.fichier}}",)
        utility = "Téléverser un fichier préparé par une fixture."
    elif role == "textbox":
        actions = ("fill",)
        assertions = ("visible", "enabled", "value")
        examples = (
            ("{{secret.valeur}}",)
            if input_type == "password"
            else ("{{data.valeur}}", "{{fixture.valeur}}")
        )
        utility = "Saisir une valeur puis vérifier sa présence ou son état."
    elif role == "combobox":
        actions = ("select",)
        assertions = ("visible", "enabled", "value")
        examples = options or ("{{data.option}}",)
        utility = "Sélectionner une option puis vérifier la valeur retenue."
    elif role == "checkbox":
        actions = ("check", "uncheck")
        assertions = ("visible", "enabled", "checked")
        examples = ()
        utility = "Cocher ou décocher puis vérifier l’état observable."
    elif role in {"button", "link"}:
        actions = ("click",)
        assertions = ("visible", "enabled", "text")
        examples = ()
        utility = "Déclencher une action et vérifier que l’élément est utilisable."
    else:
        actions = ()
        assertions = ("visible", "text")
        examples = ()
        utility = "Utiliser cet élément comme résultat observable."
    return HtmlFieldGuidance(
        reference=str(element.get("reference") or ""),
        label=str(element.get("label") or ""),
        role=role,
        actions=actions,
        assertions=assertions,
        value_examples=examples,
        utility=utility,
    )


def _mappings(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _values(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())
