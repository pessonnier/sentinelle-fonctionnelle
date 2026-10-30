"""Point d'entrée non interactif de développement."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from sentinelle_fonctionnelle.application import (
    ApplicationMode,
    build_deployment_demo,
    build_hierarchy_demo,
    build_persistence_demo,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinelle-fonctionnelle")
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
    hr_seed = subcommands.add_parser(
        "seed-hr-demo-project",
        help="ajoute à Sentinelle le projet d’exemple de la cible RH intégrée",
    )
    hr_seed.add_argument(
        "--database",
        type=Path,
        default=Path("data/sentinelle_fonctionnelle.db"),
        help="base SQLite locale à alimenter",
    )
    hr_seed.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="racine contenant config/examples et outputs/hr-demo",
    )
    hr_seed.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="origine locale de Sentinelle et de la cible RH",
    )
    orders_seed = subcommands.add_parser(
        "seed-orders-demo-project",
        help="ajoute le projet d’exemple de commande multi-écrans",
    )
    orders_seed.add_argument(
        "--database",
        type=Path,
        default=Path("data/sentinelle_fonctionnelle.db"),
        help="base SQLite locale à alimenter",
    )
    orders_seed.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="origine locale de Sentinelle et de la cible commandes",
    )
    serve = subcommands.add_parser(
        "serve",
        help="démarre l'interface web locale (ACC-060 et ACC-061)",
    )
    serve.add_argument(
        "--mode",
        choices=[mode.value for mode in ApplicationMode],
        help=("mode de déploiement (défaut : SENTINELLE_FONCTIONNELLE_MODE ou local)"),
    )
    serve.add_argument(
        "--database",
        type=Path,
        help=(
            "fichier SQLite (défaut : SENTINELLE_FONCTIONNELLE_DATABASE ou data/...)"
        ),
    )
    serve.add_argument(
        "--host",
        help=("adresse d'écoute (défaut : SENTINELLE_FONCTIONNELLE_HOST ou 127.0.0.1)"),
    )
    serve.add_argument(
        "--port",
        type=int,
        help=("port HTTP (défaut : SENTINELLE_FONCTIONNELLE_PORT ou 8000)"),
    )
    generation = subcommands.add_parser(
        "generate-playwright",
        help="génère un test Python Playwright depuis un workflow confirmé",
    )
    generation.add_argument(
        "--workflow",
        type=Path,
        required=True,
        help="document JSON contenant le workflow et les données XLSX",
    )
    generation.add_argument(
        "--output",
        type=Path,
        required=True,
        help="fichier Python candidat à produire",
    )
    execution = subcommands.add_parser(
        "run-playwright",
        help="valide localement un test généré et produit JUnit + execution.json",
    )
    execution.add_argument(
        "--test",
        type=Path,
        required=True,
        help="fichier Python situé sous tests/generated",
    )
    execution.add_argument(
        "--base-url",
        required=True,
        help="cible HTTP sur la boucle locale avec port explicite",
    )
    execution.add_argument(
        "--output",
        type=Path,
        required=True,
        help="répertoire local destiné aux rapports et preuves",
    )
    execution.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
    )
    execution.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="délai maximal global en secondes",
    )
    exploration = subcommands.add_parser(
        "analyze-rendered-page",
        help="catalogue le DOM rendu après une exploration Playwright bornée",
    )
    exploration.add_argument("--plan", type=Path, required=True)
    exploration.add_argument("--output", type=Path, required=True)
    exploration.add_argument(
        "--base-url",
        help="origine locale d'exécution substituée à celle du plan",
    )
    exploration.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default="chromium",
    )
    catalog = subcommands.add_parser(
        "apply-page-catalog",
        help="applique un catalogue rendu en préservant les références stables",
    )
    catalog.add_argument("--catalog", type=Path, required=True)
    catalog.add_argument("--workflow", type=Path, required=True)
    catalog.add_argument("--output", type=Path, required=True)
    retention = subcommands.add_parser(
        "purge-artifacts",
        help="prévisualise ou applique la politique de conservation des artefacts",
    )
    retention.add_argument("--root", type=Path, required=True)
    retention.add_argument("--days", type=int, required=True)
    retention.add_argument(
        "--apply",
        action="store_true",
        help="supprime les exécutions expirées (prévisualisation par défaut)",
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
            raise SystemExit("Le mode online exige une identité via --subject.")
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
    if arguments.command == "seed-hr-demo-project":
        from sentinelle_fonctionnelle.application import (
            ProjectApplication,
            seed_hr_demo_project,
        )

        result = seed_hr_demo_project(
            ProjectApplication.sqlite(arguments.database),
            root_directory=arguments.root,
            base_url=arguments.base_url,
        )
        print(
            json.dumps(
                result.as_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "seed-orders-demo-project":
        from sentinelle_fonctionnelle.application import (
            ProjectApplication,
            seed_orders_demo_project,
        )

        result = seed_orders_demo_project(
            ProjectApplication.sqlite(arguments.database),
            base_url=arguments.base_url,
        )
        print(
            json.dumps(
                result.as_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if arguments.command == "serve":
        from sentinelle_fonctionnelle.web import (
            ServerSettings,
            UnsupportedDeploymentMode,
            create_web_app,
        )

        environment = dict(os.environ)
        if arguments.mode is not None:
            environment["SENTINELLE_FONCTIONNELLE_MODE"] = arguments.mode
        if arguments.database is not None:
            environment["SENTINELLE_FONCTIONNELLE_DATABASE"] = str(arguments.database)
        if arguments.host is not None:
            environment["SENTINELLE_FONCTIONNELLE_HOST"] = arguments.host
        if arguments.port is not None:
            environment["SENTINELLE_FONCTIONNELLE_PORT"] = str(arguments.port)
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
    if arguments.command == "generate-playwright":
        from sentinelle_fonctionnelle.application import (
            CodeGenerationError,
            generate_python_playwright_file,
        )

        try:
            artifact = generate_python_playwright_file(
                arguments.workflow,
                arguments.output,
            )
        except CodeGenerationError as error:
            raise SystemExit(f"Génération refusée : {error}") from error
        print(
            json.dumps(
                {
                    "case_slug": artifact.case_slug,
                    "test_name": artifact.test_name,
                    "output": str(arguments.output),
                    "manifest": str(arguments.output.with_suffix(".manifest.json")),
                    "source_sha256": artifact.source_sha256,
                    "workflow_sha256": artifact.workflow_sha256,
                    "data_case_count": artifact.data_case_count,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if arguments.command == "run-playwright":
        from sentinelle_fonctionnelle.application import (
            ExecutionRunnerError,
            run_generated_playwright,
        )

        try:
            report = run_generated_playwright(
                test_path=arguments.test,
                base_url=arguments.base_url,
                output_directory=arguments.output,
                root_directory=Path.cwd(),
                browser=arguments.browser,
                timeout_seconds=arguments.timeout,
            )
        except ExecutionRunnerError as error:
            raise SystemExit(f"Exécution refusée : {error}") from error
        print(
            json.dumps(
                report.as_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return report.exit_code
    if arguments.command == "analyze-rendered-page":
        from sentinelle_fonctionnelle.application import (
            RenderedPageAnalysisError,
            analyze_rendered_page_file,
        )

        try:
            artifact = analyze_rendered_page_file(
                arguments.plan,
                arguments.output,
                root_directory=Path.cwd(),
                base_url=arguments.base_url,
                browser=arguments.browser,
            )
        except RenderedPageAnalysisError as error:
            raise SystemExit(f"Exploration refusée : {error}") from error
        print(
            json.dumps(
                {
                    "output": str(arguments.output),
                    "page_url": artifact.page.url,
                    "element_count": len(artifact.page.elements),
                    "action_count": artifact.action_count,
                    "browser": artifact.browser,
                    "fingerprint": artifact.page.fingerprint,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if arguments.command == "apply-page-catalog":
        from sentinelle_fonctionnelle.application import (
            RenderedPageAnalysisError,
            apply_rendered_catalog_file,
        )

        try:
            result = apply_rendered_catalog_file(
                arguments.catalog,
                arguments.workflow,
                arguments.output,
                root_directory=Path.cwd(),
            )
        except RenderedPageAnalysisError as error:
            raise SystemExit(f"Application refusée : {error}") from error
        print(
            json.dumps(
                result.as_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if arguments.command == "purge-artifacts":
        from sentinelle_fonctionnelle.application import (
            RetentionError,
            apply_artifact_retention,
        )

        try:
            result = apply_artifact_retention(
                arguments.root,
                retention_days=arguments.days,
                apply=arguments.apply,
            )
        except RetentionError as error:
            raise SystemExit(f"Rétention refusée : {error}") from error
        print(
            json.dumps(
                {
                    "mode": "apply" if arguments.apply else "preview",
                    "expired": result.expired,
                    "removed": result.removed,
                    "ignored": result.ignored,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    raise AssertionError(f"Commande non gérée : {arguments.command}")


if __name__ == "__main__":
    raise SystemExit(main())
