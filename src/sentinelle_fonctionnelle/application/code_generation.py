"""Première verticale déterministe de génération Python Playwright."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping

from sentinelle_fonctionnelle.domain import (
    GenerationWorkflowInput,
    PageElement,
    WorkflowAction,
    WorkflowAssertion,
    WorkflowError,
)


class CodeGenerationError(ValueError):
    """Le workflow ne peut pas être matérialisé en code sûr."""


@dataclass(frozen=True, slots=True)
class GeneratedCodeArtifact:
    case_slug: str
    test_name: str
    source: str
    source_sha256: str
    workflow_sha256: str
    data_case_count: int
    manifest: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class DataSourceDefinition:
    id: str
    path: str
    key_column: str


@dataclass(frozen=True, slots=True)
class DataCaseDefinition:
    id: str
    rows: tuple[tuple[str, str], ...]


_PYTHON_IDENTIFIER = re.compile(r"[a-z_][a-z0-9_]*\Z")
_DATA_IDENTIFIER = re.compile(r"[a-z][a-z0-9_-]*\Z")
GENERATOR_VERSION = "0.3.0"
CUSTOMIZATION_CONTRACT = "python-playwright-page-data-v1"


def generate_python_playwright(
    document: Mapping[str, Any],
    *,
    data_fingerprints: Mapping[str, str] | None = None,
) -> GeneratedCodeArtifact:
    """Transforme un workflow confirmé en test Playwright lisible."""

    workflow_value = document.get("workflow")
    if not isinstance(workflow_value, Mapping):
        raise CodeGenerationError("Le document doit contenir un workflow.")
    try:
        workflow = GenerationWorkflowInput.from_mapping(workflow_value)
    except WorkflowError as error:
        raise CodeGenerationError(str(error)) from error
    if not workflow.confirmed:
        raise CodeGenerationError("Le workflow doit être confirmé avant génération.")
    case_slug = str(document.get("case_slug") or "").strip()
    test_name = str(document.get("test_name") or "").strip()
    if not _PYTHON_IDENTIFIER.fullmatch(case_slug):
        raise CodeGenerationError(
            "Le slug du cas doit être un identifiant Python en minuscules."
        )
    if not _PYTHON_IDENTIFIER.fullmatch(test_name) or not test_name.startswith("test_"):
        raise CodeGenerationError(
            "Le nom du test doit être un identifiant Python préfixé par test_."
        )
    data_sources, data_cases, legacy_data_files = _data_configuration(document)
    elements = _element_catalog(workflow.pages)

    body: list[str] = []
    if workflow.precondition_dependencies:
        body.append("    # Traductions de préconditions confirmées")
        for dependency in workflow.precondition_dependencies:
            reference = (
                f" · référence {dependency.reference}" if dependency.reference else ""
            )
            description = " ".join(dependency.description.splitlines())
            body.append(f"    # [{dependency.kind.value}{reference}] {description}")
        body.append("")
    for step in workflow.steps:
        body.append(f"    # {step.name}")
        if step.precondition:
            body.append(f"    # Précondition : {step.precondition}")
        if step.action is WorkflowAction.NAVIGATE:
            body.append(f"    page.goto(_target_url(base_url, {step.page_url!r}))")
        elif step.action is not WorkflowAction.NONE:
            locator = _locator_source(elements, step.target)
            body.extend(_action_lines(step.action, locator, step.value))
        if step.assertion is not WorkflowAssertion.NONE:
            assertion_target = (
                "page"
                if step.assertion is WorkflowAssertion.URL
                else _locator_source(elements, step.assertion_target)
            )
            body.extend(
                _assertion_lines(
                    step.assertion,
                    assertion_target,
                    step.expected,
                )
            )
        body.append("")

    source = _module_header(
        case_slug=case_slug,
        test_name=test_name,
        data_sources=data_sources,
        data_cases=data_cases,
        legacy_data_files=legacy_data_files,
        data_fingerprints=data_fingerprints or {},
        timeout_seconds=workflow.timeout_seconds,
        body=body,
    )
    workflow_sha256 = _json_sha256(document)
    source_sha256 = hashlib.sha256(source.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": 1,
        "generator": "sentinelle-python-playwright",
        "generator_version": GENERATOR_VERSION,
        "case_slug": case_slug,
        "test_name": test_name,
        "workflow_sha256": workflow_sha256,
        "source_sha256": source_sha256,
        "precondition_dependencies": [
            dependency.as_dict() for dependency in workflow.precondition_dependencies
        ],
        "data_case_count": len(data_cases) if data_cases else 1,
        "data_sources": [
            {
                "id": source_definition.id,
                "path": source_definition.path,
                "key_column": source_definition.key_column,
                "sha256": (data_fingerprints or {}).get(
                    source_definition.id,
                    "",
                ),
            }
            for source_definition in data_sources
        ],
        "customization_contracts": {
            "after_workflow": CUSTOMIZATION_CONTRACT,
        },
    }
    return GeneratedCodeArtifact(
        case_slug=case_slug,
        test_name=test_name,
        source=source,
        source_sha256=source_sha256,
        workflow_sha256=workflow_sha256,
        data_case_count=len(data_cases) if data_cases else 1,
        manifest=manifest,
    )


def generate_python_playwright_file(
    input_path: Path,
    output_path: Path,
    *,
    root_directory: Path | None = None,
) -> GeneratedCodeArtifact:
    """Lit le JSON, génère le code et écrit seulement dans la cible explicite."""

    try:
        document = json.loads(input_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CodeGenerationError(
            f"Le document de génération est illisible : {error}."
        ) from error
    if not isinstance(document, Mapping):
        raise CodeGenerationError("Le document de génération doit être un objet.")
    root = (root_directory or Path.cwd()).resolve()
    data_sources, _, legacy_data_files = _data_configuration(document)
    fingerprints: dict[str, str] = {}
    if data_sources:
        for source_definition in data_sources:
            data_path = _resolve_data_path(root, source_definition.path)
            try:
                content = data_path.read_bytes()
            except OSError as error:
                raise CodeGenerationError(
                    f"La source XLSX {source_definition.id} est illisible : {error}."
                ) from error
            fingerprints[source_definition.id] = hashlib.sha256(content).hexdigest()
    else:
        for relative_path in legacy_data_files:
            data_path = _resolve_data_path(root, relative_path)
            try:
                content = data_path.read_bytes()
            except OSError as error:
                raise CodeGenerationError(
                    f"La source XLSX {relative_path} est illisible : {error}."
                ) from error
            fingerprints[relative_path] = hashlib.sha256(content).hexdigest()
    artifact = generate_python_playwright(
        document,
        data_fingerprints=fingerprints,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(artifact.source, encoding="utf-8", newline="\n")
    output_path.with_suffix(".manifest.json").write_text(
        json.dumps(
            artifact.manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return artifact


def _data_files(value: Any) -> tuple[str, ...]:
    if value is None:
        value = []
    if not isinstance(value, list):
        raise CodeGenerationError("data_files doit être une liste.")
    result: list[str] = []
    for item in value:
        normalized = str(item).strip().replace("\\", "/")
        path = PurePosixPath(normalized)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.suffix.casefold() != ".xlsx"
        ):
            raise CodeGenerationError(
                "Chaque donnée doit être un chemin XLSX relatif et sûr."
            )
        result.append(normalized)
    if len(result) > 8:
        raise CodeGenerationError(
            "Un test ne peut pas fusionner plus de huit fichiers de données."
        )
    return tuple(result)


def _data_configuration(
    document: Mapping[str, Any],
) -> tuple[
    tuple[DataSourceDefinition, ...],
    tuple[DataCaseDefinition, ...],
    tuple[str, ...],
]:
    """Valide soit la matrice explicite, soit l’ancien mode première ligne."""

    raw_sources = document.get("data_sources")
    raw_cases = document.get("data_cases")
    if raw_sources is None and raw_cases is None:
        return (), (), _data_files(document.get("data_files"))
    if document.get("data_files") is not None:
        raise CodeGenerationError(
            "Utilisez data_sources/data_cases ou data_files, jamais les deux."
        )
    if not isinstance(raw_sources, list) or not 1 <= len(raw_sources) <= 8:
        raise CodeGenerationError(
            "data_sources doit contenir entre une et huit sources XLSX."
        )
    sources: list[DataSourceDefinition] = []
    source_ids: set[str] = set()
    for raw_source in raw_sources:
        if not isinstance(raw_source, Mapping):
            raise CodeGenerationError("Chaque source de données doit être un objet.")
        source_id = str(raw_source.get("id") or "").strip()
        if not _DATA_IDENTIFIER.fullmatch(source_id):
            raise CodeGenerationError(
                "L’identifiant d’une source doit utiliser minuscules, chiffres, "
                "tirets ou soulignés."
            )
        if source_id in source_ids:
            raise CodeGenerationError(f"Identifiant de source dupliqué : {source_id}.")
        source_ids.add(source_id)
        path = _safe_xlsx_path(raw_source.get("path"))
        key_column = str(raw_source.get("key_column") or "").strip()
        if not _PYTHON_IDENTIFIER.fullmatch(key_column):
            raise CodeGenerationError(
                f"La colonne clé de {source_id} doit être un identifiant simple."
            )
        sources.append(
            DataSourceDefinition(
                id=source_id,
                path=path,
                key_column=key_column,
            )
        )
    if not isinstance(raw_cases, list) or not 1 <= len(raw_cases) <= 100:
        raise CodeGenerationError(
            "data_cases doit contenir entre un et cent cas explicites."
        )
    cases: list[DataCaseDefinition] = []
    case_ids: set[str] = set()
    for raw_case in raw_cases:
        if not isinstance(raw_case, Mapping):
            raise CodeGenerationError("Chaque cas de données doit être un objet.")
        case_id = str(raw_case.get("id") or "").strip()
        if not _DATA_IDENTIFIER.fullmatch(case_id):
            raise CodeGenerationError(
                "L’identifiant d’un cas de données doit être stable et lisible."
            )
        if case_id in case_ids:
            raise CodeGenerationError(f"Cas de données dupliqué : {case_id}.")
        case_ids.add(case_id)
        raw_rows = raw_case.get("rows")
        if not isinstance(raw_rows, Mapping):
            raise CodeGenerationError(
                f"Le cas {case_id} doit associer ses lignes par source."
            )
        normalized_rows = {
            str(source_id): str(row_key).strip()
            for source_id, row_key in raw_rows.items()
        }
        if set(normalized_rows) != source_ids or any(
            not value for value in normalized_rows.values()
        ):
            raise CodeGenerationError(
                f"Le cas {case_id} doit sélectionner exactement une ligne "
                "de chaque source."
            )
        cases.append(
            DataCaseDefinition(
                id=case_id,
                rows=tuple(
                    (source.id, normalized_rows[source.id]) for source in sources
                ),
            )
        )
    return tuple(sources), tuple(cases), ()


def _safe_xlsx_path(value: Any) -> str:
    normalized = str(value or "").strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix.casefold() != ".xlsx"
    ):
        raise CodeGenerationError(
            "Chaque source doit être un chemin XLSX relatif et sûr."
        )
    return normalized


def _resolve_data_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    if candidate != root and root not in candidate.parents:
        raise CodeGenerationError("Le chemin XLSX sort du répertoire racine autorisé.")
    return candidate


def _json_sha256(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _element_catalog(
    pages: tuple[Any, ...],
) -> dict[str, PageElement]:
    result: dict[str, PageElement] = {}
    for page in pages:
        for element in page.elements:
            if element.reference in result:
                raise CodeGenerationError(
                    f"Référence de page dupliquée : {element.reference}."
                )
            result[element.reference] = element
    return result


def _locator_source(
    elements: Mapping[str, PageElement],
    reference: str,
) -> str:
    try:
        element = elements[reference]
    except KeyError as error:
        raise CodeGenerationError(
            f"Le champ {reference} n’existe dans aucune page analysée."
        ) from error
    strategy = element.locator.strategy
    value = element.locator.value
    if strategy == "label":
        return f"page.get_by_label({value!r}, exact=True)"
    if strategy == "role":
        role, separator, name = value.partition("|")
        if not separator:
            raise CodeGenerationError(
                f"Le localisateur de rôle {reference} est invalide."
            )
        return f"page.get_by_role({role!r}, name={name!r}, exact=True)"
    if strategy == "test_id":
        return f"page.get_by_test_id({value!r})"
    if strategy == "placeholder":
        return f"page.get_by_placeholder({value!r}, exact=True)"
    if strategy == "css":
        return f"page.locator({value!r})"
    raise CodeGenerationError(f"Stratégie de localisation interdite : {strategy}.")


def _action_lines(
    action: WorkflowAction,
    locator: str,
    value: str,
) -> list[str]:
    if action is WorkflowAction.CLICK:
        return [f"    {locator}.click()"]
    if action is WorkflowAction.FILL:
        return [f"    _fill({locator}, _value({value!r}, data))"]
    if action is WorkflowAction.SELECT:
        return [f"    {locator}.select_option(label=_value({value!r}, data))"]
    if action is WorkflowAction.CHECK:
        return [f"    {locator}.check()"]
    if action is WorkflowAction.UNCHECK:
        return [f"    {locator}.uncheck()"]
    if action is WorkflowAction.UPLOAD:
        return [f"    {locator}.set_input_files(_value({value!r}, data))"]
    if action is WorkflowAction.WAIT:
        return [f"    expect({locator}).to_be_visible()"]
    raise CodeGenerationError(
        f"L’action {action.value} n’est pas générable dans cette verticale."
    )


def _assertion_lines(
    assertion: WorkflowAssertion,
    target: str,
    expected: str,
) -> list[str]:
    if assertion is WorkflowAssertion.VISIBLE:
        return [f"    expect({target}).to_be_visible()"]
    if assertion is WorkflowAssertion.HIDDEN:
        return [f"    expect({target}).to_be_hidden()"]
    if assertion is WorkflowAssertion.TEXT:
        return [f"    expect({target}).to_contain_text(_value({expected!r}, data))"]
    if assertion is WorkflowAssertion.VALUE:
        return [f"    expect({target}).to_have_value(_value({expected!r}, data))"]
    if assertion is WorkflowAssertion.URL:
        return [
            f"    expect({target}).to_have_url(_target_url(base_url, "
            f"_value({expected!r}, data)))"
        ]
    if assertion is WorkflowAssertion.COUNT:
        return [f"    expect({target}).to_have_count(int(_value({expected!r}, data)))"]
    if assertion is WorkflowAssertion.ENABLED:
        return [f"    expect({target}).to_be_enabled()"]
    if assertion is WorkflowAssertion.CHECKED:
        return [f"    expect({target}).to_be_checked()"]
    raise CodeGenerationError(f"L’assertion {assertion.value} n’est pas générable.")


def _module_header(
    *,
    case_slug: str,
    test_name: str,
    data_sources: tuple[DataSourceDefinition, ...],
    data_cases: tuple[DataCaseDefinition, ...],
    legacy_data_files: tuple[str, ...],
    data_fingerprints: Mapping[str, str],
    timeout_seconds: int,
    body: list[str],
) -> str:
    body_text = "\n".join(body).rstrip()
    if data_sources:
        sources_literal = "\n".join(
            "    "
            + repr(
                (
                    source.id,
                    source.path,
                    source.key_column,
                    data_fingerprints.get(source.id, ""),
                )
            )
            + ","
            for source in data_sources
        )
        cases_literal = "\n".join(
            "    " + repr((case.id, dict(case.rows))) + "," for case in data_cases
        )
        data_declarations = f"""DATA_SOURCES = (
{sources_literal}
)
DATA_CASES = (
{cases_literal}
)"""
        data_helpers = """
