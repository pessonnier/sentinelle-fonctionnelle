"""Profils versionnés d'approche de test décrits en YAML.

Une approche de test indique comment les cas seront sélectionnés et conçus.
Le plan de test référence un profil et une version ; il ne duplique pas une
description libre susceptible d'être interprétée différemment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class TestApproachError(ValueError):
    """Signale un profil absent, dupliqué ou invalide."""


@dataclass(frozen=True, slots=True)
class TestApproachProfile:
    """Version immuable d'une approche de test administrable."""

    id: str
    version: int
    name: str
    description: str
    test_levels: tuple[str, ...]
    test_types: tuple[str, ...]
    test_design_techniques: tuple[str, ...]
    risk_based: bool
    automation_strategy: str
    evidence_requirements: tuple[str, ...]
    generation_instructions: tuple[str, ...]
    enabled: bool = True

    def __post_init__(self) -> None:
        normalized_id = self.id.strip()
        if not PROFILE_ID_PATTERN.fullmatch(normalized_id):
            raise TestApproachError(
                "L'identifiant doit utiliser des minuscules, des chiffres "
                "et des tirets simples."
            )
        if self.version < 1:
            raise TestApproachError("La version doit être supérieure ou égale à 1.")
        for value, label in (
            (self.name, "Le libellé"),
            (self.description, "La description"),
            (self.automation_strategy, "La stratégie d'automatisation"),
        ):
            if not value.strip():
                raise TestApproachError(f"{label} est obligatoire.")
        for values, label in (
            (self.test_levels, "Un niveau de test"),
            (self.test_types, "Un type de test"),
            (self.test_design_techniques, "Une technique de conception de tests"),
            (self.generation_instructions, "Une instruction de génération"),
        ):
            if not values or any(not value.strip() for value in values):
                raise TestApproachError(f"{label} est obligatoire.")


