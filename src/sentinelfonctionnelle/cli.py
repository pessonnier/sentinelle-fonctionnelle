"""Point d'entrée non interactif de développement."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from sentinelfonctionnelle.application import (
    ApplicationMode,
    build_deployment_demo,
    build_hierarchy_demo,
    build_persistence_demo,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinelfonctionnelle")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "demo-hierarchy",
        help="exerce ACC-002 et ACC-003 sur une arborescence en mémoire",
    )
    deployment = subcommands.add_parser(
        "demo-deployment",
        help="exerce ACC-051 et ACC-052 dans un mode de déploiement",
    )
    deployment.add_argument(
        "--mode",
        choices=[mode.value for mode in ApplicationMode],
        required=True,
    )
    deployment.add_argument(
        "--subject",
        help="identité authentifiée obligatoire en mode online",
    )
    persistence = subcommands.add_parser(
        "demo-persistence",
        help="exerce ACC-053 avec un redémarrage sur SQLite",
    )
    persistence.add_argument(
        "--database",
        type=Path,
        required=True,
        help="fichier SQLite local à créer",
    )
    serve = subcommands.add_parser(
        "serve",
        help="démarre l'interface web locale (ACC-060 et ACC-061)",
    )
    serve.add_argument(
        "--mode",
        choices=[mode.value for mode in ApplicationMode],
        help="mode de déploiement (défaut : SENTINEL_MODE ou local)",
    )
    serve.add_argument(
        "--database",
        type=Path,
        help="fichier SQLite (défaut : SENTINEL_DATABASE ou data/...)",
    )
    serve.add_argument(
        "--host",
        help="adresse d'écoute (défaut : SENTINEL_HOST ou 127.0.0.1)",
    )
    serve.add_argument(
        "--port",
        type=int,
        help="port HTTP (défaut : SENTINEL_PORT ou 8000)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "demo-hierarchy":
        print(
            json.dumps(
                build_hierarchy_demo(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "demo-deployment":
        mode = ApplicationMode(arguments.mode)
        if mode is ApplicationMode.ONLINE and not arguments.subject:
            raise SystemExit(
                "Le mode online exige une identité via --subject."
            )
        print(
            json.dumps(
                build_deployment_demo(mode, subject=arguments.subject),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "demo-persistence":
        print(
            json.dumps(
                build_persistence_demo(arguments.database),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "serve":
        from sentinelfonctionnelle.web import (
            ServerSettings,
            UnsupportedDeploymentMode,
            create_web_app,
        )

        environment = dict(os.environ)
        if arguments.mode is not None:
            environment["SENTINEL_MODE"] = arguments.mode
        if arguments.database is not None:
            environment["SENTINEL_DATABASE"] = str(arguments.database)
        if arguments.host is not None:
            environment["SENTINEL_HOST"] = arguments.host
        if arguments.port is not None:
            environment["SENTINEL_PORT"] = str(arguments.port)
        try:
            settings = ServerSettings.from_environment(
                environment,
                base_directory=Path.cwd(),
            )
        except (ValueError, UnsupportedDeploymentMode) as error:
            raise SystemExit(f"Configuration refusée : {error}") from error

        import uvicorn

        uvicorn.run(
            create_web_app(settings),
            host=settings.host,
            port=settings.port,
        )
        return 0
    raise AssertionError(f"Commande non gérée : {arguments.command}")


if __name__ == "__main__":
    raise SystemExit(main())