def _read_data_source(
    source_id: str,
    relative_path: str,
    key_column: str,
    expected_sha256: str,
) -> dict[str, dict[str, str]]:
    path = ROOT / relative_path
    content = path.read_bytes()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if expected_sha256 and actual_sha256 != expected_sha256:
        raise AssertionError(
            f"Empreinte XLSX modifiée pour {source_id} : "
            f"{actual_sha256} au lieu de {expected_sha256}"
        )
    data_set = parse_tabular_data(path.name, content)
    if key_column not in data_set.headers:
        raise AssertionError(
            f"Colonne clé XLSX absente pour {source_id} : {key_column}"
        )
    key_index = data_set.headers.index(key_column)
    indexed: dict[str, dict[str, str]] = {}
    for row in data_set.rows:
        key = row[key_index]
        if not key or key in indexed:
            raise AssertionError(
                f"Clé XLSX vide ou dupliquée pour {source_id} : {key!r}"
            )
        indexed[key] = dict(zip(data_set.headers, row, strict=True))
    return indexed


def _load_data_cases() -> list[object]:
    sources = {
        source_id: _read_data_source(
            source_id,
            relative_path,
            key_column,
            expected_sha256,
        )
        for source_id, relative_path, key_column, expected_sha256 in DATA_SOURCES
    }
    parameters: list[object] = []
    for case_id, selections in DATA_CASES:
        merged: dict[str, str] = {}
        for source_id, _, _, _ in DATA_SOURCES:
            row_key = selections[source_id]
            try:
                row = sources[source_id][row_key]
            except KeyError as error:
                raise AssertionError(
                    f"Ligne XLSX absente pour {source_id} : {row_key}"
                ) from error
            merged.update(
                {
                    f"{source_id}.{column}": value
                    for column, value in row.items()
                }
            )
        parameters.append(pytest.param(merged, id=case_id))
    return parameters
