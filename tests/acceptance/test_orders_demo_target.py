"""Cible commandes multi-écrans et projet de conception associé."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.adapters.page_analysis import analyze_html_page
from sentinelle_fonctionnelle.application import seed_orders_demo_project
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.orders_demo import reset_orders_demo
from sentinelle_fonctionnelle.web.settings import ServerSettings


class OrdersDemoTargetAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_orders_demo()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.app = create_web_app(
            ServerSettings(
                database=Path(self.temporary_directory.name) / "sentinelle.db"
            )
        )
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def test_order_crosses_four_screens_and_calculates_read_only_tables(self) -> None:
        client_page = self.client.get("/demo/commandes/client")
        self.assertEqual(200, client_page.status_code)
        self.assertIn("Identifier le demandeur", client_page.text)
        self.assertIn('name="customer_type"', client_page.text)
        self.assertIn(
            'href="https://github.com/pessonnier/sentinelle-fonctionnelle"',
            client_page.text,
        )

        client_saved = self.client.post(
            "/demo/commandes/client",
            data={
                "customer_name": "Ada Martin",
                "email": "ada.martin@example.test",
                "customer_type": "Entreprise",
                "requested_date": "2026-11-15",
                "priority": "Haute",
                "notes": "Livrer à l’accueil.",
            },
            follow_redirects=False,
        )
        self.assertEqual(303, client_saved.status_code)
        items_url = client_saved.headers["location"]

        items_page = self.client.get(items_url)
        self.assertIn("Composer la commande", items_page.text)
        self.assertIn("product-table", items_page.text)
        selected = self.client.post(
            items_url,
            data={
                "quantity_CLAV-01": "2",
                "quantity_ECR-27": "0",
                "quantity_SUP-USB": "1",
                "quantity_CAS-RED": "0",
                "delivery_mode": "standard",
                "discount_code": "DEMO10",
                "gift_wrap": "yes",
            },
            follow_redirects=False,
        )
        self.assertEqual(303, selected.status_code)

        review_url = selected.headers["location"]
        review = self.client.get(review_url)
        self.assertIn("Vérifier le récapitulatif", review.text)
        self.assertIn("287.12 €", review.text)
        self.assertIn("25.43 €", review.text)
        confirmed = self.client.post(
            review_url,
            data={"payment_method": "invoice", "terms": "accepted"},
            follow_redirects=False,
        )
        self.assertEqual(303, confirmed.status_code)

        tracking = self.client.get(confirmed.headers["location"])
        self.assertIn("Confirmée", tracking.text)
        self.assertIn("Ada Martin", tracking.text)
        self.assertIn("Clavier mécanique azur", tracking.text)
        self.assertIn("Station USB-C", tracking.text)
        listing = self.client.get("/demo/commandes/liste")
        self.assertIn("Ada Martin", listing.text)
        self.assertIn("287.12 €", listing.text)

    def test_static_pages_expose_selects_tables_and_read_values_to_analyzer(
        self,
    ) -> None:
        items_html = self.client.get("/demo/commandes/parser/articles").text
        items = analyze_html_page(
            "http://127.0.0.1:8000/demo/commandes/parser/articles",
            items_html,
        )
        references = {element.reference for element in items.elements}
        self.assertIn("page:articles#quantity-clav-01", references)
        self.assertIn("page:articles#delivery-mode", references)
        self.assertIn("page:articles#gift-wrap", references)

        review_html = self.client.get("/demo/commandes/parser/recapitulatif").text
        self.assertIn("287.12 €", review_html)
        self.assertIn("<table", review_html)
        tracking_html = self.client.get("/demo/commandes/parser/suivi").text
        self.assertIn("tracking-table", tracking_html)
        self.assertIn("Confirmée", tracking_html)

    def test_seeded_project_contains_a_confirmed_multi_screen_workflow(self) -> None:
        seeded = seed_orders_demo_project(self.app.state.project_application)
        project = self.app.state.project_application.get_project(
            None, seeded.project_id
        )
        case = project.test_plan(seeded.plan_id).node(seeded.case_id)
        self.assertIsNotNone(case.specification)
        workflow = case.specification.workflow
        self.assertTrue(workflow.confirmed)
        self.assertEqual(4, len(workflow.pages))
        self.assertGreaterEqual(len(workflow.steps), 18)
        self.assertEqual("count", workflow.steps[-1].assertion.value)


if __name__ == "__main__":
    unittest.main()
