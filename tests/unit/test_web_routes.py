"""Contrats d'isolation des quatre routeurs fonctionnels."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from fastapi.routing import APIRoute
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.web.cases_routes import build_cases_router
from sentinelle_fonctionnelle.web.catalogue_routes import build_catalogue_router
from sentinelle_fonctionnelle.web.composition import WebServices
from sentinelle_fonctionnelle.web.configuration_routes import (
    build_configuration_router,
)
from sentinelle_fonctionnelle.web.generation_routes import build_generation_router

TEMPLATES = Jinja2Templates(
    directory=(
        Path(__file__).resolve().parents[2]
        / "src"
        / "sentinelle_fonctionnelle"
        / "web"
        / "templates"
    )
)


def _unconfigured_services() -> WebServices:
    """Crée un double suffisant : construire un routeur ne doit appeler aucun port."""

    return cast(
        WebServices,
        SimpleNamespace(
            projects=object(),
            test_approaches=object(),
            generation_profiles=object(),
            functional_intents=object(),
            candidates=object(),
        ),
    )


class RouterIsolationTests(unittest.TestCase):
    def test_each_router_can_be_built_without_database_or_network(self) -> None:
        services = _unconfigured_services()
        expectations = (
            (
                build_catalogue_router,
                "catalogue",
                lambda path: (
                    path == "/"
                    or "/projects" in path
                    or path in {"/documentation", "/tutorials/test-case"}
                ),
            ),
            (
                build_configuration_router,
                "configuration",
                lambda path: path.startswith("/configuration/"),
            ),
            (build_cases_router, "cases", lambda path: "/cases/" in path),
            (build_generation_router, "generation", lambda path: "/cases/" in path),
        )

        for builder, expected_tag, owns_path in expectations:
            with self.subTest(router=expected_tag):
                router = builder(services, TEMPLATES)
                routes = tuple(
                    route for route in router.routes if isinstance(route, APIRoute)
                )
                self.assertTrue(routes)
                self.assertTrue(all(expected_tag in route.tags for route in routes))
                self.assertTrue(all(owns_path(route.path) for route in routes))

    def test_router_route_names_and_paths_are_unique(self) -> None:
        services = _unconfigured_services()
        routers = (
            build_catalogue_router(services, TEMPLATES),
            build_configuration_router(services, TEMPLATES),
            build_cases_router(services, TEMPLATES),
            build_generation_router(services, TEMPLATES),
        )
        signatures: set[tuple[str, str]] = set()
        for router in routers:
            for route in router.routes:
                if not isinstance(route, APIRoute):
                    continue
                for method in route.methods:
                    signature = method, route.path
                    self.assertNotIn(signature, signatures)
                    signatures.add(signature)

        self.assertGreaterEqual(len(signatures), 30)
