"""Fabrique FastAPI locale de Sentinelle Fonctionnelle."""

from __future__ import annotations

from pathlib import Path
from time import monotonic
import json
import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sentinelle_fonctionnelle.adapters.design_llm import DesignLLMError
from sentinelle_fonctionnelle.adapters.persistence.sqlite import SCHEMA_VERSION
from sentinelle_fonctionnelle.application import (
    CodeCustomizationError,
    ExecutionRunnerError,
)
from sentinelle_fonctionnelle.domain import (
    CandidateError,
    DesignDialogueError,
    FunctionalIntentError,
    GenerationProfileError,
    HierarchyError,
    TabularDataError,
    TestApproachError,
    WorkflowError,
)
from sentinelle_fonctionnelle.web.composition import (
    DEFAULT_TEST_APPROACHES as DEFAULT_TEST_APPROACHES,
)
from sentinelle_fonctionnelle.web.composition import (
    compose_web_services,
)
from sentinelle_fonctionnelle.web.hr_demo import build_hr_demo_router
from sentinelle_fonctionnelle.web.orders_demo import build_orders_demo_router
from sentinelle_fonctionnelle.web.routes import build_web_routers
from sentinelle_fonctionnelle.web.security import SameOriginMutationMiddleware
from sentinelle_fonctionnelle.web.settings import ServerSettings

PACKAGE_DIRECTORY = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=PACKAGE_DIRECTORY / "templates")
_WEB_ERRORS = (
    CandidateError,
    CodeCustomizationError,
    ExecutionRunnerError,
    HierarchyError,
    TabularDataError,
    TestApproachError,
    GenerationProfileError,
    FunctionalIntentError,
    DesignDialogueError,
    DesignLLMError,
    WorkflowError,
)


def create_web_app(settings: ServerSettings | None = None) -> FastAPI:
    """Compose l'application locale autour de services et routeurs explicites."""

    services = compose_web_services(settings or ServerSettings())
    app = FastAPI(
        title="Sentinelle Fonctionnelle",
        version="0.1.0.dev0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    app.state.settings = services.settings
    app.state.project_application = services.projects
    app.state.test_approach_catalog = services.test_approaches
    app.state.generation_profile_catalog = services.generation_profiles
    app.state.functional_intent_catalog = services.functional_intents
    app.state.design_llm = services.design_llm
    app.state.page_loader = services.page_loader
    app.state.candidate_lifecycle = services.candidates
    app.add_middleware(SameOriginMutationMiddleware)

    @app.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", "")
        if not request_id.isascii() or not 1 <= len(request_id) <= 128:
            request_id = uuid4().hex
        started = monotonic()
        response = await call_next(request)
        duration_ms = round((monotonic() - started) * 1000, 3)
        response.headers["X-Request-ID"] = request_id
        logging.getLogger("sentinelle.http").info(
            json.dumps(
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                    "mode": services.settings.mode.value,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return response

    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIRECTORY / "static"),
        name="static",
    )
    app.include_router(build_hr_demo_router(templates))
    app.include_router(build_orders_demo_router(templates))
    routers = build_web_routers(services, templates)
    for router in routers.all():
        app.include_router(router)

    async def web_error(request: Request, error: Exception) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"message": str(error)},
            status_code=400,
        )

    for error_type in _WEB_ERRORS:
        app.add_exception_handler(error_type, web_error)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str | int]:
        return {
            "status": "ok",
            "mode": services.settings.mode.value,
            "schema_version": SCHEMA_VERSION,
        }

    @app.get("/ready", tags=["system"])
    def ready() -> dict[str, str]:
        services.projects.list_projects(None)
        return {"status": "ready", "mode": services.settings.mode.value}

    return app
