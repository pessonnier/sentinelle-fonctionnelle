"""Runner autonome du bundle approuvé, sans accès au service de conception."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

from .bundle_export import BUNDLE_FORMAT_VERSION, safe_bundle_path


class BundleRunnerError(RuntimeError):
    """Le précontrôle du bundle ou de l'environnement a échoué."""


@dataclass(frozen=True, slots=True)
class BundleRunReport:
    execution_id: str
    status: str
    exit_code: int
    duration_seconds: float
    bundle_sha256: str
    declaration: str
    artifact_directory: str
    checks: tuple[Mapping[str, str], ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "bundle_sha256": self.bundle_sha256,
            "declaration": self.declaration,
            "artifact_directory": self.artifact_directory,
            "checks": list(self.checks),
        }


def validate_bundle(
    bundle_directory: Path,
) -> tuple[Mapping[str, Any], tuple[Mapping[str, str], ...]]:
    root = bundle_directory.resolve()
    manifest_path = root / "sentinelle-manifest.json"
    if not manifest_path.is_file():
        raise BundleRunnerError("Le manifeste sentinelle-manifest.json est absent.")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BundleRunnerError("Le manifeste du bundle est illisible.") from error
    if manifest.get("format") != "sentinelle-functional-bundle":
        raise BundleRunnerError("Le format du bundle est inconnu.")
    if manifest.get("format_version") != BUNDLE_FORMAT_VERSION:
        raise BundleRunnerError("La version du format de bundle est incompatible.")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise BundleRunnerError("Le manifeste ne contient aucun fichier vérifiable.")
    expected_paths: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            raise BundleRunnerError("Un enregistrement de fichier est invalide.")
        raw_path = str(record.get("path", ""))
        relative = safe_bundle_path(raw_path)
        path = (root / Path(*relative.parts)).resolve()
        if root not in path.parents or not path.is_file() or path.is_symlink():
            raise BundleRunnerError(f"Fichier absent ou interdit : {raw_path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != record.get("sha256"):
            raise BundleRunnerError(f"Empreinte différente pour {raw_path}.")
        if raw_path in expected_paths:
            raise BundleRunnerError(f"Chemin dupliqué dans le manifeste : {raw_path}")
        expected_paths.add(raw_path)
        normalized.append(
            {"path": raw_path, "sha256": digest, "size": path.stat().st_size}
        )
    actual_paths = {
        item.relative_to(root).as_posix()
        for item in root.rglob("*")
        if item.is_file() and item != manifest_path
    }
    unknown = sorted(actual_paths - expected_paths)
    if unknown:
        raise BundleRunnerError(
            "Fichiers non déclarés dans le bundle : " + ", ".join(unknown)
        )
    canonical = json.dumps(
        {"files": sorted(normalized, key=lambda item: item["path"])},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    bundle_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if bundle_sha256 != manifest.get("bundle_sha256"):
        raise BundleRunnerError("L'empreinte globale du bundle est différente.")
    return manifest, (
        {"name": "manifest", "status": "passed"},
        {"name": "file_hashes", "status": "passed"},
        {"name": "bundle_hash", "status": "passed"},
    )


def run_bundle(
    *,
    bundle_directory: Path,
    artifact_directory: Path,
    base_url: str,
    declaration: str = "manual",
    allowed_origins: Sequence[str] = (),
    timeout_seconds: int = 300,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> BundleRunReport:
    """Vérifie puis exécute la sélection sans écrire dans le bundle."""

    bundle = bundle_directory.resolve()
    artifacts = artifact_directory.resolve()
    if (
        artifacts == bundle
        or bundle in artifacts.parents
        or artifacts in bundle.parents
    ):
        raise BundleRunnerError("Le répertoire d'artefacts doit être séparé du bundle.")
    if timeout_seconds < 1 or timeout_seconds > 3600:
        raise BundleRunnerError("Le délai global doit être compris entre 1 et 3600 s.")
    manifest, checks = validate_bundle(bundle)
    origin = _validate_target(base_url, allowed_origins)
    cases = manifest.get("cases", [])
    selected = [
        case
        for case in cases
        if declaration in case.get("declarations", [])
        and case.get("status") == "approved"
    ]
    if not selected:
        raise BundleRunnerError(
            f"Aucun cas approuvé ne correspond à la déclaration {declaration!r}."
        )
    test_paths = [
        str(bundle / Path(*safe_bundle_path(path).parts))
        for case in selected
        for path in case.get("source_paths", [])
    ]
    if not test_paths:
        raise BundleRunnerError("La sélection ne référence aucun script de test.")
    artifacts.mkdir(parents=True, exist_ok=True)
    execution_id = uuid4().hex
    started = datetime.now(timezone.utc)
    start_clock = monotonic()
    command = [
        sys.executable,
        "-m",
        "pytest",
        *test_paths,
        "-p",
        "no:cacheprovider",
        f"--output={artifacts / 'playwright'}",
        f"--junitxml={artifacts / 'junit.xml'}",
    ]
    environment = dict(os.environ)
    environment["TARGET_BASE_URL"] = base_url
    # Compatibilité des candidats MVP antérieurs au contrat TARGET_BASE_URL.
    environment["HR_DEMO_BASE_URL"] = base_url
    environment["SENTINELLE_FONCTIONNELLE_DECLARATION"] = declaration
    environment["SENTINELLE_FONCTIONNELLE_BUNDLE_SHA256"] = str(
        manifest["bundle_sha256"]
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        process = command_runner(
            command,
            cwd=bundle,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = int(process.returncode)
        stdout = process.stdout or ""
        stderr = process.stderr or ""
    except subprocess.TimeoutExpired as error:
        exit_code = 124
        stdout = str(error.stdout or "")
        stderr = "Délai global dépassé."
    duration = monotonic() - start_clock
    status = "passed" if exit_code == 0 else "failed"
    (artifacts / "stdout.log").write_text(stdout, encoding="utf-8")
    (artifacts / "stderr.log").write_text(stderr, encoding="utf-8")
    report = BundleRunReport(
        execution_id=execution_id,
        status=status,
        exit_code=exit_code,
        duration_seconds=duration,
        bundle_sha256=str(manifest["bundle_sha256"]),
        declaration=declaration,
        artifact_directory=str(artifacts),
        checks=checks
        + (
            {"name": "target_origin", "status": "passed", "detail": origin},
            {"name": "llm_execution", "status": "forbidden"},
        ),
    )
    document = {
        **report.as_dict(),
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "selected_case_ids": [str(case["id"]) for case in selected],
        "command": [
            "python",
            "-m",
            "pytest",
            "<approved-tests>",
            "--junitxml=<artifact>",
        ],
    }
    (artifacts / "execution.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _validate_target(base_url: str, allowed_origins: Sequence[str]) -> str:
    target = urlsplit(base_url)
    if (
        target.scheme not in {"http", "https"}
        or not target.hostname
        or target.path not in {"", "/"}
    ):
        raise BundleRunnerError("La cible doit être une origine HTTP(S) sans chemin.")
    origin = f"{target.scheme}://{target.netloc}"
    normalized_allowed = {value.rstrip("/") for value in allowed_origins}
    if origin not in normalized_allowed:
        raise BundleRunnerError(
            "La cible n'appartient pas aux origines explicitement autorisées."
        )
    return origin
