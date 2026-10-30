"""Tests unitaires des frontières HTTP et réseau du lot 1."""

from __future__ import annotations

import tempfile
import unittest
from collections.abc import Iterable
from email.message import Message
from pathlib import Path

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.security import (
    DestinationPolicy,
    DestinationRejected,
    ResolvedDestination,
    SecurePageLoader,
)
from sentinelle_fonctionnelle.web.settings import ServerSettings


class _SequenceResolver:
    def __init__(self, *answers: tuple[str, ...]) -> None:
        self.answers = iter(answers)

    def __call__(self, _hostname: str, _port: int) -> Iterable[str]:
        return next(self.answers)


class _Connection:
    def close(self) -> None:
        pass


class _Response:
    def __init__(
        self,
        status: int,
        *,
        location: str = "",
        content: bytes = b"<html><title>OK</title></html>",
    ) -> None:
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"
        if location:
            self.headers["Location"] = location
        self._content = content

    def read(self, _limit: int) -> bytes:
        return self._content


class _ScriptedPageLoader(SecurePageLoader):
    def __init__(self, policy: DestinationPolicy, *responses: _Response) -> None:
        super().__init__(policy)
        self.responses = iter(responses)
        self.destinations: list[ResolvedDestination] = []

    def _request(self, destination: ResolvedDestination):
        self.destinations.append(destination)
        return next(self.responses), _Connection()


class DestinationPolicyTests(unittest.TestCase):
    def test_private_and_reserved_destinations_are_rejected(self) -> None:
        for address in ("10.0.0.8", "169.254.169.254", "0.0.0.0", "224.0.0.1"):
            with self.subTest(address=address):
                policy = DestinationPolicy(
                    lambda _host, _port, resolved=address: (resolved,)
                )
                with self.assertRaisesRegex(
                    DestinationRejected,
                    "privée ou réservée",
                ):
                    policy.authorize(
                        "https://example.test/login",
                        project_target="https://example.test",
                        security_policy="same-origin",
                    )

    def test_loopback_requires_an_explicit_project_policy(self) -> None:
        policy = DestinationPolicy(lambda _host, _port: ("127.0.0.1",))
        with self.assertRaises(DestinationRejected):
            policy.authorize(
                "http://localhost:8000/demo",
                project_target="http://localhost:8000",
                security_policy="same-origin",
            )

        destination = policy.authorize(
            "http://localhost:8000/demo",
            project_target="http://localhost:8000",
            security_policy="same-origin local-loopback",
        )
        self.assertEqual(("127.0.0.1",), tuple(map(str, destination.addresses)))

    def test_dns_change_is_rejected(self) -> None:
        policy = DestinationPolicy(
            _SequenceResolver(("93.184.216.34",), ("93.184.216.35",))
        )
        first = policy.authorize(
            "https://example.test/login",
            project_target="https://example.test",
            security_policy="same-origin",
        )
        with self.assertRaisesRegex(DestinationRejected, "DNS.*changé"):
            policy.assert_unchanged(
                first,
                project_target="https://example.test",
                security_policy="same-origin",
            )

    def test_another_origin_is_rejected_before_resolution(self) -> None:
        policy = DestinationPolicy(lambda _host, _port: ("93.184.216.34",))
        with self.assertRaisesRegex(DestinationRejected, "cible web du projet"):
            policy.authorize(
                "https://other.test/login",
                project_target="https://example.test",
                security_policy="same-origin",
            )

    def test_cross_origin_redirect_is_rejected(self) -> None:
        loader = _ScriptedPageLoader(
            DestinationPolicy(lambda _host, _port: ("93.184.216.34",)),
            _Response(302, location="https://other.test/private"),
        )
        with self.assertRaisesRegex(DestinationRejected, "cible web du projet"):
            loader(
                "https://example.test/start",
                project_target="https://example.test",
                security_policy="same-origin",
            )

    def test_dns_change_across_redirect_is_rejected(self) -> None:
        loader = _ScriptedPageLoader(
            DestinationPolicy(
                _SequenceResolver(("93.184.216.34",), ("93.184.216.35",))
            ),
            _Response(302, location="/final"),
        )
        with self.assertRaisesRegex(DestinationRejected, "DNS.*changé"):
            loader(
                "https://example.test/start",
                project_target="https://example.test",
                security_policy="same-origin",
            )

    def test_authorized_address_is_pinned_for_the_request(self) -> None:
        loader = _ScriptedPageLoader(
            DestinationPolicy(lambda _host, _port: ("93.184.216.34",)),
            _Response(200),
        )
        html = loader(
            "https://example.test/start",
            project_target="https://example.test",
            security_policy="same-origin",
        )
        self.assertIn("<title>OK</title>", html)
        self.assertEqual(
            ("93.184.216.34",),
            tuple(map(str, loader.destinations[0].addresses)),
        )


class CrossSiteMutationTests(unittest.TestCase):
    def test_cross_site_project_creation_is_refused_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_web_app(
                ServerSettings(database=Path(temporary_directory) / "sentinel.db")
            )
            with TestClient(app) as client:
                response = client.post(
                    "/projects",
                    headers={
                        "Origin": "https://attacker.invalid",
                        "Sec-Fetch-Site": "cross-site",
                    },
                    data={
                        "name": "Projet injecté",
                        "description": "",
                        "web_target": "https://target.invalid",
                        "security_policy": "same-origin",
                    },
                )

            self.assertEqual(403, response.status_code)
            self.assertEqual(
                [], list(app.state.project_application.list_projects(None))
            )

    def test_same_origin_project_creation_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_web_app(
                ServerSettings(database=Path(temporary_directory) / "sentinel.db")
            )
            with TestClient(app) as client:
                response = client.post(
                    "/projects",
                    headers={
                        "Origin": "http://testserver",
                        "Sec-Fetch-Site": "same-origin",
                    },
                    data={
                        "name": "Projet légitime",
                        "description": "",
                        "web_target": "https://target.invalid",
                        "security_policy": "same-origin",
                    },
                    follow_redirects=False,
                )

            self.assertEqual(303, response.status_code)
            self.assertEqual(1, len(app.state.project_application.list_projects(None)))

    def test_foreign_referer_is_rejected_without_origin_header(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            app = create_web_app(
                ServerSettings(database=Path(temporary_directory) / "sentinel.db")
            )
            with TestClient(app) as client:
                response = client.post(
                    "/projects",
                    headers={"Referer": "https://attacker.invalid/form"},
                    data={
                        "name": "Projet injecté",
                        "description": "",
                        "web_target": "https://target.invalid",
                        "security_policy": "same-origin",
                    },
                )

            self.assertEqual(403, response.status_code)
            self.assertFalse(app.state.project_application.list_projects(None))
