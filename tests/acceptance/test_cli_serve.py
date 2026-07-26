"""ACC-060 et ACC-061 — contrat du point d'entrée web."""

from __future__ import annotations

import unittest
from pathlib import Path

from sentinelfonctionnelle.cli import build_parser


class ServeCommandAcceptanceTests(unittest.TestCase):
    def test_serve_command_exposes_explicit_local_options(self) -> None:
        arguments = build_parser().parse_args(
            [
                "serve",
                "--database",
                "state/local.db",
                "--host",
                "localhost",
                "--port",
                "9123",
            ]
        )
        self.assertEqual("serve", arguments.command)
        self.assertEqual(Path("state/local.db"), arguments.database)
        self.assertEqual("localhost", arguments.host)
        self.assertEqual(9123, arguments.port)


if __name__ == "__main__":
    unittest.main()
