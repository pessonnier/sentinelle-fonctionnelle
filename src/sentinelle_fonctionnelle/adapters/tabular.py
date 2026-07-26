"""Lecture bornée de fichiers CSV et Excel Open XML sans calcul actif.

Références : EF-007.5, ACC-066.
"""

from __future__ import annotations

import csv
import hashlib
import io
import posixpath
import re
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree

from sentinelle_fonctionnelle.domain.tabular_data import (
    TabularDataError,
    TabularDataSet,
)


MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_UNCOMPRESSED_XLSX_BYTES = 10 * 1024 * 1024
MAX_COLUMNS = 50
MAX_ROWS = 1_000
MAX_CELL_CHARACTERS = 4_000
_SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/package/2006/relationships"
)
_OFFICE_RELATIONSHIP_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)


def parse_tabular_data(filename: str, content: bytes) -> TabularDataSet:
    normalized_filename = PurePosixPath(filename.replace("\\", "/")).name
    suffix = PurePosixPath(normalized_filename).suffix.casefold()
    if not content:
        raise TabularDataError("Le fichier de données est vide.")
    if len(content) > MAX_FILE_BYTES:
        raise TabularDataError("Le fichier dépasse la limite de 2 Mio.")
    if suffix == ".csv":
        rows = _read_csv(content)
    elif suffix == ".xlsx":
        rows = _read_xlsx(content)
    else:
        raise TabularDataError("Seuls les fichiers .csv et .xlsx sont acceptés.")
    headers, data_rows = _canonicalize(rows)
    return TabularDataSet.create(
        filename=normalized_filename,
        fingerprint=hashlib.sha256(content).hexdigest(),
        headers=headers,
        rows=data_rows,
    )


def _read_csv(content: bytes) -> tuple[tuple[str, ...], ...]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise TabularDataError("Le CSV doit être encodé en UTF-8.") from error
    if "\x00" in text:
        raise TabularDataError("Le CSV contient un caractère nul interdit.")
    try:
        dialect = csv.Sniffer().sniff(text[:8_192], delimiters=",;\t")
    except csv.Error:
        dialect = None
    try:
        reader = (
            csv.reader(io.StringIO(text, newline=""), dialect)
            if dialect is not None
            else csv.reader(io.StringIO(text, newline=""), delimiter=";")
        )
        return tuple(
            tuple(cell for cell in row)
            for row in reader
        )
    except csv.Error as error:
        raise TabularDataError(f"Le CSV est invalide : {error}.") from error


def _read_xlsx(content: bytes) -> tuple[tuple[str, ...], ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as error:
        raise TabularDataError("Le fichier XLSX n'est pas une archive valide.") from error
    with archive:
        members = archive.infolist()
        if len(members) > 200:
            raise TabularDataError("Le classeur XLSX contient trop de composants.")
        if sum(member.file_size for member in members) > MAX_UNCOMPRESSED_XLSX_BYTES:
            raise TabularDataError("Le contenu décompressé du XLSX dépasse 10 Mio.")
        names = {member.filename for member in members}
        if "xl/workbook.xml" not in names:
            raise TabularDataError("Le classeur XLSX ne contient pas de workbook.")
        shared_strings = _shared_strings(archive, names)
        worksheet_paths = _worksheet_paths(archive, names)
        for worksheet_path in worksheet_paths:
            rows = _worksheet_rows(
                archive.read(worksheet_path),
                shared_strings,
            )
            if any(any(cell.strip() for cell in row) for row in rows):
                return rows
    raise TabularDataError("Le classeur XLSX ne contient aucun onglet de données.")


def _shared_strings(
    archive: zipfile.ZipFile,
    names: set[str],
) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in names:
        return ()
    root = _xml_root(archive.read("xl/sharedStrings.xml"), "sharedStrings.xml")
    return tuple(
        "".join(text.text or "" for text in item.iter(f"{{{_SPREADSHEET_NS}}}t"))
        for item in root.findall(f"{{{_SPREADSHEET_NS}}}si")
    )


def _worksheet_paths(
    archive: zipfile.ZipFile,
    names: set[str],
) -> tuple[str, ...]:
    workbook = _xml_root(archive.read("xl/workbook.xml"), "workbook.xml")
    relationship_path = "xl/_rels/workbook.xml.rels"
    if relationship_path not in names:
        raise TabularDataError("Les relations du classeur XLSX sont absentes.")
    relationships = _xml_root(
        archive.read(relationship_path),
        "workbook.xml.rels",
    )
    targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships.findall(
            f"{{{_RELATIONSHIP_NS}}}Relationship"
        )
        if "Id" in relationship.attrib and "Target" in relationship.attrib
    }
    paths: list[str] = []
    sheets = workbook.find(f"{{{_SPREADSHEET_NS}}}sheets")
    if sheets is None:
        return ()
    for sheet in sheets.findall(f"{{{_SPREADSHEET_NS}}}sheet"):
        relationship_id = sheet.attrib.get(
            f"{{{_OFFICE_RELATIONSHIP_NS}}}id"
        )
        target = targets.get(relationship_id or "")
        if not target:
            continue
        normalized = (
            target.lstrip("/")
            if target.startswith("/")
            else posixpath.normpath(posixpath.join("xl", target))
        )
        if normalized in names and normalized.startswith("xl/worksheets/"):
            paths.append(normalized)
    return tuple(paths)


