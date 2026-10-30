from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess
from uuid import uuid4
from zipfile import ZipFile

import pytest

from sentinelle_fonctionnelle.application import (
    ApplicationMode,
    AuthenticatedIdentity,
    BundleExportError,
    BundleRunnerError,
    ConcurrentProjectUpdate,
    ProjectApplication,
    apply_artifact_retention,
    export_approved_candidate,
    run_bundle,
    validate_bundle,
)
from sentinelle_fonctionnelle.adapters.persistence.in_memory import (
    InMemoryProjectRepository,
)
from sentinelle_fonctionnelle.adapters.persistence.postgresql import (
    _project_document,
    _project_from_document,
)
from sentinelle_fonctionnelle.domain import (
    CandidateExecution,
    CandidateFile,
    CandidateOrigin,
    CandidateStatus,
    NodeKind,
    TestCandidate,
)


def approved_candidate() -> TestCandidate:
    source = (
        "def test_approved():\n"
        "    assert __import__('os').environ['TARGET_BASE_URL'].startswith('http')\n"
    )
    source_sha = hashlib.sha256(source.encode()).hexdigest()
    execution = CandidateExecution(
        execution_id=uuid4(),
        occurred_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        status="passed",
        test_sha256=source_sha,
        duration_seconds=0.1,
        report={},
    )
    return TestCandidate(
        id=uuid4(),
        project_id=uuid4(),
        test_plan_id=uuid4(),
        case_id=uuid4(),
        sequence=1,
        origin=CandidateOrigin.DETERMINISTIC,
        created_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        specification_version=2,
        specification_sha256="a" * 64,
        candidate_sha256="b" * 64,
        prompt_sha256="",
        files=(
            CandidateFile(
                path="tests/cases/test_approved.py",
                content=source,
                sha256=source_sha,
            ),
        ),
        manifest={
            "test_type": "acceptance",
            "tags": ["smoke"],
            "ci_declaration": ["manual", "on_merge_request"],
        },
        status=CandidateStatus.APPROVED,
        decision_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
        decision_reason="Revue humaine.",
        executions=(execution,),
    )


def test_export_is_reproducible_complete_and_approved_only(tmp_path: Path) -> None:
    candidate = approved_candidate()
    first = export_approved_candidate(
        candidate,
        project_name="Portail RH",
        plan_name="Non-régression",
        case_name="Connexion",
        specification={"objective": "Vérifier la connexion"},
    )
    second = export_approved_candidate(
        candidate,
        project_name="Portail RH",
        plan_name="Non-régression",
        case_name="Connexion",
        specification={"objective": "Vérifier la connexion"},
    )
    assert first.content == second.content
    archive_path = tmp_path / "bundle.zip"
    archive_path.write_bytes(first.content)
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert "sentinelle-manifest.json" in names
        assert "docs/functional.md" in names
        assert "docs/deploy-github-actions.md" in names
        assert "docs/deploy-gitlab-ci.md" in names
        assert "ci/github-actions.yml" in names
        assert "ci/gitlab-ci.yml" in names
        assert b"--allow-origin" in archive.read("ci/github-actions.yml")
        assert b"--allow-origin" in archive.read("ci/gitlab-ci.yml")
        archive.extractall(tmp_path / "bundle")
    manifest, checks = validate_bundle(tmp_path / "bundle")
    assert manifest["bundle_sha256"] == first.sha256
    assert len(checks) == 3

    with pytest.raises(BundleExportError, match="approuvé"):
        export_approved_candidate(
            replace(candidate, status=CandidateStatus.VALIDATED),
            project_name="Portail RH",
            plan_name="Non-régression",
            case_name="Connexion",
        )


def test_runner_refuses_tampering_and_writes_only_to_artifacts(
    tmp_path: Path,
) -> None:
    artifact = export_approved_candidate(
        approved_candidate(),
        project_name="Projet",
        plan_name="Plan",
        case_name="Cas",
    )
    zip_path = tmp_path / "bundle.zip"
    zip_path.write_bytes(artifact.content)
    bundle = tmp_path / "bundle"
    with ZipFile(zip_path) as archive:
        archive.extractall(bundle)

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "1 passed", "")

    report = run_bundle(
        bundle_directory=bundle,
        artifact_directory=tmp_path / "artifacts",
        base_url="http://target:8080",
        allowed_origins=("http://target:8080",),
        command_runner=fake_run,
    )
    assert report.exit_code == 0
    assert (tmp_path / "artifacts" / "execution.json").is_file()
    assert calls[0][1]["cwd"] == bundle.resolve()
    assert not any(path.name == "execution.json" for path in bundle.rglob("*"))

    test_file = bundle / "tests" / "cases" / "test_approved.py"
    test_file.write_text("def test_changed(): assert True\n", encoding="utf-8")
    with pytest.raises(BundleRunnerError, match="Empreinte différente"):
        validate_bundle(bundle)


