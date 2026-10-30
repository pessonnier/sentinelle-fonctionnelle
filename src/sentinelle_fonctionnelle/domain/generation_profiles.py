"""Profils versionnés d’accès LLM et de génération de code.

Les valeurs secrètes ne font jamais partie de ce modèle. Un profil d’accès
référence uniquement le nom de la variable d’environnement résolue au moment
de l’appel au fournisseur.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlparse

import yaml


PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROFILE_REFERENCE_PATTERN = re.compile(
    r"^(?P<profile_id>[a-z0-9]+(?:-[a-z0-9]+)*)@(?P<version>[1-9][0-9]*)$"
)
ENVIRONMENT_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
SUPPORTED_PROVIDERS = (
    "openai",
    "azure-openai",
    "anthropic",
    "mistral",
    "ollama",
    "openai-compatible",
)
SUPPORTED_LANGUAGES = ("python", "typescript")
SUPPORTED_FRAMEWORKS = {
    "python": ("pytest-playwright",),
    "typescript": ("playwright-test",),
}
SUPPORTED_EVIDENCE_MODES = ("none", "on-failure", "each-step")
SUPPORTED_OVERWRITE_POLICIES = ("proposal-only", "refuse-existing")
SUPPORTED_VALIDATION_STEPS = (
    "syntax",
    "format",
    "lint",
    "type-check",
    "targeted-test",
)
SUPPORTED_GENERATION_SKILLS = (
    "functional-test-generation@1",
    "generate-python-playwright-code@1",
)
DEFAULT_GENERATION_SKILLS = SUPPORTED_GENERATION_SKILLS


class GenerationProfileError(ValueError):
    """Signale un profil absent, dupliqué ou invalide."""


@dataclass(frozen=True, slots=True)
class LLMAccessProfile:
    """Accès à un modèle sans valeur d’authentification persistée."""

    id: str
    version: int
    name: str
    provider: str
    base_url: str
    model: str
    api_key_environment: str
    organization_environment: str
    request_timeout_seconds: int
    max_retries: int
    enabled: bool = True

    def __post_init__(self) -> None:
        _validate_identity(self.id, self.version, self.name)
        if self.provider not in SUPPORTED_PROVIDERS:
            raise GenerationProfileError(
                f"Fournisseur LLM non pris en charge : {self.provider}."
            )
        if not self.model.strip():
            raise GenerationProfileError("Le modèle LLM est obligatoire.")
        _validate_endpoint(self.base_url, self.provider)
        if self.provider != "ollama" and not self.api_key_environment:
            raise GenerationProfileError(
                "Une variable d’environnement de clé API est obligatoire."
            )
        for value, label in (
            (self.api_key_environment, "La variable de clé API"),
            (self.organization_environment, "La variable d’organisation"),
        ):
            if value and not ENVIRONMENT_NAME_PATTERN.fullmatch(value):
                raise GenerationProfileError(
                    f"{label} doit être un nom de variable d’environnement."
                )
        if not 1 <= self.request_timeout_seconds <= 600:
            raise GenerationProfileError(
                "Le délai LLM doit être compris entre 1 et 600 secondes."
            )
        if not 0 <= self.max_retries <= 10:
            raise GenerationProfileError(
                "Le nombre de nouvelles tentatives doit être compris entre 0 et 10."
            )

    @property
    def reference(self) -> str:
        return f"{self.id}@{self.version}"


@dataclass(frozen=True, slots=True)
class CodeGenerationProfile:
    """Contraintes déterministes appliquées après la finalisation LLM."""

    id: str
    version: int
    name: str
    llm_profile: str
    language: str
    framework: str
    output_root: str
    test_file_pattern: str
    page_object_pattern: str
    use_page_objects: bool
    include_comments: bool
    evidence_mode: str
    overwrite_policy: str
    validation_steps: tuple[str, ...]
    generation_instructions: tuple[str, ...]
    max_generated_files: int
    enabled: bool = True
    generation_skills: tuple[str, ...] = DEFAULT_GENERATION_SKILLS

    def __post_init__(self) -> None:
        _validate_identity(self.id, self.version, self.name)
        parse_profile_reference(self.llm_profile)
        if self.language not in SUPPORTED_LANGUAGES:
            raise GenerationProfileError(
                f"Langage de génération non pris en charge : {self.language}."
            )
        if self.framework not in SUPPORTED_FRAMEWORKS[self.language]:
            raise GenerationProfileError(
                f"Le framework {self.framework} ne correspond pas au langage "
                f"{self.language}."
            )
        _validate_relative_directory(self.output_root)
        _validate_file_pattern(
            self.test_file_pattern,
            required_token="{case_slug}",
            label="Le motif de fichier de test",
        )
        _validate_file_pattern(
            self.page_object_pattern,
            required_token="{page_slug}",
            label="Le motif de page object",
        )
        if self.evidence_mode not in SUPPORTED_EVIDENCE_MODES:
            raise GenerationProfileError(
                f"Politique de preuve inconnue : {self.evidence_mode}."
            )
        if self.overwrite_policy not in SUPPORTED_OVERWRITE_POLICIES:
            raise GenerationProfileError(
                f"Politique d’écrasement inconnue : {self.overwrite_policy}."
            )
        if not self.validation_steps:
            raise GenerationProfileError(
                "Au moins une étape de validation du code est obligatoire."
            )
        unknown_steps = set(self.validation_steps) - set(SUPPORTED_VALIDATION_STEPS)
        if unknown_steps:
            raise GenerationProfileError(
                "Étape de validation inconnue : "
                + ", ".join(sorted(unknown_steps))
                + "."
            )
        if not self.generation_instructions or any(
            not value.strip() for value in self.generation_instructions
        ):
            raise GenerationProfileError(
                "Au moins une instruction de génération est obligatoire."
            )
        if not self.generation_skills:
            raise GenerationProfileError(
                "Au moins un skill de génération est obligatoire."
            )
        unknown_skills = set(self.generation_skills) - set(
            SUPPORTED_GENERATION_SKILLS
        )
        if unknown_skills:
            raise GenerationProfileError(
                "Skill de génération inconnu : "
                + ", ".join(sorted(unknown_skills))
                + "."
            )
        if len(set(self.generation_skills)) != len(self.generation_skills):
            raise GenerationProfileError(
                "Un skill de génération ne peut pas être déclaré deux fois."
            )
        if not 1 <= self.max_generated_files <= 100:
            raise GenerationProfileError(
                "Le nombre maximal de fichiers doit être compris entre 1 et 100."
            )

    @property
    def reference(self) -> str:
        return f"{self.id}@{self.version}"


class GenerationProfileCatalog:
    """Catalogue YAML traçable des accès LLM et règles de génération."""

    SCHEMA_VERSION = 1

    def __init__(
        self,
        path: Path,
        llm_access_profiles: tuple[LLMAccessProfile, ...],
        code_generation_profiles: tuple[CodeGenerationProfile, ...],
    ) -> None:
        self.path = Path(path)
        self._llm_access_profiles = llm_access_profiles
        self._code_generation_profiles = code_generation_profiles
        self._validate_catalog()

    @classmethod
    def open(
        cls,
        path: Path,
        *,
        defaults_path: Path | None = None,
    ) -> GenerationProfileCatalog:
        effective_path = Path(path)
        if not effective_path.exists():
            if defaults_path is None:
                raise GenerationProfileError(
                    f"Catalogue de génération introuvable : {effective_path}"
                )
            effective_path.parent.mkdir(parents=True, exist_ok=True)
            effective_path.write_text(
                Path(defaults_path).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        try:
            document = yaml.safe_load(effective_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise GenerationProfileError(
                f"Le catalogue de génération est illisible : {error}"
            ) from error
        if not isinstance(document, dict):
            raise GenerationProfileError(
                "Le catalogue de génération YAML doit être un objet."
            )
        if document.get("schema_version") != cls.SCHEMA_VERSION:
            raise GenerationProfileError(
                "Version de schéma du catalogue de génération non prise en charge."
            )
        try:
            access_profiles = _load_versioned_profiles(
                document.get("llm_access_profiles", []),
                _llm_access_from_mapping,
                "LLM",
            )
            generation_profiles = _load_versioned_profiles(
                document.get("code_generation_profiles", []),
                _code_generation_from_mapping,
                "de génération",
            )
        except (KeyError, TypeError, ValueError) as error:
            raise GenerationProfileError(
                f"Structure YAML de génération invalide : {error}"
            ) from error
        return cls(
            effective_path,
            tuple(access_profiles),
            tuple(generation_profiles),
        )

    @property
    def llm_access_profiles(self) -> tuple[LLMAccessProfile, ...]:
        return self._llm_access_profiles

    @property
    def code_generation_profiles(self) -> tuple[CodeGenerationProfile, ...]:
        return self._code_generation_profiles

    def current_llm_access(
        self,
        *,
        include_disabled: bool = False,
    ) -> tuple[LLMAccessProfile, ...]:
        return _current_profiles(
            self._llm_access_profiles,
            include_disabled=include_disabled,
        )

    def current_code_generation(
        self,
        *,
        include_disabled: bool = False,
    ) -> tuple[CodeGenerationProfile, ...]:
        return _current_profiles(
            self._code_generation_profiles,
            include_disabled=include_disabled,
        )

    def get_llm_access(
        self,
        profile_id: str,
        version: int | None = None,
    ) -> LLMAccessProfile:
        return _get_profile(
            self._llm_access_profiles,
            profile_id,
            version,
            "Profil d’accès LLM",
        )

    def get_code_generation(
        self,
        profile_id: str,
        version: int | None = None,
    ) -> CodeGenerationProfile:
        return _get_profile(
            self._code_generation_profiles,
            profile_id,
            version,
            "Profil de génération",
        )

    def create_llm_access(self, **values: object) -> LLMAccessProfile:
        profile_id = str(values["profile_id"]).strip()
        if any(profile.id == profile_id for profile in self._llm_access_profiles):
            raise GenerationProfileError(
                f"L’identifiant {profile_id} existe déjà."
            )
        profile = _new_llm_access(version=1, **values)
        self._llm_access_profiles = (*self._llm_access_profiles, profile)
        self.save()
        return profile

    def update_llm_access(
        self,
        profile_id: str,
        **values: object,
    ) -> LLMAccessProfile:
        current = self.get_llm_access(profile_id)
        profile = _new_llm_access(
            profile_id=current.id,
            version=current.version + 1,
            **values,
        )
        self._llm_access_profiles = (*self._llm_access_profiles, profile)
        self.save()
        return profile

    def create_code_generation(
        self,
        **values: object,
    ) -> CodeGenerationProfile:
        profile_id = str(values["profile_id"]).strip()
        if any(
            profile.id == profile_id
            for profile in self._code_generation_profiles
        ):
            raise GenerationProfileError(
                f"L’identifiant {profile_id} existe déjà."
            )
        profile = _new_code_generation(version=1, **values)
        self._validate_llm_reference(profile.llm_profile)
        self._code_generation_profiles = (
            *self._code_generation_profiles,
            profile,
        )
        self.save()
        return profile

    def update_code_generation(
        self,
        profile_id: str,
        **values: object,
    ) -> CodeGenerationProfile:
        current = self.get_code_generation(profile_id)
        profile = _new_code_generation(
            profile_id=current.id,
            version=current.version + 1,
            **values,
        )
        self._validate_llm_reference(profile.llm_profile)
        self._code_generation_profiles = (
            *self._code_generation_profiles,
            profile,
        )
        self.save()
        return profile

    def save(self) -> None:
        document = {
            "schema_version": self.SCHEMA_VERSION,
            "llm_access_profiles": _versioned_document(
                self._llm_access_profiles,
                _llm_access_to_mapping,
            ),
            "code_generation_profiles": _versioned_document(
                self._code_generation_profiles,
                _code_generation_to_mapping,
            ),
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
        for profiles, label in (
            (self._llm_access_profiles, "LLM"),
            (self._code_generation_profiles, "de génération"),
        ):
            seen: set[tuple[str, int]] = set()
            for profile in profiles:
                key = (profile.id, profile.version)
                if key in seen:
                    raise GenerationProfileError(
                        f"Version dupliquée du profil {label} : "
                        f"{profile.reference}."
                    )
                seen.add(key)
        for profile in self._code_generation_profiles:
            self._validate_llm_reference(profile.llm_profile)

    def _validate_llm_reference(self, reference: str) -> None:
        profile_id, version = parse_profile_reference(reference)
        self.get_llm_access(profile_id, version)


def parse_profile_reference(reference: str) -> tuple[str, int]:
    match = PROFILE_REFERENCE_PATTERN.fullmatch(reference.strip())
    if match is None:
        raise GenerationProfileError(
            "Une référence de profil doit suivre la syntaxe identifiant@version."
        )
    return match.group("profile_id"), int(match.group("version"))


def _validate_identity(profile_id: str, version: int, name: str) -> None:
    if not PROFILE_ID_PATTERN.fullmatch(profile_id.strip()):
        raise GenerationProfileError(
            "L’identifiant doit utiliser des minuscules, chiffres et tirets simples."
        )
    if version < 1:
        raise GenerationProfileError(
            "La version doit être supérieure ou égale à 1."
        )
    if not name.strip():
        raise GenerationProfileError("Le libellé du profil est obligatoire.")


def _validate_endpoint(value: str, provider: str) -> None:
    if not value:
        if provider in {"openai", "anthropic", "mistral"}:
            return
        raise GenerationProfileError(
            "L’URL de base est obligatoire pour ce fournisseur."
        )
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise GenerationProfileError(
            "L’URL LLM doit être une origine HTTP(S) sans identifiants, "
            "paramètres ni fragment."
        )
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not loopback:
        raise GenerationProfileError(
            "Une URL LLM distante doit utiliser HTTPS."
        )


def _validate_relative_directory(value: str) -> None:
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or ":" in normalized
    ):
        raise GenerationProfileError(
            "Le répertoire de sortie doit être un chemin relatif sûr."
        )


def _validate_file_pattern(
    value: str,
    *,
    required_token: str,
    label: str,
) -> None:
    if (
        required_token not in value
        or "/" in value
        or "\\" in value
        or ".." in value
        or not value.endswith((".py", ".ts"))
    ):
        raise GenerationProfileError(
            f"{label} doit contenir {required_token}, rester un nom de fichier "
            "et utiliser l’extension .py ou .ts."
        )


def _new_llm_access(
    *,
    profile_id: object,
    version: int,
    name: object,
    provider: object,
    base_url: object,
    model: object,
    api_key_environment: object,
    organization_environment: object,
    request_timeout_seconds: object,
    max_retries: object,
    enabled: object,
) -> LLMAccessProfile:
    return LLMAccessProfile(
        id=str(profile_id).strip(),
        version=int(version),
        name=str(name).strip(),
        provider=str(provider).strip(),
        base_url=str(base_url).strip().rstrip("/"),
        model=str(model).strip(),
        api_key_environment=str(api_key_environment).strip(),
        organization_environment=str(organization_environment).strip(),
        request_timeout_seconds=int(request_timeout_seconds),
        max_retries=int(max_retries),
        enabled=_boolean(enabled, "enabled"),
    )


def _new_code_generation(
    *,
    profile_id: object,
    version: int,
    name: object,
    llm_profile: object,
    language: object,
    framework: object,
    output_root: object,
    test_file_pattern: object,
    page_object_pattern: object,
    use_page_objects: object,
    include_comments: object,
    evidence_mode: object,
    overwrite_policy: object,
    validation_steps: object,
    generation_instructions: object,
    max_generated_files: object,
    enabled: object,
    generation_skills: object = DEFAULT_GENERATION_SKILLS,
) -> CodeGenerationProfile:
    return CodeGenerationProfile(
        id=str(profile_id).strip(),
        version=int(version),
        name=str(name).strip(),
        llm_profile=str(llm_profile).strip(),
        language=str(language).strip(),
        framework=str(framework).strip(),
        output_root=str(output_root).strip().replace("\\", "/"),
        test_file_pattern=str(test_file_pattern).strip(),
        page_object_pattern=str(page_object_pattern).strip(),
        use_page_objects=_boolean(use_page_objects, "use_page_objects"),
        include_comments=_boolean(include_comments, "include_comments"),
        evidence_mode=str(evidence_mode).strip(),
        overwrite_policy=str(overwrite_policy).strip(),
        validation_steps=_normalized_values(validation_steps),
        generation_instructions=_normalized_values(generation_instructions),
        max_generated_files=int(max_generated_files),
        enabled=_boolean(enabled, "enabled"),
        generation_skills=_normalized_values(generation_skills),
    )


def _llm_access_from_mapping(
    profile_id: str,
    value: dict[object, object],
) -> LLMAccessProfile:
    return _new_llm_access(
        profile_id=profile_id,
        version=value["version"],
        name=value["name"],
        provider=value["provider"],
        base_url=value.get("base_url", ""),
        model=value["model"],
        api_key_environment=value.get("api_key_environment", ""),
        organization_environment=value.get("organization_environment", ""),
        request_timeout_seconds=value.get("request_timeout_seconds", 60),
        max_retries=value.get("max_retries", 2),
        enabled=value.get("enabled", True),
    )


def _code_generation_from_mapping(
    profile_id: str,
    value: dict[object, object],
) -> CodeGenerationProfile:
    return _new_code_generation(
        profile_id=profile_id,
        version=value["version"],
        name=value["name"],
        llm_profile=value["llm_profile"],
        language=value["language"],
        framework=value["framework"],
        output_root=value["output_root"],
        test_file_pattern=value["test_file_pattern"],
        page_object_pattern=value["page_object_pattern"],
        use_page_objects=value.get("use_page_objects", True),
        include_comments=value.get("include_comments", False),
        evidence_mode=value.get("evidence_mode", "on-failure"),
        overwrite_policy=value.get("overwrite_policy", "proposal-only"),
        validation_steps=value["validation_steps"],
        generation_instructions=value["generation_instructions"],
        max_generated_files=value.get("max_generated_files", 20),
        enabled=value.get("enabled", True),
        generation_skills=value.get(
            "generation_skills",
            DEFAULT_GENERATION_SKILLS,
        ),
    )


def _llm_access_to_mapping(profile: LLMAccessProfile) -> dict[str, object]:
    return {
        "version": profile.version,
        "name": profile.name,
        "provider": profile.provider,
        "base_url": profile.base_url,
        "model": profile.model,
        "api_key_environment": profile.api_key_environment,
        "organization_environment": profile.organization_environment,
        "request_timeout_seconds": profile.request_timeout_seconds,
        "max_retries": profile.max_retries,
        "enabled": profile.enabled,
    }


def _code_generation_to_mapping(
    profile: CodeGenerationProfile,
) -> dict[str, object]:
    return {
        "version": profile.version,
        "name": profile.name,
        "llm_profile": profile.llm_profile,
        "language": profile.language,
        "framework": profile.framework,
        "output_root": profile.output_root,
        "test_file_pattern": profile.test_file_pattern,
        "page_object_pattern": profile.page_object_pattern,
        "use_page_objects": profile.use_page_objects,
        "include_comments": profile.include_comments,
        "evidence_mode": profile.evidence_mode,
        "overwrite_policy": profile.overwrite_policy,
        "validation_steps": list(profile.validation_steps),
        "generation_instructions": list(profile.generation_instructions),
        "generation_skills": list(profile.generation_skills),
        "max_generated_files": profile.max_generated_files,
        "enabled": profile.enabled,
    }


def _load_versioned_profiles(
    values: object,
    factory: object,
    label: str,
) -> list[object]:
    if not isinstance(values, list):
        raise GenerationProfileError(
            f"La liste des profils {label} doit être un tableau YAML."
        )
    profiles: list[object] = []
    for family in values:
        if not isinstance(family, dict):
            raise GenerationProfileError(
                f"Un profil {label} doit être un objet YAML."
            )
        profile_id = str(family["id"])
        versions = family["versions"]
        if not isinstance(versions, list) or not versions:
            raise GenerationProfileError(
                f"Le profil {profile_id} ne contient aucune version."
            )
        for version in versions:
            if not isinstance(version, dict):
                raise GenerationProfileError(
                    f"Une version du profil {profile_id} doit être un objet."
                )
            profiles.append(factory(profile_id, version))
    return profiles


def _versioned_document(
    profiles: tuple[object, ...],
    serializer: object,
) -> list[dict[str, object]]:
    by_id: dict[str, list[object]] = {}
    for profile in profiles:
        by_id.setdefault(profile.id, []).append(profile)
    return [
        {
            "id": profile_id,
            "versions": [
                serializer(profile)
                for profile in sorted(
                    versions,
                    key=lambda item: item.version,
                )
            ],
        }
        for profile_id, versions in sorted(by_id.items())
    ]


def _normalized_values(values: object) -> tuple[str, ...]:
    if isinstance(values, str):
        return tuple(
            line.strip() for line in values.splitlines() if line.strip()
        )
    if not isinstance(values, (list, tuple)):
        raise GenerationProfileError("Une liste de valeurs est attendue.")
    return tuple(str(value).strip() for value in values if str(value).strip())


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise GenerationProfileError(
            f"Le champ {label} doit être un booléen."
        )
    return value


def _current_profiles(
    profiles: tuple[object, ...],
    *,
    include_disabled: bool,
) -> tuple[object, ...]:
    latest: dict[str, object] = {}
    for profile in profiles:
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


def _get_profile(
    profiles: tuple[object, ...],
    profile_id: str,
    version: int | None,
    label: str,
) -> object:
    matches = tuple(
        profile
        for profile in profiles
        if profile.id == profile_id
        and (version is None or profile.version == version)
    )
    if not matches:
        suffix = f" version {version}" if version is not None else ""
        raise GenerationProfileError(
            f"{label} inconnu : {profile_id}{suffix}."
        )
    return max(matches, key=lambda profile: profile.version)
