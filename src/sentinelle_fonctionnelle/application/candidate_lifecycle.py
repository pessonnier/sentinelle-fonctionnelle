"""Cas d'usage du cycle génération, validation et décision humaine."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID, uuid4

from sentinelle_fonctionnelle.domain import (
    CandidateComparison,
    CandidateError,
    CandidateExecution,
    CandidateFile,
    CandidateOrigin,
    CandidateStatus,
    TestCandidate,
)

from .execution_runner import ExecutionReport, run_generated_playwright
from .code_customization import (
    CodeCustomizationError,
    merge_customized_source,
    protected_regions,
    validate_customized_source,
)


class CandidateRepository(Protocol):
    def add_candidate(self, **values: Any) -> TestCandidate: ...

    def list_candidates(
        self, project_id: UUID, test_plan_id: UUID, case_id: UUID
    ) -> tuple[TestCandidate, ...]: ...

    def get_candidate(self, candidate_id: UUID) -> TestCandidate | None: ...

    def set_candidate_status(
        self,
        candidate_id: UUID,
        status: CandidateStatus,
        *,
        occurred_at: datetime,
        reason: str,
    ) -> None: ...

    def add_candidate_execution(
        self, candidate_id: UUID, execution: CandidateExecution
    ) -> None: ...

    def invalidate_case_candidates(
        self,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        *,
        specification_version: int,
        occurred_at: datetime,
    ) -> int: ...


class CandidateLifecycleApplication:
    """Orchestre sans coupler le domaine à SQLite, FastAPI ou pytest."""

    def __init__(
        self,
        repository: CandidateRepository,
        *,
        root_directory: Path,
    ) -> None:
        self._repository = repository
        self.root_directory = root_directory.resolve()

    @staticmethod
    def specification_fingerprint(
        *, specification_version: int, workflow: Mapping[str, Any]
    ) -> str:
        return _json_sha256(
            {"specification_version": specification_version, "workflow": workflow}
        )

    def create(
        self,
        *,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        origin: CandidateOrigin,
        specification_version: int,
        specification_sha256: str,
        files: tuple[tuple[str, str], ...],
        manifest: Mapping[str, Any],
        prompt_sha256: str = "",
        now: datetime | None = None,
    ) -> TestCandidate:
        candidate_files = tuple(
            CandidateFile(
                path=path,
                content=content,
                sha256=_file_sha256(content),
            )
            for path, content in files
        )
        if not candidate_files:
            raise CandidateError("La génération n'a produit aucun fichier.")
        manifest_document = dict(manifest)
        manifest_document.setdefault("schema_version", 1)
        manifest_document["files"] = [
            {"path": item.path, "sha256": item.sha256} for item in candidate_files
        ]
        if len(candidate_files) == 1:
            manifest_document["source_sha256"] = candidate_files[0].sha256
        manifest_document.setdefault(
            "bundle_layout",
            [
                "tests/cases",
                "tests/pages",
                "tests/fixtures",
                "test-data",
                "generation",
                "config",
            ],
        )
        candidate_sha256 = _json_sha256(
            {
                "specification_sha256": specification_sha256,
                "files": [
                    {"path": item.path, "sha256": item.sha256}
                    for item in candidate_files
                ],
                "manifest": manifest_document,
            }
        )
        manifest_document["candidate_sha256"] = candidate_sha256
        return self._repository.add_candidate(
            candidate_id=uuid4(),
            project_id=project_id,
            test_plan_id=test_plan_id,
            case_id=case_id,
            origin=origin,
            created_at=now or datetime.now(timezone.utc),
            specification_version=specification_version,
            specification_sha256=specification_sha256,
            candidate_sha256=candidate_sha256,
            prompt_sha256=prompt_sha256,
            files=candidate_files,
            manifest=manifest_document,
        )

    def list_for_case(
        self,
        *,
        project_id: UUID,
        test_plan_id: UUID,
        case_id: UUID,
        specification_version: int | None = None,
    ) -> tuple[TestCandidate, ...]:
        if specification_version is not None:
            self._repository.invalidate_case_candidates(
                project_id,
                test_plan_id,
                case_id,
                specification_version=specification_version,
                occurred_at=datetime.now(timezone.utc),
            )
        return self._repository.list_candidates(project_id, test_plan_id, case_id)

    def get(self, candidate_id: UUID) -> TestCandidate:
        candidate = self._repository.get_candidate(candidate_id)
        if candidate is None:
            raise CandidateError("Le candidat demandé est introuvable.")
        return candidate

    def compare(
        self, current: TestCandidate, previous: TestCandidate | None
    ) -> CandidateComparison:
        current_files = {item.path: item.sha256 for item in current.files}
        previous_files = (
            {item.path: item.sha256 for item in previous.files} if previous else {}
        )
        return CandidateComparison(
            previous_id=previous.id if previous else None,
            current_id=current.id,
            added=tuple(sorted(current_files.keys() - previous_files.keys())),
            changed=tuple(
                sorted(
                    path
                    for path in current_files.keys() & previous_files.keys()
                    if current_files[path] != previous_files[path]
                )
            ),
            removed=tuple(sorted(previous_files.keys() - current_files.keys())),
        )

    def customize(
        self,
        candidate_id: UUID,
        *,
        path: str,
        content: str,
        now: datetime | None = None,
    ) -> TestCandidate:
        """Crée un nouveau candidat si seules les zones protégées ont changé."""

        base = self.get(candidate_id)
        if base.status in {CandidateStatus.REJECTED, CandidateStatus.INVALIDATED}:
            raise CandidateError(
                "Un candidat rejeté ou invalidé ne peut pas servir de base."
            )
        if len(content.encode("utf-8")) > 1_048_576:
            raise CandidateError("Le fichier personnalisé dépasse la limite de 1 Mio.")
        base_by_path = {item.path: item for item in base.files}
        base_file = base_by_path.get(path)
        if base_file is None:
            raise CandidateError(
                "Le fichier personnalisé n'appartient pas au candidat."
            )
        try:
            changed_regions = validate_customized_source(base_file.content, content)
        except CodeCustomizationError as error:
            raise CandidateError(str(error)) from error
        if path.endswith(".py"):
            try:
                compile(content, path, "exec")
            except SyntaxError as error:
                raise CandidateError(
                    f"Le fichier Python personnalisé est invalide : {error.msg} "
                    f"(ligne {error.lineno})."
                ) from error

        previous_customization = base.manifest.get("customization", {})
        previous_files = (
            previous_customization.get("files", {})
            if isinstance(previous_customization, Mapping)
            else {}
        )
        previous_region_names: set[str] = set()
        previous_file = (
            previous_files.get(path, {}) if isinstance(previous_files, Mapping) else {}
        )
        if isinstance(previous_file, Mapping):
            for item in previous_file.get("regions", ()):
                if isinstance(item, Mapping) and item.get("name"):
                    previous_region_names.add(str(item["name"]))
        region_names = previous_region_names | {
            region.name for region in changed_regions
        }
        customized_regions = {
            region.name: region for region in protected_regions(content)
        }
        files = tuple(
            (item.path, content if item.path == path else item.content)
            for item in base.files
        )
        manifest = dict(base.manifest)
        for stale_key in ("candidate_sha256", "source_sha256"):
            manifest.pop(stale_key, None)
        manifest["files"] = [
            {"path": file_path, "sha256": _file_sha256(file_content)}
            for file_path, file_content in files
        ]
        manifest.pop("customization_conflicts", None)
        customization_files = (
            {str(key): dict(value) for key, value in previous_files.items()}
            if isinstance(previous_files, Mapping)
            and all(isinstance(value, Mapping) for value in previous_files.values())
            else {}
        )
        customization_files[path] = {
            "regions": [
                {
                    "name": name,
                    "contract": customized_regions[name].contract,
                    "sha256": customized_regions[name].sha256,
                }
                for name in sorted(region_names)
            ]
        }
        manifest["customization"] = {
            "source_candidate_id": str(base.id),
            "files": customization_files,
        }
        return self.create(
            project_id=base.project_id,
            test_plan_id=base.test_plan_id,
            case_id=base.case_id,
            origin=base.origin,
            specification_version=base.specification_version,
            specification_sha256=base.specification_sha256,
            files=files,
            manifest=manifest,
            prompt_sha256=base.prompt_sha256,
            now=now,
        )

    def reapply_customizations(
        self,
        source_candidate: TestCandidate,
        generated_files: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[tuple[str, str], ...], dict[str, Any]]:
        """Fusionne les zones humaines compatibles dans une nouvelle génération."""

        customization = source_candidate.manifest.get("customization")
        if not isinstance(customization, Mapping):
            raise CandidateError(
                "Le candidat sélectionné ne contient aucune personnalisation."
            )
        customization_files = customization.get("files")
        if not isinstance(customization_files, Mapping):
            raise CandidateError("Le manifeste de personnalisation est invalide.")
        source_by_path = {item.path: item.content for item in source_candidate.files}
        generated_by_path = dict(generated_files)
        applied: list[str] = []
        conflicts: list[str] = []
        for path, metadata in customization_files.items():
            path = str(path)
            if path not in source_by_path:
                conflicts.append(f"{path}: fichier personnalisé absent")
                continue
            if path not in generated_by_path:
                conflicts.append(f"{path}: fichier absent de la nouvelle génération")
                continue
            region_names: tuple[str, ...] = ()
            if isinstance(metadata, Mapping):
                region_names = tuple(
                    str(item.get("name"))
                    for item in metadata.get("regions", ())
                    if isinstance(item, Mapping) and item.get("name")
                )
            if not region_names:
                conflicts.append(f"{path}: aucune zone déclarée dans le manifeste")
                continue
            try:
                merge = merge_customized_source(
                    generated_by_path[path],
                    source_by_path[path],
                    region_names=region_names,
                )
            except CodeCustomizationError as error:
                conflicts.append(f"{path}: {error}")
                continue
            generated_by_path[path] = merge.content
            applied.extend(f"{path}#{name}" for name in merge.applied)
            conflicts.extend(f"{path}#{detail}" for detail in merge.conflicts)
        merged_files = tuple(
            (path, generated_by_path[path]) for path, _ in generated_files
        )
        return merged_files, {
            "source_candidate_id": str(source_candidate.id),
            "applied": applied,
            "conflicts": conflicts,
        }

    def execute(
        self,
        candidate_id: UUID,
        *,
        base_url: str,
        browser: str = "chromium",
        command_runner: Any = None,
    ) -> tuple[TestCandidate, ExecutionReport]:
        candidate = self.get(candidate_id)
        if candidate.status in {CandidateStatus.REJECTED, CandidateStatus.INVALIDATED}:
            raise CandidateError(
                "Un candidat rejeté ou invalidé doit être régénéré avant exécution."
            )
        conflicts = candidate.manifest.get("customization_conflicts", ())
        if conflicts:
            raise CandidateError(
                "Les conflits de personnalisation doivent être résolus avant exécution."
            )
        python_files = [item for item in candidate.files if item.path.endswith(".py")]
        if len(python_files) != 1:
            raise CandidateError(
                "La validation locale exige exactement un fichier de test Python."
            )
        source = python_files[0]
        generated_root = self.root_directory / "tests" / "generated"
        test_path = generated_root / f"candidate_{candidate.id.hex}.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(source.content, encoding="utf-8", newline="\n")
        runner_manifest = dict(candidate.manifest)
        runner_manifest["source_sha256"] = source.sha256
        materialized_manifest = test_path.with_suffix(".manifest.json")
        materialized_manifest.write_text(
            json.dumps(runner_manifest, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        execution_directory = (
            self.root_directory
            / "outputs"
            / "candidate-validations"
            / candidate.id.hex
            / uuid4().hex
        )
        try:
            report = run_generated_playwright(
                test_path=test_path,
                base_url=base_url,
                output_directory=execution_directory,
                root_directory=self.root_directory,
                browser=browser,
                command_runner=command_runner,
            )
        finally:
            test_path.unlink(missing_ok=True)
            materialized_manifest.unlink(missing_ok=True)
        execution = CandidateExecution(
            execution_id=UUID(report.execution_id),
            occurred_at=datetime.fromisoformat(report.started_at),
            status=report.status,
            test_sha256=report.test_sha256,
            duration_seconds=report.duration_seconds,
            report=report.as_dict(),
        )
        self._repository.add_candidate_execution(candidate.id, execution)
        if candidate.status is CandidateStatus.APPROVED:
            return self.get(candidate.id), report
        next_status = (
            CandidateStatus.VALIDATED if execution.passed else CandidateStatus.PENDING
        )
        reason = (
            "Empreinte exécutée avec succès ; approbation humaine requise."
            if execution.passed
            else "La dernière validation individuelle a échoué."
        )
        self._repository.set_candidate_status(
            candidate.id,
            next_status,
            occurred_at=execution.occurred_at,
            reason=reason,
        )
        return self.get(candidate.id), report

    def decide(
        self,
        candidate_id: UUID,
        *,
        approved: bool,
        reason: str,
        now: datetime | None = None,
    ) -> TestCandidate:
        candidate = self.get(candidate_id)
        normalized_reason = " ".join(reason.split())
        if approved:
            if not candidate.can_be_approved:
                raise CandidateError(
                    "L'approbation exige une exécution individuelle réussie de cette empreinte."
                )
            status = CandidateStatus.APPROVED
            normalized_reason = normalized_reason or "Revue humaine approuvée."
        else:
            if candidate.status is CandidateStatus.APPROVED:
                raise CandidateError("Une version approuvée est immuable.")
            if not normalized_reason:
                raise CandidateError("Le motif de rejet est obligatoire.")
            status = CandidateStatus.REJECTED
        self._repository.set_candidate_status(
            candidate.id,
            status,
            occurred_at=now or datetime.now(timezone.utc),
            reason=normalized_reason,
        )
        return self.get(candidate.id)


def _json_sha256(value: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _file_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
