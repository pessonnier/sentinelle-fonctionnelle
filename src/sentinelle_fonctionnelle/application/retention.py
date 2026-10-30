"""Rétention explicite et sûre des répertoires d'artefacts terminés."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil


class RetentionError(ValueError):
    """La politique ou une cible de suppression est ambiguë."""


@dataclass(frozen=True, slots=True)
class RetentionResult:
    expired: tuple[str, ...]
    removed: tuple[str, ...]
    ignored: tuple[str, ...]


def apply_artifact_retention(
    root_directory: Path,
    *,
    retention_days: int,
    now: datetime | None = None,
    apply: bool = False,
) -> RetentionResult:
    """Liste, ou supprime explicitement, les exécutions finalisées expirées."""

    if retention_days < 1:
        raise RetentionError("La durée de conservation doit être positive.")
    root = root_directory.resolve()
    if not root.is_dir():
        raise RetentionError("Le répertoire d'artefacts est introuvable.")
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=retention_days)
    expired: list[str] = []
    removed: list[str] = []
    ignored: list[str] = []
    for manifest_path in sorted(root.rglob("execution.json")):
        execution_dir = manifest_path.parent.resolve()
        if root not in execution_dir.parents:
            raise RetentionError("Une cible de rétention sort de la racine autorisée.")
        try:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            raw_date = document.get("finished_at") or document.get("started_at")
            occurred_at = datetime.fromisoformat(str(raw_date))
            if occurred_at.tzinfo is None:
                raise ValueError
        except (OSError, ValueError, json.JSONDecodeError):
            ignored.append(str(execution_dir))
            continue
        if occurred_at >= cutoff:
            continue
        expired.append(str(execution_dir))
        if apply:
            shutil.rmtree(execution_dir)
            removed.append(str(execution_dir))
    return RetentionResult(tuple(expired), tuple(removed), tuple(ignored))
