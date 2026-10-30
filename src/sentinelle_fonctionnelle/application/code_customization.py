"""Personnalisation contrôlée des fichiers de code générés.

Les marqueurs appartiennent au contrat du générateur. Le contenu situé entre
deux marqueurs peut être modifié ; toute autre différence est refusée.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


class CodeCustomizationError(ValueError):
    """Une personnalisation sort des zones autorisées ou devient incompatible."""


_START = re.compile(
    r"^(?P<indent>[ \t]*)# sentinelle:custom:start "
    r"(?P<name>[a-z][a-z0-9_-]*) contract=(?P<contract>[A-Za-z0-9_.-]+)[ \t]*$"
)
_END = re.compile(
    r"^(?P<indent>[ \t]*)# sentinelle:custom:end "
    r"(?P<name>[a-z][a-z0-9_-]*)[ \t]*$"
)


@dataclass(frozen=True, slots=True)
class ProtectedCodeRegion:
    name: str
    contract: str
    indent: str
    body: str
    start_line: int
    end_line: int

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.body.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class CustomizationMerge:
    content: str
    applied: tuple[str, ...]
    conflicts: tuple[str, ...]


def protected_regions(source: str) -> tuple[ProtectedCodeRegion, ...]:
    """Extrait les zones protégées et refuse les marqueurs ambigus."""

    lines = source.splitlines(keepends=True)
    regions: list[ProtectedCodeRegion] = []
    opened: tuple[re.Match[str], int] | None = None
    names: set[str] = set()
    for index, line in enumerate(lines):
        text = line.rstrip("\r\n")
        start = _START.fullmatch(text)
        end = _END.fullmatch(text)
        if start:
            if opened is not None:
                raise CodeCustomizationError(
                    "Les zones personnalisables ne peuvent pas être imbriquées."
                )
            if start.group("name") in names:
                raise CodeCustomizationError(
                    f"La zone personnalisable {start.group('name')} est dupliquée."
                )
            opened = (start, index)
            continue
        if end:
            if opened is None:
                raise CodeCustomizationError(
                    f"La fin de zone {end.group('name')} n'a pas de début."
                )
            start_match, start_index = opened
            if end.group("name") != start_match.group("name"):
                raise CodeCustomizationError(
                    "Les marqueurs de personnalisation ne correspondent pas."
                )
            if end.group("indent") != start_match.group("indent"):
                raise CodeCustomizationError(
                    "Les marqueurs d'une zone doivent avoir la même indentation."
                )
            name = start_match.group("name")
            regions.append(
                ProtectedCodeRegion(
                    name=name,
                    contract=start_match.group("contract"),
                    indent=start_match.group("indent"),
                    body="".join(lines[start_index + 1 : index]),
                    start_line=start_index,
                    end_line=index,
                )
            )
            names.add(name)
            opened = None
    if opened is not None:
        raise CodeCustomizationError(
            f"La zone {opened[0].group('name')} n'est pas refermée."
        )
    return tuple(regions)


def validate_customized_source(
    generated: str,
    customized: str,
) -> tuple[ProtectedCodeRegion, ...]:
    """Valide que seules les zones déclarées ont été modifiées."""

    generated_regions = protected_regions(generated)
    customized_regions = protected_regions(customized)
    if not generated_regions:
        raise CodeCustomizationError(
            "Ce fichier ne contient aucune zone personnalisable."
        )
    generated_contracts = tuple(
        (region.name, region.contract) for region in generated_regions
    )
    customized_contracts = tuple(
        (region.name, region.contract) for region in customized_regions
    )
    if generated_contracts != customized_contracts:
        raise CodeCustomizationError(
            "Les marqueurs ou contrats de personnalisation ont été modifiés."
        )
    if _skeleton(generated, generated_regions) != _skeleton(
        customized, customized_regions
    ):
        raise CodeCustomizationError(
            "Une modification a été détectée hors des zones personnalisables."
        )
    changed = tuple(
        customized_region
        for generated_region, customized_region in zip(
            generated_regions, customized_regions, strict=True
        )
        if generated_region.body != customized_region.body
    )
    if not changed:
        raise CodeCustomizationError("Aucune personnalisation n'a été détectée.")
    return changed


def merge_customized_source(
    generated: str,
    customized: str,
    *,
    region_names: tuple[str, ...] | None = None,
) -> CustomizationMerge:
    """Réapplique les zones compatibles sur une nouvelle génération."""

    generated_regions = protected_regions(generated)
    customized_regions = protected_regions(customized)
    generated_by_name = {region.name: region for region in generated_regions}
    customized_by_name = {region.name: region for region in customized_regions}
    replacements: dict[str, str] = {}
    applied: list[str] = []
    conflicts: list[str] = []
    selected_names = tuple(customized_by_name) if region_names is None else region_names
    for name in selected_names:
        custom_region = customized_by_name.get(name)
        if custom_region is None:
            conflicts.append(f"{name}: zone absente du candidat personnalisé")
            continue
        generated_region = generated_by_name.get(name)
        if generated_region is None:
            conflicts.append(f"{name}: zone absente de la nouvelle génération")
            continue
        if generated_region.contract != custom_region.contract:
            conflicts.append(
                f"{name}: contrat {custom_region.contract} devenu "
                f"{generated_region.contract}"
            )
            continue
        replacements[name] = custom_region.body
        applied.append(name)
    content = _replace_bodies(generated, generated_regions, replacements)
    return CustomizationMerge(
        content=content,
        applied=tuple(applied),
        conflicts=tuple(conflicts),
    )


def _skeleton(source: str, regions: tuple[ProtectedCodeRegion, ...]) -> str:
    return _replace_bodies(
        source,
        regions,
        {
            region.name: f"{region.indent}# sentinelle:custom:body\n"
            for region in regions
        },
    )


def _replace_bodies(
    source: str,
    regions: tuple[ProtectedCodeRegion, ...],
    replacements: dict[str, str],
) -> str:
    lines = source.splitlines(keepends=True)
    by_start = {region.start_line: region for region in regions}
    result: list[str] = []
    index = 0
    while index < len(lines):
        region = by_start.get(index)
        if region is None:
            result.append(lines[index])
            index += 1
            continue
        result.append(lines[index])
        body = replacements.get(region.name, region.body)
        if body and not body.endswith(("\n", "\r")):
            body += "\n"
        result.append(body)
        result.append(lines[region.end_line])
        index = region.end_line + 1
    return "".join(result)
