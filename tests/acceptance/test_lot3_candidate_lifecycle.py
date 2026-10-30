"""Lot 3 — cycle de vie persistant du candidat et parcours web."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from subprocess import CompletedProcess
import tempfile
import unittest

from fastapi.testclient import TestClient

from sentinelle_fonctionnelle.adapters.persistence.sqlite import (
    SQLiteProjectRepository,
)
from sentinelle_fonctionnelle.application import (
    CandidateLifecycleApplication,
    seed_hr_demo_project,
)
from sentinelle_fonctionnelle.domain import (
    CandidateError,
    CandidateOrigin,
    CandidateStatus,
)
from sentinelle_fonctionnelle.web.app import create_web_app
from sentinelle_fonctionnelle.web.settings import ServerSettings


class CandidateLifecycleAcceptanceTests(unittest.TestCase):
    def _application(self, directory: Path) -> CandidateLifecycleApplication:
        repository = SQLiteProjectRepository(directory / "sentinelle.db")
        repository.migrate()
        return CandidateLifecycleApplication(repository, root_directory=directory)

    def _create(
        self,
        application: CandidateLifecycleApplication,
        *,
        content: str = "def test_candidate():\n    assert True\n",
        specification_version: int = 1,
    ):
        from uuid import UUID

        return application.create(
            project_id=UUID(int=1),
            test_plan_id=UUID(int=2),
            case_id=UUID(int=3),
            origin=CandidateOrigin.DETERMINISTIC,
            specification_version=specification_version,
            specification_sha256=f"spec-{specification_version}",
            files=(("tests/cases/test_candidate.py", content),),
            manifest={"generator": "acceptance-test", "generator_version": "1"},
            now=datetime(2026, 9, 8, 8, 0, tzinfo=timezone.utc),
        )

    def test_success_requires_a_separate_human_approval_and_survives_restart(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            directory = Path(raw_directory)
            application = self._application(directory)
            candidate = self._create(application)

            with self.assertRaisesRegex(CandidateError, "exécution individuelle"):
                application.decide(candidate.id, approved=True, reason="revue")

            def successful_runner(
                command: list[str],
                *,
                cwd: Path,
                env: dict[str, str],
                timeout: int,
            ) -> CompletedProcess[str]:
                del cwd, env, timeout
                junit = Path(command[command.index("--junitxml") + 1])
                junit.write_text('<testsuites tests="1" failures="0"/>', "utf-8")
                return CompletedProcess(command, 0, "1 passed", "")

            validated, report = application.execute(
                candidate.id,
                base_url="http://127.0.0.1:8765",
                command_runner=successful_runner,
            )
            self.assertEqual("passed", report.status)
            self.assertEqual(CandidateStatus.VALIDATED, validated.status)
            self.assertNotEqual(CandidateStatus.APPROVED, validated.status)
            self.assertEqual(candidate.files[0].sha256, report.test_sha256)
            self.assertFalse(
                (
                    directory
                    / "tests"
                    / "generated"
                    / f"candidate_{candidate.id.hex}.py"
                ).exists()
            )

            approved = application.decide(
                candidate.id,
                approved=True,
                reason="Parcours et preuves relus.",
            )
            self.assertEqual(CandidateStatus.APPROVED, approved.status)

            reloaded = self._application(directory).get(candidate.id)
            self.assertEqual(CandidateStatus.APPROVED, reloaded.status)
            self.assertEqual(1, len(reloaded.executions))
            self.assertEqual("passed", reloaded.executions[0].status)
            self.assertIn("artifact_directory", reloaded.executions[0].report)

    def test_regeneration_compares_files_and_invalidates_previous_validation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            application = self._application(Path(raw_directory))
            first = self._create(
                application, content="def test_a():\n    assert True\n"
            )
            application._repository.set_candidate_status(
                first.id,
                CandidateStatus.VALIDATED,
                occurred_at=datetime.now(timezone.utc),
                reason="validation de préparation",
            )

            second = self._create(
                application,
                content="def test_a():\n    assert 1 == 1\n",
            )
            history = application.list_for_case(
                project_id=second.project_id,
                test_plan_id=second.test_plan_id,
                case_id=second.case_id,
                specification_version=1,
            )
            comparison = application.compare(history[0], history[1])

            self.assertEqual(CandidateStatus.PENDING, history[0].status)
            self.assertEqual(CandidateStatus.INVALIDATED, history[1].status)
            self.assertEqual(("tests/cases/test_candidate.py",), comparison.changed)
            self.assertFalse(comparison.unchanged)

    def test_customization_rejects_changes_outside_zones_and_survives_regeneration(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            application = self._application(Path(raw_directory))
            generated = """from __future__ import annotations

def customize(page: object, data: dict[str, str]) -> None:
    # sentinelle:custom:start after_workflow contract=python-playwright-page-data-v1
    pass
    # sentinelle:custom:end after_workflow
