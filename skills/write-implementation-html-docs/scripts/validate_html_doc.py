"""Validate a standalone, traceable implementation HTML guide."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


REQUIRED_SECTIONS = {
    "current-status",
    "prerequisites",
    "configuration",
    "launch",
    "scenarios",
    "troubleshooting",
    "limitations",
    "traceability",
}
SPEC_PATTERN = re.compile(r"\b(?:ACC|DOC|EF|ENF|GEN|LOAD)-\d+(?:\.\d+)?\b")


class GuideParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype = False
        self.html_lang = ""
        self.title_depth = 0
        self.title = ""
        self.ids: list[str] = []
        self.anchors: list[str] = []
        self.h1_count = 0
        self.main_count = 0
        self.nav_count = 0
        self.trace_markers: list[tuple[set[str], str]] = []
        self.external_assets: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.lower() == "doctype html":
            self.doctype = True

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "html":
            self.html_lang = attributes.get("lang") or ""
        elif tag == "title":
            self.title_depth += 1
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "nav":
            self.nav_count += 1

        identifier = attributes.get("id")
        if identifier:
            self.ids.append(identifier)
        href = attributes.get("href")
        if href and href.startswith("#"):
            self.anchors.append(href[1:])

        for attribute in ("src",):
            value = attributes.get(attribute) or ""
            if value.startswith(("http://", "https://", "//")):
                self.external_assets.append(value)
        if tag == "link":
            value = attributes.get("href") or ""
            if value.startswith(("http://", "https://", "//")):
                self.external_assets.append(value)

        data_spec = attributes.get("data-spec")
        if data_spec:
            identifiers = set(SPEC_PATTERN.findall(data_spec))
            status = attributes.get("data-status") or ""
            self.trace_markers.append((identifiers, status))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title += data


def _verified_identifiers(status_text: str) -> set[str]:
    verified: set[str] = set()
    for line in status_text.splitlines():
        if "Vérifiée" in line:
            verified.update(SPEC_PATTERN.findall(line))
    return verified


def validate(
    html_path: Path,
    specification_path: Path,
    status_path: Path,
) -> list[str]:
    errors: list[str] = []
    parser = GuideParser()
    parser.feed(html_path.read_text(encoding="utf-8"))
    specification = specification_path.read_text(encoding="utf-8")
    verified = _verified_identifiers(status_path.read_text(encoding="utf-8"))

    if not parser.doctype:
        errors.append("Le document doit commencer par <!doctype html>.")
    if not parser.html_lang:
        errors.append("L’élément html doit déclarer une langue.")
    if not parser.title.strip():
        errors.append("Le document doit contenir un titre non vide.")
    if parser.h1_count != 1:
        errors.append(f"Un seul h1 est requis, trouvé : {parser.h1_count}.")
    if parser.main_count != 1:
        errors.append(f"Un seul main est requis, trouvé : {parser.main_count}.")
    if parser.nav_count < 1:
        errors.append("Une navigation sémantique est requise.")

    duplicate_ids = sorted(
        identifier
        for identifier in set(parser.ids)
        if parser.ids.count(identifier) > 1
    )
    if duplicate_ids:
        errors.append(f"Identifiants HTML dupliqués : {', '.join(duplicate_ids)}.")

    missing_sections = sorted(REQUIRED_SECTIONS - set(parser.ids))
    if missing_sections:
        errors.append(f"Sections manquantes : {', '.join(missing_sections)}.")

    missing_anchors = sorted(set(parser.anchors) - set(parser.ids))
    if missing_anchors:
        errors.append(f"Ancres internes introuvables : {', '.join(missing_anchors)}.")

    if "main-content" not in parser.anchors:
        errors.append("Un lien d’évitement vers #main-content est requis.")
    if parser.external_assets:
        errors.append(
            "Ressources réseau interdites : "
            + ", ".join(sorted(parser.external_assets))
        )
    if not parser.trace_markers:
        errors.append("Au moins un marqueur data-spec est requis.")

    for identifiers, implementation_status in parser.trace_markers:
        if not identifiers:
            errors.append("Un marqueur data-spec ne contient aucun identifiant valide.")
            continue
        if implementation_status not in {"implemented", "planned"}:
            errors.append(
                "Chaque data-spec doit déclarer data-status=implemented ou planned."
            )
        for identifier in identifiers:
            if identifier not in specification:
                errors.append(f"Identifiant absent des spécifications : {identifier}.")
            if (
                implementation_status == "implemented"
                and identifier not in verified
            ):
                errors.append(
                    f"Identifiant présenté comme implémenté mais non vérifié : "
                    f"{identifier}."
                )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--status", type=Path, required=True)
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    errors = validate(arguments.html, arguments.spec, arguments.status)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: {arguments.html} est structurellement valide et traçable."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
