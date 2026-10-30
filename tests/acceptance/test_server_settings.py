"""ACC-061 — configuration sûre du serveur local."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sentinelle_fonctionnelle.application import ApplicationMode
from sentinelle_fonctionnelle.web.settings import (
    ServerSettings,
    UnsupportedDeploymentMode,
)


class ServerSettingsAcceptanceTests(unittest.TestCase):
    def test_local_defaults_are_loopback_and_workspace_relative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base_directory = Path(temporary_directory)
            settings = ServerSettings.from_environment(
                {},
                base_directory=base_directory,
            )
            self.assertEqual(ApplicationMode.LOCAL, settings.mode)
            self.assertEqual("127.0.0.1", settings.host)
            self.assertEqual(8000, settings.port)
            self.assertEqual(
                base_directory / "data" / "sentinelle_fonctionnelle.db",
                settings.database,
            )
            self.assertEqual(
                base_directory / "data" / "test-approaches.yaml",
                settings.test_approaches,
            )
            self.assertEqual(
                base_directory / "data" / "generation-profiles.yaml",
                settings.generation_profiles,
            )
            self.assertEqual(
                base_directory / "data" / "test-intents.yaml",
                settings.test_intents,
            )
            settings.prepare()
            self.assertTrue(settings.database.parent.is_dir())

    def test_environment_can_override_local_database_host_and_port(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base_directory = Path(temporary_directory)
            settings = ServerSettings.from_environment(
                {
                    "SENTINELLE_FONCTIONNELLE_MODE": "local",
                    "SENTINELLE_FONCTIONNELLE_DATABASE": "var/custom.db",
                    "SENTINELLE_FONCTIONNELLE_TEST_APPROACHES": (
                        "configuration/approaches.yaml"
                    ),
                    "SENTINELLE_FONCTIONNELLE_GENERATION_PROFILES": (
                        "configuration/generation.yaml"
                    ),
                    "SENTINELLE_FONCTIONNELLE_TEST_INTENTS": (
                        "configuration/intents.yaml"
                    ),
                    "SENTINELLE_FONCTIONNELLE_HOST": "localhost",
                    "SENTINELLE_FONCTIONNELLE_PORT": "9123",
                },
                base_directory=base_directory,
            )
            self.assertEqual(base_directory / "var" / "custom.db", settings.database)
            self.assertEqual(
                base_directory / "configuration" / "approaches.yaml",
                settings.test_approaches,
            )
            self.assertEqual(
                base_directory / "configuration" / "generation.yaml",
                settings.generation_profiles,
            )
            self.assertEqual(
                base_directory / "configuration" / "intents.yaml",
                settings.test_intents,
            )
            self.assertEqual("localhost", settings.host)
            self.assertEqual(9123, settings.port)

    def test_online_mode_is_refused_until_required_adapters_exist(self) -> None:
        with self.assertRaisesRegex(
            UnsupportedDeploymentMode,
            "authentification",
        ):
            ServerSettings.from_environment(
                {"SENTINELLE_FONCTIONNELLE_MODE": "online"},
                base_directory=Path.cwd(),
            )

    def test_invalid_port_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "SENTINELLE_FONCTIONNELLE_PORT",
        ):
            ServerSettings.from_environment(
                {"SENTINELLE_FONCTIONNELLE_PORT": "70000"},
                base_directory=Path.cwd(),
            )


if __name__ == "__main__":
    unittest.main()
