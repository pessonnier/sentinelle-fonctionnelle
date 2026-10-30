"""Contrôles déterministes précédant la génération et l’exécution d’un cas.

Références : EF-007.1, EF-007.2, ACC-033 et contribution à ACC-034.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable
from urllib.parse import urlparse

from sentinelle_fonctionnelle.domain.workflow import (
    GenerationWorkflowInput,
    PreconditionDependencyKind,
)


class ReadinessStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    code: str
    label: str
    status: ReadinessStatus
    detail: str
    blocking: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "code": self.code,
            "label": self.label,
            "status": self.status.value,
            "detail": self.detail,
            "blocking": self.blocking,
        }


@dataclass(frozen=True, slots=True)
class WorkflowReadiness:
    checks: tuple[ReadinessCheck, ...]

    @property
    def ready(self) -> bool:
        return not any(
            check.blocking and check.status is ReadinessStatus.FAILED
            for check in self.checks
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "checks": [check.as_dict() for check in self.checks],
        }


def assess_workflow_readiness(
    workflow: GenerationWorkflowInput,
    *,
    project_target: str,
    available_secret_refs: Iterable[str] = (),
    browser_available: bool = True,
) -> WorkflowReadiness:
    """Évalue des faits locaux ; aucune réponse LLM ne peut modifier le résultat."""

    checks: list[ReadinessCheck] = []
    checks.append(
        _check(
            "environment-profile",
            "Profil d’environnement",
            bool(workflow.environment_profile.strip()),
            "Le profil d’environnement est sélectionné."
            if workflow.environment_profile.strip()
            else "Sélectionnez un profil d’environnement avant l’exécution.",
        )
    )

    authorized = _same_origin(workflow.start_url, project_target)
    checks.append(
        _check(
            "target-origin",
            "Destination autorisée",
            authorized,
            "La page de départ appartient à l’origine de la cible du projet."
            if authorized
            else "La page de départ n’appartient pas à l’origine de la cible du projet.",
        )
    )

    if workflow.schema_version < 2:
        checks.append(
            ReadinessCheck(
                code="precondition-review",
                label="Traduction des préconditions",
                status=ReadinessStatus.WARNING,
                detail=(
                    "Workflow historique : ouvrez puis enregistrez le cas pour "
                    "préparer la traduction explicite de ses préconditions."
                ),
                blocking=False,
            )
        )
    else:
        covered = {
            dependency.source
            for dependency in workflow.precondition_dependencies
            if dependency.confirmed
        }
        missing = [source for source in workflow.setup if source not in covered]
        checks.append(
            _check(
                "precondition-review",
                "Traduction des préconditions",
                not missing
                and all(
                    dependency.confirmed
                    for dependency in workflow.precondition_dependencies
                ),
                "Toutes les préconditions sont traduites et confirmées."
                if not missing
                and all(
                    dependency.confirmed
                    for dependency in workflow.precondition_dependencies
                )
                else "Confirmez la traduction de chaque précondition métier.",
            )
        )

    declared_fixtures = set(workflow.fixture_refs)
    missing_fixtures = sorted(
        {
            dependency.reference
            for dependency in workflow.precondition_dependencies
            if dependency.kind is PreconditionDependencyKind.FIXTURE
            and dependency.reference not in declared_fixtures
        }
    )
    checks.append(
        _check(
            "fixture-references",
            "Fixtures et jeux de données",
            not missing_fixtures,
            "Toutes les fixtures traduites sont déclarées dans les données du cas."
            if not missing_fixtures
            else "Références de données absentes : "
            + ", ".join(missing_fixtures)
            + ".",
        )
    )

    available_secrets = set(available_secret_refs)
    missing_secrets = sorted(set(workflow.secret_refs) - available_secrets)
    checks.append(
        _check(
            "secret-references",
            "Secrets référencés",
            not missing_secrets,
            "Toutes les références de secrets sont disponibles sans exposer leur valeur."
            if not missing_secrets
            else "Secrets indisponibles : " + ", ".join(missing_secrets) + ".",
        )
    )
    checks.append(
        _check(
            "browser-runtime",
            "Navigateur et dépendances",
            browser_available,
            "Le runtime Playwright est disponible."
            if browser_available
            else "Le runtime Playwright n’est pas disponible.",
        )
    )
    return WorkflowReadiness(tuple(checks))


def _check(code: str, label: str, passed: bool, detail: str) -> ReadinessCheck:
    return ReadinessCheck(
        code=code,
        label=label,
        status=ReadinessStatus.PASSED if passed else ReadinessStatus.FAILED,
        detail=detail,
        blocking=not passed,
    )


def _same_origin(left: str, right: str) -> bool:
    left_url = urlparse(left)
    right_url = urlparse(right)
    return (
        left_url.scheme in {"http", "https"}
        and left_url.scheme == right_url.scheme
        and left_url.hostname == right_url.hostname
        and (left_url.port or _default_port(left_url.scheme))
        == (right_url.port or _default_port(right_url.scheme))
    )


def _default_port(scheme: str) -> int | None:
    return {"http": 80, "https": 443}.get(scheme)
