"""Données de saisie tabulaires et plans d'itération déterministes.

Références : EF-007.2, EF-007.5, ACC-066 à ACC-068.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class TabularDataError(ValueError):
    """Le fichier ou sa stratégie ne peut pas produire un plan sûr."""


class DataIterationMode(StrEnum):
    SERIAL = "serial"
    PARALLEL = "parallel"
    RANDOM = "random"

    @property
    def label(self) -> str:
        return {
            self.SERIAL: "Série",
            self.PARALLEL: "Parallèle",
            self.RANDOM: "Aléatoire",
        }[self]


@dataclass(frozen=True, slots=True)
class TabularDataSet:
    id: UUID
    filename: str
    fingerprint: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    @classmethod
    def create(
        cls,
        *,
        filename: str,
        fingerprint: str,
        headers: tuple[str, ...],
        rows: tuple[tuple[str, ...], ...],
        data_set_id: UUID | None = None,
    ) -> TabularDataSet:
        normalized_filename = filename.strip()
        normalized_headers = tuple(header.strip() for header in headers)
        if not normalized_filename:
            raise TabularDataError("Le nom du fichier est obligatoire.")
        if not normalized_headers or any(not header for header in normalized_headers):
            raise TabularDataError("Chaque colonne doit posséder un en-tête.")
        folded = tuple(header.casefold() for header in normalized_headers)
        if len(set(folded)) != len(folded):
            raise TabularDataError("Les en-têtes de colonnes doivent être uniques.")
        if not rows:
            raise TabularDataError("Le fichier doit contenir au moins un cas.")
        if any(len(row) != len(normalized_headers) for row in rows):
            raise TabularDataError(
                "Chaque cas doit respecter le nombre de colonnes de l'en-tête."
            )
        return cls(
            id=data_set_id or uuid4(),
            filename=normalized_filename,
            fingerprint=fingerprint,
            headers=normalized_headers,
            rows=tuple(tuple(str(value) for value in row) for row in rows),
        )

    @property
    def row_count(self) -> int:
        return len(self.rows)


@dataclass(frozen=True, slots=True)
class DataExecutionCase:
    source_index: int
    values: tuple[tuple[str, str], ...]

    @property
    def value_map(self) -> dict[str, str]:
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class DataExecutionBatch:
    index: int
    cases: tuple[DataExecutionCase, ...]


@dataclass(frozen=True, slots=True)
class DataExecutionPlan:
    mode: DataIterationMode
    batches: tuple[DataExecutionBatch, ...]

    @property
    def cases(self) -> tuple[DataExecutionCase, ...]:
        return tuple(case for batch in self.batches for case in batch.cases)

    @property
    def source_indexes(self) -> tuple[int, ...]:
        return tuple(case.source_index for case in self.cases)

    @property
    def batch_sizes(self) -> tuple[int, ...]:
        return tuple(len(batch.cases) for batch in self.batches)


@dataclass(frozen=True, slots=True)
class TabularDataBinding:
    version: int
    data_set: TabularDataSet
    mode: DataIterationMode
    max_parallelism: int
    random_seed: int
    sample_count: int

    @classmethod
    def create(
        cls,
        *,
        version: int,
        data_set: TabularDataSet,
        mode: DataIterationMode,
        max_parallelism: int = 1,
        random_seed: int = 0,
        sample_count: int | None = None,
    ) -> TabularDataBinding:
        normalized_mode = DataIterationMode(mode)
        if version < 1:
            raise TabularDataError("La version de liaison doit être positive.")
        if not 1 <= max_parallelism <= 20:
            raise TabularDataError(
                "La concurrence maximale doit être comprise entre 1 et 20."
            )
        effective_sample_count = (
            data_set.row_count if sample_count is None else sample_count
        )
        if not 1 <= effective_sample_count <= data_set.row_count:
            raise TabularDataError(
                "Le nombre de cas doit être compris entre 1 et le nombre de lignes."
            )
        if normalized_mode is not DataIterationMode.RANDOM:
            effective_sample_count = data_set.row_count
        return cls(
            version=version,
            data_set=data_set,
            mode=normalized_mode,
            max_parallelism=(
                max_parallelism
                if normalized_mode is DataIterationMode.PARALLEL
                else 1
            ),
            random_seed=random_seed,
            sample_count=effective_sample_count,
        )

    @property
    def plan(self) -> DataExecutionPlan:
        indexes = list(range(1, self.data_set.row_count + 1))
        if self.mode is DataIterationMode.RANDOM:
            indexes = random.Random(self.random_seed).sample(
                indexes,
                self.sample_count,
            )
        cases = tuple(
            DataExecutionCase(
                source_index=index,
                values=tuple(
                    zip(
                        self.data_set.headers,
                        self.data_set.rows[index - 1],
                        strict=True,
                    )
                ),
            )
            for index in indexes
        )
        batch_size = (
            self.max_parallelism
            if self.mode is DataIterationMode.PARALLEL
            else 1
        )
        batches = tuple(
            DataExecutionBatch(
                index=(offset // batch_size) + 1,
                cases=cases[offset : offset + batch_size],
            )
            for offset in range(0, len(cases), batch_size)
        )
        return DataExecutionPlan(mode=self.mode, batches=batches)