def _worksheet_rows(
    content: bytes,
    shared_strings: tuple[str, ...],
) -> tuple[tuple[str, ...], ...]:
    root = _xml_root(content, "worksheet")
    if root.find(f".//{{{_SPREADSHEET_NS}}}f") is not None:
        raise TabularDataError(
            "Les cellules contenant des formules Excel sont interdites."
        )
    result: list[tuple[str, ...]] = []
    sheet_data = root.find(f"{{{_SPREADSHEET_NS}}}sheetData")
    if sheet_data is None:
        return ()
    for row in sheet_data.findall(f"{{{_SPREADSHEET_NS}}}row"):
        values: dict[int, str] = {}
        for cell in row.findall(f"{{{_SPREADSHEET_NS}}}c"):
            reference = cell.attrib.get("r", "")
            column = _column_index(reference)
            if column is None:
                continue
            cell_type = cell.attrib.get("t", "")
            if cell_type == "inlineStr":
                value = "".join(
                    text.text or ""
                    for text in cell.iter(f"{{{_SPREADSHEET_NS}}}t")
                )
            else:
                raw = cell.findtext(f"{{{_SPREADSHEET_NS}}}v", default="")
                if cell_type == "s":
                    try:
                        value = shared_strings[int(raw)]
                    except (ValueError, IndexError) as error:
                        raise TabularDataError(
                            "Une chaîne partagée du XLSX est invalide."
                        ) from error
                elif cell_type == "b":
                    value = "true" if raw == "1" else "false"
                else:
                    value = raw
            values[column] = value
        width = max(values, default=0)
        result.append(tuple(values.get(index, "") for index in range(1, width + 1)))
    return tuple(result)


def _xml_root(content: bytes, label: str) -> ElementTree.Element:
    try:
        return ElementTree.fromstring(content)
    except ElementTree.ParseError as error:
        raise TabularDataError(f"Le composant XLSX {label} est invalide.") from error


def _column_index(reference: str) -> int | None:
    match = re.match(r"^([A-Za-z]+)\d+$", reference)
    if match is None:
        return None
    index = 0
    for character in match.group(1).upper():
        index = index * 26 + ord(character) - 64
    return index


def _canonicalize(
    raw_rows: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    rows = [tuple(cell.strip() for cell in row) for row in raw_rows]
    rows = [row for row in rows if any(row)]
    if not rows:
        raise TabularDataError("Le tableau est vide.")
    headers = rows[0]
    if len(headers) > MAX_COLUMNS:
        raise TabularDataError("Le tableau dépasse la limite de 50 colonnes.")
    if not headers or any(not header for header in headers):
        raise TabularDataError("Chaque colonne doit posséder un en-tête.")
    folded = tuple(header.casefold() for header in headers)
    if len(set(folded)) != len(folded):
        raise TabularDataError("Les en-têtes de colonnes doivent être uniques.")
    normalized_rows: list[tuple[str, ...]] = []
    for row in rows[1:]:
        if len(row) > len(headers) and any(row[len(headers) :]):
            raise TabularDataError(
                "Une ligne contient plus de cellules que l'en-tête."
            )
        normalized = (row + ("",) * len(headers))[: len(headers)]
        if any(len(cell) > MAX_CELL_CHARACTERS for cell in normalized):
            raise TabularDataError("Une cellule dépasse 4 000 caractères.")
        normalized_rows.append(normalized)
    if not normalized_rows:
        raise TabularDataError("Le tableau doit contenir au moins un cas.")
    if len(normalized_rows) > MAX_ROWS:
        raise TabularDataError("Le tableau dépasse la limite de 1 000 cas.")
    return headers, tuple(normalized_rows)
