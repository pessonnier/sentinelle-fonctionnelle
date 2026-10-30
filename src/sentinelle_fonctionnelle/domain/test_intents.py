"""Catalogue versionné des intentions fonctionnelles de test.

Références : EF-017 et ACC-032.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

import yaml


_IDENTIFIER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_REFERENCE = re.compile(
    r"(?P<identifier>[a-z0-9]+(?:-[a-z0-9]+)*)@(?P<version>[1-9][0-9]*)\Z"
)


class FunctionalIntentError(ValueError):
    """Signale un catalogue ou une intention fonctionnelle invalide."""


@dataclass(frozen=True, slots=True)
class IntentRequirement:
    """Information attendue et question métier utilisée pour l'obtenir."""

    key: str
    label: str
    question: str
    utility: str
    target: str

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.key):
            raise FunctionalIntentError(
                "La clé d’une information attendue doit utiliser des minuscules "
                "et des tirets."
            )
        for value, label in (
            (self.label, "Le libellé"),
            (self.question, "La question"),
            (self.utility, "L’utilité"),
            (self.target, "La cible de formulaire"),
        ):
            if not value.strip():
                raise FunctionalIntentError(f"{label} est obligatoire.")

    def as_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "question": self.question,
            "utility": self.utility,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class FunctionalIntent:
    """Version immuable d'une phrase d'intention administrable."""

    id: str
    version: int
    label: str
    category: str
    description: str
    examples: tuple[str, ...]
    suggested_test_types: tuple[str, ...]
    required_information: tuple[IntentRequirement, ...]
    enabled: bool = True

    def __post_init__(self) -> None:
        if not _IDENTIFIER.fullmatch(self.id):
            raise FunctionalIntentError(
                "L’identifiant d’intention doit utiliser des minuscules, "
                "des chiffres et des tirets."
            )
        if self.version < 1:
            raise FunctionalIntentError(
                "La version d’intention doit être supérieure ou égale à 1."
            )
        for value, label in (
            (self.label, "Le libellé"),
            (self.category, "La catégorie"),
            (self.description, "La description"),
        ):
            if not value.strip():
                raise FunctionalIntentError(f"{label} est obligatoire.")
        if not self.examples or any(not value.strip() for value in self.examples):
            raise FunctionalIntentError(
                "Une intention doit contenir au moins un exemple."
            )
        if (
            not self.suggested_test_types
            or any(not value.strip() for value in self.suggested_test_types)
        ):
            raise FunctionalIntentError(
                "Une intention doit conseiller au moins un type de test."
            )
        if not self.required_information:
            raise FunctionalIntentError(
                "Une intention doit déclarer les informations nécessaires."
            )
        keys = tuple(item.key for item in self.required_information)
        if len(keys) != len(set(keys)):
            raise FunctionalIntentError(
                f"L’intention {self.id} contient une information attendue dupliquée."
            )

    @property
    def reference(self) -> str:
        return f"{self.id}@{self.version}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "reference": self.reference,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "examples": list(self.examples),
            "suggested_test_types": list(self.suggested_test_types),
            "required_information": [
                item.as_dict() for item in self.required_information
            ],
            "enabled": self.enabled,
        }