"""
        test_signature = (
            f'@pytest.mark.parametrize("data", _load_data_cases())\n'
            f"def {test_name}(page: Page, data: dict[str, str]) -> None:"
        )
        data_initialization = ""
    else:
        files_literal = "\n".join(f"    {value!r}," for value in legacy_data_files)
        fingerprint_literal = repr(dict(data_fingerprints))
        data_declarations = f"""DATA_FILES = (
{files_literal}
)
DATA_FINGERPRINTS = {fingerprint_literal}"""
        data_helpers = """
def _load_data() -> dict[str, str]:
    merged: dict[str, str] = {}
    for relative_path in DATA_FILES:
        path = ROOT / relative_path
        content = path.read_bytes()
        expected_sha256 = DATA_FINGERPRINTS.get(relative_path, "")
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if expected_sha256 and actual_sha256 != expected_sha256:
            raise AssertionError(
                f"Empreinte XLSX modifiée pour {relative_path}"
            )
        data_set = parse_tabular_data(path.name, content)
        merged.update(dict(zip(data_set.headers, data_set.rows[0], strict=True)))
    return merged
"""
        test_signature = f"def {test_name}(page: Page) -> None:"
        data_initialization = "    data = _load_data()\n"
    return f'''"""Généré depuis le workflow {case_slug}.

