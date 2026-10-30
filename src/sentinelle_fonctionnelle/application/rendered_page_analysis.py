"""Exploration bornée d'une page rendue et application de son catalogue.

Ce cas d'usage sépare le plan déclaratif, l'accès aux données et le navigateur.
Le processus web n'exécute donc jamais une instruction de navigation arbitraire.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.adapters.tabular import parse_tabular_data
from sentinelle_fonctionnelle.domain.workflow import AnalyzedPage


MAX_ACTIONS = 20
MAX_TIMEOUT_SECONDS = 120
_TOKEN = re.compile(r"\{\{data\.([a-z][a-z0-9_-]*)\.([A-Za-z_][A-Za-z0-9_.-]*)\}\}")
_ID = re.compile(r"[a-z][a-z0-9_-]*\Z")
_ACTIONS = frozenset(
    {"fill", "check", "uncheck", "click", "select", "wait_visible", "wait_hidden"}
)
_STRATEGIES = frozenset({"label", "role", "test_id", "placeholder", "css"})


class RenderedPageAnalysisError(ValueError):
    """Le plan d'exploration ou son résultat n'est pas sûr ou cohérent."""


@dataclass(frozen=True, slots=True)
class ExplorationLocator:
    strategy: str
    value: str


@dataclass(frozen=True, slots=True)
class ExplorationAction:
    action: str
    locator: ExplorationLocator
    value: str = ""


@dataclass(frozen=True, slots=True)
class ExplorationDataSource:
    id: str
    path: str
    key_column: str
    row_key: str


@dataclass(frozen=True, slots=True)
class RenderedPageExplorationPlan:
    catalog_url: str
    start_url: str
    timeout_seconds: int
    data_sources: tuple[ExplorationDataSource, ...]
    actions: tuple[ExplorationAction, ...]


@dataclass(frozen=True, slots=True)
class RenderedPageSnapshot:
    final_url: str
    title: str
    html: str
    browser: str
    source_html: str = ""


@dataclass(frozen=True, slots=True)
class RenderedPageCatalogArtifact:
    page: AnalyzedPage
    browser: str
    final_url: str
    action_count: int
    data_case_ids: Mapping[str, str]
    data_fingerprints: Mapping[str, str]
    server_references: tuple[str, ...]
    rendered_only_references: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "engine": "playwright",
            "browser": self.browser,
            "final_url": self.final_url,
            "action_count": self.action_count,
            "data_case_ids": dict(self.data_case_ids),
            "data_fingerprints": dict(self.data_fingerprints),
            "discovery": {
                "server_html_count": len(self.server_references),
                "rendered_only_count": len(self.rendered_only_references),
                "rendered_only_references": list(self.rendered_only_references),
            },
            "page": self.page.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class CatalogApplicationResult:
    matched_references: int
    new_references: int
    page_url: str
    output: Path

    def as_dict(self) -> dict[str, Any]:
        return {
            "matched_references": self.matched_references,
            "new_references": self.new_references,
            "page_url": self.page_url,
            "output": str(self.output),
        }


class RenderedPageExplorer(Protocol):
    def explore(
        self,
        plan: RenderedPageExplorationPlan,
        actions: tuple[ExplorationAction, ...],
    ) -> RenderedPageSnapshot: ...


def parse_exploration_plan(
    document: Mapping[str, Any],
) -> RenderedPageExplorationPlan:
    if document.get("schema_version") != 1:
        raise RenderedPageAnalysisError(
            "Le plan d'exploration doit utiliser schema_version = 1."
        )
    catalog_url = _local_url(document.get("catalog_url"), "catalog_url")
    start_url = _local_url(document.get("start_url"), "start_url")
    if _origin(catalog_url) != _origin(start_url):
        raise RenderedPageAnalysisError(
            "catalog_url et start_url doivent partager la même origine locale."
        )
    timeout = document.get("timeout_seconds", 30)
    if not isinstance(timeout, int) or isinstance(timeout, bool):
        raise RenderedPageAnalysisError("timeout_seconds doit être un entier.")
    if not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
        raise RenderedPageAnalysisError(
            f"timeout_seconds doit être compris entre 1 et {MAX_TIMEOUT_SECONDS}."
        )

    raw_sources = _sequence(document.get("data_sources", ()), "data_sources")
    sources: list[ExplorationDataSource] = []
    source_ids: set[str] = set()
    for raw_source in raw_sources:
        source = _mapping(raw_source, "Une source de données")
        source_id = _identifier(source.get("id"), "L'identifiant de source")
        if source_id in source_ids:
            raise RenderedPageAnalysisError(
                f"La source de données « {source_id} » est déclarée deux fois."
            )
        source_ids.add(source_id)
        sources.append(
            ExplorationDataSource(
                id=source_id,
                path=_safe_xlsx_path(source.get("path")),
                key_column=_text(source.get("key_column"), "La colonne clé"),
                row_key=_text(source.get("row_key"), "La clé de ligne"),
            )
        )

    raw_actions = _sequence(document.get("actions"), "actions")
    if not raw_actions:
        raise RenderedPageAnalysisError(
            "Le plan doit contenir au moins une action d'exploration."
        )
    if len(raw_actions) > MAX_ACTIONS:
        raise RenderedPageAnalysisError(
            f"Le plan dépasse la limite de {MAX_ACTIONS} actions."
        )
    actions: list[ExplorationAction] = []
    for raw_action in raw_actions:
        item = _mapping(raw_action, "Une action")
        action = _text(item.get("action"), "Le type d'action")
        if action not in _ACTIONS:
            raise RenderedPageAnalysisError(
                f"L'action « {action} » est interdite ou inconnue."
            )
        raw_locator = _mapping(item.get("locator"), "Le localisateur")
        strategy = _text(
            raw_locator.get("strategy"), "La stratégie de localisation"
        )
        if strategy not in _STRATEGIES:
            raise RenderedPageAnalysisError(
                f"La stratégie « {strategy} » est interdite ou inconnue."
            )
        locator_value = _text(
            raw_locator.get("value"), "La valeur de localisation"
        )
        if len(locator_value) > 500:
            raise RenderedPageAnalysisError(
                "Une valeur de localisation dépasse 500 caractères."
            )
        value = str(item.get("value") or "")
        if len(value) > 4_000:
            raise RenderedPageAnalysisError(
                "Une valeur d'action dépasse 4 000 caractères."
            )
        if action in {"fill", "select"} and not value:
            raise RenderedPageAnalysisError(
                f"L'action « {action} » exige une valeur."
            )
        tokens = _TOKEN.findall(value)
        for source_id, _ in tokens:
            if source_id not in source_ids:
                raise RenderedPageAnalysisError(
                    f"La valeur utilise la source inconnue « {source_id} »."
                )
        if "{{" in value and not tokens:
            raise RenderedPageAnalysisError(
                f"La valeur « {value} » contient un jeton invalide."
            )
        actions.append(
            ExplorationAction(
                action=action,
                locator=ExplorationLocator(strategy, locator_value),
                value=value,
            )
        )
    return RenderedPageExplorationPlan(
        catalog_url=catalog_url,
        start_url=start_url,
        timeout_seconds=timeout,
        data_sources=tuple(sources),
        actions=tuple(actions),
    )


def analyze_rendered_page(
    document: Mapping[str, Any],
    *,
    root_directory: Path,
    explorer: RenderedPageExplorer,
) -> RenderedPageCatalogArtifact:
    plan = parse_exploration_plan(document)
    values, case_ids, fingerprints = _load_data(plan, root_directory)
    resolved_actions = tuple(
        ExplorationAction(
            action=action.action,
            locator=action.locator,
            value=_resolve_value(action.value, values),
        )
        for action in plan.actions
    )
    snapshot = explorer.explore(plan, resolved_actions)
    if _path_and_query(snapshot.final_url) != _path_and_query(plan.catalog_url):
        raise RenderedPageAnalysisError(
            "La page finale ne correspond pas à catalog_url : "
            f"{_path_and_query(snapshot.final_url)} au lieu de "
            f"{_path_and_query(plan.catalog_url)}."
        )
    page = analyze_html_page(plan.catalog_url, snapshot.html)
    server_references = (
        tuple(
            element.reference
            for element in analyze_html_page(
                plan.catalog_url,
                snapshot.source_html,
            ).elements
        )
        if snapshot.source_html
        else ()
    )
    server_reference_set = set(server_references)
    rendered_only_references = tuple(
        element.reference
        for element in page.elements
        if element.reference not in server_reference_set
    )
    return RenderedPageCatalogArtifact(
        page=page,
        browser=snapshot.browser,
        final_url=snapshot.final_url,
        action_count=len(resolved_actions),
        data_case_ids=case_ids,
        data_fingerprints=fingerprints,
        server_references=server_references,
        rendered_only_references=rendered_only_references,
    )


def analyze_rendered_page_file(
    plan_path: Path,
    output_path: Path,
    *,
    root_directory: Path,
    base_url: str | None = None,
    browser: str = "chromium",
) -> RenderedPageCatalogArtifact:
    from sentinelle_fonctionnelle.adapters.playwright_explorer import (
        PlaywrightRenderedPageExplorer,
    )

    resolved_plan = _inside(root_directory, plan_path, "Le plan")
    resolved_output = _inside(root_directory, output_path, "La sortie")
    try:
        document = json.loads(resolved_plan.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RenderedPageAnalysisError(
            f"Le plan d'exploration est illisible : {error}."
        ) from error
    if not isinstance(document, Mapping):
        raise RenderedPageAnalysisError("Le plan JSON doit être un objet.")
    if base_url is not None:
        _local_url(base_url, "base_url")
    artifact = analyze_rendered_page(
        document,
        root_directory=root_directory,
        explorer=PlaywrightRenderedPageExplorer(
            base_url=base_url,
            browser=browser,
        ),
    )
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(
        json.dumps(
            artifact.as_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return artifact


def apply_rendered_catalog_file(
    catalog_path: Path,
    workflow_path: Path,
    output_path: Path,
    *,
    root_directory: Path,
) -> CatalogApplicationResult:
    resolved_catalog = _inside(root_directory, catalog_path, "Le catalogue")
    resolved_workflow = _inside(root_directory, workflow_path, "Le workflow")
    resolved_output = _inside(root_directory, output_path, "La sortie")
    try:
        catalog = json.loads(resolved_catalog.read_text(encoding="utf-8"))
        document = json.loads(resolved_workflow.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RenderedPageAnalysisError(f"Un document JSON est illisible : {error}.") from error
    if not isinstance(catalog, Mapping) or not isinstance(document, Mapping):
        raise RenderedPageAnalysisError("Le catalogue et le workflow doivent être des objets.")
    page = AnalyzedPage.from_mapping(_mapping(catalog.get("page"), "La page cataloguée"))
    updated, matched, new = _apply_page(document, page)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(
        json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return CatalogApplicationResult(
        matched_references=matched,
        new_references=new,
        page_url=page.url,
        output=resolved_output,
    )


def _apply_page(
    document: Mapping[str, Any],
    page: AnalyzedPage,
) -> tuple[dict[str, Any], int, int]:
    updated = json.loads(json.dumps(document, ensure_ascii=False))
    workflow = updated.get("workflow", updated)
    if not isinstance(workflow, dict):
        raise RenderedPageAnalysisError("Le document ne contient pas de workflow valide.")
    pages = workflow.get("pages")
    if not isinstance(pages, list):
        raise RenderedPageAnalysisError("Le workflow ne contient pas de catalogue pages.")
    indexes = [
        index
        for index, existing in enumerate(pages)
        if isinstance(existing, Mapping) and existing.get("url") == page.url
    ]
    if len(indexes) != 1:
        raise RenderedPageAnalysisError(
            f"Le workflow doit contenir exactement une page « {page.url} »."
        )
    index = indexes[0]
    previous = pages[index]
    previous_elements = previous.get("elements", [])
    if not isinstance(previous_elements, list):
        previous_elements = []
    previous_references = {
        str(element.get("reference"))
        for element in previous_elements
        if isinstance(element, Mapping) and element.get("reference")
    }
    stable_by_locator = {
        _element_match_key(element): str(element.get("reference"))
        for element in previous_elements
        if isinstance(element, Mapping) and element.get("reference")
    }
    next_page = page.as_dict()
    matched = 0
    for element in next_page["elements"]:
        stable_reference = stable_by_locator.get(_element_match_key(element))
        if stable_reference:
            element["reference"] = stable_reference
            matched += 1
    references = {element["reference"] for element in next_page["elements"]}
    if len(references) != len(next_page["elements"]):
        raise RenderedPageAnalysisError(
            "Le rapprochement du catalogue produit des références dupliquées."
        )
    used = {
        str(step.get(field))
        for step in workflow.get("steps", [])
        if isinstance(step, Mapping)
        for field in ("target", "assertion_target")
        if str(step.get(field) or "") in previous_references
    }
    missing = sorted(used - references)
    if missing:
        raise RenderedPageAnalysisError(
            "Le catalogue rendu ne retrouve pas les références utilisées : "
            + ", ".join(missing)
            + "."
        )
    pages[index] = next_page
    return updated, matched, len(next_page["elements"]) - matched


def _element_match_key(element: Mapping[str, Any]) -> tuple[str, str, str]:
    locator = element.get("locator")
    if isinstance(locator, Mapping):
        return (
            str(locator.get("strategy") or ""),
            str(locator.get("value") or ""),
            str(element.get("role") or ""),
        )
    return ("", str(element.get("label") or ""), str(element.get("role") or ""))


def _load_data(
    plan: RenderedPageExplorationPlan,
    root_directory: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, str]]:
    values: dict[str, dict[str, str]] = {}
    case_ids: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for source in plan.data_sources:
        path = _inside(root_directory, Path(source.path), f"La source {source.id}")
        try:
            content = path.read_bytes()
            data_set = parse_tabular_data(path.name, content)
        except (OSError, ValueError) as error:
            raise RenderedPageAnalysisError(
                f"La source « {source.id} » est illisible : {error}."
            ) from error
        folded_headers = [header.casefold() for header in data_set.headers]
        try:
            key_index = folded_headers.index(source.key_column.casefold())
        except ValueError as error:
            raise RenderedPageAnalysisError(
                f"La colonne clé « {source.key_column} » manque dans « {source.id} »."
            ) from error
        matches = [row for row in data_set.rows if row[key_index] == source.row_key]
        if len(matches) != 1:
            raise RenderedPageAnalysisError(
                f"La clé « {source.row_key} » doit identifier exactement une ligne "
                f"dans « {source.id} »."
            )
        values[source.id] = dict(
            zip(data_set.headers, matches[0], strict=True)
        )
        case_ids[source.id] = source.row_key
        fingerprints[source.id] = sha256(content).hexdigest()
    return values, case_ids, fingerprints


def _resolve_value(value: str, data: Mapping[str, Mapping[str, str]]) -> str:
    def replace(match: re.Match[str]) -> str:
        source_id, column = match.groups()
        source = data.get(source_id)
        if source is None or column not in source:
            raise RenderedPageAnalysisError(
                f"Le jeton « {match.group(0)} » ne correspond à aucune colonne."
            )
        return source[column]

    resolved = _TOKEN.sub(replace, value)
    if "{{" in resolved or "}}" in resolved:
        raise RenderedPageAnalysisError(
            f"La valeur « {value} » contient un jeton non résolu."
        )
    return resolved


def _local_url(value: Any, field: str) -> str:
    text = _text(value, field)
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"}:
        raise RenderedPageAnalysisError(f"{field} doit être une URL HTTP(S).")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RenderedPageAnalysisError(
            f"{field} doit cibler explicitement la boucle locale."
        )
    try:
        port = parsed.port
    except ValueError as error:
        raise RenderedPageAnalysisError(f"{field} contient un port invalide.") from error
    if port is None:
        raise RenderedPageAnalysisError(f"{field} doit indiquer un port explicite.")
    if parsed.username or parsed.password or parsed.fragment:
        raise RenderedPageAnalysisError(
            f"{field} ne doit contenir ni identité, ni mot de passe, ni fragment."
        )
    return text


def _origin(url: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(url)
    return parsed.scheme, parsed.hostname or "", parsed.port


def _path_and_query(url: str) -> str:
    parsed = urlsplit(url)
    return parsed.path + (f"?{parsed.query}" if parsed.query else "")


def _safe_xlsx_path(value: Any) -> str:
    text = _text(value, "Le chemin XLSX")
    path = Path(text)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.suffix.casefold() != ".xlsx"
    ):
        raise RenderedPageAnalysisError(
            "Une source doit être un chemin XLSX relatif sans remontée."
        )
    return path.as_posix()


def _inside(root: Path, path: Path, label: str) -> Path:
    resolved_root = root.resolve()
    candidate = path if path.is_absolute() else resolved_root / path
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise RenderedPageAnalysisError(
            f"{label} doit rester dans le répertoire du projet."
        )
    return resolved


def _identifier(value: Any, label: str) -> str:
    text = _text(value, label)
    if not _ID.fullmatch(text):
        raise RenderedPageAnalysisError(
            f"{label} doit utiliser des minuscules, chiffres, tirets ou underscores."
        )
    return text


def _text(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise RenderedPageAnalysisError(f"{label} est obligatoire.")
    return text


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RenderedPageAnalysisError(f"{label} doit être un objet.")
    return value


def _sequence(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise RenderedPageAnalysisError(f"{label} doit être une liste.")
    return value
