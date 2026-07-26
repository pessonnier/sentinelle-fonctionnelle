"""ACC-066 à ACC-068 — données CSV/XLSX et stratégies d'itération."""

from __future__ import annotations

import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from sentinelfonctionnelle.adapters.tabular import parse_tabular_data
from sentinelfonctionnelle.application import ProjectApplication
from sentinelfonctionnelle.domain import (
    DataIterationMode,
    HierarchyError,
    NodeKind,
    TabularDataError,
)


def _xlsx_bytes(
    rows: tuple[tuple[str, ...], ...],
    *,
    formula_cell: bool = False,
) -> bytes:
    """Construit le strict classeur Open XML requis par le test d'adaptateur."""

    def column_name(index: int) -> str:
        name = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            name = chr(65 + remainder) + name
        return name

    sheet_rows: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            reference = f"{column_name(column_index)}{row_index}"
            if formula_cell and row_index == 2 and column_index == 1:
                cells.append(
                    f'<c r="{reference}"><f>1+1</f><v>2</v></c>'
                )
            else:
                escaped = (
                    value.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                cells.append(
                    f'<c r="{reference}" t="inlineStr"><is><t>{escaped}</t></is></c>'
                )
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        workbook.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        workbook.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Données" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        )
        workbook.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""",
        )
        workbook.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>"""
            + "".join(sheet_rows)
            + """</sheetData>
</worksheet>""",
        )
    return stream.getvalue()


class TabularDataAcceptanceTests(unittest.TestCase):
    rows = (
        ("courriel", "profil", "montant"),
        ("alice@example.invalid", "standard", "10.50"),
        ("bob@example.invalid", "premium", "25"),
        ("chloe@example.invalid", "standard", "0"),
        ("david@example.invalid", "premium", "99.90"),
    )

    def test_csv_and_xlsx_produce_the_same_canonical_data(self) -> None:
        csv_content = (
            "\ufeffcourriel;profil;montant\r\n"
            '"alice@example.invalid";standard;10.50\r\n'
            '"bob@example.invalid";premium;25\r\n'
            '"chloe@example.invalid";standard;0\r\n'
            '"david@example.invalid";premium;99.90\r\n'
        ).encode()

        csv_data = parse_tabular_data("saisies.csv", csv_content)
        xlsx_data = parse_tabular_data("saisies.xlsx", _xlsx_bytes(self.rows))

        self.assertEqual(("courriel", "profil", "montant"), csv_data.headers)
        self.assertEqual(csv_data.headers, xlsx_data.headers)
        self.assertEqual(csv_data.rows, xlsx_data.rows)
        self.assertEqual(4, csv_data.row_count)
        self.assertNotEqual(csv_data.fingerprint, xlsx_data.fingerprint)

    def test_documented_excel_template_is_really_importable(self) -> None:
        template = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "examples"
            / "modele-donnees-tests.xlsx"
        )
        imported = parse_tabular_data(template.name, template.read_bytes())
        self.assertEqual(
            ("courriel", "profil", "montant", "actif", "date_reservation"),
            imported.headers,
        )
        self.assertEqual(5, imported.row_count)

    def test_invalid_and_active_excel_content_is_rejected(self) -> None:
        invalid_cases = (
            ("vide.csv", b""),
            ("sans-cas.csv", b"a;b\n"),
            ("doublon.csv", b"a;a\n1;2\n"),
            ("inconnu.json", b'{"a": 1}'),
            ("cassé.xlsx", b"not-a-zip"),
            ("formule.xlsx", _xlsx_bytes(self.rows, formula_cell=True)),
            ("trop-grand.csv", b"a;b\n" + b"x;y\n" * 400_000),
        )
        for filename, content in invalid_cases:
            with self.subTest(filename=filename):
                with self.assertRaises(TabularDataError):
                    parse_tabular_data(filename, content)

    def test_serial_parallel_random_plans_and_restart_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "sentinel.db"
            application = ProjectApplication.sqlite(database)
            project = application.create_project(
                None,
                name="Données",
                description="Itérations tabulaires",
                web_target="https://data.demo.invalid",
                security_policy="demo-only",
            )
            test_set = application.create_test_set(
                None,
                project_id=project.id,
                name="Connexion",
                objective="Exécuter plusieurs profils",
                test_type="acceptance",
                target="recette",
            )
            suite = application.add_node(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                kind=NodeKind.SUITE,
                name="Accès",
                objective="Vérifier les accès paramétrés",
            )
            test = application.add_node(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                kind=NodeKind.TEST,
                name="Connexion paramétrée",
                parent_id=suite.id,
            )
            data_set = parse_tabular_data(
                "saisies.xlsx",
                _xlsx_bytes(self.rows),
            )

            serial = application.bind_test_data(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                test_id=test.id,
                data_set=data_set,
                mode=DataIterationMode.SERIAL,
            )
            self.assertEqual((1, 2, 3, 4), serial.plan.source_indexes)
            self.assertEqual((1, 1, 1, 1), serial.plan.batch_sizes)

            parallel = application.bind_test_data(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                test_id=test.id,
                data_set=data_set,
                mode=DataIterationMode.PARALLEL,
                max_parallelism=3,
            )
            self.assertEqual((3, 1), parallel.plan.batch_sizes)

            random_first = application.bind_test_data(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                test_id=test.id,
                data_set=data_set,
                mode=DataIterationMode.RANDOM,
                random_seed=20260726,
                sample_count=3,
            )
            random_second = application.bind_test_data(
                None,
                project_id=project.id,
                test_set_id=test_set.id,
                test_id=test.id,
                data_set=data_set,
                mode=DataIterationMode.RANDOM,
                random_seed=20260726,
                sample_count=3,
            )
            self.assertEqual(
                random_first.plan.source_indexes,
                random_second.plan.source_indexes,
            )
            self.assertEqual(3, len(set(random_first.plan.source_indexes)))
            self.assertEqual(4, random_second.version)

            restarted = ProjectApplication.sqlite(database)
            restored = restarted.get_project(None, project.id).test_set(
                test_set.id
            ).node(test.id)
            self.assertEqual(4, restored.data_binding.version)
            self.assertEqual(DataIterationMode.RANDOM, restored.data_binding.mode)
            self.assertEqual(
                random_second.plan.source_indexes,
                restored.data_binding.plan.source_indexes,
            )
            self.assertEqual(data_set.fingerprint, restored.data_binding.data_set.fingerprint)

            with self.assertRaises(HierarchyError):
                application.bind_test_data(
                    None,
                    project_id=project.id,
                    test_set_id=test_set.id,
                    test_id=test.id,
                    data_set=data_set,
                    mode=DataIterationMode.PARALLEL,
                    max_parallelism=0,
                )


if __name__ == "__main__":
    unittest.main()
