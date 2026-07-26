"""ACC-063 à ACC-065 — spécifications fonctionnelles et organisations."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sentinelle_fonctionnelle.application import ProjectApplication
from sentinelle_fonctionnelle.domain import (
    HierarchyError,
    NodeKind,
    OrganizationView,
    SpecificationStyle,
)


class FunctionalSpecificationAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.application = ProjectApplication.in_memory("local")
        self.project = self.application.create_project(
            None,
            name="Spécifications",
            description="Plusieurs modes de rédaction",
            web_target="https://specifications.demo.invalid",
            security_policy="demo-only",
        )
        self.test_plan = self.application.create_test_plan(
            None,
            project_id=self.project.id,
            name="Parcours métier",
            objective="Comparer les formes de spécification",
            scope="Parcours métier critiques",
            approach="Spécification fonctionnelle guidée",
            test_type="acceptance",
            target="demo",
        )
        self.suite = self.application.add_node(
            None,
            project_id=self.project.id,
            test_set_id=self.test_plan.id,
            kind=NodeKind.SUITE,
            name="Parcours critiques",
            objective="Regrouper les cas fonctionnels critiques",
        )

    def test_four_business_friendly_styles_share_one_canonical_model(self) -> None:
        cases = (
            (
                SpecificationStyle.STEPS,
                "Saisir un identifiant => Le champ contient l’identifiant\n"
                "Valider le formulaire => Le tableau de bord est affiché",
                2,
                0,
            ),
            (
                SpecificationStyle.GHERKIN,
                "Étant donné un client actif\n"
                "Quand il valide ses identifiants\n"
                "Alors son tableau de bord est affiché",
                3,
                0,
            ),
            (
                SpecificationStyle.EXAMPLES,
                "profil ; statut ; résultat\n"
                "client ; actif ; accès autorisé\n"
                "client ; bloqué ; accès refusé",
                0,
                2,
            ),
            (
                SpecificationStyle.CHECKLIST,
                "Le titre de la page est affiché\n"
                "Le bouton de déconnexion est visible",
                2,
                0,
            ),
        )

        for index, (style, source, clause_count, example_count) in enumerate(cases):
            with self.subTest(style=style):
                test = self.application.add_node(
                    None,
                    project_id=self.project.id,
                    test_set_id=self.test_plan.id,
                    kind=NodeKind.TEST,
                    name=f"Cas {index + 1}",
                    parent_id=self.suite.id,
                    tags=("critique", style.value),
                )
                specification = self.application.define_test(
                    None,
                    project_id=self.project.id,
                    test_set_id=self.test_plan.id,
                    test_id=test.id,
                    style=style,
                    objective="Vérifier un résultat métier observable",
                    actor_name="Client authentifié",
                    source_text=source,
                    environment="recette",
                    preconditions=("Le compte existe",),
                    data_sets=("client-standard",),
                    postconditions=("La session est fermée",),
                    requirements=("REQ-AUTH-01",),
                    business_rules=("BR-SEC-02",),
                    execution_declaration=("on_merge_request",),
                )
                self.assertEqual(style, specification.style)
                self.assertEqual(1, specification.version)
                self.assertEqual(clause_count, len(specification.clauses))
                self.assertEqual(example_count, len(specification.example_rows))
                self.assertEqual(("REQ-AUTH-01",), specification.requirements)
                self.assertNotIn("yaml", specification.source_text.lower())

    def test_invalid_content_is_rejected_for_each_style(self) -> None:
        invalid_cases = (
            (SpecificationStyle.STEPS, "Cliquer sans résultat"),
            (
                SpecificationStyle.GHERKIN,
                "Étant donné un client\nQuand il se connecte",
            ),
            (
                SpecificationStyle.EXAMPLES,
                "profil ; résultat\nclient\nadministrateur ; autorisé",
            ),
            (SpecificationStyle.CHECKLIST, "  \n"),
        )
        for style, source in invalid_cases:
            with self.subTest(style=style):
                node = self.application.add_node(
                    None,
                    project_id=self.project.id,
                    test_set_id=self.test_plan.id,
                    kind=NodeKind.TEST,
                    name=f"Invalide {style.value}",
                    parent_id=self.suite.id,
                )
                with self.assertRaises(HierarchyError):
                    self.application.define_test(
                        None,
                        project_id=self.project.id,
                        test_set_id=self.test_plan.id,
                        test_id=node.id,
                        style=style,
                        objective="Vérifier le refus",
                        actor_name="Utilisateur",
                        source_text=source,
                    )

    def test_versions_persist_and_views_do_not_change_tree_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "sentinel.db"
            first = ProjectApplication.sqlite(database)
            project = first.create_project(
                None,
                name="Organisation",
                description="Vues calculées",
                web_target="https://organisation.demo.invalid",
                security_policy="demo-only",
            )
            test_set = first.create_test_set(
                None,
                project_id=project.id,
                name="Paiement",
                objective="Organiser les tests",
                test_type="regression",
                target="recette",
            )
            suite = first.add_node(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                kind=NodeKind.SUITE,
                name="Carte bancaire",
                objective="Vérifier les paiements par carte",
            )
            test = first.add_node(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                kind=NodeKind.TEST,
                name="Paiement accepté",
                parent_id=suite.id,
                tags=("paiement", "critique"),
            )
            common = dict(
                actor=None,
                project_id=project.id,
                test_set_id=test_set.id,
                test_id=test.id,
                style=SpecificationStyle.STEPS,
                objective="Autoriser une carte valide",
                actor_name="Client",
                environment="recette",
                preconditions=("Le panier contient un produit",),
                data_sets=("carte-valide",),
                postconditions=("La commande est créée",),
                requirements=("REQ-PAY-01",),
                business_rules=("BR-PAY-VALID",),
                execution_declaration=("on_commit", "nightly"),
            )
            first.define_test(
                **common,
                source_text=(
                    "Saisir une carte valide => La carte est acceptée\n"
                    "Confirmer => La commande est créée"
                ),
            )
            updated = first.define_test(
                **common,
                source_text=(
                    "Saisir une carte valide => La carte est acceptée\n"
                    "Confirmer le paiement => La commande est créée"
                ),
            )
            self.assertEqual(2, updated.version)

            restarted = ProjectApplication.sqlite(database)
            restored_project = restarted.get_project(None, project.id)
            restored_set = restored_project.test_set(test_set.id)
            restored_test = restored_set.node(test.id)
            self.assertEqual(test.id, restored_test.id)
            self.assertEqual(suite.id, restored_test.parent_id)
            self.assertEqual(2, restored_test.specification.version)
            self.assertIn("Confirmer le paiement", restored_test.specification.source_text)

            views = {
                OrganizationView.TAG: "paiement",
                OrganizationView.REQUIREMENT: "REQ-PAY-01",
                OrganizationView.BUSINESS_RULE: "BR-PAY-VALID",
                OrganizationView.STYLE: "Pas-à-pas",
            }
            for view, expected_group in views.items():
                with self.subTest(view=view):
                    groups = restored_set.organize_tests(view)
                    group = next(item for item in groups if item.label == expected_group)
                    self.assertEqual((test.id,), tuple(node.id for node in group.tests))
                    self.assertEqual(suite.id, restored_test.parent_id)

            search = restored_set.organize_tests(
                OrganizationView.TREE,
                query="commande",
            )
            self.assertEqual((test.id,), tuple(node.id for node in search[0].tests))


if __name__ == "__main__":
    unittest.main()
