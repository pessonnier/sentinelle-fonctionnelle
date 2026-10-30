"""Prompt traçable demandant la production d’un candidat de code de test."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re
from typing import Any, Mapping

from sentinelle_fonctionnelle.domain import (
    CodeGenerationProfile,
    LLMAccessProfile,
)


CODE_GENERATION_SKILLS: dict[str, dict[str, Any]] = {
    "functional-test-generation@1": {
        "name": "Génération fonctionnelle traçable",
        "source": ("skills/software-development/functional-test-generation/SKILL.md"),
        "instructions": (
            "Générer uniquement depuis une définition structurée confirmée.",
            "Conserver les actions, assertions et localisateurs acceptés.",
            "Produire un candidat contrôlable, jamais un artefact approuvé.",
        ),
    },
    "generate-python-playwright-code@1": {
        "name": "Générer un test Playwright Python",
        "source": "skills/generate-python-playwright-code/SKILL.md",
        "instructions": (
            "Utiliser pytest-playwright et les localisateurs HTML analysés.",
            "Émettre une assertion pour chaque contrôle observable confirmé.",
            "Répondre avec le contrat JSON de fichiers sans aucun secret.",
        ),
    },
}

_GENERATED_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


class CodeGenerationPromptError(ValueError):
    """Le workflow ou son profil ne permet pas de construire le prompt."""


@dataclass(frozen=True, slots=True)
class CodeGenerationPromptArtifact:
    document: dict[str, Any]
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {**self.document, "sha256": self.sha256}


@dataclass(frozen=True, slots=True)
class LLMGeneratedFile:
    path: str
    content: str
    sha256: str


@dataclass(frozen=True, slots=True)
class LLMCodeCandidate:
    files: tuple[LLMGeneratedFile, ...]
    assumptions: tuple[str, ...]
    warnings: tuple[str, ...]
    sha256: str

    @property
    def primary_file(self) -> LLMGeneratedFile:
        return self.files[0]


def validate_code_generation_response(
    response: Mapping[str, Any],
    *,
    prompt: CodeGenerationPromptArtifact,
    profile: CodeGenerationProfile,
) -> LLMCodeCandidate:
    """Ferme la réponse LLM avant qu'un octet soit proposé au téléchargement."""

    unexpected_keys = set(response) - {
        "schema_version",
        "files",
        "assumptions",
        "warnings",
    }
    if unexpected_keys:
        raise CodeGenerationPromptError(
            "La réponse LLM contient des propriétés hors contrat : "
            + ", ".join(sorted(str(key) for key in unexpected_keys))
            + "."
        )
    if response.get("schema_version") != 1:
        raise CodeGenerationPromptError(
            "La réponse LLM doit utiliser le schéma de génération version 1."
        )
    raw_files = response.get("files")
    if (
        not isinstance(raw_files, list)
        or not 1 <= len(raw_files) <= profile.max_generated_files
    ):
        raise CodeGenerationPromptError(
            "La réponse LLM contient un nombre de fichiers invalide."
        )
    effective_configuration = prompt.document["generation_input"][
        "effective_configuration"
    ]
    expected_path = str(effective_configuration["expected_test_path"])
    output_root = PurePosixPath(profile.output_root)
    expected_suffix = ".py" if profile.language == "python" else ".ts"
    files: list[LLMGeneratedFile] = []
    seen_paths: set[str] = set()
    total_size = 0
    for value in raw_files:
        if not isinstance(value, Mapping):
            raise CodeGenerationPromptError(
                "Chaque fichier généré doit être un objet JSON."
            )
        if set(value) != {"path", "content"}:
            raise CodeGenerationPromptError(
                "Un fichier généré contient des propriétés hors contrat."
            )
        raw_path = value.get("path")
        content = value.get("content")
        if not isinstance(raw_path, str) or not isinstance(content, str):
            raise CodeGenerationPromptError(
                "Chaque fichier généré doit posséder un chemin et un contenu texte."
            )
        normalized_path = raw_path.strip().replace("\\", "/")
        path = PurePosixPath(normalized_path)
        if (
            not normalized_path
            or len(normalized_path) > 240
            or not _GENERATED_PATH_PATTERN.fullmatch(normalized_path)
            or path.is_absolute()
            or ".." in path.parts
            or "." in path.parts
            or tuple(path.parts[: len(output_root.parts)]) != output_root.parts
            or path.suffix.casefold() != expected_suffix
        ):
            raise CodeGenerationPromptError(
                f"Le chemin généré {raw_path!r} sort de la racine autorisée."
            )
        if normalized_path in seen_paths:
            raise CodeGenerationPromptError(
                f"Le fichier {normalized_path} est présent plusieurs fois."
            )
        if not content.strip():
            raise CodeGenerationPromptError(f"Le fichier {normalized_path} est vide.")
        content_size = len(content.encode("utf-8"))
        total_size += content_size
        if content_size > 512 * 1024 or total_size > 1024 * 1024:
            raise CodeGenerationPromptError(
                "Le code généré dépasse la limite autorisée de 1 Mio."
            )
        if profile.language == "python":
            try:
                compile(content, normalized_path, "exec")
            except SyntaxError as error:
                raise CodeGenerationPromptError(
                    f"Le fichier {normalized_path} contient une erreur Python "
                    f"à la ligne {error.lineno}."
                ) from error
        seen_paths.add(normalized_path)
        files.append(
            LLMGeneratedFile(
                path=normalized_path,
                content=content,
                sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
            )
        )
    if expected_path not in seen_paths:
        raise CodeGenerationPromptError(
            f"Le fichier de test attendu {expected_path} est absent."
        )
    files.sort(key=lambda item: (item.path != expected_path, item.path))
    assumptions = _response_text_list(response.get("assumptions"), "assumptions")
    warnings = _response_text_list(response.get("warnings"), "warnings")
    canonical = json.dumps(
        {
            "prompt_sha256": prompt.sha256,
            "files": [{"path": item.path, "sha256": item.sha256} for item in files],
            "assumptions": assumptions,
            "warnings": warnings,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return LLMCodeCandidate(
        files=tuple(files),
        assumptions=assumptions,
        warnings=warnings,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def _response_text_list(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 100:
        raise CodeGenerationPromptError(
            f"Le champ {name} de la réponse LLM doit être une liste bornée."
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 2_000:
            raise CodeGenerationPromptError(
                f"Le champ {name} contient une valeur invalide."
            )
        result.append(item.strip())
    return tuple(result)


def build_code_generation_prompt(
    *,
    case_id: str,
    case_name: str,
    specification_version: int,
    objective: str,
    actor: str,
    summary: str,
    workflow: Mapping[str, Any],
    code_profile: CodeGenerationProfile,
    llm_profile: LLMAccessProfile,
) -> CodeGenerationPromptArtifact:
    """Produit les messages exacts à transmettre au LLM de génération."""

    if not bool(workflow.get("confirmed")):
        raise CodeGenerationPromptError(
            "Le workflow doit être confirmé avant de produire le prompt."
        )
    if code_profile.llm_profile != llm_profile.reference:
        raise CodeGenerationPromptError(
            "Le profil de génération ne référence pas l’accès LLM sélectionné."
        )
    skills = _resolve_skills(code_profile.generation_skills)
    sanitized_workflow = _sanitize_workflow(workflow)
    case_slug = f"case_{case_id.replace('-', '')}"
    output_path = (
        code_profile.output_root.rstrip("/")
        + "/"
        + code_profile.test_file_pattern.format(case_slug=case_slug)
    )
    generation_input = {
        "case": {
            "id": case_id,
            "name": case_name,
            "specification_version": specification_version,
            "objective": objective,
            "actor": actor,
            "summary": summary,
        },
        "workflow": sanitized_workflow,
        "effective_configuration": {
            "language": code_profile.language,
            "framework": code_profile.framework,
            "output_root": code_profile.output_root,
            "test_file_pattern": code_profile.test_file_pattern,
            "page_object_pattern": code_profile.page_object_pattern,
            "use_page_objects": code_profile.use_page_objects,
            "include_comments": code_profile.include_comments,
            "evidence_mode": code_profile.evidence_mode,
            "overwrite_policy": code_profile.overwrite_policy,
            "validation_steps": list(code_profile.validation_steps),
            "generation_instructions": list(code_profile.generation_instructions),
            "max_generated_files": code_profile.max_generated_files,
            "expected_test_path": output_path,
        },
        "output_contract": {
            "schema_version": 1,
            "files": [
                {
                    "path": output_path,
                    "content": "<code source complet>",
                }
            ],
            "assumptions": [],
            "warnings": [],
        },
    }
    system_prompt = _system_prompt(skills, code_profile)
    user_prompt = (
        "Génère le candidat à partir de cette entrée JSON. Respecte exactement "
        "le workflow confirmé et le contrat de sortie :\n"
        + json.dumps(
            generation_input,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    document: dict[str, Any] = {
        "schema_version": 1,
        "prompt_version": "code-generation-v1",
        "llm_access_profile": llm_profile.reference,
        "model": llm_profile.model,
        "code_generation_profile": code_profile.reference,
        "skills": skills,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "generation_input": generation_input,
    }
    canonical = json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return CodeGenerationPromptArtifact(
        document=document,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )


def generation_skill_documents(
    references: tuple[str, ...],
) -> tuple[dict[str, Any], ...]:
    return tuple(_resolve_skills(references))


def _resolve_skills(references: tuple[str, ...]) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for reference in references:
        try:
            definition = CODE_GENERATION_SKILLS[reference]
        except KeyError as error:
            raise CodeGenerationPromptError(
                f"Le skill de génération {reference} est introuvable."
            ) from error
        resolved.append(
            {
                "reference": reference,
                "name": definition["name"],
                "source": definition["source"],
                "instructions": list(definition["instructions"]),
            }
        )
    return resolved


def _system_prompt(
    skills: list[dict[str, Any]],
    profile: CodeGenerationProfile,
) -> str:
    skill_rules = "\n".join(
        f"- {skill['reference']} — {instruction}"
        for skill in skills
        for instruction in skill["instructions"]
    )
    profile_rules = "\n".join(
        f"- {instruction}" for instruction in profile.generation_instructions
    )
    return (
        "Génère le code d’un candidat de test fonctionnel, sans modifier ni "
        "compléter les faits confirmés. Réponds uniquement avec l’objet JSON "
        "demandé, sans Markdown. Ne produis aucun secret, aucune commande shell "
        "libre et aucune navigation hors des origines du workflow.\n\n"
        "Skills applicables :\n"
        + skill_rules
        + "\n\nInstructions du profil :\n"
        + profile_rules
    )


def _sanitize_workflow(workflow: Mapping[str, Any]) -> dict[str, Any]:
    sanitized = deepcopy(dict(workflow))
    password_references = {
        str(element.get("reference"))
        for page in sanitized.get("pages", [])
        if isinstance(page, Mapping)
        for element in page.get("elements", [])
        if isinstance(element, Mapping)
        and str(element.get("input_type", "")).casefold() == "password"
    }
    for step in sanitized.get("steps", []):
        if not isinstance(step, dict):
            continue
        if step.get("target") in password_references and step.get("value"):
            step["value"] = "<secret-value-redacted>"
        if step.get("assertion_target") in password_references and step.get("expected"):
            step["expected"] = "<secret-value-redacted>"
    return sanitized
