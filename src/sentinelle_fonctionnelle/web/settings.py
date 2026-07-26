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

    def __post_init__(self) -> None:
        object.__setattr__(self, "database", Path(self.database))
        object.__setattr__(self, "mode", ApplicationMode(self.mode))
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
        )

    def prepare(self) -> None:
        """Crée uniquement le répertoire de données nécessaire au mode local."""

        self.database.parent.mkdir(parents=True, exist_ok=True)
