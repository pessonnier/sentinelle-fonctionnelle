"""Configuration explicite et sûre du serveur SentinelleFonctionnelle.

Références : EF-001.2, ENF-013 et ACC-061.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from sentinelle_fonctionnelle.application import ApplicationMode


class UnsupportedDeploymentMode(RuntimeError):
    """Le mode demandé n'a pas encore tous ses adaptateurs obligatoires."""


@dataclass(frozen=True, slots=True)
class ServerSettings:
    """Paramètres effectifs du point d'entrée web."""

    database: Path = Path("data/sentinelle_fonctionnelle.db")
    host: str = "127.0.0.1"
    port: int = 8000
    mode: ApplicationMode = ApplicationMode.LOCAL
    test_approaches: Path | None = None
    generation_profiles: Path | None = None
    test_intents: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "database", Path(self.database))
        object.__setattr__(self, "mode", ApplicationMode(self.mode))
        object.__setattr__(
            self,
            "test_approaches",
            (
                Path(self.test_approaches)
                if self.test_approaches is not None
                else Path(self.database).parent / "test-approaches.yaml"
            ),
        )
        object.__setattr__(
            self,
            "generation_profiles",
            (
                Path(self.generation_profiles)
                if self.generation_profiles is not None
                else Path(self.database).parent / "generation-profiles.yaml"
            ),
        )
        object.__setattr__(
            self,
            "test_intents",
            (
                Path(self.test_intents)
                if self.test_intents is not None
                else Path(self.database).parent / "test-intents.yaml"
            ),
        )
        if not self.host.strip():
            raise ValueError("L'adresse d'écoute ne peut pas être vide.")
        if not 1 <= self.port <= 65535:
            raise ValueError(
                "SENTINELLE_FONCTIONNELLE_PORT doit être compris entre 1 et 65535."
            )
        if self.mode is ApplicationMode.ONLINE:
            raise UnsupportedDeploymentMode(
                "Le mode online exige les adaptateurs d'authentification et "
                "de persistance partagée, qui ne sont pas encore disponibles."
            )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str],
        *,
        base_directory: Path,
    ) -> ServerSettings:
        """Construit la configuration à partir des seules variables documentées."""

        mode_value = environment.get(
            "SENTINELLE_FONCTIONNELLE_MODE",
            ApplicationMode.LOCAL.value,
        )
        database_value = environment.get(
            "SENTINELLE_FONCTIONNELLE_DATABASE",
            "data/sentinelle_fonctionnelle.db",
        )
        database = Path(database_value)
        if not database.is_absolute():
            database = base_directory / database
        approaches_value = environment.get(
            "SENTINELLE_FONCTIONNELLE_TEST_APPROACHES",
            "",
        )
        test_approaches = Path(approaches_value) if approaches_value else None
        if test_approaches is not None and not test_approaches.is_absolute():
            test_approaches = base_directory / test_approaches
        generation_value = environment.get(
            "SENTINELLE_FONCTIONNELLE_GENERATION_PROFILES",
            "",
        )
        generation_profiles = Path(generation_value) if generation_value else None
        if generation_profiles is not None and not generation_profiles.is_absolute():
            generation_profiles = base_directory / generation_profiles
        intents_value = environment.get(
            "SENTINELLE_FONCTIONNELLE_TEST_INTENTS",
            "",
        )
        test_intents = Path(intents_value) if intents_value else None
        if test_intents is not None and not test_intents.is_absolute():
            test_intents = base_directory / test_intents
        raw_port = environment.get("SENTINELLE_FONCTIONNELLE_PORT", "8000")
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError(
                "SENTINELLE_FONCTIONNELLE_PORT doit être un entier."
            ) from error
        return cls(
            database=database,
            host=environment.get(
                "SENTINELLE_FONCTIONNELLE_HOST",
                "127.0.0.1",
            ),
            port=port,
            mode=ApplicationMode(mode_value),
            test_approaches=test_approaches,
            generation_profiles=generation_profiles,
            test_intents=test_intents,
        )

    def prepare(self) -> None:
        """Crée uniquement le répertoire de données nécessaire au mode local."""

        self.database.parent.mkdir(parents=True, exist_ok=True)
        if self.test_approaches is not None:
            self.test_approaches.parent.mkdir(parents=True, exist_ok=True)
        if self.generation_profiles is not None:
            self.generation_profiles.parent.mkdir(parents=True, exist_ok=True)
        if self.test_intents is not None:
            self.test_intents.parent.mkdir(parents=True, exist_ok=True)
