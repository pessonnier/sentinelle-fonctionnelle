"""Point d'entrée autonome `sentinelle-run` destiné aux postes et CI."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from sentinelle_fonctionnelle.application.bundle_runner import (
    BundleRunnerError,
    run_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinelle-run")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument(
        "--base-url", default=os.environ.get("TARGET_BASE_URL", ""), required=False
    )
    parser.add_argument(
        "--allow-origin",
        action="append",
        default=[],
        help="origine réseau autorisée ; option répétable",
    )
    parser.add_argument(
        "--declaration",
        default=os.environ.get("SENTINELLE_FONCTIONNELLE_DECLARATION", "manual"),
        choices=("manual", "on_commit", "on_merge_request", "nightly", "release"),
    )
    parser.add_argument("--timeout", type=int, default=300)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if not arguments.base_url:
        raise SystemExit("Exécution refusée : --base-url est obligatoire.")
    configured_origins = tuple(
        item.strip()
        for item in os.environ.get(
            "SENTINELLE_FONCTIONNELLE_ALLOWED_ORIGINS", ""
        ).split(",")
        if item.strip()
    )
    allowed = tuple(arguments.allow_origin) + configured_origins
    if not allowed:
        raise SystemExit(
            "Exécution refusée : fournissez --allow-origin ou "
            "SENTINELLE_FONCTIONNELLE_ALLOWED_ORIGINS."
        )
    try:
        report = run_bundle(
            bundle_directory=arguments.bundle,
            artifact_directory=arguments.artifacts,
            base_url=arguments.base_url,
            declaration=arguments.declaration,
            allowed_origins=allowed,
            timeout_seconds=arguments.timeout,
        )
    except BundleRunnerError as error:
        raise SystemExit(f"Exécution refusée : {error}") from error
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