"""
            base = self._create(application, content=generated)
            customized_source = generated.replace(
                "    pass\n",
                "    assert data.get('reference') == 'DEMO'\n",
            )
            customized = application.customize(
                base.id,
                path=base.files[0].path,
                content=customized_source,
            )

            self.assertEqual(CandidateOrigin.DETERMINISTIC, customized.origin)
            self.assertIn("assert data.get", customized.files[0].content)
            self.assertEqual(
                str(base.id),
                customized.manifest["customization"]["source_candidate_id"],
            )

            with self.assertRaisesRegex(CandidateError, "hors des zones"):
                application.customize(
                    base.id,
                    path=base.files[0].path,
                    content=customized_source.replace(
                        "from __future__ import annotations",
                        "from __future__ import annotations\nimport os",
                    ),
                )

            regenerated = generated.replace("def customize", "def customize")
            merged, report = application.reapply_customizations(
                customized,
                ((base.files[0].path, regenerated),),
            )
            self.assertEqual([], report["conflicts"])
            self.assertIn("assert data.get", merged[0][1])

            incompatible = regenerated.replace(
                "contract=python-playwright-page-data-v1",
                "contract=python-playwright-page-data-v2",
            )
            _, conflict_report = application.reapply_customizations(
                customized,
                ((base.files[0].path, incompatible),),
            )
            self.assertIn("devenu", conflict_report["conflicts"][0])

    def test_specification_change_invalidates_draft_but_keeps_approval_immutable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            application = self._application(Path(raw_directory))
            draft = self._create(application)
            approved = self._create(application, content="def test_b():\n    pass\n")
            application._repository.set_candidate_status(
                approved.id,
                CandidateStatus.APPROVED,
                occurred_at=datetime.now(timezone.utc),
                reason="approuvé",
            )

            history = application.list_for_case(
                project_id=draft.project_id,
                test_plan_id=draft.test_plan_id,
                case_id=draft.case_id,
                specification_version=2,
            )
            statuses = {item.id: item.status for item in history}

            self.assertEqual(CandidateStatus.INVALIDATED, statuses[draft.id])
            self.assertEqual(CandidateStatus.APPROVED, statuses[approved.id])
            with self.assertRaisesRegex(CandidateError, "immuable"):
                application.decide(approved.id, approved=False, reason="retour arrière")

    def test_case_page_generates_and_displays_persistent_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            app = create_web_app(
                ServerSettings(database=Path(raw_directory) / "sentinelle.db")
            )
            seeded = seed_hr_demo_project(
                app.state.project_application,
                root_directory=Path(__file__).resolve().parents[2],
            )
            case_url = (
                f"/projects/{seeded.project_id}/test-plans/{seeded.plan_id}"
                f"/cases/{seeded.nominal_case_id}"
            )

            with TestClient(app) as client:
                empty = client.get(case_url)
                self.assertIn("Aucun candidat enregistré", empty.text)
                created = client.post(f"{case_url}/candidates", follow_redirects=True)
                self.assertEqual(200, created.status_code, created.text)
                self.assertIn("Candidat #", created.text)
                self.assertIn("À valider", created.text)
                self.assertIn("Empreinte du bundle", created.text)
                self.assertIn("Voir le manifeste", created.text)
                persisted = client.get(case_url)
                self.assertIn("Générateur déterministe", persisted.text)

    def test_case_page_imports_and_reapplies_protected_customization(self) -> None:
        with tempfile.TemporaryDirectory() as raw_directory:
            app = create_web_app(
                ServerSettings(database=Path(raw_directory) / "sentinelle.db")
            )
            seeded = seed_hr_demo_project(
                app.state.project_application,
                root_directory=Path(__file__).resolve().parents[2],
            )
            case_url = (
                f"/projects/{seeded.project_id}/test-plans/{seeded.plan_id}"
                f"/cases/{seeded.nominal_case_id}"
            )
            with TestClient(app) as client:
                client.post(f"{case_url}/candidates")
                base = app.state.candidate_lifecycle.list_for_case(
                    project_id=seeded.project_id,
                    test_plan_id=seeded.plan_id,
                    case_id=seeded.nominal_case_id,
                )[0]
                customized_source = base.files[0].content.replace(
                    "    pass\n    # sentinelle:custom:end after_workflow",
                    "    assert data == data\n    # sentinelle:custom:end after_workflow",
                )
                imported = client.post(
                    f"{case_url}/candidates/{base.id}/customize",
                    files={
                        "source_file": (
                            "test_customized.py",
                            customized_source.encode("utf-8"),
                            "text/x-python",
                        )
                    },
                    follow_redirects=True,
                )
                self.assertEqual(200, imported.status_code, imported.text)
                self.assertIn("Personnalisation humaine protégée", imported.text)
                customized = app.state.candidate_lifecycle.list_for_case(
                    project_id=seeded.project_id,
                    test_plan_id=seeded.plan_id,
                    case_id=seeded.nominal_case_id,
                )[0]

                regenerated = client.post(
                    f"{case_url}/candidates",
                    data={"customization_source": str(customized.id)},
                    follow_redirects=True,
                )
                self.assertEqual(200, regenerated.status_code, regenerated.text)
                self.assertIn("Personnalisations réappliquées", regenerated.text)
                latest = app.state.candidate_lifecycle.list_for_case(
                    project_id=seeded.project_id,
                    test_plan_id=seeded.plan_id,
                    case_id=seeded.nominal_case_id,
                )[0]
                self.assertIn("assert data == data", latest.files[0].content)


if __name__ == "__main__":
    unittest.main()
