"""Cible RH hétérogène utilisée par l’analyse, les données et Playwright."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.hr_demo import reset_hr_demo_records
from sentinelle_fonctionnelle.web.settings import ServerSettings


class HrDemoTargetAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_hr_demo_records()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        app = create_web_app(
            ServerSettings(
                database=Path(self.temporary_directory.name) / "sentinelle.db"
            )
        )
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_manager_login_entry_and_consultation_preserve_every_value(self) -> None:
        login = self.client.get("/demo/hr/login")
        self.assertEqual(200, login.status_code)
        self.assertIn("Bureau des Talents Intersidéraux", login.text)
        self.assertIn(
            'href="https://github.com/pessonnier/sentinelle-fonctionnelle"',
            login.text,
        )
        self.assertNotIn('name="portal_code"', login.text)

        authenticated = self.client.post(
            "/demo/hr/login",
            data={
                "email": "camille.cactus@example.test",
                "password": "Cactus!2026",
                "portal_code": "CACTUS-42",
            },
            follow_redirects=False,
        )
        self.assertEqual(303, authenticated.status_code)
        self.assertEqual("/demo/hr/saisie", authenticated.headers["location"])

        form = self.client.get("/demo/hr/saisie")
        self.assertEqual(200, form.status_code)
        self.assertIn('name="manager_budget"', form.text)
        self.assertNotIn('name="favorite_color"', form.text)
        self.assertIn("dynamic-employee-fields", form.text)

        created = self.client.post(
            "/demo/hr/saisie",
            data={
                "employee_number": "EMP-NEB-042",
                "first_name": "Zoé",
                "last_name": "Nébuleuse",
                "work_email": "zoe.nebuleuse@example.test",
                "hire_date": "2026-09-01",
                "department": "Recrutement de licornes",
                "contract_type": "CDI intersidéral",
                "animal_totem": "Poulpe comptable",
                "favorite_color": "#ff4fd8",
                "energy_level": "87",
                "remote_days": "3",
                "skills": "Python, négociation avec les dragons",
                "manager_budget": "42000",
                "manager_comment": "Installer un hamac ergonomique homologué.",
            },
            follow_redirects=False,
        )
        self.assertEqual(303, created.status_code)
        self.assertRegex(
            created.headers["location"],
            r"/demo/hr/consultation/RH-[A-F0-9]{8}",
        )

        consultation = self.client.get(created.headers["location"])
        self.assertEqual(200, consultation.status_code)
        for expected in (
            "Zoé Nébuleuse",
            "EMP-NEB-042",
            "zoe.nebuleuse@example.test",
            "Recrutement de licornes",
            "Poulpe comptable",
            "42000",
            "#ff4fd8",
            "87",
        ):
            self.assertIn(expected, consultation.text)

    def test_static_parser_sees_server_fields_but_not_javascript_fields(self) -> None:
        login_html = self.client.get("/demo/hr/login").text
        login_page = analyze_html_page(
            "http://127.0.0.1:8000/demo/hr/login",
            login_html,
        )
        login_references = {element.reference for element in login_page.elements}
        self.assertIn("page:login#email", login_references)
        self.assertIn("page:login#password", login_references)
        self.assertNotIn("page:login#portal-code", login_references)

        manager_html = self.client.get(
            "/demo/hr/parser/saisie/manager-cactus"
        ).text
        manager_page = analyze_html_page(
            "http://127.0.0.1:8000/demo/hr/parser/saisie/manager-cactus",
            manager_html,
        )
        names = {element.reference for element in manager_page.elements}
        self.assertIn(
            "page:manager-cactus#manager-budget",
            names,
        )
        self.assertIn(
            "page:manager-cactus#animal-totem",
            names,
        )
        self.assertNotIn(
            "page:manager-cactus#favorite-color",
            names,
        )

        agent_html = self.client.get(
            "/demo/hr/parser/saisie/agent-lama"
        ).text
        self.assertNotIn('name="manager_budget"', agent_html)


if __name__ == "__main__":
    unittest.main()