class TestApproachCatalog:
    """Catalogue YAML conservant toutes les versions référencées par les plans."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        path: Path,
        profiles: tuple[TestApproachProfile, ...],
    ) -> None:
        self.path = Path(path)
        self._profiles = profiles
        self._validate_catalog()

    @classmethod
    def open(
        cls,
        path: Path,
        *,
        defaults_path: Path | None = None,
    ) -> TestApproachCatalog:
        """Charge le catalogue et l'initialise depuis les profils fournis."""

        effective_path = Path(path)
        if not effective_path.exists():
            if defaults_path is None:
                raise TestApproachError(
                    f"Catalogue d'approches de test introuvable : {effective_path}"
                )
            effective_path.parent.mkdir(parents=True, exist_ok=True)
            effective_path.write_text(
                Path(defaults_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        try:
            document = yaml.safe_load(effective_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise TestApproachError(
                f"Le catalogue YAML est illisible : {error}"
            ) from error
        if not isinstance(document, dict):
            raise TestApproachError("Le catalogue YAML doit être un objet.")
        if document.get("schema_version") != cls.SCHEMA_VERSION:
            raise TestApproachError(
                "Version de schéma YAML d'approches de test non prise en charge."
            )
        approaches = document.get("approaches")
        if not isinstance(approaches, list) or not approaches:
            raise TestApproachError(
                "Le catalogue doit contenir au moins une approche de test."
            )
        profiles: list[TestApproachProfile] = []
        try:
            for approach in approaches:
                approach_id = str(approach["id"])
                versions = approach["versions"]
                if not isinstance(versions, list) or not versions:
                    raise TestApproachError(
                        f"L'approche {approach_id} ne contient aucune version."
                    )
                profiles.extend(
                    _profile_from_mapping(approach_id, version)
                    for version in versions
                )
        except (KeyError, TypeError, ValueError) as error:
            raise TestApproachError(
                f"Structure YAML d'approche de test invalide : {error}"
            ) from error
        return cls(effective_path, tuple(profiles))

    @property
    def profiles(self) -> tuple[TestApproachProfile, ...]:
        return self._profiles

    def current_profiles(
        self,
        *,
        include_disabled: bool = False,
    ) -> tuple[TestApproachProfile, ...]:
        """Retourne la dernière version de chaque profil, triée par libellé."""

        latest: dict[str, TestApproachProfile] = {}
        for profile in self._profiles:
            current = latest.get(profile.id)
            if current is None or profile.version > current.version:
                latest[profile.id] = profile
        return tuple(
            sorted(
                (
                    profile
                    for profile in latest.values()
                    if include_disabled or profile.enabled
                ),
                key=lambda profile: (profile.name.casefold(), profile.id),
            )
        )

    def get(
        self,
        profile_id: str,
        version: int | None = None,
    ) -> TestApproachProfile:
        matches = tuple(
            profile
            for profile in self._profiles
            if profile.id == profile_id
            and (version is None or profile.version == version)
        )
        if not matches:
            suffix = f" version {version}" if version is not None else ""
            raise TestApproachError(
                f"Approche de test inconnue : {profile_id}{suffix}."
            )
        return max(matches, key=lambda profile: profile.version)

    def create(
        self,
        *,
        profile_id: str,
        name: str,
        description: str,
        test_levels: tuple[str, ...],
        test_types: tuple[str, ...],
        test_design_techniques: tuple[str, ...],
        risk_based: bool,
        automation_strategy: str,
        evidence_requirements: tuple[str, ...],
        generation_instructions: tuple[str, ...],
        enabled: bool,
    ) -> TestApproachProfile:
        if any(profile.id == profile_id.strip() for profile in self._profiles):
            raise TestApproachError(
                f"L'identifiant {profile_id.strip()} existe déjà."
            )
        profile = _new_profile(
            profile_id=profile_id,
            version=1,
            name=name,
            description=description,
            test_levels=test_levels,
            test_types=test_types,
            test_design_techniques=test_design_techniques,
            risk_based=risk_based,
            automation_strategy=automation_strategy,
            evidence_requirements=evidence_requirements,
            generation_instructions=generation_instructions,
            enabled=enabled,
        )
        self._profiles = (*self._profiles, profile)
        self.save()
        return profile

    def update(
        self,
        profile_id: str,
        *,
        name: str,
        description: str,
        test_levels: tuple[str, ...],
        test_types: tuple[str, ...],
        test_design_techniques: tuple[str, ...],
        risk_based: bool,
        automation_strategy: str,
        evidence_requirements: tuple[str, ...],
        generation_instructions: tuple[str, ...],
        enabled: bool,
    ) -> TestApproachProfile:
        current = self.get(profile_id)
        profile = _new_profile(
            profile_id=current.id,
            version=current.version + 1,
            name=name,
            description=description,
            test_levels=test_levels,
            test_types=test_types,
            test_design_techniques=test_design_techniques,
            risk_based=risk_based,
            automation_strategy=automation_strategy,
            evidence_requirements=evidence_requirements,
            generation_instructions=generation_instructions,
            enabled=enabled,
        )
        self._profiles = (*self._profiles, profile)
        self.save()
        return profile

    def save(self) -> None:
        """Écrit atomiquement le catalogue sans supprimer les anciennes versions."""

        by_id: dict[str, list[TestApproachProfile]] = {}
        for profile in self._profiles:
            by_id.setdefault(profile.id, []).append(profile)
        document = {
            "schema_version": self.SCHEMA_VERSION,
            "approaches": [
                {
                    "id": profile_id,
                    "versions": [
                        _profile_to_mapping(profile)
                        for profile in sorted(
                            versions,
                            key=lambda item: item.version,
                        )
                    ],
                }
                for profile_id, versions in sorted(by_id.items())
            ],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            yaml.safe_dump(
                document,
                allow_unicode=True,
                sort_keys=False,
                width=100,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(self.path)

    def _validate_catalog(self) -> None:
        seen: set[tuple[str, int]] = set()
        for profile in self._profiles:
            key = (profile.id, profile.version)
            if key in seen:
                raise TestApproachError(
                    f"Version dupliquée dans le catalogue : {profile.id} "
                    f"version {profile.version}."
                )
            seen.add(key)


def _new_profile(
    *,
    profile_id: str,
    version: int,
    name: str,
    description: str,
    test_levels: tuple[str, ...],
    test_types: tuple[str, ...],
    test_design_techniques: tuple[str, ...],
    risk_based: bool,
    automation_strategy: str,
    evidence_requirements: tuple[str, ...],
    generation_instructions: tuple[str, ...],
    enabled: bool,
) -> TestApproachProfile:
    return TestApproachProfile(
        id=profile_id.strip(),
        version=version,
        name=name.strip(),
        description=description.strip(),
        test_levels=_normalized_values(test_levels),
        test_types=_normalized_values(test_types),
        test_design_techniques=_normalized_values(test_design_techniques),
        risk_based=bool(risk_based),
        automation_strategy=automation_strategy.strip(),
        evidence_requirements=_normalized_values(evidence_requirements),
        generation_instructions=_normalized_values(generation_instructions),
        enabled=bool(enabled),
    )


def _profile_from_mapping(
    profile_id: str,
    value: object,
) -> TestApproachProfile:
    if not isinstance(value, dict):
        raise TestApproachError(
            f"Une version de l'approche {profile_id} doit être un objet."
        )
    return _new_profile(
        profile_id=profile_id,
        version=int(value["version"]),
        name=str(value["name"]),
        description=str(value["description"]),
        test_levels=_mapping_values(value, "test_levels"),
        test_types=_mapping_values(value, "test_types"),
        test_design_techniques=_mapping_values(
            value,
            "test_design_techniques",
        ),
        risk_based=_mapping_bool(value, "risk_based", default=False),
        automation_strategy=str(value["automation_strategy"]),
        evidence_requirements=_mapping_values(
            value,
            "evidence_requirements",
            required=False,
        ),
        generation_instructions=_mapping_values(
            value,
            "generation_instructions",
        ),
        enabled=_mapping_bool(value, "enabled", default=True),
    )


def _mapping_values(
    mapping: dict[object, object],
    key: str,
    *,
    required: bool = True,
) -> tuple[str, ...]:
    value = mapping.get(key, [])
    if not isinstance(value, list):
        raise TestApproachError(f"Le champ {key} doit être une liste YAML.")
    result = tuple(str(item).strip() for item in value)
    if required and not result:
        raise TestApproachError(f"Le champ {key} ne peut pas être vide.")
    return result


def _mapping_bool(
    mapping: dict[object, object],
    key: str,
    *,
    default: bool,
) -> bool:
    value = mapping.get(key, default)
    if not isinstance(value, bool):
        raise TestApproachError(
            f"Le champ {key} doit être un booléen YAML."
        )
    return value


def _normalized_values(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(value.strip() for value in values if value.strip())


def _profile_to_mapping(profile: TestApproachProfile) -> dict[str, object]:
    return {
        "version": profile.version,
        "name": profile.name,
        "description": profile.description,
        "test_levels": list(profile.test_levels),
        "test_types": list(profile.test_types),
        "test_design_techniques": list(profile.test_design_techniques),
        "risk_based": profile.risk_based,
        "automation_strategy": profile.automation_strategy,
        "evidence_requirements": list(profile.evidence_requirements),
        "generation_instructions": list(profile.generation_instructions),
        "enabled": profile.enabled,
    }