Les modifications manuelles sont autorisées uniquement dans les zones
``sentinelle:custom`` ; elles peuvent être réimportées puis régénérées.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

from playwright.sync_api import Page, expect
import pytest

from sentinelle_fonctionnelle.adapters.tabular import parse_tabular_data


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_VERSION = {GENERATOR_VERSION!r}
{data_declarations}
TOKEN = re.compile(r"\\{{\\{{data\\.([A-Za-z_][A-Za-z0-9_.-]*)\\}}\\}}")


{data_helpers.strip()}


def _value(template: str, data: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in data:
            raise AssertionError(f"Donnée XLSX absente : {{key}}")
        return data[key]

    return TOKEN.sub(replace, template)


def _target_url(base_url: str, configured_url: str) -> str:
    parsed = urlsplit(configured_url)
    suffix = parsed.path or "/"
    if parsed.query:
        suffix += "?" + parsed.query
    return base_url.rstrip("/") + suffix


def _fill(locator: object, value: str) -> None:
    input_type = locator.get_attribute("type")
    if input_type in {{"color", "range"}}:
        locator.evaluate(
            """(element, nextValue) => {{
                element.value = nextValue;
                element.dispatchEvent(new Event("input", {{ bubbles: true }}));
                element.dispatchEvent(new Event("change", {{ bubbles: true }}));
            }}""",
            value,
        )
        return
    locator.fill(value)


def _sentinelle_customize(page: Page, data: dict[str, str]) -> None:
    # sentinelle:custom:start after_workflow contract={CUSTOMIZATION_CONTRACT}
    # Ajoutez ici des actions ou assertions propres à ce cas.
    pass
    # sentinelle:custom:end after_workflow


{test_signature}
    page.set_default_timeout({timeout_seconds * 1_000})
    base_url = os.environ.get(
        "HR_DEMO_BASE_URL",
        "http://127.0.0.1:8000",
    )
{data_initialization.rstrip()}

{body_text}
    _sentinelle_customize(page, data)
'''
