"""Export reproductible d'un candidat approuvé vers le contrat CI portable."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
from pathlib import PurePosixPath
from typing import Any, Mapping
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import yaml

from sentinelle_fonctionnelle.domain import CandidateStatus, TestCandidate


BUNDLE_FORMAT_VERSION = 1
_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


class BundleExportError(ValueError):
    """Le candidat ne peut pas être exporté sous une identité approuvée."""


@dataclass(frozen=True, slots=True)
class BundleArtifact:
    content: bytes
    manifest: Mapping[str, Any]

    @property
    def sha256(self) -> str:
        return str(self.manifest["bundle_sha256"])


def export_approved_candidate(
    candidate: TestCandidate,
    *,
    project_name: str,
    plan_name: str,
    case_name: str,
    specification: Mapping[str, Any] | None = None,
    environment: str = "development",
) -> BundleArtifact:
    """Construit un ZIP byte-à-byte stable, sans dépendre du service web."""

    _validate_approved_candidate(candidate)
    specification_document = dict(specification or {})
    case_id = str(candidate.case_id)
    declarations = _strings(
        candidate.manifest.get("ci_declaration")
        or specification_document.get("execution_declaration")
        or ("manual",)
    )
    files: dict[str, bytes] = {
        item.path: item.content.encode("utf-8") for item in candidate.files
    }
    files.update(
        _supporting_files(
            candidate,
            project_name=project_name,
            plan_name=plan_name,
            case_name=case_name,
            specification=specification_document,
            environment=environment,
            declarations=declarations,
        )
    )
    records = [
        {
            "path": path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content),
        }
        for path, content in sorted(files.items())
    ]
    bundle_sha256 = _canonical_sha256({"files": records})
    source_paths = sorted(item.path for item in candidate.files)
    manifest: dict[str, Any] = {
        "format": "sentinelle-functional-bundle",
        "format_version": BUNDLE_FORMAT_VERSION,
        "bundle_sha256": bundle_sha256,
        "project": {"id": str(candidate.project_id), "name": project_name},
        "test_plan": {
            "id": str(candidate.test_plan_id),
            "name": plan_name,
            "version": 1,
        },
        "cases": [
            {
                "id": case_id,
                "name": case_name,
                "version": candidate.specification_version,
                "type": str(candidate.manifest.get("test_type", "acceptance")),
                "status": CandidateStatus.APPROVED.value,
                "candidate_sha256": candidate.candidate_sha256,
                "specification_sha256": candidate.specification_sha256,
                "source_paths": source_paths,
                "source_sha256": [item.sha256 for item in candidate.files],
                "tags": _strings(candidate.manifest.get("tags")),
                "declarations": declarations,
            }
        ],
        "runtime": {
            "python": ">=3.12,<3.15",
            "pytest": ">=8,<10",
            "playwright": ">=1.55,<2",
            "runner_image": "sentinelle-fonctionnelle-runner:0.1.0",
        },
        "environment": environment,
        "llm_execution": "forbidden",
        "documentation": [
            "docs/functional.md",
            "docs/deploy-github-actions.md",
            "docs/deploy-gitlab-ci.md",
        ],
        "ci_templates": ["ci/github-actions.yml", "ci/gitlab-ci.yml"],
        "files": records,
    }
    files["sentinelle-manifest.json"] = _json_bytes(manifest)
    archive = BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, content in sorted(files.items()):
            info = ZipInfo(path, date_time=_ZIP_DATE)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, content, compresslevel=9)
    return BundleArtifact(content=archive.getvalue(), manifest=manifest)


def _validate_approved_candidate(candidate: TestCandidate) -> None:
    if candidate.status is not CandidateStatus.APPROVED:
        raise BundleExportError(
            "L'export CI exige un candidat approuvé après validation individuelle."
        )
    execution = candidate.latest_execution
    file_hashes = {item.sha256 for item in candidate.files}
    if (
        execution is None
        or not execution.passed
        or execution.test_sha256 not in file_hashes
    ):
        raise BundleExportError(
            "La dernière exécution réussie ne correspond pas aux fichiers approuvés."
        )
    for item in candidate.files:
        if hashlib.sha256(item.content.encode("utf-8")).hexdigest() != item.sha256:
            raise BundleExportError(f"Le fichier candidat a été altéré : {item.path}")


def _supporting_files(
    candidate: TestCandidate,
    *,
    project_name: str,
    plan_name: str,
    case_name: str,
    specification: Mapping[str, Any],
    environment: str,
    declarations: list[str],
) -> dict[str, bytes]:
    case_id = str(candidate.case_id)
    spec = {
        "id": case_id,
        "name": case_name,
        "version": candidate.specification_version,
        "status": "approved",
        "sha256": candidate.specification_sha256,
        **specification,
    }
    metadata = {
        "origin": candidate.origin.value,
        "candidate_sha256": candidate.candidate_sha256,
        "prompt_sha256": candidate.prompt_sha256 or None,
        "generator_version": candidate.manifest.get("generator_version", "0.1.0"),
        "model": candidate.manifest.get("model"),
    }
    docs = _functional_documentation(
        project_name, plan_name, case_name, spec, candidate, environment, declarations
    )
    return {
        "specifications/plan.yaml": _yaml_bytes(
            {"id": str(candidate.test_plan_id), "name": plan_name, "version": 1}
        ),
        "specifications/hierarchy.yaml": _yaml_bytes(
            {"plan": str(candidate.test_plan_id), "cases": [case_id]}
        ),
        f"specifications/cases/{case_id}.yaml": _yaml_bytes(spec),
        (
            f"generation/cases/{case_id}/{candidate.specification_version}/metadata.json"
        ): _json_bytes(metadata),
        (
            f"generation/cases/{case_id}/{candidate.specification_version}/sequence.jsonl"
        ): b"",
        "config/runner.json": _json_bytes(
            {
                "declaration": "manual",
                "browser": "chromium",
                "timeout_seconds": 300,
                "llm_execution": "forbidden",
                "allowed_origins": [],
            }
        ),
        "docs/functional.md": docs.encode("utf-8"),
        "docs/deploy-github-actions.md": _github_guide().encode("utf-8"),
        "docs/deploy-gitlab-ci.md": _gitlab_guide().encode("utf-8"),
        "ci/github-actions.yml": _github_actions().encode("utf-8"),
        "ci/gitlab-ci.yml": _gitlab_ci().encode("utf-8"),
        "requirements.lock": (
            "pytest>=8,<10\npytest-playwright>=0.7,<1\nplaywright>=1.55,<2\n"
        ).encode("utf-8"),
        "pytest.ini": b"[pytest]\ntestpaths = tests/cases\naddopts = --strict-config\n",
        ".gitignore": b"artifacts/\n",
        "README.md": _bundle_readme().encode("utf-8"),
    }


def _functional_documentation(
    project_name: str,
    plan_name: str,
    case_name: str,
    spec: Mapping[str, Any],
    candidate: TestCandidate,
    environment: str,
    declarations: list[str],
) -> str:
    objective = str(spec.get("objective") or "Objectif approuvé dans la définition")
    summary = str(spec.get("summary") or spec.get("description") or objective)
    return (
        f"# {plan_name}\n\n"
        f"Projet : **{project_name}**  \nEnvironnement logique : `{environment}`\n\n"
        "## Périmètre exporté\n\n"
        f"- {case_name} (cas `{candidate.case_id}`, version "
        f"{candidate.specification_version})\n\n"
        f"## {case_name}\n\n{summary}\n\n"
        f"Objectif : {objective}\n\n"
        f"État : approuvé — empreinte `{candidate.specification_sha256}`.\n\n"
        f"Déclarations CI : {', '.join(declarations)}.\n\n"
        "Les secrets et l'historique de conversation ne font pas partie de ce document.\n"
    )


def _bundle_readme() -> str:
    return """# Bundle Sentinelle Fonctionnelle

