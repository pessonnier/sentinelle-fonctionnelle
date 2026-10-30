"""Validation locale bornée d’un test Playwright généré.

Cette verticale reste volontairement locale : elle ne remplace pas encore le
runner OCI isolé exigé pour la CI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4
from xml.etree import ElementTree


class ExecutionRunnerError(ValueError):
    """La validation locale ne peut pas démarrer dans un périmètre sûr."""


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    schema_version: int
    execution_id: str
    status: str
    exit_code: int
    started_at: str
    duration_seconds: float
    test_path: str
    test_sha256: str
    manifest_sha256: str
    browser: str
    base_url: str
    collected_case_count: int
    failed_case_count: int
    junit_path: str
    artifact_directory: str
    stdout_path: str
    stderr_path: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_generated_playwright(
    *,
    test_path: Path,
    base_url: str,
    output_directory: Path,
    root_directory: Path | None = None,
    browser: str = "chromium",
    timeout_seconds: int = 300,
    command_runner: CommandRunner | None = None,
) -> ExecutionReport:
    """Exécute pytest sans shell et conserve un rapport minimal vérifiable."""

    root = (root_directory or Path.cwd()).resolve()
    generated_root = (root / "tests" / "generated").resolve()
    resolved_test = test_path.resolve()
    if (
        resolved_test.suffix.casefold() != ".py"
        or resolved_test == generated_root
        or generated_root not in resolved_test.parents
    ):
        raise ExecutionRunnerError(
            "La validation locale accepte uniquement un fichier sous tests/generated."
        )
    if not resolved_test.is_file():
        raise ExecutionRunnerError("Le fichier de test généré est introuvable.")
    manifest_path = resolved_test.with_suffix(".manifest.json")
    if not manifest_path.is_file():
        raise ExecutionRunnerError(
            "Le manifeste d’intégrité du test généré est absent."
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExecutionRunnerError(
            "Le manifeste d’intégrité du test généré est illisible."
        ) from error
    actual_test_sha256 = _file_sha256(resolved_test)
    if (
        not isinstance(manifest, dict)
        or manifest.get("source_sha256") != actual_test_sha256
    ):
        raise ExecutionRunnerError(
            "L’empreinte du test ne correspond pas à son manifeste ; "
            "régénérez le candidat avant de l’exécuter."
        )
    resolved_output = output_directory.resolve()
    if resolved_output != root and root not in resolved_output.parents:
        raise ExecutionRunnerError(
            "Le répertoire d’artefacts doit rester dans le dépôt."
        )
    parsed_url = urlsplit(base_url)
    if (
        parsed_url.scheme != "http"
        or parsed_url.hostname not in {"127.0.0.1", "localhost", "::1"}
        or not parsed_url.port
    ):
        raise ExecutionRunnerError(
            "Cette première verticale limite la cible à la boucle locale HTTP "
            "avec un port explicite."
        )
    if browser not in {"chromium", "firefox", "webkit"}:
        raise ExecutionRunnerError("Le navigateur demandé est inconnu.")
    if not 1 <= timeout_seconds <= 3_600:
        raise ExecutionRunnerError(
            "Le délai d’exécution doit être compris entre 1 et 3 600 secondes."
        )

    resolved_output.mkdir(parents=True, exist_ok=True)
    playwright_output = resolved_output / "playwright"
    playwright_output.mkdir(parents=True, exist_ok=True)
    junit_path = resolved_output / "junit.xml"
    stdout_path = resolved_output / "stdout.log"
    stderr_path = resolved_output / "stderr.log"

    relative_test = resolved_test.relative_to(root).as_posix()
    command = [
        sys.executable,
        "-m",
        "pytest",
        relative_test,
        "-q",
        "--browser",
        browser,
        "--junitxml",
        str(junit_path),
        "--output",
        str(playwright_output),
        "--tracing",
        "retain-on-failure",
        "--screenshot",
        "only-on-failure",
    ]
    environment = dict(os.environ)
    environment["HR_DEMO_BASE_URL"] = base_url.rstrip("/")
    started = datetime.now(timezone.utc)
    monotonic_started = time.monotonic()
    runner = command_runner or _run_command
    try:
        completed = runner(
            command,
            cwd=root,
            env=environment,
            timeout=timeout_seconds,
        )
        exit_code = int(completed.returncode)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        status = "passed" if exit_code == 0 else "failed"
    except subprocess.TimeoutExpired as error:
        exit_code = 124
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr) + (
            f"\nExécution interrompue après {timeout_seconds} secondes."
        )
        status = "timeout"
    duration = round(time.monotonic() - monotonic_started, 3)
    stdout_path.write_text(stdout, encoding="utf-8", newline="\n")
    stderr_path.write_text(stderr, encoding="utf-8", newline="\n")
    collected, failed = _junit_counts(junit_path)
    report = ExecutionReport(
        schema_version=1,
        execution_id=str(uuid4()),
        status=status,
        exit_code=exit_code,
        started_at=started.isoformat(),
        duration_seconds=duration,
        test_path=relative_test,
        test_sha256=actual_test_sha256,
        manifest_sha256=_file_sha256(manifest_path),
        browser=browser,
        base_url=base_url.rstrip("/"),
        collected_case_count=collected,
        failed_case_count=failed,
        junit_path=junit_path.relative_to(root).as_posix(),
        artifact_directory=playwright_output.relative_to(root).as_posix(),
        stdout_path=stdout_path.relative_to(root).as_posix(),
        stderr_path=stderr_path.relative_to(root).as_posix(),
    )
    (resolved_output / "execution.json").write_text(
        json.dumps(
            report.as_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        timeout=timeout,
        check=False,
        capture_output=True,
        text=True,
        shell=False,
    )


def _junit_counts(path: Path) -> tuple[int, int]:
    if not path.is_file():
        return 0, 0
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return 0, 0
    if root.tag == "testsuite":
        suites = (root,)
    else:
        suites = tuple(root.findall("testsuite"))
    if not suites and root.tag == "testsuites":
        return (
            int(root.attrib.get("tests", "0")),
            int(root.attrib.get("failures", "0"))
            + int(root.attrib.get("errors", "0")),
        )
    collected = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    failed = sum(
        int(suite.attrib.get("failures", "0"))
        + int(suite.attrib.get("errors", "0"))
        for suite in suites
    )
    return collected, failed


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
