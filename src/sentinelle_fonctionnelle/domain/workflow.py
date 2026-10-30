"""Contrat structuré transmis au futur workflow de génération.

Références : EF-007.6, EF-010, GEN-001, GEN-002, ACC-074 à ACC-077.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re
from typing import Any, Mapping


class WorkflowError(ValueError):
    """La définition guidée ne peut pas produire une entrée de génération valide."""


_TOKEN = re.compile(r"\{\{(?:data|fixture|secret)\.[A-Za-z_][A-Za-z0-9_.-]*\}\}")
_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
_PROFILE_REFERENCE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*@[1-9][0-9]*\Z")


class WorkflowAction(StrEnum):
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    UPLOAD = "upload"
    WAIT = "wait"
    NONE = "none"

    @property
    def label(self) -> str:
        return {
            self.NAVIGATE: "Ouvrir la page",
            self.CLICK: "Cliquer",
            self.FILL: "Saisir",
            self.SELECT: "Sélectionner",
            self.CHECK: "Cocher",
            self.UNCHECK: "Décocher",
            self.UPLOAD: "Téléverser un fichier",
            self.WAIT: "Attendre un état",
            self.NONE: "Aucune action",
        }[self]


class WorkflowAssertion(StrEnum):
    NONE = "none"
    VISIBLE = "visible"
    HIDDEN = "hidden"
    TEXT = "text"
    VALUE = "value"
    URL = "url"
    COUNT = "count"
    ENABLED = "enabled"
    CHECKED = "checked"

    @property
    def label(self) -> str:
        return {
            self.NONE: "Aucune validation",
            self.VISIBLE: "Est visible",
            self.HIDDEN: "Est masqué",
            self.TEXT: "Contient le texte",
            self.VALUE: "Contient la valeur",
            self.URL: "L’URL correspond",
            self.COUNT: "Le nombre correspond",
            self.ENABLED: "Est activé",
            self.CHECKED: "Est coché",
        }[self]


class WorkflowAuthoringMode(StrEnum):
    FORM = "form"
    STEP_TEXT = "step_text"
    SCENARIO_TEXT = "scenario_text"

    @property
    def label(self) -> str:
        return {
            self.FORM: "Formulaires action et contrôle",
            self.STEP_TEXT: "Un texte par étape",
            self.SCENARIO_TEXT: "Un texte pour tout le scénario",
        }[self]

    @property
    def skill_name(self) -> str:
        return {
            self.FORM: "analyze-form-test-steps",
            self.STEP_TEXT: "analyze-step-test-narratives",
            self.SCENARIO_TEXT: "analyze-full-test-narrative",
        }[self]


class PreconditionDependencyKind(StrEnum):
    VERIFICATION = "verification"
    FIXTURE = "fixture"
    TECHNICAL_DEPENDENCY = "technical_dependency"
    SETUP = "setup"
    CLEANUP = "cleanup"

    @property
    def label(self) -> str:
        return {
            self.VERIFICATION: "Condition vérifiable",
            self.FIXTURE: "Fixture ou jeu de données",
            self.TECHNICAL_DEPENDENCY: "Dépendance technique",
            self.SETUP: "Action de préparation",
            self.CLEANUP: "Action de nettoyage",
        }[self]


@dataclass(frozen=True, slots=True)
class PreconditionDependency:
    """Traduction relue d’une précondition métier en élément exécutable."""

    id: str
    source: str
    kind: PreconditionDependencyKind
    description: str
    reference: str = ""
    confirmed: bool = False

    def __post_init__(self) -> None:
        if not _REFERENCE.fullmatch(self.id):
            raise WorkflowError(
                "L’identifiant d’une dépendance de précondition est invalide."
            )
        if not self.source.strip():
            raise WorkflowError("La précondition métier source est obligatoire.")
        if not self.description.strip():
            raise WorkflowError("La traduction de la précondition est obligatoire.")
        if self.reference and not _REFERENCE.fullmatch(self.reference):
            raise WorkflowError(
                f"La référence « {self.reference} » contient un caractère interdit."
            )
        if (
            self.kind
            in {
                PreconditionDependencyKind.FIXTURE,
                PreconditionDependencyKind.TECHNICAL_DEPENDENCY,
            }
            and not self.reference
        ):
            raise WorkflowError(
                "Une fixture ou dépendance technique doit posséder une référence."
            )

    @classmethod
    def from_mapping(
        cls, value: Mapping[str, Any], index: int
    ) -> PreconditionDependency:
        try:
            kind = PreconditionDependencyKind(str(value.get("kind") or "verification"))
        except ValueError as error:
            raise WorkflowError(
                "Le type de traduction d’une précondition est inconnu."
            ) from error
        return cls(
            id=str(value.get("id") or f"precondition-{index}").strip(),
            source=_required(
                value.get("source"),
                "La précondition métier source",
            ),
            kind=kind,
            description=_required(
                value.get("description"),
                "La traduction de la précondition",
            ),
            reference=str(value.get("reference") or "").strip(),
            confirmed=bool(value.get("confirmed", False)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "kind": self.kind.value,
            "description": self.description,
            "reference": self.reference,
            "confirmed": self.confirmed,
        }


@dataclass(frozen=True, slots=True)
class PageLocator:
    strategy: str
    value: str

    def as_dict(self) -> dict[str, str]:
        return {"strategy": self.strategy, "value": self.value}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PageLocator:
        return cls(
            strategy=_required(value.get("strategy"), "La stratégie de localisation"),
            value=_required(value.get("value"), "La valeur de localisation"),
        )


@dataclass(frozen=True, slots=True)
class PageElement:
    reference: str
    kind: str
    role: str
    label: str
    input_type: str
    locator: PageLocator
    options: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "kind": self.kind,
            "role": self.role,
            "label": self.label,
            "input_type": self.input_type,
            "locator": self.locator.as_dict(),
            "options": list(self.options),
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> PageElement:
        return cls(
            reference=_required(value.get("reference"), "La référence de champ"),
            kind=_required(value.get("kind"), "La nature du champ"),
            role=_required(value.get("role"), "Le rôle du champ"),
            label=_required(value.get("label"), "Le libellé du champ"),
            input_type=str(value.get("input_type") or ""),
            locator=PageLocator.from_mapping(_mapping(value.get("locator"))),
            options=_strings(value.get("options", ())),
        )


@dataclass(frozen=True, slots=True)
class AnalyzedPage:
    url: str
    title: str
    fingerprint: str
    elements: tuple[PageElement, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "fingerprint": self.fingerprint,
            "elements": [element.as_dict() for element in self.elements],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> AnalyzedPage:
        return cls(
            url=_http_url(value.get("url"), "L’URL de la page analysée"),
            title=str(value.get("title") or "").strip(),
            fingerprint=_required(value.get("fingerprint"), "L’empreinte de la page"),
            elements=tuple(
                PageElement.from_mapping(_mapping(element))
                for element in _sequence(value.get("elements", ()))
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    id: str
    name: str
    page_url: str
    precondition: str
    action: WorkflowAction
    target: str
    value: str
    assertion: WorkflowAssertion
    assertion_target: str
    expected: str
    evidence: bool = False

    def __post_init__(self) -> None:
        if (
            self.action is WorkflowAction.NONE
            and self.assertion is WorkflowAssertion.NONE
        ):
            raise WorkflowError(
                f"L’étape « {self.name} » doit contenir une action ou une validation."
            )
        if self.action is WorkflowAction.NAVIGATE and not self.page_url:
            raise WorkflowError(
                f"L’étape « {self.name} » doit indiquer la page à ouvrir."
            )
        if (
            self.action
            in {
                WorkflowAction.CLICK,
                WorkflowAction.FILL,
                WorkflowAction.SELECT,
                WorkflowAction.CHECK,
                WorkflowAction.UNCHECK,
                WorkflowAction.UPLOAD,
            }
            and not self.target
        ):
            raise WorkflowError(
                f"L’étape « {self.name} » doit cibler un champ de page."
            )
        if (
            self.action
            in {
                WorkflowAction.FILL,
                WorkflowAction.SELECT,
                WorkflowAction.UPLOAD,
            }
            and not self.value
        ):
            raise WorkflowError(f"L’étape « {self.name} » doit fournir une valeur.")
        if (
            self.assertion
            not in {
                WorkflowAssertion.NONE,
                WorkflowAssertion.URL,
            }
            and not self.assertion_target
        ):
            raise WorkflowError(
                f"L’étape « {self.name} » doit cibler l’élément à valider."
            )
        if (
            self.assertion
            in {
                WorkflowAssertion.TEXT,
                WorkflowAssertion.VALUE,
                WorkflowAssertion.URL,
                WorkflowAssertion.COUNT,
            }
            and not self.expected
        ):
            raise WorkflowError(
                f"L’étape « {self.name} » doit indiquer le résultat attendu."
            )
        _validate_tokens(self.value, self.name)
        _validate_tokens(self.expected, self.name)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], index: int) -> WorkflowStep:
        name = _required(value.get("name"), f"Le nom de l’étape {index}")
        return cls(
            id=str(value.get("id") or f"step-{index}").strip(),
            name=name,
            page_url=_optional_http_url(value.get("page_url"), "L’URL de l’étape"),
            precondition=str(value.get("precondition") or "").strip(),
            action=WorkflowAction(str(value.get("action") or "none")),
            target=str(value.get("target") or "").strip(),
            value=str(value.get("value") or "").strip(),
            assertion=WorkflowAssertion(str(value.get("assertion") or "none")),
            assertion_target=str(value.get("assertion_target") or "").strip(),
            expected=str(value.get("expected") or "").strip(),
            evidence=bool(value.get("evidence", False)),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "page_url": self.page_url,
            "precondition": self.precondition,
            "action": self.action.value,
            "target": self.target,
            "value": self.value,
            "assertion": self.assertion.value,
            "assertion_target": self.assertion_target,
            "expected": self.expected,
            "evidence": self.evidence,
        }

    @property
    def action_text(self) -> str:
        parts = [self.action.label]
        if self.target:
            parts.append(self.target)
        if self.value:
            parts.append(f"avec {self.value}")
        return " ".join(parts)

    @property
    def assertion_text(self) -> str:
        parts = [self.assertion.label]
        if self.assertion_target:
            parts.append(self.assertion_target)
        if self.expected:
            parts.append(f": {self.expected}")
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class GenerationWorkflowInput:
    """Données case-level versionnées données au futur générateur."""

    schema_version: int
    start_url: str
    environment_profile: str
    actor_profile: str
    functional_intent: str
    fixture_refs: tuple[str, ...]
    secret_refs: tuple[str, ...]
    setup: tuple[str, ...]
    cleanup: tuple[str, ...]
    evidence_policy: str
    llm_policy: str
    llm_access_profile: str
    code_generation_profile: str
    timeout_seconds: int
    assumptions: tuple[str, ...]
    authoring_mode: WorkflowAuthoringMode
    step_narratives: tuple[str, ...]
    scenario_narrative: str
    confirmed: bool
    pages: tuple[AnalyzedPage, ...]
    steps: tuple[WorkflowStep, ...]
    precondition_dependencies: tuple[PreconditionDependency, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version not in {1, 2}:
            raise WorkflowError("La version du schéma de génération doit être 1 ou 2.")
        has_narrative_draft = (
            self.authoring_mode is WorkflowAuthoringMode.STEP_TEXT
            and bool(self.step_narratives)
        ) or (
            self.authoring_mode is WorkflowAuthoringMode.SCENARIO_TEXT
            and bool(self.scenario_narrative.strip())
        )
        if self.confirmed and not self.steps:
            raise WorkflowError(
                "Un brouillon narratif doit être structuré avant confirmation."
            )
        if not self.steps and not has_narrative_draft:
            raise WorkflowError("Le workflow doit contenir au moins une étape.")
        if self.steps and not any(
            step.assertion is not WorkflowAssertion.NONE for step in self.steps
        ):
            raise WorkflowError(
                "Le workflow doit contenir au moins une validation observable."
            )
        if len(self.step_narratives) > 100:
            raise WorkflowError("Le brouillon dépasse cent textes d’étape.")
        if any(len(value) > 4_000 for value in self.step_narratives):
            raise WorkflowError("Un texte d’étape dépasse 4 000 caractères.")
        if len(self.scenario_narrative) > 40_000:
            raise WorkflowError("Le texte du scénario dépasse 40 000 caractères.")
        if self.evidence_policy not in {"none", "on_failure", "each_step"}:
            raise WorkflowError("La politique de preuve est inconnue.")
        if self.llm_policy not in {
            "disabled",
            "design_only",
            "adaptive_approved",
        }:
            raise WorkflowError("La politique LLM est inconnue.")
        for reference, label in (
            (self.functional_intent, "L’intention fonctionnelle"),
            (self.llm_access_profile, "Le profil d’accès LLM"),
            (self.code_generation_profile, "Le profil de génération de code"),
        ):
            if reference and not _PROFILE_REFERENCE.fullmatch(reference):
                raise WorkflowError(
                    f"{label} doit suivre la syntaxe identifiant@version."
                )
        if not 1 <= self.timeout_seconds <= 3600:
            raise WorkflowError("Le délai du cas doit être compris entre 1 et 3 600 s.")
        if self.confirmed and self.assumptions:
            raise WorkflowError(
                "Un workflow confirmé ne peut pas conserver d’hypothèse ouverte."
            )
        for reference in (*self.fixture_refs, *self.secret_refs):
            if not _REFERENCE.fullmatch(reference):
                raise WorkflowError(
                    f"La référence « {reference} » contient un caractère interdit."
                )
        dependency_ids = tuple(item.id for item in self.precondition_dependencies)
        if len(dependency_ids) != len(set(dependency_ids)):
            raise WorkflowError(
                "Deux traductions de précondition ne peuvent pas partager le même identifiant."
            )
        unknown_sources = {
            item.source for item in self.precondition_dependencies
        } - set(self.setup)
        if unknown_sources:
            raise WorkflowError(
                "Une traduction référence une précondition absente du brouillon."
            )
        if self.schema_version >= 2 and self.confirmed:
            covered = {item.source for item in self.precondition_dependencies}
            missing = [source for source in self.setup if source not in covered]
            if missing:
                raise WorkflowError(
                    "Chaque précondition doit être traduite avant confirmation."
                )
            if any(not item.confirmed for item in self.precondition_dependencies):
                raise WorkflowError(
                    "Chaque traduction de précondition doit être confirmée avant génération."
                )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> GenerationWorkflowInput:
        try:
            schema_version = int(value.get("schema_version", 1))
            timeout_seconds = int(value.get("timeout_seconds", 30))
        except (TypeError, ValueError) as error:
            raise WorkflowError(
                "La version du schéma et le délai doivent être des entiers."
            ) from error
        try:
            authoring_mode = WorkflowAuthoringMode(
                str(value.get("authoring_mode") or "form")
            )
        except ValueError as error:
            raise WorkflowError("Le mode de saisie des étapes est inconnu.") from error
        return cls(
            schema_version=schema_version,
            start_url=_http_url(value.get("start_url"), "La page de départ"),
            environment_profile=_required(
                value.get("environment_profile"),
                "Le profil d’environnement",
            ),
            actor_profile=_required(value.get("actor_profile"), "Le profil d’acteur"),
            functional_intent=str(value.get("functional_intent") or "").strip(),
            fixture_refs=_strings(value.get("fixture_refs", ())),
            secret_refs=_strings(value.get("secret_refs", ())),
            setup=_strings(value.get("setup", ())),
            cleanup=_strings(value.get("cleanup", ())),
            evidence_policy=str(value.get("evidence_policy") or "on_failure"),
            llm_policy=str(value.get("llm_policy") or "design_only"),
            llm_access_profile=str(value.get("llm_access_profile") or "").strip(),
            code_generation_profile=str(
                value.get("code_generation_profile") or ""
            ).strip(),
            timeout_seconds=timeout_seconds,
            assumptions=_strings(value.get("assumptions", ())),
            authoring_mode=authoring_mode,
            step_narratives=_strings(value.get("step_narratives", ())),
            scenario_narrative=str(value.get("scenario_narrative") or "").strip(),
            confirmed=bool(value.get("confirmed", False)),
            pages=tuple(
                AnalyzedPage.from_mapping(_mapping(page))
                for page in _sequence(value.get("pages", ()))
            ),
            steps=tuple(
                WorkflowStep.from_mapping(_mapping(step), index)
                for index, step in enumerate(
                    _sequence(value.get("steps", ())),
                    start=1,
                )
            ),
            precondition_dependencies=tuple(
                PreconditionDependency.from_mapping(_mapping(item), index)
                for index, item in enumerate(
                    _sequence(value.get("precondition_dependencies", ())),
                    start=1,
                )
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "start_url": self.start_url,
            "environment_profile": self.environment_profile,
            "actor_profile": self.actor_profile,
            "functional_intent": self.functional_intent,
            "fixture_refs": list(self.fixture_refs),
            "secret_refs": list(self.secret_refs),
            "setup": list(self.setup),
            "cleanup": list(self.cleanup),
            "evidence_policy": self.evidence_policy,
            "llm_policy": self.llm_policy,
            "llm_access_profile": self.llm_access_profile,
            "code_generation_profile": self.code_generation_profile,
            "timeout_seconds": self.timeout_seconds,
            "assumptions": list(self.assumptions),
            "authoring_mode": self.authoring_mode.value,
            "step_narratives": list(self.step_narratives),
            "scenario_narrative": self.scenario_narrative,
            "confirmed": self.confirmed,
            "pages": [page.as_dict() for page in self.pages],
            "steps": [step.as_dict() for step in self.steps],
            "precondition_dependencies": [
                item.as_dict() for item in self.precondition_dependencies
            ],
        }


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkflowError("Une partie du workflow doit être un objet structuré.")
    return value


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise WorkflowError("Une partie du workflow doit être une liste.")
    return tuple(value)


def _strings(value: Any) -> tuple[str, ...]:
    values = tuple(str(item).strip() for item in _sequence(value))
    if any(not item for item in values):
        raise WorkflowError("Une liste du workflow ne peut contenir de valeur vide.")
    return values


def _required(value: Any, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise WorkflowError(f"{label} est obligatoire.")
    return normalized


def _http_url(value: Any, label: str) -> str:
    normalized = _required(value, label)
    if not normalized.startswith(("http://", "https://")):
        raise WorkflowError(f"{label} doit être une URL HTTP ou HTTPS absolue.")
    return normalized


def _optional_http_url(value: Any, label: str) -> str:
    normalized = str(value or "").strip()
    return _http_url(normalized, label) if normalized else ""


def _validate_tokens(value: str, step_name: str) -> None:
    remaining = _TOKEN.sub("", value)
    if "{{" in remaining or "}}" in remaining:
        raise WorkflowError(
            f"L’étape « {step_name} » contient un jeton inconnu. "
            "Utilisez {{data.x}}, {{fixture.x}} ou {{secret.x}}."
        )
