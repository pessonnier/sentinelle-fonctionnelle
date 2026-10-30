"""Contrôle qualité reproductible du socle SentinelleFonctionnelle."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from html.parser import HTMLParser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCOPE = (
    "src",
    "tests/acceptance",
    "tests/documentation",
    "tests/unit",
    "tools",
)
FORMATTED_BASELINE = (
    "src/sentinelle_fonctionnelle/application/code_generation_prompt.py",
    "src/sentinelle_fonctionnelle/application/precondition_readiness.py",
    "src/sentinelle_fonctionnelle/application/projects.py",
    "src/sentinelle_fonctionnelle/application/bundle_export.py",
    "src/sentinelle_fonctionnelle/application/bundle_runner.py",
    "src/sentinelle_fonctionnelle/application/retention.py",
    "src/sentinelle_fonctionnelle/adapters/persistence/postgresql.py",
    "src/sentinelle_fonctionnelle/runner_cli.py",
    "src/sentinelle_fonctionnelle/domain/workflow.py",
    "src/sentinelle_fonctionnelle/web/settings.py",
    "src/sentinelle_fonctionnelle/web/app.py",
    "src/sentinelle_fonctionnelle/web/routes.py",
    "src/sentinelle_fonctionnelle/web/route_support.py",
    "src/sentinelle_fonctionnelle/web/composition.py",
    "src/sentinelle_fonctionnelle/web/security.py",
    "src/sentinelle_fonctionnelle/web/catalogue_routes.py",
    "src/sentinelle_fonctionnelle/web/configuration_routes.py",
    "src/sentinelle_fonctionnelle/web/cases_routes.py",
    "src/sentinelle_fonctionnelle/web/generation_routes.py",
    "tools/check_quality.py",
    "tests/documentation/test_quality_baseline.py",
    "tests/unit/test_web_security.py",
    "tests/unit/test_web_routes.py",
)
TYPED_BASELINE = (
    "src/sentinelle_fonctionnelle/application/code_generation_prompt.py",
    "src/sentinelle_fonctionnelle/application/precondition_readiness.py",
    "src/sentinelle_fonctionnelle/application/projects.py",
    "src/sentinelle_fonctionnelle/application/bundle_export.py",
    "src/sentinelle_fonctionnelle/application/bundle_runner.py",
    "src/sentinelle_fonctionnelle/application/retention.py",
    "src/sentinelle_fonctionnelle/adapters/persistence/postgresql.py",
    "src/sentinelle_fonctionnelle/runner_cli.py",
    "src/sentinelle_fonctionnelle/domain/hierarchy.py",
    "src/sentinelle_fonctionnelle/domain/workflow.py",
    "src/sentinelle_fonctionnelle/web/settings.py",
    "src/sentinelle_fonctionnelle/web/app.py",
    "src/sentinelle_fonctionnelle/web/routes.py",
    "src/sentinelle_fonctionnelle/web/composition.py",
    "src/sentinelle_fonctionnelle/web/security.py",
    "src/sentinelle_fonctionnelle/web/catalogue_routes.py",
    "src/sentinelle_fonctionnelle/web/configuration_routes.py",
    "src/sentinelle_fonctionnelle/web/cases_routes.py",
    "src/sentinelle_fonctionnelle/web/generation_routes.py",
    "src/sentinelle_fonctionnelle/web/route_support.py",
)
MARKDOWN_LINK = re.compile(r"!?\[[^]]*]\(([^)]+)\)")
LOCKED_REQUIREMENT = re.compile(r"^([A-Za-z0-9_.-]+)==([^\s]+)$")


class _HtmlLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        link_attribute = (
            "href" if tag == "a" else "src" if tag in {"img", "script"} else ""
        )
        if not link_attribute:
            return
        for name, value in attrs:
            if name == link_attribute and value:
                self.targets.append(value)


def find_broken_document_links(root: Path = ROOT) -> tuple[str, ...]:
    """Retourne les liens locaux absents des documents maintenus par le projet."""

    documents = [root / "README.md"]
    documents.extend(
        path for path in (root / "docs").rglob("*.md") if "vendor" not in path.parts
    )
    documents.extend(
        path for path in (root / "docs").rglob("*.html") if "vendor" not in path.parts
    )
    failures: list[str] = []
    for document in sorted(documents):
        content = document.read_text(encoding="utf-8")
        if document.suffix == ".md":
            targets = [match.group(1) for match in MARKDOWN_LINK.finditer(content)]
        else:
            parser = _HtmlLinks()
            parser.feed(content)
            targets = parser.targets
        for target in targets:
            normalized = target.strip().strip("<>").split("#", 1)[0]
            if not normalized or normalized.startswith("#"):
                continue
            parsed = urlsplit(normalized)
            if parsed.scheme or normalized.startswith("//"):
                continue
            path_text = unquote(parsed.path)
            if path_text.startswith("/"):
                # Les chemins absolus décrivent les routes de l’application web.
                continue
            candidate = (document.parent / path_text).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                failures.append(
                    f"{document.relative_to(root)} -> {target} (hors dépôt)"
                )
                continue
            if not candidate.exists():
                failures.append(f"{document.relative_to(root)} -> {target}")
    return tuple(failures)


def find_constraint_mismatches(root: Path = ROOT) -> tuple[str, ...]:
    """Compare l’environnement courant à l’instantané Python 3.12 validé."""

    constraints = root / "requirements" / "constraints-py312.txt"
    failures: list[str] = []
    for line in constraints.read_text(encoding="utf-8").splitlines():
        match = LOCKED_REQUIREMENT.fullmatch(line.strip())
        if match is None:
            continue
        package, expected = match.groups()
        try:
            installed = version(package)
        except PackageNotFoundError:
            failures.append(f"{package} absent (version attendue : {expected})")
            continue
        if installed != expected:
            failures.append(f"{package}=={installed} (version attendue : {expected})")
    return tuple(failures)


def _run(label: str, arguments: tuple[str, ...]) -> bool:
    print(f"\n== {label} ==", flush=True)
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        shell=False,
    )
    return completed.returncode == 0


def _static_checks() -> list[tuple[str, tuple[str, ...]]]:
    python = sys.executable
    return [
        (
            "Syntaxe et erreurs Python critiques",
            (
                python,
                "-m",
                "ruff",
                "check",
                "--select",
                "E9,F63,F7,F82",
                *PYTHON_SCOPE,
            ),
        ),
        (
            "Formatage de la base progressive",
            (python, "-m", "ruff", "format", "--check", *FORMATTED_BASELINE),
        ),
        (
            "Typage de la base progressive",
            (
                python,
                "-m",
                "mypy",
                "--follow-imports=skip",
                "--ignore-missing-imports",
                *TYPED_BASELINE,
            ),
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Vérifie syntaxe, formatage, typage, liens et tests rapides."
    )
    parser.add_argument(
        "--static-only",
        action="store_true",
        help="n’exécute pas la suite pytest",
    )
    arguments = parser.parse_args(argv)

    print("\n== Environnement Python contraint ==", flush=True)
    constraint_mismatches = find_constraint_mismatches()
    if constraint_mismatches:
        for mismatch in constraint_mismatches:
            print(f"ERREUR: {mismatch}")
    else:
        print("Toutes les versions correspondent à l’instantané Python 3.12.")

    check_results = [_run(label, command) for label, command in _static_checks()]
    successful = not constraint_mismatches and all(check_results)
    print("\n== Liens documentaires locaux ==", flush=True)
    broken_links = find_broken_document_links()
    if broken_links:
        successful = False
        for broken_link in broken_links:
            print(f"ERREUR: {broken_link}")
    else:
        print("Tous les liens locaux pointent vers une ressource existante.")

    if not arguments.static_only:
        successful = (
            _run(
                "Tests produit et documentation",
                (
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--basetemp",
                    str(ROOT / ".tmp" / "pytest-quality"),
                ),
            )
            and successful
        )

    print(
        "\nContrôle qualité réussi." if successful else "\nContrôle qualité en échec.",
        flush=True,
    )
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main())