Ce répertoire est immuable pendant l'exécution. Les résultats sont écrits dans
un répertoire `artifacts/` frère.

```bash
python -m pip install -r requirements.lock
playwright install --with-deps chromium
sentinelle-run --bundle . --artifacts ../artifacts --base-url "$TARGET_BASE_URL" \
  --allow-origin "$TARGET_BASE_URL"
```
"""


def _github_actions() -> str:
    return """name: functional-tests
on:
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  sentinelle:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - name: Prepare artifacts
        run: mkdir -p artifacts && sudo chown 10001:10001 artifacts
      - name: Run approved bundle without PR secrets
        run: |
          docker run --rm --user=10001:10001 --read-only --cap-drop=ALL \
            --security-opt=no-new-privileges --pids-limit=256 --memory=2g --cpus=2 \
            --tmpfs /tmp:rw,noexec,nosuid,size=512m \
            -v "$PWD/sentinelle-bundle:/bundle:ro" \
            -v "$PWD/artifacts:/artifacts:rw" \
            -e TARGET_BASE_URL \
            sentinelle-fonctionnelle-runner:0.1.0 \
            --bundle /bundle --artifacts /artifacts --base-url "$TARGET_BASE_URL" \
            --allow-origin "$TARGET_BASE_URL" \
            --declaration on_merge_request
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: sentinelle-results
          path: artifacts/