def test_online_roles_and_optimistic_revision_prevent_stale_overwrite() -> None:
    repository = InMemoryProjectRepository()
    application = ProjectApplication(
        mode=ApplicationMode.ONLINE,
        repository=repository,
    )
    owner = AuthenticatedIdentity("owner@example.test")
    project = application.create_project(
        owner,
        name="Projet",
        description="Initial",
        web_target="https://example.test",
        security_policy="Restreinte",
    )
    revision = application.project_revision(owner, project.id)
    application.update_project(
        owner,
        project_id=project.id,
        name="Projet partagé",
        description="Version 2",
        web_target="https://example.test",
        security_policy="Restreinte",
        expected_revision=revision,
    )
    with pytest.raises(ConcurrentProjectUpdate, match="Révision attendue"):
        application.update_project(
            owner,
            project_id=project.id,
            name="Écrasement",
            description="Obsolète",
            web_target="https://example.test",
            security_policy="Restreinte",
            expected_revision=revision,
        )
    assert application.get_project(owner, project.id).name == "Projet partagé"


def test_retention_previews_then_removes_only_expired_execution(
    tmp_path: Path,
) -> None:
    old = tmp_path / "executions" / "old"
    recent = tmp_path / "executions" / "recent"
    old.mkdir(parents=True)
    recent.mkdir(parents=True)
    now = datetime(2026, 9, 8, tzinfo=timezone.utc)
    (old / "execution.json").write_text(
        '{"finished_at":"2026-06-01T00:00:00+00:00"}',
        encoding="utf-8",
    )
    (recent / "execution.json").write_text(
        '{"finished_at":"2026-09-07T00:00:00+00:00"}',
        encoding="utf-8",
    )
    preview = apply_artifact_retention(
        tmp_path, retention_days=30, now=now, apply=False
    )
    assert preview.expired == (str(old.resolve()),)
    assert old.exists()
    applied = apply_artifact_retention(tmp_path, retention_days=30, now=now, apply=True)
    assert applied.removed == (str(old.resolve()),)
    assert not old.exists()
    assert recent.exists()


def test_postgresql_document_codec_preserves_project_tree() -> None:
    application = ProjectApplication.in_memory(ApplicationMode.LOCAL)
    project = application.create_project(
        None,
        name="Projet",
        description="Partagé",
        web_target="https://example.test",
        security_policy="Restreinte",
    )
    plan = application.create_test_plan(
        None,
        project_id=project.id,
        name="Plan",
        objective="Vérifier",
        target="https://example.test",
        scope="Parcours critique",
        test_approach_id="functional-risk-based",
        test_approach_version=1,
    )
    suite = application.add_node(
        None,
        project_id=project.id,
        test_set_id=plan.id,
        kind=NodeKind.SUITE,
        name="Authentification",
        objective="Regrouper les cas de connexion",
    )
    test = application.add_node(
        None,
        project_id=project.id,
        test_set_id=plan.id,
        kind=NodeKind.TEST,
        name="Connexion",
        parent_id=suite.id,
    )
    restored = _project_from_document(_project_document(project))
    assert restored.id == project.id
    assert restored.test_plan(plan.id).node(test.id).name == "Connexion"


def test_oci_and_ci_profiles_enforce_the_minimum_isolation_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    compose = (root / "deployment" / "compose.runner.yml").read_text(encoding="utf-8")
    runner = (root / "deployment" / "runner.Dockerfile").read_text(encoding="utf-8")
    github = (root / "deployment" / "github-actions.yml").read_text(encoding="utf-8")
    gitlab = (root / "deployment" / "gitlab-ci.yml").read_text(encoding="utf-8")
    for required in (
        'user: "10001:10001"',
        "read_only: true",
        "cap_drop: [ALL]",
        "no-new-privileges:true",
        "pids_limit: 256",
        "mem_limit: 2g",
        "/bundle:ro",
        "/artifacts:rw",
        "internal: true",
    ):
        assert required in compose
    assert "USER 10001:10001" in runner
    assert "/var/run/docker.sock" not in compose
    assert "permissions:\n  contents: read" in github
    assert "secrets." not in github
    assert "artifacts/junit.xml" in gitlab