class FunctionalIntentCatalog:
    """Catalogue YAML chargé sans dépendre de l'interface web."""

    SCHEMA_VERSION = 1

    def __init__(self, path: Path, intents: tuple[FunctionalIntent, ...]) -> None:
        self.path = Path(path)
        self._intents = intents
        seen: set[tuple[str, int]] = set()
        for intent in intents:
            key = (intent.id, intent.version)
            if key in seen:
                raise FunctionalIntentError(
                    f"Version d’intention dupliquée : {intent.reference}."
                )
            seen.add(key)

    @classmethod
    def open(
        cls,
        path: Path,
        *,
        defaults_path: Path | None = None,
    ) -> FunctionalIntentCatalog:
        effective_path = Path(path)
        if not effective_path.exists():
            if defaults_path is None:
                raise FunctionalIntentError(
                    f"Catalogue d’intentions introuvable : {effective_path}"
                )
            effective_path.parent.mkdir(parents=True, exist_ok=True)
            effective_path.write_text(
                Path(defaults_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        try:
            document = yaml.safe_load(effective_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise FunctionalIntentError(
                f"Le catalogue d’intentions YAML est illisible : {error}"
            ) from error
        if not isinstance(document, Mapping):
            raise FunctionalIntentError(
                "Le catalogue d’intentions YAML doit être un objet."
            )
        if document.get("schema_version") != cls.SCHEMA_VERSION:
            raise FunctionalIntentError(
                "Version de schéma du catalogue d’intentions non prise en charge."
            )
        raw_intents = document.get("intents")
        if not isinstance(raw_intents, list) or not raw_intents:
            raise FunctionalIntentError(
                "Le catalogue doit contenir au moins une intention."
            )
        try:
            intents = tuple(
                _intent_from_mapping(raw_intent) for raw_intent in raw_intents
            )
        except (KeyError, TypeError, ValueError) as error:
            raise FunctionalIntentError(
                f"Structure YAML d’intention invalide : {error}"
            ) from error
        return cls(effective_path, intents)

    @property
    def intents(self) -> tuple[FunctionalIntent, ...]:
        return self._intents

    def current_intents(
        self,
        *,
        include_disabled: bool = False,
    ) -> tuple[FunctionalIntent, ...]:
        latest: dict[str, FunctionalIntent] = {}
        for intent in self._intents:
            current = latest.get(intent.id)
            if current is None or intent.version > current.version:
                latest[intent.id] = intent
        return tuple(
            sorted(
                (
                    intent
                    for intent in latest.values()
                    if include_disabled or intent.enabled
                ),
                key=lambda item: (item.category.casefold(), item.label.casefold()),
            )
        )

    def get(self, intent_id: str, version: int | None = None) -> FunctionalIntent:
        matches = tuple(
            intent
            for intent in self._intents
            if intent.id == intent_id
            and (version is None or intent.version == version)
        )
        if not matches:
            suffix = f" version {version}" if version is not None else ""
            raise FunctionalIntentError(
                f"Intention fonctionnelle inconnue : {intent_id}{suffix}."
            )
        return max(matches, key=lambda item: item.version)

    def get_reference(self, reference: str) -> FunctionalIntent:
        intent_id, version = parse_intent_reference(reference)
        return self.get(intent_id, version)


def parse_intent_reference(reference: str) -> tuple[str, int]:
    match = _REFERENCE.fullmatch(reference.strip())
    if match is None:
        raise FunctionalIntentError(
            "La référence d’intention doit suivre la syntaxe identifiant@version."
        )
    return match.group("identifier"), int(match.group("version"))


def _intent_from_mapping(value: object) -> FunctionalIntent:
    if not isinstance(value, Mapping):
        raise FunctionalIntentError("Une intention YAML doit être un objet.")
    requirements = value["required_information"]
    if not isinstance(requirements, list):
        raise FunctionalIntentError(
            "Le champ required_information doit être une liste YAML."
        )
    return FunctionalIntent(
        id=str(value["id"]).strip(),
        version=int(value["version"]),
        label=str(value["label"]).strip(),
        category=str(value["category"]).strip(),
        description=str(value["description"]).strip(),
        examples=_strings(value.get("examples")),
        suggested_test_types=_strings(value.get("suggested_test_types")),
        required_information=tuple(
            _requirement_from_mapping(item) for item in requirements
        ),
        enabled=_boolean(value.get("enabled", True), "enabled"),
    )


def _requirement_from_mapping(value: object) -> IntentRequirement:
    if not isinstance(value, Mapping):
        raise FunctionalIntentError(
            "Une information attendue doit être un objet YAML."
        )
    return IntentRequirement(
        key=str(value["key"]).strip(),
        label=str(value["label"]).strip(),
        question=str(value["question"]).strip(),
        utility=str(value["utility"]).strip(),
        target=str(value["target"]).strip(),
    )


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise FunctionalIntentError("Une liste YAML attendue est absente.")
    return tuple(str(item).strip() for item in value)


def _boolean(value: object, key: str) -> bool:
    if not isinstance(value, bool):
        raise FunctionalIntentError(f"Le champ {key} doit être un booléen YAML.")
    return value