"""


def _gitlab_ci() -> str:
    return """sentinelle-functional-tests:
  image:
    name: sentinelle-fonctionnelle-runner:0.1.0
    entrypoint: [""]
  variables:
    SENTINELLE_FONCTIONNELLE_DECLARATION: on_merge_request
  script:
    - mkdir -p artifacts
    - sentinelle-run --bundle ./sentinelle-bundle --artifacts ./artifacts --base-url "$TARGET_BASE_URL" --allow-origin "$TARGET_BASE_URL" --declaration "$SENTINELLE_FONCTIONNELLE_DECLARATION"
  artifacts:
    when: always
    reports:
      junit: artifacts/junit.xml
    paths:
      - artifacts/
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
"""


def _github_guide() -> str:
    return """# Déployer avec GitHub Actions

Copiez `ci/github-actions.yml` vers `.github/workflows/functional-tests.yml`.
Le workflow utilise l'image `sentinelle-fonctionnelle-runner:0.1.0`, monte le
bundle en lecture seule et publie `artifacts/`. Les pull requests ne reçoivent
aucun secret. Réservez les secrets GitHub et cibles sensibles à un environnement
protégé déclenché manuellement. Épinglez l'image par digest en production.

Validez d'abord avec `sentinelle-run --bundle . --artifacts ../artifacts
--base-url "$TARGET_BASE_URL" --allow-origin "$TARGET_BASE_URL"`. Un échec
d'empreinte exige un nouvel export ;
pour revenir en arrière, restaurez intégralement un ancien bundle versionné.
"""


def _gitlab_guide() -> str:
    return """# Déployer avec GitLab CI

Incluez `ci/gitlab-ci.yml` dans votre `.gitlab-ci.yml`. Le job utilise l'image
`sentinelle-fonctionnelle-runner:0.1.0`, écrit les résultats dans `artifacts/`
et publie `artifacts/junit.xml`. Les variables sensibles doivent être masquées
et protégées ; elles ne doivent pas être accessibles aux merge requests non
approuvées. Le runner GitLab doit être non privilégié, sans socket de runtime,
avec limites de ressources et egress limité à la cible. Épinglez l'image par
digest en production.

Testez la commande locale du README. Un échec d'empreinte impose un nouvel
export ; restaurez un bundle versionné complet pour revenir en arrière.
"""


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    return []


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    data = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _yaml_bytes(value: Mapping[str, Any]) -> bytes:
    return yaml.safe_dump(
        dict(value), allow_unicode=True, sort_keys=True, default_flow_style=False
    ).encode("utf-8")


def safe_bundle_path(path: str) -> PurePosixPath:
    candidate = PurePosixPath(path)
    if not path or candidate.is_absolute() or ".." in candidate.parts:
        raise BundleExportError(f"Chemin de bundle interdit : {path!r}")
    return candidate
