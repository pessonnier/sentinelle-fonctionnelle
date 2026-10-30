"""Agrégation explicite des routeurs fonctionnels."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.web.cases_routes import build_cases_router
from sentinelle_fonctionnelle.web.catalogue_routes import build_catalogue_router
from sentinelle_fonctionnelle.web.composition import WebServices
from sentinelle_fonctionnelle.web.configuration_routes import build_configuration_router
from sentinelle_fonctionnelle.web.generation_routes import build_generation_router


@dataclass(frozen=True, slots=True)
class RouterBundle:
    """Routeurs fonctionnels inclus explicitement par la fabrique web."""

    catalogue: APIRouter
    configuration: APIRouter
    cases: APIRouter
    generation: APIRouter

    def all(self) -> tuple[APIRouter, ...]:
        return self.catalogue, self.configuration, self.cases, self.generation


def build_web_routers(
    services: WebServices,
    templates: Jinja2Templates,
) -> RouterBundle:
    """Construit chaque frontière indépendamment avec les mêmes services."""

    return RouterBundle(
        catalogue=build_catalogue_router(services, templates),
        configuration=build_configuration_router(services, templates),
        cases=build_cases_router(services, templates),
        generation=build_generation_router(services, templates),
    )
