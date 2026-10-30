"""Cycle de vie auditable d'un artefact candidat de test.

Le candidat est volontairement distinct du cas de test : une nouvelle
génération ne doit jamais effacer l'artefact, la décision ou les preuves de la
version précédente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any, Mapping
from uuid import UUID


class CandidateError(ValueError):
    """Une opération violerait le cycle de vie du candidat."""


class CandidateOrigin(StrEnum):
    DETERMINISTIC = "deterministic"
    LLM = "llm"

    @property
    def label(self) -> str:
        return {
            self.DETERMINISTIC: "Générateur déterministe",
            self.LLM: "LLM de génération",
        }[self]


class CandidateStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"
    INVALIDATED = "invalidated"

    @property
    def label(self) -> str:
        return {
            self.PENDING: "À valider",
            self.VALIDATED: "Validé individuellement",
            self.APPROVED: "Approuvé",
            self.REJECTED: "Rejeté",
            self.INVALIDATED: "Invalidé",
        }[self]


@dataclass(frozen=True, slots=True)
class CandidateFile:
    path: str
    content: str
    sha256: str

    def __post_init__(self) -> None:
        path = PurePosixPath(self.path)
        if not self.path or path.is_absolute() or ".." in path.parts:
            raise CandidateError("Le chemin d'un fichier candidat doit être relatif.")
        if len(self.sha256) != 64:
            raise CandidateError("L'empreinte d'un fichier candidat est invalide.")


@dataclass(frozen=True, slots=True)
class CandidateExecution:
    execution_id: UUID
    occurred_at: datetime
    status: str
    test_sha256: str
    duration_seconds: float
    report: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise CandidateError("La date d'exécution doit inclure un fuseau horaire.")

    @property
    def passed(self) -> bool:
        return self.status == "passed"


@dataclass(frozen=True, slots=True)
class TestCandidate:
    id: UUID
    project_id: UUID
    test_plan_id: UUID
    case_id: UUID
    sequence: int
    origin: CandidateOrigin
    created_at: datetime
    specification_version: int
    specification_sha256: str
    candidate_sha256: str
    prompt_sha256: str
    files: tuple[CandidateFile, ...]
    manifest: Mapping[str, Any]
    status: CandidateStatus
    decision_at: datetime | None = None
    decision_reason: str = ""
    executions: tuple[CandidateExecution, ...] = ()

    def __post_init__(self) -> None:
        if self.sequence < 1 or self.specification_version < 1:
            raise CandidateError("Les versions du candidat doivent être positives.")
        if self.created_at.tzinfo is None:
            raise CandidateError(
                "La date de génération doit inclure un fuseau horaire."
            )
        if not self.files:
            raise CandidateError("Un candidat doit contenir au moins un fichier.")

    @property
    def short_sha256(self) -> str:
        return self.candidate_sha256[:12]

    @property
    def latest_execution(self) -> CandidateExecution | None:
        return self.executions[-1] if self.executions else None

    @property
    def can_be_approved(self) -> bool:
        execution = self.latest_execution
        return (
            self.status is CandidateStatus.VALIDATED
            and execution is not None
            and execution.passed
            and execution.test_sha256 in {item.sha256 for item in self.files}
        )


@dataclass(frozen=True, slots=True)
class CandidateComparison:
    previous_id: UUID | None
    current_id: UUID
    added: tuple[str, ...]
    changed: tuple[str, ...]
    removed: tuple[str, ...]

    @property
    def unchanged(self) -> bool:
        return not (self.added or self.changed or self.removed)
