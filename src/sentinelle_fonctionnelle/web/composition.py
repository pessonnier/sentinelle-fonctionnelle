"""Composition des adaptateurs utilisés par l'interface web locale."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sentinelle_fonctionnelle.adapters.design_llm import ConfiguredDesignLLM
from sentinelle_fonctionnelle.adapters.persistence.sqlite import (
    SQLiteProjectRepository,
)
from sentinelle_fonctionnelle.application import (
    CandidateLifecycleApplication,
    ProjectApplication,
)
from sentinelle_fonctionnelle.domain import (
    FunctionalIntentCatalog,
    GenerationProfileCatalog,
    TestApproachCatalog,
)
from sentinelle_fonctionnelle.web.security import SecurePageLoader
from sentinelle_fonctionnelle.web.settings import ServerSettings

PACKAGE_DIRECTORY = Path(__file__).resolve().parent.parent
DEFAULT_TEST_APPROACHES = PACKAGE_DIRECTORY / "configuration" / "test-approaches.yaml"
DEFAULT_GENERATION_PROFILES = (
    PACKAGE_DIRECTORY / "configuration" / "generation-profiles.yaml"
)
DEFAULT_TEST_INTENTS = PACKAGE_DIRECTORY / "configuration" / "test-intents.yaml"


@dataclass(frozen=True, slots=True)
class WebServices:
    """Dépendances explicites partagées par les routeurs web."""

    settings: ServerSettings
    projects: ProjectApplication
    test_approaches: TestApproachCatalog
    generation_profiles: GenerationProfileCatalog
    functional_intents: FunctionalIntentCatalog
    design_llm: ConfiguredDesignLLM
    page_loader: SecurePageLoader
    candidates: CandidateLifecycleApplication


def compose_web_services(settings: ServerSettings) -> WebServices:
    """Instancie les adaptateurs locaux sans les importer dans les cas d'usage."""

    settings.prepare()
    repository = SQLiteProjectRepository(settings.database)
    repository.migrate()
    projects = ProjectApplication(mode=settings.mode, repository=repository)
    if settings.test_approaches is None:
        raise RuntimeError("Le chemin du catalogue d'approches de test est absent.")
    if settings.generation_profiles is None:
        raise RuntimeError("Le chemin du catalogue de génération est absent.")
    if settings.test_intents is None:
        raise RuntimeError("Le chemin du catalogue d’intentions est absent.")
    return WebServices(
        settings=settings,
        projects=projects,
        test_approaches=TestApproachCatalog.open(
            settings.test_approaches,
            defaults_path=DEFAULT_TEST_APPROACHES,
        ),
        generation_profiles=GenerationProfileCatalog.open(
            settings.generation_profiles,
            defaults_path=DEFAULT_GENERATION_PROFILES,
        ),
        functional_intents=FunctionalIntentCatalog.open(
            settings.test_intents,
            defaults_path=DEFAULT_TEST_INTENTS,
        ),
        design_llm=ConfiguredDesignLLM(),
        page_loader=SecurePageLoader(),
        candidates=CandidateLifecycleApplication(
            repository,
            root_directory=Path.cwd(),
        ),
    )
